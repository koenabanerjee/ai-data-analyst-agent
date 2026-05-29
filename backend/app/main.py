"""
app/main.py — FastAPI application entry point
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models.database import init_db
from app.routes import analysis, datasets, query, report, upload
from app.utils.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Data Analyst Agent API (env=%s)", settings.app_env)
    await init_db()
    logger.info("Database initialised")
    yield
    logger.info("Shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Data Analyst Agent",
    description="Agentic AI system for automated EDA, statistical insights, and intelligent reporting.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware: request timing ────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time(request: Request, call_next):
    t0 = time.monotonic()
    response = await call_next(request)
    elapsed = (time.monotonic() - t0) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.1f}"
    return response


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(upload.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "1.0.0", "env": settings.app_env}


@app.get("/", tags=["system"])
async def root():
    return {
        "name": "AI Data Analyst Agent",
        "version": "1.0.0",
        "docs": "/docs",
    }

from app.config import get_settings

settings = get_settings()
print("API KEY:", settings.google_api_key)