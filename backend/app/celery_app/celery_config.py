"""
Celery application configuration.
"""
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "testgen",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.celery_app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="testgen",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # 24 hours
)
