import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.whatsapp.real_client import RealWhatsAppClient

async def main():
    settings = get_settings()
    # Check if access token is configured
    if not settings.whatsapp_access_token:
        print("Error: WHATSAPP_ACCESS_TOKEN is not set.")
        return
        
    client = RealWhatsAppClient(
        access_token=settings.whatsapp_access_token,
        api_version=settings.whatsapp_api_version,
        default_phone_number_id=settings.whatsapp_phone_number_id,
    )
    
    # We will send a test PDF to the user's number from the logs
    to_phone = "919315860035"
    pdf_url = "https://pdfobject.com/pdf/sample.pdf"
    filename = "Prestige-Home-Catalog-2025.pdf"
    
    print(f"Sending test PDF document to {to_phone}...")
    print(f"URL: {pdf_url}")
    print(f"Filename: {filename}")
    print(f"Phone Number ID: {settings.whatsapp_phone_number_id}")
    print(f"API Version: {settings.whatsapp_api_version}")
    
    try:
        res = await client.send_document(
            to=to_phone,
            document_url=pdf_url,
            filename=filename,
        )
        print("Success! WhatsApp API Response:")
        print(res)
    except Exception as e:
        print(f"Failed to send document: {e}")

if __name__ == "__main__":
    asyncio.run(main())
