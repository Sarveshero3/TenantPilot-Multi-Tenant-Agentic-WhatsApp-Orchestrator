"""Fix tenant phone_number_ids in the database for live testing."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pymongo import AsyncMongoClient
from app.config import get_settings

REAL_PHONE_NUMBER_ID = "1202145532976125"

async def main():
    s = get_settings()
    c = AsyncMongoClient(s.mongodb_uri)
    db = c[s.mongodb_db_name]

    # Update Tenant A (luxury-furniture) to use the real phone number ID
    result = await db.tenants.update_one(
        {"tenant_id": "luxury-furniture"},
        {"$set": {"whatsapp_phone_number_id": REAL_PHONE_NUMBER_ID}},
    )
    print(f"luxury-furniture: matched={result.matched_count}, modified={result.modified_count}")

    # Verify
    async for t in db.tenants.find():
        print(f"  {t['tenant_id']} -> phone_number_id={t['whatsapp_phone_number_id']}")

asyncio.run(main())
