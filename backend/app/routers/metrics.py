"""Prometheus metrics endpoint - custom application metrics."""
from fastapi import APIRouter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

router = APIRouter(tags=["Metrics"])

# ----- Custom Prometheus metrics -----
RUNS_TOTAL = Counter(
    "testgen_runs_total",
    "Total test generation runs",
    ["status"],
)
RUN_DURATION = Histogram(
    "testgen_run_duration_seconds",
    "Duration of test generation runs",
    buckets=[5, 10, 30, 60, 120, 300, 600],
)
GPT_CALLS = Counter(
    "testgen_gpt_calls_total",
    "Total GPT API calls made",
)
GPT_TOKENS = Counter(
    "testgen_gpt_tokens_total",
    "Total GPT tokens consumed",
    ["type"],  # prompt / completion
)
COMPILATION_SUCCESS = Counter(
    "testgen_compilation_success_total",
    "Compilation results",
    ["success"],
)
ERRORS_TOTAL = Counter(
    "testgen_errors_total",
    "Total errors by type",
    ["error_type"],
)
CELERY_QUEUE_LENGTH = Gauge(
    "testgen_celery_queue_length",
    "Current Celery queue depth",
)


@router.get("/metrics")
def prometheus_metrics():
    """Expose Prometheus metrics at /metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
