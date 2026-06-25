"""Report & Metrics Pydantic schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ReportResponse(BaseModel):
    id: int
    run_id: int
    class_name: str
    method_name: str
    method_source: Optional[str] = None
    strategy: Optional[str] = None
    generated_test: Optional[str] = None
    compiled: bool = False
    compilation_error: Optional[str] = None
    assertion_count: int = 0
    score: float = 0.0
    gpt_tokens_used: int = 0
    gpt_cost_usd: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int


class RunMetricsResponse(BaseModel):
    run_id: int
    total_classes: int = 0
    total_methods: int = 0
    tests_generated: int = 0
    tests_compiled: int = 0
    avg_score: float = 0.0
    compilation_rate: float = 0.0
    total_gpt_tokens: int = 0
    total_gpt_cost_usd: float = 0.0
    total_duration_s: float = 0.0

    model_config = {"from_attributes": True}
