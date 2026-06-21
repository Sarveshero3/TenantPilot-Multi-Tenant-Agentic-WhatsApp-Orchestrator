"""WhatsApp Cloud API client factory and public exports."""

from __future__ import annotations

import logging

from app.config import get_settings
from app.whatsapp.client_interface import WhatsAppClient, WhatsAppPayloadBuilder
from app.whatsapp.mock_client import MockWhatsAppClient

logger = logging.getLogger(__name__)


def get_whatsapp_client() -> WhatsAppClient:
    """Return a real or mock WhatsApp client based on current settings.

    Mock mode is the safe default. Even if WHATSAPP_MODE=real, the factory falls
    back to mock logging when the Meta access token is missing.
    """
    settings = get_settings()
    mode = settings.whatsapp_mode.lower().strip()

    if mode == "real" and settings.whatsapp_access_token:
        from app.whatsapp.real_client import RealWhatsAppClient

        return RealWhatsAppClient(
            access_token=settings.whatsapp_access_token,
            api_version=settings.whatsapp_api_version,
            default_phone_number_id=settings.whatsapp_phone_number_id,
        )

    if mode == "real":
        logger.warning(
            "WHATSAPP_MODE=real but WHATSAPP_ACCESS_TOKEN is not set; "
            "falling back to MockWhatsAppClient."
        )
    elif mode != "mock":
        logger.warning(
            "Unknown WHATSAPP_MODE=%r; falling back to MockWhatsAppClient.",
            settings.whatsapp_mode,
        )

    return MockWhatsAppClient(
        api_version=settings.whatsapp_api_version,
        default_phone_number_id=settings.whatsapp_phone_number_id,
    )


__all__ = [
    "MockWhatsAppClient",
    "WhatsAppClient",
    "WhatsAppPayloadBuilder",
    "get_whatsapp_client",
]
