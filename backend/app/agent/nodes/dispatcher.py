"""
Dispatcher Node — fourth and final node in the LangGraph pipeline.

Responsibilities:
  1. Based on response_type, send the appropriate WhatsApp message
     (text, image, or document) via the WhatsApp client
  2. Turn off the typing indicator
  3. Log the outbound message to MessageLog
  4. Update ChatSession status to WAITING_FOR_BOT, is_typing = False
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.agent.state import AgentState
from app.models.chat_session import ChatSession, SessionStatus
from app.models.message_log import MessageLog, MessageDirection, MessageType
from app.whatsapp import get_whatsapp_client

logger = logging.getLogger(__name__)


async def dispatcher_node(state: AgentState) -> dict:
    """
    Send the LLM's response to the customer via WhatsApp and log everything.
    """
    tenant_id = state["tenant_id"]
    customer_phone = state["customer_phone"]
    session_id = state["session_id"]
    response_type = state.get("response_type", "text")
    response_text = state.get("response_text")
    response_media_url = state.get("response_media_url")
    response_media_filename = state.get("response_media_filename")

    logger.info(
        "Dispatcher: tenant=%s phone=%s type=%s",
        tenant_id, customer_phone, response_type,
    )

    wa_client = get_whatsapp_client()
    wa_message_id = None

    # ── 1. Send the appropriate WhatsApp message ─────────────────────────────
    try:
        if response_type == "image" and response_media_url:
            # Send accompanying text first (if any), then the image
            if response_text:
                result = await wa_client.send_text(customer_phone, response_text)
                logger.debug("Sent pre-image text to %s", customer_phone)

            result = await wa_client.send_image(customer_phone, response_media_url)
            wa_message_id = _extract_message_id(result)
            logger.info("Sent image to %s: %s", customer_phone, response_media_url)

        elif response_type == "document" and response_media_url:
            # Send accompanying text first (if any), then the document
            if response_text:
                result = await wa_client.send_text(customer_phone, response_text)
                logger.debug("Sent pre-document text to %s", customer_phone)

            filename = response_media_filename or "document.pdf"
            result = await wa_client.send_document(
                customer_phone, response_media_url, filename,
            )
            wa_message_id = _extract_message_id(result)
            logger.info("Sent document to %s: %s (%s)", customer_phone, response_media_url, filename)

        else:
            # Default: send text
            text = response_text or "I'm sorry, I couldn't generate a response."
            result = await wa_client.send_text(customer_phone, text)
            wa_message_id = _extract_message_id(result)
            logger.info("Sent text to %s (%d chars)", customer_phone, len(text))

    except Exception as exc:
        logger.error("Failed to send WhatsApp message: %s", exc, exc_info=True)

    # ── 2. Turn off typing indicator ─────────────────────────────────────────
    try:
        await wa_client.typing_off(customer_phone)
        logger.debug("Typing indicator OFF for %s", customer_phone)
    except Exception as exc:
        logger.warning("Failed to stop typing indicator: %s", exc)

    # ── 3. Log the outbound message ──────────────────────────────────────────
    now = datetime.now(timezone.utc)

    try:
        msg_type_enum = MessageType(response_type)
    except ValueError:
        msg_type_enum = MessageType.TEXT

    outbound_log = MessageLog(
        session_id=session_id,
        tenant_id=tenant_id,
        customer_phone=customer_phone,
        direction=MessageDirection.OUTBOUND,
        sender="bot",
        message_type=msg_type_enum,
        text_content=response_text,
        media_url=response_media_url,
        media_filename=response_media_filename,
        whatsapp_message_id=wa_message_id,
        timestamp=now,
    )
    await outbound_log.insert()
    logger.debug("Outbound message logged: session=%s", session_id)

    # ── 4. Update ChatSession ────────────────────────────────────────────────
    session = await ChatSession.find_one(
        ChatSession.tenant_id == tenant_id,
        ChatSession.customer_phone == customer_phone,
    )
    if session:
        session.status = (
            SessionStatus.NEEDS_HUMAN
            if response_type == "handover"
            else SessionStatus.WAITING_FOR_BOT
        )
        session.is_typing = False
        session.updated_at = now
        await session.save()
        logger.debug("Session updated: status=%s, is_typing=False", session.status)

    return {}  # Terminal node — no new state fields needed


def _extract_message_id(result: dict) -> str | None:
    """
    Extract the WhatsApp message ID from the API response.
    Real API returns: {"messages": [{"id": "wamid.xxx"}]}
    Mock client returns: {"method": ..., ...}
    """
    try:
        messages = result.get("messages", [])
        if messages and isinstance(messages[0], dict):
            return messages[0].get("id")
    except (AttributeError, IndexError, TypeError):
        pass
    return None
