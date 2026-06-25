"""Reports router - aggregate analytics and per-run metrics."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.run import Run
from app.models.report import Report
from app.models.metric import Metric
from app.schemas.reports import ReportResponse, ReportListResponse, RunMetricsResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/", response_model=ReportListResponse)
def list_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reports across all runs for the current user."""
    query = (
        db.query(Report)
        .join(Run, Report.run_id == Run.id)
        .filter(Run.user_id == current_user.id)
    )
    total = query.count()
    reports = (
        query.order_by(Report.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return ReportListResponse(reports=reports, total=total)


@router.get("/metrics/{run_id}", response_model=RunMetricsResponse)
def get_run_metrics(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregate metrics for a specific run."""
    run = db.query(Run).filter(Run.id == run_id, Run.user_id == current_user.id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    reports = db.query(Report).filter(Report.run_id == run_id).all()
    total_methods = len(reports)
    tests_compiled = sum(1 for r in reports if r.compiled)
    avg_score = sum((r.score or 0.0) for r in reports) / total_methods if total_methods > 0 else 0.0
    compilation_rate = (tests_compiled / total_methods * 100) if total_methods > 0 else 0.0
    total_tokens = sum(r.gpt_tokens_used for r in reports)
    total_cost = sum(r.gpt_cost_usd for r in reports)

    # Try to get timing from Metric table
    metric = db.query(Metric).filter(Metric.run_id == run_id).first()
    total_duration = metric.total_duration_s if metric else 0.0

    return RunMetricsResponse(
        run_id=run_id,
        total_classes=run.total_classes,
        total_methods=total_methods,
        tests_generated=total_methods,
        tests_compiled=tests_compiled,
        avg_score=round(avg_score, 2),
        compilation_rate=round(compilation_rate, 1),
        total_gpt_tokens=total_tokens,
        total_gpt_cost_usd=round(total_cost, 4),
        total_duration_s=round(total_duration, 2),
    )


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Quick dashboard summary stats for the current user."""
    total_runs = db.query(Run).filter(Run.user_id == current_user.id).count()
    completed_runs = (
        db.query(Run)
        .filter(Run.user_id == current_user.id, Run.status == "completed")
        .count()
    )
    total_reports = (
        db.query(Report)
        .join(Run, Report.run_id == Run.id)
        .filter(Run.user_id == current_user.id)
        .count()
    )
    compiled_reports = (
        db.query(Report)
        .join(Run, Report.run_id == Run.id)
        .filter(Run.user_id == current_user.id, Report.compiled == True)
        .count()
    )
    avg_score_result = (
        db.query(func.avg(Report.score))
        .join(Run, Report.run_id == Run.id)
        .filter(Run.user_id == current_user.id)
        .scalar()
    )
    total_cost = (
        db.query(func.sum(Report.gpt_cost_usd))
        .join(Run, Report.run_id == Run.id)
        .filter(Run.user_id == current_user.id)
        .scalar()
    ) or 0.0

    return {
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "total_tests_generated": total_reports,
        "total_tests_compiled": compiled_reports,
        "compilation_rate": round((compiled_reports / total_reports * 100) if total_reports > 0 else 0.0, 1),
        "compilation_success_rate": round((compiled_reports / total_reports * 100) if total_reports > 0 else 0.0, 1),
        "avg_score": round(avg_score_result or 0.0, 2),
        "total_gpt_cost_usd": round(total_cost, 4),
    }
