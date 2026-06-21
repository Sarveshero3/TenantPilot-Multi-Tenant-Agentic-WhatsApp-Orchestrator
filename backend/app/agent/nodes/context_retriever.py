"""
Context Retriever Node — second node in the LangGraph pipeline.

Responsibilities:
  1. Load the Tenant document to get system_prompt and media_library
  2. Load the last 5 messages from MessageLog for this session
  3. Return state with system_prompt, media_library (as serializable dict),
     and chat_history populated
"""

from __future__ import annotations

import logging
from typing import Any

from app.agent.state import AgentState
from app.models.tenant import Tenant
from app.models.message_log import MessageLog

logger = logging.getLogger(__name__)

# Number of recent messages to include as conversation context
HISTORY_LIMIT = 5


async def context_retriever_node(state: AgentState) -> dict:
    """
    Pull the tenant's configuration and recent chat history from MongoDB.
    """
    tenant_id = state["tenant_id"]
    session_id = state["session_id"]

    logger.info("Context retriever: tenant=%s session=%s", tenant_id, session_id)

    # ── 1. Load tenant ───────────────────────────────────────────────────────
    tenant = await Tenant.find_one(Tenant.tenant_id == tenant_id)

    if tenant is None:
        logger.error("Tenant not found: %s", tenant_id)
        return {
            "system_prompt": "You are a helpful customer service assistant.",
            "media_library": {},
            "chat_history": [],
            "error": f"Tenant '{tenant_id}' not found in database",
        }

    # Serialize media_library to a plain dict so the LLM node can pass it
    # into tool descriptions without Pydantic objects
    media_lib_dict: dict[str, Any] = {}
    for key, item in tenant.media_library.items():
        media_lib_dict[key] = item.model_dump()

    logger.debug(
        "Tenant loaded: %s, media keys=%s",
        tenant.name,
        list(media_lib_dict.keys()),
    )

    # ── 2. Load chat history (last N messages) ───────────────────────────────
    recent_messages = await MessageLog.find(
        MessageLog.session_id == session_id,
    ).sort("+timestamp").limit(HISTORY_LIMIT).to_list()

    chat_history: list[dict[str, Any]] = []
    for msg in recent_messages:
        chat_history.append({
            "role": "user" if msg.direction.value == "inbound" else "assistant",
            "content": msg.text_content or f"[{msg.message_type.value}: {msg.media_url or 'media'}]",
            "message_type": msg.message_type.value,
            "timestamp": msg.timestamp.isoformat(),
        })

    logger.debug("Chat history loaded: %d messages", len(chat_history))

    # ── 3. Return state update ───────────────────────────────────────────────
    return {
        "system_prompt": tenant.system_prompt,
        "media_library": media_lib_dict,
        "chat_history": chat_history,
    }
