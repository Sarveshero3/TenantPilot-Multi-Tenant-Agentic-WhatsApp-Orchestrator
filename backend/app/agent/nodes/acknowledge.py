"""
Acknowledge Node — first node in the LangGraph pipeline.

Responsibilities:
  1. Send "read receipt" for the inbound message via WhatsApp
  2. Start the typing indicator via WhatsApp
  3. Upsert the ChatSession (find or create by tenant_id + phone)
  4. Log the inbound message to MessageLog
  5. Return state with session_id populated
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.agent.state import AgentState
from app.models.chat_session import ChatSession, SessionStatus
from app.models.message_log import MessageLog, MessageDirection, MessageType
from app.whatsapp import get_whatsapp_client

logger = logging.getLogger(__name__)


async def acknowledge_node(state: AgentState) -> dict:
    """
    Process an inbound WhatsApp message: acknowledge receipt, start typing,
    persist session + message log, and return the session_id.
    """
    tenant_id = state["tenant_id"]
    customer_phone = state["customer_phone"]
    message_id = state["inbound_message_id"]
    message_text = state.get("message_text", "")
    message_type_str = state.get("message_type", "text")

    logger.info(
        "Acknowledge node: tenant=%s phone=%s msg_id=%s",
        tenant_id, customer_phone, message_id,
    )

    wa_client = get_whatsapp_client()

    # ── 1. Send read receipt ─────────────────────────────────────────────────
    try:
        await wa_client.mark_as_read(message_id)
        logger.debug("Read receipt sent for message %s", message_id)
    except Exception as exc:
        logger.warning("Failed to send read receipt: %s", exc)

    # ── 2. Start typing indicator ────────────────────────────────────────────
    try:
        await wa_client.typing_on(customer_phone)
        logger.debug("Typing indicator ON for %s", customer_phone)
    except Exception as exc:
        logger.warning("Failed to start typing indicator: %s", exc)

    # ── 3. Upsert ChatSession ────────────────────────────────────────────────
    session = await ChatSession.find_one(
        ChatSession.tenant_id == tenant_id,
        ChatSession.customer_phone == customer_phone,
    )

    now = datetime.now(timezone.utc)

    if session is None:
        session = ChatSession(
            tenant_id=tenant_id,
            customer_phone=customer_phone,
            status=SessionStatus.AGENT_RESPONDING,
            is_typing=True,
            context_vars={},
            created_at=now,
            updated_at=now,
        )
        await session.insert()
        logger.info("Created new ChatSession for %s / %s", tenant_id, customer_phone)
    else:
        if session.status == SessionStatus.NEEDS_HUMAN:
            logger.info("Session %s is in NEEDS_HUMAN status. Halting auto-reply.", session.id)
            try:
                msg_type_enum = MessageType(message_type_str)
            except ValueError:
                msg_type_enum = MessageType.TEXT

            inbound_log = MessageLog(
                session_id=str(session.id),
                tenant_id=tenant_id,
                customer_phone=customer_phone,
                direction=MessageDirection.INBOUND,
                sender="customer",
                message_type=msg_type_enum,
                text_content=message_text if message_text else None,
                media_url=state.get("media_url"),
                whatsapp_message_id=message_id,
                timestamp=now,
            )
            await inbound_log.insert()
            
            # Update session's updated_at so it bubbles up on the dashboard
            session.updated_at = now
            await session.save()
            
            return {
                "session_id": str(session.id),
                "skip_agent": True,
                "status": SessionStatus.NEEDS_HUMAN,
            }

        session.status = SessionStatus.AGENT_RESPONDING
        session.is_typing = True
        session.updated_at = now
        await session.save()
        logger.info("Updated existing ChatSession for %s / %s", tenant_id, customer_phone)

    session_id = str(session.id)

    # ── 4. Log the inbound message ───────────────────────────────────────────
    # Map the inbound type string to our MessageType enum
    try:
        msg_type_enum = MessageType(message_type_str)
    except ValueError:
        msg_type_enum = MessageType.TEXT

    inbound_log = MessageLog(
        session_id=session_id,
        tenant_id=tenant_id,
        customer_phone=customer_phone,
        direction=MessageDirection.INBOUND,
        sender="customer",
        message_type=msg_type_enum,
        text_content=message_text if message_text else None,
        media_url=state.get("media_url"),
        whatsapp_message_id=message_id,
        timestamp=now,
    )
    await inbound_log.insert()
    logger.debug("Inbound message logged: session=%s", session_id)

    # ── 5. Return state update ───────────────────────────────────────────────
    return {"session_id": session_id}
