"""Runs router - upload files, list runs, get run details & results."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.run import Run
from app.models.report import Report
from app.schemas.runs import RunResponse, RunListResponse, RunDetailResponse
from app.schemas.reports import ReportResponse, ReportListResponse
from app.services.auth_service import get_current_user
from app.services.run_service import save_upload, create_run, enqueue_run
from app.limiter import limiter

router = APIRouter(prefix="/api/runs", tags=["Runs"])


@router.post("/", response_model=RunResponse, status_code=201)
@limiter.limit("10/minute")
def create_new_run(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a .java or .zip file to start a new test generation run."""
    file_name, file_path = save_upload(file, current_user.id)
    run = create_run(db, current_user.id, file_name, file_path)

    # Enqueue Celery task
    celery_task_id = enqueue_run(run.id)
    run.celery_task_id = celery_task_id
    db.commit()
    db.refresh(run)

    return run


@router.get("/", response_model=RunListResponse)
def list_runs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Paginated list of runs for the current user."""
    query = db.query(Run).filter(Run.user_id == current_user.id)
    if status:
        query = query.filter(Run.status == status)

    total = query.count()
    runs = (
        query.order_by(Run.uploaded_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return RunListResponse(runs=runs, total=total, page=page, per_page=per_page)


@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single run's status and details."""
    run = db.query(Run).filter(Run.id == run_id, Run.user_id == current_user.id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/results", response_model=ReportListResponse)
def get_run_results(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get generated test reports for a completed run."""
    run = db.query(Run).filter(Run.id == run_id, Run.user_id == current_user.id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    reports = db.query(Report).filter(Report.run_id == run_id).all()
    return ReportListResponse(reports=reports, total=len(reports))
