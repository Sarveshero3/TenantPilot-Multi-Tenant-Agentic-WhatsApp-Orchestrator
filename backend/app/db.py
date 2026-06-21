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

# Module-level client (set during init_db, reused across requests)
_client: AsyncMongoClient | None = None

# Ordered list of all Beanie document models that need to be registered
DOCUMENT_MODELS = [Tenant, ChatSession, MessageLog]


async def init_db() -> None:
    """
    Initialise the pymongo AsyncMongoClient and Beanie ODM.
    Must be called once during application startup (FastAPI lifespan).
    """
    global _client
    settings = get_settings()

    logger.info("Connecting to MongoDB: db=%s", settings.mongodb_db_name)
    _client = AsyncMongoClient(settings.mongodb_uri)
    db = _client[settings.mongodb_db_name]

    await init_beanie(database=db, document_models=DOCUMENT_MODELS)
    logger.info("Beanie ODM initialised with %d document models", len(DOCUMENT_MODELS))


async def close_db() -> None:
    """
    Close the client gracefully.
    Must be called during application shutdown (FastAPI lifespan).
    """
    global _client
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")
        _client = None
