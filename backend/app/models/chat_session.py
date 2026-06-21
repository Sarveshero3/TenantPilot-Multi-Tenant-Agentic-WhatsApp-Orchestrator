"""
ChatSession document model.

Collection: chat_sessions
One document per (tenant_id, customer_phone) pair.
Upserted by the Acknowledge node each time a new inbound message arrives.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from beanie import Document, Indexed
from pydantic import Field
from pymongo import IndexModel, ASCENDING


class SessionStatus(str, Enum):
    """
    Lifecycle status of a chat session.

    WAITING_FOR_BOT  — customer sent a message; bot hasn't started yet
    AGENT_RESPONDING — LangGraph pipeline is actively running for this session
    RESOLVED         — conversation concluded (bot or human closed it)
    NEEDS_HUMAN      — (bonus) LLM detected frustration; halts auto-replies
    """

    WAITING_FOR_BOT = "WAITING_FOR_BOT"
    AGENT_RESPONDING = "AGENT_RESPONDING"
    RESOLVED = "RESOLVED"
    NEEDS_HUMAN = "NEEDS_HUMAN"


class ChatSession(Document):
    """
    Tracks one customer's ongoing conversation with a tenant's bot.

    `tenant_id` + `customer_phone` is the compound logical key used
    for upserts — Beanie's `_id` is the internal MongoDB ObjectId.
    """

    # ── Key fields ────────────────────────────────────────────────────────────
    tenant_id: str = Field(
        description="References Tenant.tenant_id slug"
    )
    customer_phone: str = Field(
        description="Customer's WhatsApp phone number in E.164 format, e.g. '+919876543210'"
    )

    # ── State ─────────────────────────────────────────────────────────────────
    status: SessionStatus = Field(
        default=SessionStatus.WAITING_FOR_BOT,
        description="Current lifecycle status of the conversation",
    )
    is_typing: bool = Field(
        default=False,
        description=(
            "True while the bot has sent a typing indicator to WhatsApp "
            "and hasn't yet extinguished it. Used by the dashboard to show "
            "the typing-state badge in real time."
        ),
    )

    # ── Flexible context store ────────────────────────────────────────────────
    context_vars: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Arbitrary key-value context persisted across turns. "
            "Examples: last_product_viewed, appointment_date, quote_id."
        ),
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "chat_sessions"
        indexes = [
            # Compound index — the primary lookup pattern for every agent run
            IndexModel(
                [("tenant_id", ASCENDING), ("customer_phone", ASCENDING)],
                unique=True,
                name="tenant_phone_unique",
            ),
            # Dashboard queries: list all sessions for a tenant, sorted by recency
            IndexModel(
                [("tenant_id", ASCENDING), ("updated_at", ASCENDING)],
                name="tenant_updated_at",
            ),
            # Filter by status (e.g. show only AGENT_RESPONDING sessions)
            IndexModel([("status", ASCENDING)], name="status"),
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "luxury-furniture",
                "customer_phone": "+919876543210",
                "status": "WAITING_FOR_BOT",
                "is_typing": False,
                "context_vars": {"last_product_viewed": "sofa"},
            }
        }
