"""Run Pydantic schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class RunCreate(BaseModel):
    """Created server-side after upload - not user-facing input."""
    file_name: str
    file_path: str


class RunResponse(BaseModel):
    id: int
    status: str
    file_name: str
    total_classes: int = 0
    total_methods: int = 0
    tests_generated: int = 0
    tests_compiled: int = 0
    uploaded_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    runs: List[RunResponse]
    total: int
    page: int
    per_page: int


class RunDetailResponse(RunResponse):
    result_path: Optional[str] = None
    celery_task_id: Optional[str] = None
