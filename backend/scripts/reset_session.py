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
    
    # We will reset the status of the session for customer phone "919315860035"
    phone = "919315860035"
    res = db.chat_sessions.update_one(
        {"customer_phone": phone, "tenant_id": "luxury-furniture"},
        {"$set": {"status": "WAITING_FOR_BOT", "is_typing": False}}
    )
    if res.matched_count > 0:
        print(f"Success! Reset session status for {phone} to WAITING_FOR_BOT.")
    else:
        print(f"No session found for {phone}.")

if __name__ == "__main__":
    main()
