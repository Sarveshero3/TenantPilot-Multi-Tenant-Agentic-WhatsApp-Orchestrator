"""Quick import smoke test — run with: python scripts\\test_imports.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.tenant import Tenant, MediaItem
from app.models.chat_session import ChatSession, SessionStatus
from app.models.message_log import MessageLog, MessageDirection, MessageType
from app.config import get_settings

print("OK: Tenant, MediaItem imported")
print("OK: ChatSession, SessionStatus imported")
print("OK: MessageLog, MessageDirection, MessageType imported")
print("OK: Settings imported")

# Validate pydantic schemas parse correctly
item = MediaItem(
    url="https://example.com/catalog.pdf",
    media_type="document",
    filename="catalog.pdf",
    description="Test catalog",
)
print("OK: MediaItem schema valid:", item.model_dump())

settings = get_settings()
print("OK: Settings loaded: env=%s, whatsapp_mode=%s" % (settings.app_env, settings.whatsapp_mode))

# Validate SessionStatus enum
assert SessionStatus.WAITING_FOR_BOT == "WAITING_FOR_BOT"
assert SessionStatus.NEEDS_HUMAN == "NEEDS_HUMAN"
print("OK: SessionStatus enum values correct")

# Validate MessageType enum
assert MessageType.TEXT == "text"
assert MessageType.IMAGE == "image"
assert MessageType.DOCUMENT == "document"
print("OK: MessageType enum values correct")

print("")
print("All imports and schema validations passed.")
