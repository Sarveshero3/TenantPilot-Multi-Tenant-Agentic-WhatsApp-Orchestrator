"""
WhatsApp Webhook Router — handles Meta's verification challenge and inbound messages.

Endpoints:
  GET  /api/webhook  — Meta verification challenge (hub.verify_token check)
  POST /api/webhook  — Inbound message handler → fires LangGraph pipeline in background

The POST handler extracts tenant_id from the phone_number_id in the payload,
then dispatches the agent graph as a BackgroundTask so the 200 response
returns immediately (Meta requires < 5s response time).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query, Request, Response, HTTPException

from app.config import get_settings
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


# ── GET /api/webhook — Meta Verification Challenge ───────────────────────────
@router.get("/webhook")
async def verify_webhook(
    response: Response,
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    """
    Meta sends a GET request to verify webhook ownership.
    We check the verify_token matches our secret and echo back the challenge.
    """
    settings = get_settings()

    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook verification succeeded")
        # Meta expects the raw challenge string, not JSON
        return Response(content=hub_challenge or "", media_type="text/plain")

    logger.warning(
        "Webhook verification failed: mode=%s, token_match=%s",
        hub_mode,
        hub_verify_token == settings.whatsapp_verify_token,
    )
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_inbound(request: Request, background_tasks: BackgroundTasks):
    """
    Receive an inbound WhatsApp message from Meta's Cloud API.

    Flow:
      1. Validate payload signature (X-Hub-Signature-256) if app secret is configured
      2. Parse the webhook payload
      3. Extract message details (phone, text, message_id)
      4. Resolve tenant_id from the phone_number_id
      5. Fire the LangGraph agent pipeline as a background task
      6. Return 200 immediately (Meta requires < 5s)
    """
    settings = get_settings()
    body_bytes = await request.body()

    # Webhook signature security (X-Hub-Signature-256)
    if settings.whatsapp_app_secret:
        signature_header = request.headers.get("X-Hub-Signature-256")
        if not signature_header:
            logger.warning("Missing X-Hub-Signature-256 header when secret is configured")
            raise HTTPException(status_code=403, detail="Signature missing")
        
        try:
            parts = signature_header.split("=")
            if len(parts) == 2 and parts[0] == "sha256":
                expected_sig = parts[1]
                import hmac
                import hashlib
                actual_sig = hmac.new(
                    settings.whatsapp_app_secret.encode("utf-8"),
                    body_bytes,
                    hashlib.sha256
                ).hexdigest()
                if not hmac.compare_digest(actual_sig, expected_sig):
                    logger.warning("Invalid X-Hub-Signature-256 signature detected")
                    raise HTTPException(status_code=403, detail="Invalid signature")
            else:
                logger.warning("Malformed X-Hub-Signature-256 header")
                raise HTTPException(status_code=400, detail="Malformed signature header")
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise exc
            logger.error("Error validating webhook signature: %s", exc)
            raise HTTPException(status_code=403, detail="Signature validation failed")

    # Parse JSON body
    import json
    try:
        body: dict[str, Any] = json.loads(body_bytes)
    except Exception as exc:
        logger.error("Failed to parse JSON body: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Meta sends various webhook types — we only care about messages
    # Payload structure: body.entry[].changes[].value.messages[]
    try:
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})

                # Skip non-message notifications (e.g., status updates)
                if "messages" not in value:
                    if "statuses" in value:
                        for status in value["statuses"]:
                            msg_id = status.get("id")
                            status_val = status.get("status")
                            errors = status.get("errors")
                            recipient_id = status.get("recipient_id")
                            if status_val == "failed":
                                logger.error(
                                    "WhatsApp delivery FAILED to %s: msg_id=%s, errors=%s",
                                    recipient_id, msg_id, errors
                                )
                            else:
                                logger.info(
                                    "WhatsApp delivery status update: msg_id=%s, status=%s",
                                    msg_id, status_val
                                )
                    continue

                metadata = value.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id", "")

                messages = value.get("messages", [])
                for message in messages:
                    msg_from = message.get("from", "")  # Customer's phone number
                    msg_id = message.get("id", "")       # WhatsApp message ID
                    msg_type = message.get("type", "text")

                    # Extract text content
                    text_content = ""
                    if msg_type == "text":
                        text_content = message.get("text", {}).get("body", "")
                    elif msg_type == "image":
                        text_content = message.get("image", {}).get("caption", "")
                    elif msg_type == "document":
                        text_content = message.get("document", {}).get("caption", "")

                    # Extract media URL (if present)
                    media_url = None
                    if msg_type == "image":
                        media_url = message.get("image", {}).get("id")
                    elif msg_type == "document":
                        media_url = message.get("document", {}).get("id")

                    if not msg_from or not msg_id:
                        logger.warning("Skipping message with missing from/id")
                        continue

                    # Resolve tenant_id from phone_number_id
                    tenant_id = await _resolve_tenant_id(phone_number_id)

                    if not tenant_id:
                        logger.error(
                            "No tenant found for phone_number_id=%s. Dropping message.",
                            phone_number_id,
                        )
                        continue

                    logger.info(
                        "Inbound message: tenant=%s from=%s type=%s text='%s...'",
                        tenant_id, msg_from, msg_type, text_content[:40],
                    )

                    # Fire the agent pipeline in the background
                    background_tasks.add_task(
                        _run_agent_pipeline,
                        inbound_message_id=msg_id,
                        customer_phone=msg_from,
                        tenant_id=tenant_id,
                        message_text=text_content,
                        message_type=msg_type,
                        media_url=media_url,
                    )

    except Exception as exc:
        logger.error("Error processing webhook payload: %s", exc, exc_info=True)

    # Always return 200 to Meta — even if we couldn't process the message.
    # Returning non-200 causes Meta to retry, which can create duplicates.
    return {"status": "ok"}


# ── Internal helpers ─────────────────────────────────────────────────────────

async def _resolve_tenant_id(phone_number_id: str) -> str | None:
    """
    Look up which tenant owns the given Meta phone_number_id.
    Returns the tenant_id slug, or None if not found.
    """
    if not phone_number_id:
        return None

    tenant = await Tenant.find_one(
        Tenant.whatsapp_phone_number_id == phone_number_id
    )
    if tenant:
        return tenant.tenant_id

    logger.warning("No tenant found for phone_number_id=%s", phone_number_id)
    return None


async def _run_agent_pipeline(
    *,
    inbound_message_id: str,
    customer_phone: str,
    tenant_id: str,
    message_text: str,
    message_type: str,
    media_url: str | None,
) -> None:
    """
    Execute the LangGraph agent pipeline for a single inbound message.
    This runs as a FastAPI BackgroundTask so the webhook returns 200 immediately.
    """
    try:
        # Import here to avoid circular imports at module level
        from app.agent.graph import agent_graph

        initial_state = {
            "inbound_message_id": inbound_message_id,
            "customer_phone": customer_phone,
            "tenant_id": tenant_id,
            "message_text": message_text,
            "message_type": message_type,
            "media_url": media_url,
        }

        logger.info(
            "Starting agent pipeline: tenant=%s phone=%s",
            tenant_id, customer_phone,
        )

        result = await agent_graph.ainvoke(initial_state)

        error = result.get("error")
        if error:
            logger.warning("Agent pipeline completed with error: %s", error)
        else:
            logger.info(
                "Agent pipeline completed: tenant=%s phone=%s response_type=%s",
                tenant_id, customer_phone, result.get("response_type", "unknown"),
            )

    except Exception as exc:
        logger.error(
            "Agent pipeline failed: tenant=%s phone=%s error=%s",
            tenant_id, customer_phone, exc,
            exc_info=True,
        )
