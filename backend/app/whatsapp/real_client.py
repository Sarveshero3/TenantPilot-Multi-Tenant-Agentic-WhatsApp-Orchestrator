"""Real WhatsApp Cloud API client backed by httpx."""

from __future__ import annotations

import logging

import httpx

from app.whatsapp.client_interface import JsonDict, WhatsAppPayloadBuilder

logger = logging.getLogger(__name__)


class RealWhatsAppClient(WhatsAppPayloadBuilder):
    """Send real requests to Meta's WhatsApp Cloud API."""

    def __init__(
        self,
        *,
        access_token: str,
        api_version: str = "v20.0",
        default_phone_number_id: str = "",
        timeout: float = 10.0,
    ) -> None:
        super().__init__(
            api_version=api_version,
            default_phone_number_id=default_phone_number_id,
        )
        if not access_token:
            raise ValueError("WHATSAPP_ACCESS_TOKEN is required for real mode.")
        self.access_token = access_token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _post_messages(
        self,
        payload: JsonDict,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        resolved_phone_number_id = self.resolve_phone_number_id(phone_number_id)
        endpoint = self.messages_endpoint(resolved_phone_number_id)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    endpoint,
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "WhatsApp Cloud API POST failed: endpoint=%s status=%s body=%s",
                    endpoint,
                    exc.response.status_code,
                    exc.response.text,
                )
                raise
            except httpx.HTTPError:
                logger.exception(
                    "WhatsApp Cloud API POST failed: endpoint=%s", endpoint
                )
                raise

        try:
            return response.json()
        except ValueError:
            return {"status_code": response.status_code, "text": response.text}

    async def mark_as_read(
        self,
        message_id: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self._post_messages(
            self.mark_as_read_payload(message_id),
            phone_number_id,
        )

    async def set_typing_indicator(
        self,
        to: str,
        enabled: bool,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self._post_messages(
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
        return await self._post_messages(
            self.text_payload(to, text),
            phone_number_id,
        )

    async def send_image(
        self,
        to: str,
        image_url: str,
        phone_number_id: str | None = None,
    ) -> JsonDict:
        return await self._post_messages(
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
        return await self._post_messages(
            self.document_payload(to, document_url, filename),
            phone_number_id,
        )
