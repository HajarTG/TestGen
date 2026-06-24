"""
Main Celery task - orchestrates the 5-step test generation pipeline.

Steps:
  1. Java Analysis  (java_analyzer)
  2. Strategy Selection (strategy_selector)
  3. RAG Retrieval  (rag_pipeline)
  4. Prompt Building + GPT  (prompt_builder)
  5. Validation + Save  (validator)
"""
import time
import logging
from datetime import datetime

from app.celery_app.celery_config import celery_app
from app.database import SessionLocal
from app.models.run import Run, RunStatus
from app.models.report import Report
from app.models.metric import Metric
from app.routers.metrics import (
    RUNS_TOTAL, RUN_DURATION, ERRORS_TOTAL,
)

logger = logging.getLogger(__name__)

import re

def _fix_checked_exception_signatures(test_code: str) -> str:
    """
    Post-process generated test code to add 'throws Exception' to any
    @Test method that calls verify() or when() on methods that may declare
    checked exceptions, preventing javac 'unreported exception' errors.
    """
    lines = test_code.split("\n")
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Find @Test annotation
        if line.strip() == "@Test":
            fixed_lines.append(line)
            i += 1
            # Look at the method signature on the next non-empty line
            while i < len(lines) and lines[i].strip() == "":
                fixed_lines.append(lines[i])
                i += 1
            if i < len(lines):
                method_line = lines[i]
                # If method signature doesn't already declare throws, add it
                if ("void " in method_line and
                    "throws" not in method_line and
                    method_line.strip().endswith("{")):
                    method_line = method_line.replace(") {", ") throws Exception {")
                fixed_lines.append(method_line)
                i += 1
        else:
            fixed_lines.append(line)
            i += 1
    return "\n".join(fixed_lines)

def _fix_missing_imports(test_code: str) -> str:
    """
    Post-process generated test code to add missing common imports
    that the LLM frequently forgets.
    """
    additions = []

    if "UUID" in test_code and "import java.util.UUID;" not in test_code:
        additions.append("import java.util.UUID;")
    if "Arrays" in test_code and "import java.util.Arrays;" not in test_code:
        additions.append("import java.util.Arrays;")
    if "List" in test_code and "import java.util.List;" not in test_code:
        additions.append("import java.util.List;")
    if "Collections" in test_code and "import java.util.Collections;" not in test_code:
        additions.append("import java.util.Collections;")
    if "ArgumentCaptor" in test_code and "import org.mockito.ArgumentCaptor;" not in test_code:
        additions.append("import org.mockito.ArgumentCaptor;")

    if not additions:
        return test_code

    # Insert missing imports after the last existing import line
    lines = test_code.split("\n")
    last_import_idx = 0
    for idx, line in enumerate(lines):
        if line.strip().startswith("import "):
            last_import_idx = idx

    for imp in additions:
        lines.insert(last_import_idx + 1, imp)

    return "\n".join(lines)


def _update_status(db, run_id: int, status: RunStatus, **kwargs):
    run = db.query(Run).filter(Run.id == run_id).first()
    if run:
        run.status = status
        for k, v in kwargs.items():
            if hasattr(run, k):
                setattr(run, k, v)
        db.commit()


