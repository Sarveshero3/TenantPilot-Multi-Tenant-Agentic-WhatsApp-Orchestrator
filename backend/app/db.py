"""
MongoDB connection and Beanie ODM initialisation.

Call `init_db()` from the FastAPI lifespan handler — not at import time.
All Beanie document models must be listed in `DOCUMENT_MODELS`.

Beanie 2.x requires `pymongo.AsyncMongoClient` (not motor's AsyncIOMotorClient).
"""

import logging
from pymongo import AsyncMongoClient
from beanie import init_beanie

from app.config import get_settings
from app.models.tenant import Tenant
from app.models.chat_session import ChatSession
from app.models.message_log import MessageLog

logger = logging.getLogger(__name__)

# Module-level client and connection state tracking
_client: AsyncMongoClient | None = None
_db_initialized: bool = False

# Ordered list of all Beanie document models that need to be registered
DOCUMENT_MODELS = [Tenant, ChatSession, MessageLog]


def is_db_connected() -> bool:
    """Check if the database has been successfully initialized."""
    return _db_initialized


async def init_db() -> None:
    """
    Initialise the pymongo AsyncMongoClient and Beanie ODM.
    Must be called once during application startup.
    """
    global _client, _db_initialized
    settings = get_settings()

    import certifi
    logger.info("Connecting to MongoDB: db=%s", settings.mongodb_db_name)
    _client = AsyncMongoClient(
        settings.mongodb_uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,  # Fail fast (5s) to allow retries
    )
    db = _client[settings.mongodb_db_name]

    # Initialize Beanie document models
    await init_beanie(database=db, document_models=DOCUMENT_MODELS)
    _db_initialized = True
    logger.info("Beanie ODM initialised successfully with %d document models", len(DOCUMENT_MODELS))


async def init_db_with_retry() -> None:
    """
    Try to initialize Beanie in the background with exponential backoff.
    This prevents database outages or handshake failures from crashing startup.
    """
    import asyncio
    delay = 1.0
    max_delay = 30.0

    while not _db_initialized:
        try:
            await init_db()
            break
        except Exception as exc:
            logger.error(
                "Database initialization failed. Retrying in %.1fs... Error: %s",
                delay,
                exc,
                exc_info=True,
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2.0, max_delay)


async def close_db() -> None:
    """
    Close the client gracefully.
    Must be called during application shutdown (FastAPI lifespan).
    """
    global _client, _db_initialized
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")
        _client = None
        _db_initialized = False

