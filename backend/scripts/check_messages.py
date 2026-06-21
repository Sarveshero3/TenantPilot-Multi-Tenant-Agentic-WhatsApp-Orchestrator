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
    
    print("\n--- Sessions ---")
    sessions = list(db.chat_sessions.find())
    for s in sessions:
        print(f"Session ID: {s.get('_id')}, Tenant: {s.get('tenant_id')}, Phone: {s.get('customer_phone')}, Status: {s.get('status')}")

    print("\n--- Message Logs ---")
    messages = list(db.message_logs.find().sort("timestamp", 1))
    for m in messages:
        print(f"[{m.get('timestamp')}] {m.get('direction').upper()} | {m.get('sender')} | Type: {m.get('message_type')}")
        print(f"  Text: {m.get('text_content')}")
        if m.get('media_url'):
            print(f"  Media URL: {m.get('media_url')}")
            print(f"  Filename: {m.get('media_filename')}")
        if m.get('whatsapp_message_id'):
            print(f"  WhatsApp Message ID: {m.get('whatsapp_message_id')}")
        print("-" * 40)

if __name__ == "__main__":
    main()
