"""
Helper script to switch the Meta phone number routing to Tenant A or Tenant B.
Usage:
    py -3.11 backend/scripts/switch_tenant.py [luxury-furniture | automotive-care]
"""

from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pymongo import AsyncMongoClient
from app.config import get_settings

REAL_PHONE_NUMBER_ID = "1202145532976125"

async def switch_tenant(target_tenant_id: str):
    settings = get_settings()
    client = AsyncMongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    if target_tenant_id == "luxury-furniture":
        # Enable A, Disable B
        await db.tenants.update_one(
            {"tenant_id": "luxury-furniture"},
            {"$set": {"whatsapp_phone_number_id": REAL_PHONE_NUMBER_ID}},
        )
        await db.tenants.update_one(
            {"tenant_id": "automotive-care"},
            {"$set": {"whatsapp_phone_number_id": "PHONE_NUMBER_ID_TENANT_B"}},
        )
        print("Successfully routed Meta incoming webhook to Tenant A (luxury-furniture)")
    elif target_tenant_id == "automotive-care":
        # Enable B, Disable A
        await db.tenants.update_one(
            {"tenant_id": "automotive-care"},
            {"$set": {"whatsapp_phone_number_id": REAL_PHONE_NUMBER_ID}},
        )
        await db.tenants.update_one(
            {"tenant_id": "luxury-furniture"},
            {"$set": {"whatsapp_phone_number_id": "PHONE_NUMBER_ID_TENANT_A"}},
        )
        print("Successfully routed Meta incoming webhook to Tenant B (automotive-care)")
    else:
        print(f"Error: Unknown tenant ID '{target_tenant_id}'. Available options: luxury-furniture, automotive-care")
        sys.exit(1)

    # Print verification
    async for t in db.tenants.find():
        print(f"  {t['tenant_id']} -> whatsapp_phone_number_id={t['whatsapp_phone_number_id']}")

    client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Missing tenant ID argument.")
        print("Usage: py -3.11 backend/scripts/switch_tenant.py [luxury-furniture | automotive-care]")
        sys.exit(1)
    
    target = sys.argv[1]
    asyncio.run(switch_tenant(target))
