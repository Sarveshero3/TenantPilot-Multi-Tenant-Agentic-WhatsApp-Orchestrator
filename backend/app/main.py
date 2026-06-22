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
from app.db import init_db_with_retry, close_db, is_db_connected

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
    import asyncio
    logger.info("TenantPilot starting up (env=%s)", settings.app_env)
    
    # Run database connection and Beanie initialization in the background.
    # This prevents database connection timeouts or TLS handshake failures
    # from blocking port binding and crashing the container startup.
    asyncio.create_task(init_db_with_retry())
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


# ── Global Exception Handlers ─────────────────────────────────────────────────
from fastapi.responses import JSONResponse
from fastapi import Request, status

@app.exception_handler(Exception)
async def global_beanie_exception_handler(request: Request, exc: Exception):
    """
    Handle Beanie initialization errors gracefully.
    If database queries are run before initialization finishes, return 503.
    """
    exc_type_name = type(exc).__name__
    if exc_type_name in ("CollectionWasNotInitialized", "MongoDBInitError") or "not initialized" in str(exc).lower():
        logger.warning("Database query failed because DB is not initialized yet: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": "Database connection is not established yet. Please try again shortly."
            }
        )
    # Default fallback
    logger.error("Unhandled server error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "message": "Internal server error occurred."}
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
    """
    Resilient liveness probe.
    Returns 200 OK even if database is disconnected to prevent Cloud Run from killing the container.
    """
    db_connected = is_db_connected()
    return {
        "status": "ok" if db_connected else "degraded",
        "env": settings.app_env,
        "database": "connected" if db_connected else "connecting"
    }


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
