"""Run ORM model - represents a single test-generation job."""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    STRATEGIZING = "strategizing"
    RETRIEVING = "retrieving"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(
        SAEnum(RunStatus, values_callable=lambda x: [e.value for e in x]),
        default=RunStatus.PENDING,
        nullable=False,
    )
    file_name = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    result_path = Column(String(1024), nullable=True)
    error_message = Column(Text, nullable=True)
    total_classes = Column(Integer, default=0)
    total_methods = Column(Integer, default=0)
    tests_generated = Column(Integer, default=0)
    tests_compiled = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    celery_task_id = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="runs")
    reports = relationship("Report", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Run id={self.id} status={self.status}>"
