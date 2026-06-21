"""Mock WhatsApp client that logs exact request payloads instead of sending."""

from __future__ import annotations

import json
import logging

from app.whatsapp.client_interface import JsonDict, WhatsAppPayloadBuilder

logger = logging.getLogger(__name__)


class MockWhatsAppClient(WhatsAppPayloadBuilder):
    """Log Meta Graph API requests for local/dev mode without credentials."""

    def __init__(
        self,
        *,
        api_version: str = "v20.0",
        default_phone_number_id: str = "",
    ) -> None:
        super().__init__(
            api_version=api_version,
            default_phone_number_id=default_phone_number_id,
        )

    def _mock_headers(self) -> dict[str, str]:
        return {
            "Authorization": "Bearer <WHATSAPP_ACCESS_TOKEN>",
            "Content-Type": "application/json",
        }

    async def _log_post_messages(
        self,
        payload: JsonDict,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        resolved_phone_number_id = self.resolve_phone_number_id(
            phone_number_id,
            allow_placeholder=True,
        )
        request = {
            "method": "POST",
            "url": self.messages_endpoint(resolved_phone_number_id),
            "headers": self._mock_headers(),
            "json": payload,
        }
        logger.info(
            "Mock WhatsApp Cloud API request:\n%s",
            json.dumps(request, indent=2, ensure_ascii=False),
        )
        return {
            "mock": True,
            "request": request,
        }

    async def mark_as_read(
        self,
        message_id: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self._log_post_messages(
            self.mark_as_read_payload(message_id),
            phone_number_id,
        )

    async def set_typing_indicator(
        self,
        to: str,
        enabled: bool,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self._log_post_messages(
            self.typing_indicator_payload(to, enabled=enabled),
            phone_number_id,
        )

    async def typing_on(
        self,
        to: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self.set_typing_indicator(
            to,
            enabled=True,
            phone_number_id=phone_number_id,
        )

    async def typing_off(
        self,
        to: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self.set_typing_indicator(
            to,
            enabled=False,
            phone_number_id=phone_number_id,
        )

    async def send_text(
        self,
        to: str,
        text: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self._log_post_messages(
            self.text_payload(to, text),
            phone_number_id,
        )

    async def send_image(
        self,
        to: str,
        image_url: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self._log_post_messages(
            self.image_payload(to, image_url),
            phone_number_id,
        )

    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self._log_post_messages(
            self.document_payload(to, document_url, filename),
            phone_number_id,
        )
