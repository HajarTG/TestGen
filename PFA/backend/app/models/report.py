"""Report ORM model - one report per generated test (per method)."""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False, index=True)
    class_name = Column(String(512), nullable=False)
    method_name = Column(String(512), nullable=False)
    method_source = Column(Text, nullable=True)
    strategy = Column(String(128), nullable=True)
    generated_test = Column(Text, nullable=True)
    compiled = Column(Boolean, default=False)
    compilation_error = Column(Text, nullable=True)
    assertion_count = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    gpt_tokens_used = Column(Integer, default=0)
    gpt_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    run = relationship("Run", back_populates="reports")

    def __repr__(self):
        return f"<Report id={self.id} class={self.class_name}.{self.method_name}>"
