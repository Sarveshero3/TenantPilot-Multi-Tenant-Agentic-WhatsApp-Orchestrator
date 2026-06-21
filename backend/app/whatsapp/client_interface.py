"""Shared WhatsApp Cloud API client interface and payload builders."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

GRAPH_API_BASE_URL = "https://graph.facebook.com"
PLACEHOLDER_PHONE_NUMBER_ID = "<PHONE_NUMBER_ID>"

JsonDict = dict[str, Any]


@runtime_checkable
class WhatsAppClient(Protocol):
    """Async interface used by the LangGraph nodes and webhook pipeline."""

    async def mark_as_read(
        self,
        message_id: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        """Mark an inbound WhatsApp message as read."""

    async def set_typing_indicator(
        self,
        to: str,
        enabled: bool,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        """Toggle WhatsApp's native typing indicator for a customer."""

    async def typing_on(
        self,
        to: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        """Start WhatsApp's native typing indicator."""

    async def typing_off(
        self,
        to: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        """Stop WhatsApp's native typing indicator."""

    async def send_text(
        self,
        to: str,
        text: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        """Send a WhatsApp text message. WhatsApp markdown is passed through."""

    async def send_image(
        self,
        to: str,
        image_url: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        """Send a WhatsApp image message by public URL."""

    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        """Send a WhatsApp document message by public URL and filename."""


class WhatsAppPayloadBuilder:
    """Build assignment-specified WhatsApp Cloud API endpoints and payloads."""

    def __init__(
        self,
        *,
        api_version: str = "v20.0",
        default_phone_number_id: str = "",
    ) -> None:
        self.api_version = api_version
        self.default_phone_number_id = default_phone_number_id

    def resolve_phone_number_id(
        self,
        phone_number_id: str | None = None,
        *,
        allow_placeholder: bool = False,
    ) -> str:
        """Resolve per-tenant phone IDs, falling back to the configured default."""
        resolved = phone_number_id or self.default_phone_number_id
        if resolved:
            return resolved
        if allow_placeholder:
            return PLACEHOLDER_PHONE_NUMBER_ID
        raise ValueError(
            "WhatsApp phone_number_id is required. Pass a tenant phone_number_id "
            "or set WHATSAPP_PHONE_NUMBER_ID."
        )

    def messages_endpoint(self, phone_number_id: str) -> str:
        """Return the Meta Graph API messages endpoint for one phone number ID."""
        return f"{GRAPH_API_BASE_URL}/{self.api_version}/{phone_number_id}/messages"

    @staticmethod
    def mark_as_read_payload(message_id: str) -> JsonDict:
        return {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

    @staticmethod
    def typing_indicator_payload(to: str, *, enabled: bool) -> JsonDict:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "typing_indicator",
            "typing_indicator": {
                "type": "text" if enabled else "stop",
            },
        }

    @staticmethod
    def text_payload(to: str, text: str) -> JsonDict:
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": text,
            },
        }

    @staticmethod
    def image_payload(to: str, image_url: str) -> JsonDict:
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url,
            },
        }

    @staticmethod
    def document_payload(to: str, document_url: str, filename: str) -> JsonDict:
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename,
            },
        }
