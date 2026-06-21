import asyncio
import os
import sys
from pymongo import MongoClient

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings

def main():
    settings = get_settings()
    print("Connecting to MongoDB...", settings.mongodb_uri)
    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    
    print("\n--- Tenants ---")
    tenants = list(db.tenants.find())
    for t in tenants:
        print(f"Tenant: {t.get('tenant_id')} ({t.get('name')})")
        print("Media Library:")
        media = t.get("media_library", {})
        for key, item in media.items():
            print(f"  - {key}: type={item.get('media_type')}, url={item.get('url')}, filename={item.get('filename')}")
        print("-" * 40)

if __name__ == "__main__":
    main()
