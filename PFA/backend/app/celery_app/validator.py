"""
Step 5: Validator - compiles generated tests and scores them.

Writes generated test code to a temp file, attempts javac compilation,
counts assertions, and produces a quality score.
"""
import os
import re
import tempfile
import subprocess
import logging
from typing import Dict, Any

from app.config import get_settings
from app.routers.metrics import COMPILATION_SUCCESS

settings = get_settings()
logger = logging.getLogger(__name__)


def _count_assertions(test_code: str) -> int:
    """Count assertion statements in the generated test."""
    patterns = [
        r'assert\w+\s*\(',
        r'assertThat\s*\(',
        r'verify\s*\(',
        r'verifyNoMoreInteractions\s*\(',
        r'@Test',
    ]
    count = 0
    for pattern in patterns[:4]:
        count += len(re.findall(pattern, test_code))
    return count


def _count_test_methods(test_code: str) -> int:
    """Count the number of @Test annotated methods."""
    return len(re.findall(r'@Test', test_code))


def _has_valid_structure(test_code: str) -> bool:
    """Check if the test code has a valid Java class structure."""
    has_class = bool(re.search(r'class\s+\w+', test_code))
    has_test = '@Test' in test_code
    has_import = 'import' in test_code
    return has_class and has_test and has_import


def _compile_test(test_code: str, class_name: str, source_dir: str = None) -> Dict[str, Any]:
    """
    Attempt to compile the generated test alongside target source files using javac.
    Includes JUnit 5 and Mockito JARs in the classpath.
    Returns compilation result.
    """
    class_match = re.search(r'class\s+(\w+)', test_code)
    test_class_name = class_match.group(1) if class_match else f"{class_name}Test"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, f"{test_class_name}.java")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_code)

            java_home = settings.jdk_home
            configured_javac = os.path.join(java_home, "bin", "javac") if java_home else ""
            javac = configured_javac if configured_javac and os.path.exists(configured_javac) else "javac"

            classpath_entries = [tmpdir]
            if source_dir:
                classpath_entries.append(source_dir)
            classpath_entries.append("/app/lib/*")
            classpath = ":".join(classpath_entries)

            java_files_to_compile = [test_file]
            if source_dir and os.path.exists(source_dir):
                for root, _, files in os.walk(source_dir):
                    for f in files:
                        if f.endswith(".java") and not f.endswith("Test.java"):
                            java_files_to_compile.append(os.path.join(root, f))

            cmd = [
                javac,
                "-nowarn",
                "-source", "17",
                "-target", "17",
                "-d", tmpdir,
                "-cp", classpath,
            ] + java_files_to_compile

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return {"compiled": True, "error": None}
            else:
                return {"compiled": False, "error": result.stderr[:2000]}

    except subprocess.TimeoutExpired:
        return {"compiled": False, "error": "Compilation timed out"}
    except FileNotFoundError:
        logger.warning("javac not found, skipping compilation check")
        return {"compiled": False, "error": "javac not available"}
    except Exception as e:
        return {"compiled": False, "error": str(e)[:500]}


def _calculate_score(
    compiled: bool,
    assertion_count: int,
    test_method_count: int,
    has_structure: bool,
) -> float:
    """
    Calculate a quality score 0-100 based on multiple factors.

    Weights:
      - Valid structure: 15 points
      - Compilation: 35 points
      - Test methods (up to 5): 25 points
      - Assertions (up to 10): 25 points
    """
    score = 0.0

    if has_structure:
        score += 15.0
    if compiled:
        score += 35.0

    method_score = min(test_method_count / 3.0, 1.0) * 25.0
    score += method_score

    assertion_score = min(assertion_count / 5.0, 1.0) * 25.0
    score += assertion_score

    return round(score, 1)


def validate_test(test_code: str, class_name: str, source_dir: str = None) -> Dict[str, Any]:
    """
    Validate a generated test:
      1. Check structure
      2. Count assertions and test methods
      3. Attempt compilation
      4. Calculate quality score

    Returns dict with: compiled, error, assertion_count, score
    """
    if not test_code or not test_code.strip():
        return {
            "compiled": False,
            "error": "Empty test code",
            "assertion_count": 0,
            "score": 0.0,
        }

    has_structure = _has_valid_structure(test_code)
    assertion_count = _count_assertions(test_code)
    test_method_count = _count_test_methods(test_code)

    compilation_result = _compile_test(test_code, class_name, source_dir)
    compiled = compilation_result["compiled"]

    COMPILATION_SUCCESS.labels(success=str(compiled).lower()).inc()

    score = _calculate_score(compiled, assertion_count, test_method_count, has_structure)

    logger.info(
        f"Validation for {class_name}: compiled={compiled}, "
        f"assertions={assertion_count}, tests={test_method_count}, score={score}"
    )

    return {
        "compiled": compiled,
        "error": compilation_result.get("error"),
        "assertion_count": assertion_count,
        "score": score,
    }