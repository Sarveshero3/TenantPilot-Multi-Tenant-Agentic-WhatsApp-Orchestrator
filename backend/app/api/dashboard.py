"""
Dashboard REST API Router — serves the React frontend.

Endpoints:
  GET  /api/tenants                 — list all tenants
  GET  /api/tenants/{tenant_id}     — get one tenant
  GET  /api/sessions                — list sessions (optional ?tenant_id= filter)
  GET  /api/sessions/{session_id}/messages — get message history for a session
  POST /api/broadcast               — send a text message to a specific customer
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.tenant import Tenant
from app.models.chat_session import ChatSession, SessionStatus
from app.models.message_log import MessageLog, MessageDirection, MessageType
from app.whatsapp import get_whatsapp_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


# ── Response schemas ─────────────────────────────────────────────────────────

class TenantResponse(BaseModel):
    """Public-facing tenant representation."""
    tenant_id: str
    name: str
    whatsapp_phone_number_id: str
    system_prompt: str
    media_keys: list[str]
    created_at: datetime


class SessionResponse(BaseModel):
    """Public-facing chat session representation."""
    id: str
    tenant_id: str
    customer_phone: str
    status: str
    is_typing: bool
    context_vars: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Public-facing message representation."""
    id: str
    session_id: str
    tenant_id: str
    customer_phone: str
    direction: str
    sender: str
    message_type: str
    text_content: Optional[str]
    media_url: Optional[str]
    media_filename: Optional[str]
    whatsapp_message_id: Optional[str]
    timestamp: datetime


class BroadcastRequest(BaseModel):
    """Request body for sending a broadcast/manual message."""
    tenant_id: str = Field(description="Tenant slug")
    customer_phone: str = Field(description="Recipient phone in E.164 format")
    text: str = Field(description="Message text to send")


class BroadcastResponse(BaseModel):
    """Response after sending a broadcast message."""
    status: str
    message_id: Optional[str] = None


# ── GET /api/tenants ─────────────────────────────────────────────────────────
@router.get("/tenants", response_model=list[TenantResponse])
async def list_tenants():
    """List all registered tenants."""
    tenants = await Tenant.find_all().to_list()
    return [
        TenantResponse(
            tenant_id=t.tenant_id,
            name=t.name,
            whatsapp_phone_number_id=t.whatsapp_phone_number_id,
            system_prompt=t.system_prompt,
            media_keys=list(t.media_library.keys()),
            created_at=t.created_at,
        )
        for t in tenants
    ]


# ── GET /api/tenants/{tenant_id} ─────────────────────────────────────────────
@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """Get a single tenant by slug."""
    tenant = await Tenant.find_one(Tenant.tenant_id == tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found")

    return TenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        whatsapp_phone_number_id=tenant.whatsapp_phone_number_id,
        system_prompt=tenant.system_prompt,
        media_keys=list(tenant.media_library.keys()),
        created_at=tenant.created_at,
    )


# ── GET /api/sessions ────────────────────────────────────────────────────────
@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    tenant_id: str | None = Query(None, description="Filter by tenant slug"),
):
    """
    List chat sessions, optionally filtered by tenant.
    Returns most recently updated sessions first.
    """
    if tenant_id:
        sessions = await ChatSession.find(
            ChatSession.tenant_id == tenant_id,
        ).sort("-updated_at").limit(100).to_list()
    else:
        sessions = await ChatSession.find_all().sort("-updated_at").limit(100).to_list()

    return [
        SessionResponse(
            id=str(s.id),
            tenant_id=s.tenant_id,
            customer_phone=s.customer_phone,
            status=s.status.value,
            is_typing=s.is_typing,
            context_vars=s.context_vars,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


# ── GET /api/sessions/{session_id}/messages ──────────────────────────────────
@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_session_messages(session_id: str):
    """
    Get the full message history for a session, in chronological order.
    """
    messages = await MessageLog.find(
        MessageLog.session_id == session_id,
    ).sort("+timestamp").to_list()

    if not messages:
        # Check if the session itself exists
        try:
            session = await ChatSession.get(PydanticObjectId(session_id))
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        except Exception:
            raise HTTPException(status_code=404, detail="Session not found")

    return [
        MessageResponse(
            id=str(m.id),
            session_id=m.session_id,
            tenant_id=m.tenant_id,
            customer_phone=m.customer_phone,
            direction=m.direction.value,
            sender=m.sender,
            message_type=m.message_type.value,
            text_content=m.text_content,
            media_url=m.media_url,
            media_filename=m.media_filename,
            whatsapp_message_id=m.whatsapp_message_id,
            timestamp=m.timestamp,
        )
        for m in messages
    ]


# ── POST /api/broadcast ──────────────────────────────────────────────────────
@router.post("/broadcast", response_model=BroadcastResponse)
async def send_broadcast(req: BroadcastRequest):
    """
    Send a manual text message to a customer on behalf of a tenant.
    Used by the dashboard for operator-initiated messages.
    """
    # Verify tenant exists
    tenant = await Tenant.find_one(Tenant.tenant_id == req.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{req.tenant_id}' not found")

    wa_client = get_whatsapp_client()

    try:
        result = await wa_client.send_text(
            req.customer_phone,
            req.text,
            phone_number_id=tenant.whatsapp_phone_number_id,
        )

        # Extract message ID from result
        wa_msg_id = None
        try:
            msgs = result.get("messages", [])
            if msgs and isinstance(msgs[0], dict):
                wa_msg_id = msgs[0].get("id")
        except (AttributeError, IndexError, TypeError):
            pass

        # Log the outbound message
        now = datetime.now(timezone.utc)

        # Find or create session for this conversation
        session = await ChatSession.find_one(
            ChatSession.tenant_id == req.tenant_id,
            ChatSession.customer_phone == req.customer_phone,
        )
        session_id = str(session.id) if session else "broadcast"

        outbound_log = MessageLog(
            session_id=session_id,
            tenant_id=req.tenant_id,
            customer_phone=req.customer_phone,
            direction=MessageDirection.OUTBOUND,
            sender="operator",
            message_type=MessageType.TEXT,
            text_content=req.text,
            whatsapp_message_id=wa_msg_id,
            timestamp=now,
        )
        await outbound_log.insert()

        logger.info(
            "Broadcast sent: tenant=%s phone=%s text='%s...'",
            req.tenant_id, req.customer_phone, req.text[:40],
        )

        return BroadcastResponse(status="sent", message_id=wa_msg_id)

    except Exception as exc:
        logger.error("Broadcast failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send message: {exc}")
