"""
Tenant document model.

Collection: tenants
One document per retail brand (company) using the SaaS platform.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Literal

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING


class MediaItem(BaseModel):
    """
    A single asset in a tenant's media library.

    The LLM uses `description` to decide which key to call when a customer
    requests visual or document assets (e.g. "catalog", "sofa", "invoice").
    """

    url: str = Field(
        description="Publicly accessible URL to the asset (image or document)"
    )
    media_type: Literal["image", "document"] = Field(
        description="WhatsApp message type to use when dispatching this asset"
    )
    filename: Optional[str] = Field(
        default=None,
        description="Required for documents — displayed to the WhatsApp user",
    )
    description: str = Field(
        description=(
            "Human-readable description the LLM reads to decide when to "
            "use this asset, e.g. 'Luxury sofa showroom photo, JPG'"
        )
    )


class Tenant(Document):
    """
    A retail brand (company) that subscribes to the TenantPilot SaaS.

    Each tenant gets its own WhatsApp phone number, system prompt, and
    media library. The `tenant_id` slug is the stable cross-collection key.
    """

    # ── Identity ─────────────────────────────────────────────────────────────
    tenant_id: str = Field(  # Unique index declared in Settings.indexes below
        description="URL-safe slug, e.g. 'luxury-furniture'. Immutable after creation."
    )
    name: str = Field(description="Human-readable brand name, e.g. 'Luxury Furniture Store'")

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    whatsapp_phone_number_id: str = Field(
        description=(
            "Meta phone number ID assigned to this tenant's WhatsApp business account. "
            "Used as the 'from' sender ID when dispatching messages."
        )
    )

    # ── AI configuration ──────────────────────────────────────────────────────
    system_prompt: str = Field(
        description=(
            "LLM system instructions that define this brand's personality, "
            "tone, capabilities, and constraints."
        )
    )

    # ── Media library ─────────────────────────────────────────────────────────
    media_library: dict[str, MediaItem] = Field(
        default_factory=dict,
        description=(
            "Maps a short keyword (e.g. 'catalog', 'sofa') to a MediaItem. "
            "The LLM calls send_media(key) to dispatch the matching asset."
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
        name = "tenants"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True),
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "luxury-furniture",
                "name": "Luxury Furniture Store",
                "whatsapp_phone_number_id": "123456789012345",
                "system_prompt": (
                    "You are a luxury furniture concierge for Prestige Home. "
                    "Be elegant, helpful, and knowledgeable about our products. "
                    "Offer catalog PDFs and showroom images when customers ask about specific pieces."
                ),
                "media_library": {
                    "catalog": {
                        "url": "https://example.com/prestige-catalog-2025.pdf",
                        "media_type": "document",
                        "filename": "Prestige-Catalog-2025.pdf",
                        "description": "Full product catalog PDF with all furniture collections",
                    },
                    "sofa": {
                        "url": "https://example.com/sofa-showroom.jpg",
                        "media_type": "image",
                        "filename": None,
                        "description": "Showroom photo of our signature Prestige sofa collection",
                    },
                },
            }
        }
