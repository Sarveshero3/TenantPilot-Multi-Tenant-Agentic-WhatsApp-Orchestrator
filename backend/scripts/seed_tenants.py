"""
Seed script — inserts the two demo tenants into MongoDB.

Usage (from the backend/ directory):
    python -m scripts.seed_tenants

Requires:
    - MONGODB_URI and MONGODB_DB_NAME set in .env (or environment)
    - MongoDB accessible (local or Atlas)

Safe to re-run: upserts on tenant_id, so no duplicates are created.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import os

# Allow running as a script from the backend/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pymongo import AsyncMongoClient
from beanie import init_beanie

from app.config import get_settings
from app.models.tenant import Tenant, MediaItem
from app.models.chat_session import ChatSession
from app.models.message_log import MessageLog

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Tenant A: Luxury Furniture Store ─────────────────────────────────────────
TENANT_A = {
    "tenant_id": "luxury-furniture",
    "name": "Prestige Home — Luxury Furniture",
    "whatsapp_phone_number_id": "1202145532976125",  # Replace with real ID
    "system_prompt": (
        "You are Aria, a sophisticated luxury furniture concierge for Prestige Home. "
        "Your tone is elegant, warm, and deeply knowledgeable about interior design and our collections. "
        "When a customer asks about specific furniture pieces, showroom visits, or requests a catalog, "
        "proactively offer to send the relevant catalog PDF or showroom imagery. "
        "Use the send_media tool to dispatch assets from our media library. "
        "Never discuss competitors. Keep responses concise but luxurious in feel. "
        "Available media keys: 'catalog' (full product catalog PDF), "
        "'sofa' (showroom sofa photo), 'dining' (dining collection image)."
    ),
    "media_library": {
        "catalog": MediaItem(
            url="https://pdfobject.com/pdf/sample.pdf",
            media_type="document",
            filename="Prestige-Home-Catalog-2025.pdf",
            description="Full luxury furniture product catalog, 48 pages, PDF format",
        ),
        "sofa": MediaItem(
            url="https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=1200",
            media_type="image",
            filename=None,
            description="Showroom photo of our signature Prestige Chesterfield sofa collection",
        ),
        "dining": MediaItem(
            url="https://images.unsplash.com/photo-1617098900591-3f90928e8c54?w=1200",
            media_type="image",
            filename=None,
            description="Showroom image of the Grand Dining Collection — marble table and chairs",
        ),
    },
}

# ── Tenant B: Automotive Care ─────────────────────────────────────────────────
TENANT_B = {
    "tenant_id": "automotive-care",
    "name": "AutoElite — Premium Car Care",
    "whatsapp_phone_number_id": "PHONE_NUMBER_ID_TENANT_B",  # Replace with real ID
    "system_prompt": (
        "You are Max, a professional automotive service advisor for AutoElite Car Care. "
        "You help customers schedule service appointments, answer questions about car maintenance, "
        "and send repair estimates or invoice sheets when requested. "
        "Be precise, professional, and reassuring about vehicle care. "
        "Use the send_media tool to dispatch documents and images when customers ask for them. "
        "Available media keys: 'invoice' (service invoice PDF), "
        "'repair-diagram' (brake system repair diagram), 'service-menu' (service pricing PDF)."
    ),
    "media_library": {
        "invoice": MediaItem(
            url="https://pdfobject.com/pdf/sample.pdf",
            media_type="document",
            filename="AutoElite-Service-Invoice.pdf",
            description="Standard service invoice sheet for completed repairs",
        ),
        "repair-diagram": MediaItem(
            url="https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=1200",
            media_type="image",
            filename=None,
            description="Brake system repair diagram showing inspection points",
        ),
        "service-menu": MediaItem(
            url="https://pdfobject.com/pdf/sample.pdf",
            media_type="document",
            filename="AutoElite-Service-Pricing-2025.pdf",
            description="Complete service menu with pricing for all maintenance packages",
        ),
    },
}


async def seed():
    settings = get_settings()
    logger.info("Connecting to MongoDB: %s / %s", settings.mongodb_uri[:40] + "...", settings.mongodb_db_name)

    import certifi
    client = AsyncMongoClient(settings.mongodb_uri, tlsCAFile=certifi.where())
    db = client[settings.mongodb_db_name]

    await init_beanie(database=db, document_models=[Tenant, ChatSession, MessageLog])

    # Purge old data to start fresh
    logger.info("Purging old collections (Tenants, ChatSessions, MessageLogs)...")
    await Tenant.find_all().delete()
    await ChatSession.find_all().delete()
    await MessageLog.find_all().delete()

    for tenant_data in [TENANT_A, TENANT_B]:
        existing = await Tenant.find_one(Tenant.tenant_id == tenant_data["tenant_id"])
        if existing:
            # Upsert: update in place
            existing.name = tenant_data["name"]
            existing.system_prompt = tenant_data["system_prompt"]
            existing.media_library = tenant_data["media_library"]
            existing.whatsapp_phone_number_id = tenant_data["whatsapp_phone_number_id"]
            await existing.save()
            logger.info("Updated existing tenant: %s", tenant_data["tenant_id"])
        else:
            tenant = Tenant(**tenant_data)
            await tenant.insert()
            logger.info("Inserted new tenant: %s", tenant_data["tenant_id"])

    count = await Tenant.count()
    logger.info("Seed complete. Total tenants in DB: %d", count)
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
