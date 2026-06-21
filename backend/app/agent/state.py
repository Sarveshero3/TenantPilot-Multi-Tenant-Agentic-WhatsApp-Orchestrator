"""
AgentState — the typed state dictionary flowing through the LangGraph pipeline.

Each node reads from and writes to this state. Fields are populated progressively:
  - Input fields: set by the webhook handler before invoking the graph
  - Acknowledge: sets session_id
  - Context Retriever: sets system_prompt, media_library, chat_history
  - LLM Reasoning: sets response_type, response_text, response_media_*
  - Dispatcher: reads response fields, sends message, no new state fields
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """
    State flowing through the 4-node LangGraph pipeline.

    `total=False` allows nodes to return partial updates —
    only the keys they set are merged into the accumulating state.
    """

    # ── Input (set by webhook handler before graph invocation) ────────────────
    inbound_message_id: str       # WhatsApp message ID from Meta payload
    customer_phone: str           # E.164 phone number of the customer
    tenant_id: str                # Tenant slug (e.g. "luxury-furniture")
    message_text: str             # Text body of the inbound message
    message_type: str             # "text" | "image" | etc.
    media_url: Optional[str]      # If the inbound message has media

    # ── Set by Acknowledge node ──────────────────────────────────────────────
    session_id: str               # str(ChatSession._id) after upsert
    skip_agent: bool              # Set to True if we should skip agent reasoning (e.g. human handover)

    # ── Set by Context Retriever node ────────────────────────────────────────
    system_prompt: str                    # Tenant's LLM system instructions
    media_library: dict[str, Any]         # Tenant's media library (key → MediaItem dict)
    chat_history: list[dict[str, Any]]    # Last 5 messages as dicts

    # ── Set by LLM Reasoning node ────────────────────────────────────────────
    response_type: str                    # "text" | "image" | "document"
    response_text: Optional[str]          # Text body for text responses
    response_media_url: Optional[str]     # URL for image/document responses
    response_media_filename: Optional[str]  # Filename for document responses

    # ── Error tracking ───────────────────────────────────────────────────────
    error: Optional[str]          # Set if any node encounters a recoverable error
