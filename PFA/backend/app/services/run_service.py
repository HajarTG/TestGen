"""Run service - handles file upload, run creation, and Celery dispatch."""
import os
import uuid
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.config import get_settings
from app.models.run import Run, RunStatus

settings = get_settings()


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def save_upload(file: UploadFile, user_id: int) -> Tuple[str, str]:
    """
    Save an uploaded .java or .zip file to disk.
    Returns (original_filename, saved_path).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".java", ".zip"):
        raise HTTPException(status_code=400, detail="Only .java and .zip files are accepted")

    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    # Create unique directory for this upload
    upload_id = uuid.uuid4().hex[:12]
    upload_dir = os.path.join(settings.upload_dir, str(user_id), upload_id)
    _ensure_dir(upload_dir)

    saved_path = os.path.join(upload_dir, file.filename)
    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # If zip, extract it
    if ext == ".zip":
        extract_dir = os.path.abspath(os.path.join(upload_dir, "src"))
        _ensure_dir(extract_dir)
        try:
            with zipfile.ZipFile(saved_path, "r") as zf:
                # 1. Total size limit check (prevent ZIP bomb)
                total_size = 0
                max_extracted_bytes = settings.max_upload_size_mb * 5 * 1024 * 1024  # 5x max upload size
                for info in zf.infolist():
                    total_size += info.file_size
                    if total_size > max_extracted_bytes:
                        raise HTTPException(
                            status_code=400,
                            detail="ZIP extracted contents exceed maximum size limit"
                        )
                    # 2. Path traversal check (Zip Slip)
                    target_path = os.path.abspath(os.path.join(extract_dir, info.filename))
                    if os.path.commonpath([extract_dir, target_path]) != extract_dir:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Illegal path in ZIP file: {info.filename}"
                        )
                zf.extractall(extract_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file")
        # Point to extracted directory
        return file.filename, extract_dir

    return file.filename, upload_dir


def create_run(db: Session, user_id: int, file_name: str, file_path: str) -> Run:
    """Create a new Run record in the database."""
    run = Run(
        user_id=user_id,
        status=RunStatus.PENDING,
        file_name=file_name,
        file_path=file_path,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_run_status(db: Session, run_id: int, status: RunStatus, **kwargs):
    """Update run status and optional fields."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        return
    run.status = status
    for key, value in kwargs.items():
        if hasattr(run, key):
            setattr(run, key, value)
    if status == RunStatus.COMPLETED or status == RunStatus.FAILED:
        run.completed_at = datetime.utcnow()
    db.commit()


def enqueue_run(run_id: int) -> str:
    """Send the run to Celery for processing. Returns the Celery task ID."""
    from app.celery_app.tasks import generate_tests
    result = generate_tests.delay(run_id)
    return result.id
