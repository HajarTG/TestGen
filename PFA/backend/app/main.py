"""
TestGen Platform - FastAPI Application Entry Point

Registers all routers, configures CORS, and adds Prometheus instrumentation.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import auth, runs, reports, metrics, health
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

app = FastAPI(
    title="TestGen Platform API",
    description="AI-powered JUnit test generation for Java projects",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---- Prometheus instrumentation (auto HTTP metrics) ----
Instrumentator().instrument(app).expose(app, endpoint="/api/prometheus")

# ---- Routers ----
app.include_router(auth.router)
app.include_router(runs.router)
app.include_router(reports.router)
app.include_router(metrics.router)
app.include_router(health.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "TestGen Platform",
        "version": "1.0.0",
        "docs": "/docs",
    }
