"""
MessageLog document model.

Collection: message_logs
Immutable audit trail — one document per message (inbound or outbound).
Never update or delete these documents; append only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document
from pydantic import Field
from pymongo import IndexModel, ASCENDING, DESCENDING


class MessageDirection(str, Enum):
    """Whether this message came from the customer or was sent by the bot."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageType(str, Enum):
    """
    The WhatsApp message content type.
    Matches the 'type' field used in Meta's Graph API payloads.
    """

    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"


class MessageLog(Document):
    """
    Immutable record of a single WhatsApp message in either direction.

    Inbound messages are logged by the Acknowledge node.
    Outbound messages are logged by the Dispatcher node after successful send.

    `session_id` is the string representation of ChatSession._id.
    This is intentionally a string (not a Link/DBRef) to keep reads simple
    and avoid N+1 fetch patterns on the dashboard message-history endpoint.
    """

    # ── Session reference ─────────────────────────────────────────────────────
    session_id: str = Field(
        description="str(ChatSession._id) — the parent conversation session"
    )
    tenant_id: str = Field(
        description="Denormalized from ChatSession for efficient per-tenant queries"
    )
    customer_phone: str = Field(
        description="Denormalized E.164 phone number for display and filtering"
    )

    # ── Direction & sender ────────────────────────────────────────────────────
    direction: MessageDirection = Field(
        description="'inbound' = customer sent it; 'outbound' = bot sent it"
    )
    sender: str = Field(
        description=(
            "Human-readable sender label: 'customer', 'bot', or 'system'. "
            "'system' is used for meta-events like handover notices."
        )
    )

    # ── Content ───────────────────────────────────────────────────────────────
    message_type: MessageType = Field(
        description="Content type — drives which UI component the dashboard renders"
    )
    text_content: Optional[str] = Field(
        default=None,
        description="Message body for TEXT messages; caption for IMAGE/DOCUMENT",
    )

    # ── Media fields (null for TEXT messages) ─────────────────────────────────
    media_url: Optional[str] = Field(
        default=None,
        description="Public URL of the image or document asset",
    )
    media_mime_type: Optional[str] = Field(
        default=None,
        description="MIME type, e.g. 'image/jpeg', 'application/pdf'",
    )
    media_filename: Optional[str] = Field(
        default=None,
        description="Filename shown to the WhatsApp user for document messages",
    )

    # ── WhatsApp message tracking ─────────────────────────────────────────────
    whatsapp_message_id: Optional[str] = Field(
        default=None,
        description=(
            "The 'id' returned by Meta's Graph API on successful send, "
            "or the 'id' from the inbound webhook payload. Used for read receipts."
        ),
    )

    # ── Timing ────────────────────────────────────────────────────────────────
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the message was received or sent",
    )

    class Settings:
        name = "message_logs"
        indexes = [
            # Primary dashboard query: all messages for a session, chronological
            IndexModel(
                [("session_id", ASCENDING), ("timestamp", ASCENDING)],
                name="session_timeline",
            ),
            # Per-tenant audit queries and message count dashboards
            IndexModel(
                [("tenant_id", ASCENDING), ("timestamp", DESCENDING)],
                name="tenant_recent_messages",
            ),
            # Look up a specific WhatsApp message by its Meta-assigned ID
            IndexModel(
                [("whatsapp_message_id", ASCENDING)],
                sparse=True,  # Many docs will have null here
                name="whatsapp_msg_id",
            ),
            # Filter inbound vs outbound across a tenant
            IndexModel(
                [("tenant_id", ASCENDING), ("direction", ASCENDING)],
                name="tenant_direction",
            ),
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "6676a1b2c3d4e5f6a7b8c9d0",
                "tenant_id": "luxury-furniture",
                "customer_phone": "+919876543210",
                "direction": "inbound",
                "sender": "customer",
                "message_type": "text",
                "text_content": "Can you send me your product catalog?",
                "media_url": None,
                "media_mime_type": None,
                "media_filename": None,
                "whatsapp_message_id": "wamid.HBgLOTE5ODc2NTQzMjEwFQIAERgSMzA5QkE5MzY5MkEwQjk5QTIA",
                "timestamp": "2025-06-21T11:00:00Z",
            }
        }
