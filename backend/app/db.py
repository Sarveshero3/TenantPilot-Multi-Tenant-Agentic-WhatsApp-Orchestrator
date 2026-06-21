"""
MongoDB connection and Beanie ODM initialisation.

Call `init_db()` from the FastAPI lifespan handler — not at import time.
All Beanie document models must be listed in `DOCUMENT_MODELS`.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import get_settings
from app.models.tenant import Tenant
from app.models.chat_session import ChatSession
from app.models.message_log import MessageLog

logger = logging.getLogger(__name__)

# Module-level motor client (set during init_db, reused across requests)
_motor_client: AsyncIOMotorClient | None = None

# Ordered list of all Beanie document models that need to be registered
DOCUMENT_MODELS = [Tenant, ChatSession, MessageLog]


async def init_db() -> None:
    """
    Initialise the Motor client and Beanie ODM.
    Must be called once during application startup (FastAPI lifespan).
    """
    global _motor_client
    settings = get_settings()

    logger.info("Connecting to MongoDB: db=%s", settings.mongodb_db_name)
    _motor_client = AsyncIOMotorClient(settings.mongodb_uri)
    db = _motor_client[settings.mongodb_db_name]

    await init_beanie(database=db, document_models=DOCUMENT_MODELS)
    logger.info("Beanie ODM initialised with %d document models", len(DOCUMENT_MODELS))


async def close_db() -> None:
    """
    Close the Motor client gracefully.
    Must be called during application shutdown (FastAPI lifespan).
    """
    global _motor_client
    if _motor_client is not None:
        _motor_client.close()
        logger.info("MongoDB connection closed")
        _motor_client = None
