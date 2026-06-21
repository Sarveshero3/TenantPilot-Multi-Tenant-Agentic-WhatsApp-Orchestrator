"""Send a test text message to verify outbound works with the new token."""
import asyncio, sys, os, httpx
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import get_settings

async def main():
    s = get_settings()
    url = f"https://graph.facebook.com/{s.whatsapp_api_version}/{s.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {s.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": "919315860035",
        "type": "text",
        "text": {"body": "Hello from TenantPilot! Your webhook is working. Reply to this message to start testing."},
    }
    print(f"API version: {s.whatsapp_api_version}")
    print(f"Token prefix: {s.whatsapp_access_token[:20]}...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

asyncio.run(main())
