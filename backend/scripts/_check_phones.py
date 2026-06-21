import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pymongo import AsyncMongoClient
from app.config import get_settings

async def main():
    s = get_settings()
    c = AsyncMongoClient(s.mongodb_uri)
    db = c[s.mongodb_db_name]
    async for t in db.tenants.find():
        print(f"{t['tenant_id']} -> phone_number_id={t['whatsapp_phone_number_id']}")

asyncio.run(main())
