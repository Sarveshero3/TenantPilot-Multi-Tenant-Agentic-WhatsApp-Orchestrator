"""
TenantPilot FastAPI application entry point.

Lifecycle:
  startup  → init_db() (Beanie/Motor)
  shutdown → close_db()

Routers are mounted here; business logic lives in api/ and agent/ packages.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db, close_db

# ── Logging ───────────────────────────────────────────────────────────────────
settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Application lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events via the modern lifespan handler."""
    logger.info("TenantPilot starting up (env=%s)", settings.app_env)
    await init_db()
    yield
    logger.info("TenantPilot shutting down")
    await close_db()


# ── FastAPI application ───────────────────────────────────────────────────────
app = FastAPI(
    title="TenantPilot API",
    description="Multi-Tenant WhatsApp Agentic Orchestrator — backend API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    """Simple liveness probe — returns 200 if the process is running."""
    return {"status": "ok", "env": settings.app_env}


# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.webhook import router as webhook_router
from app.api.dashboard import router as dashboard_router

app.include_router(webhook_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


# ── Static files (production Docker build serves React frontend) ──────────────
import os
from pathlib import Path

_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
    logger.info("Serving frontend from %s", _static_dir)