@celery_app.task(bind=True, name="generate_tests", max_retries=2)
def generate_tests(self, run_id: int):
    """Master orchestrator for test generation."""
    db = SessionLocal()
    t_start = time.time()

    try:
        run = db.query(Run).filter(Run.id == run_id).first()
        if not run:
            logger.error(f"Run {run_id} not found")
            return {"error": "Run not found"}

        # ---------- STEP 1: Java Analysis ----------
        _update_status(db, run_id, RunStatus.ANALYZING, started_at=datetime.utcnow())
        logger.info(f"[Run {run_id}] Step 1: Analyzing Java code...")

        from app.celery_app.java_analyzer import analyze_java_code
        t1 = time.time()
        code_model = analyze_java_code(run.file_path)
        analysis_duration = time.time() - t1

        total_classes = len(code_model.get("classes", []))
        total_methods = sum(len(c.get("methods", [])) for c in code_model.get("classes", []))
        _update_status(db, run_id, RunStatus.ANALYZING,
                       total_classes=total_classes, total_methods=total_methods)

        # ---------- STEP 2: Strategy Selection ----------
        _update_status(db, run_id, RunStatus.STRATEGIZING)
        logger.info(f"[Run {run_id}] Step 2: Selecting strategies...")

        from app.celery_app.strategy_selector import select_strategies
        strategies = select_strategies(code_model)

        # ---------- STEP 3: RAG Retrieval ----------
        _update_status(db, run_id, RunStatus.RETRIEVING)
        logger.info(f"[Run {run_id}] Step 3: RAG retrieval...")

        from app.celery_app.rag_pipeline import embed_and_retrieve
        rag_contexts = embed_and_retrieve(code_model)

        # ---------- STEP 4: Prompt Building + GPT ----------
        _update_status(db, run_id, RunStatus.GENERATING)
        logger.info(f"[Run {run_id}] Step 4: Generating tests with GPT...")

        from app.celery_app.prompt_builder import generate_test_for_method
        t4 = time.time()
        generated_tests = []

        for cls in code_model.get("classes", []):
            class_name = cls.get("name", "Unknown")
            for method in cls.get("methods", []):
                method_name = method.get("name", "unknown")
                key = f"{class_name}.{method_name}"
                strategy = strategies.get(key, "unit_test")
                rag_context = rag_contexts.get(key, "")

                result = generate_test_for_method(
                    class_name=class_name,
                    method=method,
                    strategy=strategy,
                    rag_context=rag_context,
                    class_source=cls.get("source", ""),
                )
                # Post-process to fix unreported checked exception errors
                test_code = _fix_checked_exception_signatures(
                    result.get("test_code", "")
                )
                test_code = _fix_missing_imports(test_code)
                generated_tests.append({
                    "class_name": class_name,
                    "method_name": method_name,
                    "method_source": method.get("source", ""),
                    "strategy": strategy,
                    "generated_test": test_code,
                    "tokens_used": result.get("tokens_used", 0),
                    "cost_usd": result.get("cost_usd", 0.0),
                })


        generation_duration = time.time() - t4

        # ---------- STEP 5: Validation + Save ----------
        _update_status(db, run_id, RunStatus.VALIDATING)
        logger.info(f"[Run {run_id}] Step 5: Validating generated tests...")

        from app.celery_app.validator import validate_test
        t5 = time.time()
        tests_compiled = 0
        validation_scores = []

        for test in generated_tests:
            validation = validate_test(test["generated_test"], test["class_name"], source_dir=run.file_path)

            report = Report(
                run_id=run_id,
                class_name=test["class_name"],
                method_name=test["method_name"],
                method_source=test["method_source"],
                strategy=test["strategy"],
                generated_test=test["generated_test"],
                compiled=validation["compiled"],
                compilation_error=validation.get("error"),
                assertion_count=validation.get("assertion_count", 0),
                score=validation.get("score", 0.0),
                gpt_tokens_used=test["tokens_used"],
                gpt_cost_usd=test["cost_usd"],
            )
            db.add(report)
            validation_scores.append(validation.get("score", 0.0))
            if validation["compiled"]:
                tests_compiled += 1

        validation_duration = time.time() - t5
        total_duration = time.time() - t_start

        # Save aggregate metrics
        metric = Metric(
            run_id=run_id,
            total_methods=total_methods,
            tests_generated=len(generated_tests),
            tests_compiled=tests_compiled,
            avg_score=sum(validation_scores) / max(len(validation_scores), 1),
            total_gpt_tokens=sum(t["tokens_used"] for t in generated_tests),
            total_gpt_cost_usd=sum(t["cost_usd"] for t in generated_tests),
            analysis_duration_s=analysis_duration,
            generation_duration_s=generation_duration,
            validation_duration_s=validation_duration,
            total_duration_s=total_duration,
        )
        db.add(metric)

        _update_status(
            db, run_id, RunStatus.COMPLETED,
            tests_generated=len(generated_tests),
            tests_compiled=tests_compiled,
            completed_at=datetime.utcnow(),
        )
        db.commit()

        # Prometheus metrics
        RUNS_TOTAL.labels(status="completed").inc()
        RUN_DURATION.observe(total_duration)

        logger.info(f"[Run {run_id}] Completed: {len(generated_tests)} tests, {tests_compiled} compiled")
        return {
            "run_id": run_id,
            "status": "completed",
            "tests_generated": len(generated_tests),
            "tests_compiled": tests_compiled,
            "duration_s": round(total_duration, 2),
        }

    except Exception as e:
        logger.exception(f"[Run {run_id}] Failed: {e}")
        from celery.exceptions import MaxRetriesExceededError
        try:
            # Retry automatically on failure, Celery will raise MaxRetriesExceededError when limit is reached
            self.retry(exc=e, countdown=10)
        except MaxRetriesExceededError:
            _update_status(db, run_id, RunStatus.FAILED, error_message=str(e))
            db.commit()
            RUNS_TOTAL.labels(status="failed").inc()
            ERRORS_TOTAL.labels(error_type=type(e).__name__).inc()
            raise e
    finally:
        db.close()
