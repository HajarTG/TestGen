"""Metric ORM model - aggregate metrics per run for dashboard/analytics."""
import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from app.database import Base


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False, index=True)
    total_methods = Column(Integer, default=0)
    tests_generated = Column(Integer, default=0)
    tests_compiled = Column(Integer, default=0)
    avg_score = Column(Float, default=0.0)
    total_gpt_tokens = Column(Integer, default=0)
    total_gpt_cost_usd = Column(Float, default=0.0)
    analysis_duration_s = Column(Float, default=0.0)
    generation_duration_s = Column(Float, default=0.0)
    validation_duration_s = Column(Float, default=0.0)
    total_duration_s = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Metric id={self.id} run_id={self.run_id}>"
