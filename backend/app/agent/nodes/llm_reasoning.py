"""
LLM Reasoning Node — third node in the LangGraph pipeline.

Responsibilities:
  1. Build the LLM messages array from system_prompt + chat_history + current message
  2. Define the send_media tool that looks up keys in the tenant's media_library
  3. Invoke the NVIDIA Nemotron LLM with tool-calling enabled
  4. Parse the response: if tool call -> set media response fields;
     if plain text -> set text response fields
  5. Return state with response_type, response_text, response_media_* populated

The LLM decides whether to reply with text or trigger media dispatch.
This is the "agentic decision-making" the assignment requires.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool as langchain_tool

from app.agent.state import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_llm():
    """
    Construct the LLM client. Uses NVIDIA Nemotron via langchain-nvidia-ai-endpoints.
    Falls back to a simple echo if the API key is not set (for testing).
    """
    settings = get_settings()

    if not settings.nvidia_api_key:
        logger.warning(
            "NVIDIA_API_KEY not set — LLM reasoning will return a fallback response. "
            "Set the key in .env to enable real LLM calls."
        )
        return None

    try:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA

        llm = ChatNVIDIA(
            model=settings.llm_model,
            api_key=settings.nvidia_api_key,
            temperature=settings.llm_temperature,
            top_p=settings.llm_top_p,
            max_tokens=4096,  # Keep response reasonable; full 65k is for input context
        )
        return llm
    except ImportError:
        logger.error(
            "langchain-nvidia-ai-endpoints not installed. "
            "Run: pip install langchain-nvidia-ai-endpoints"
        )
        return None
    except Exception as exc:
        logger.error("Failed to initialize NVIDIA LLM: %s", exc)
        return None


def _build_media_tool_description(media_library: dict[str, Any]) -> str:
    """
    Build a human-readable description of available media assets
    for the LLM's system prompt, so it knows what keys it can use.
    """
    if not media_library:
        return "No media assets are available for this tenant."

    lines = ["Available media assets you can send to the customer:"]
    for key, item in media_library.items():
        media_type = item.get("media_type", "unknown")
        description = item.get("description", "No description")
        filename = item.get("filename", "")
        fname_str = f" (filename: {filename})" if filename else ""
        lines.append(f"  - Key: '{key}' | Type: {media_type}{fname_str} | {description}")

    lines.append("")
    lines.append(
        "To send a media asset, respond with a JSON tool call in this exact format:\n"
        '{"tool": "send_media", "media_key": "<key>"}\n'
        "Include this on its own line at the END of your response text. "
        "You may include a text message before the tool call line. "
        "If no media is appropriate, just reply with text only."
    )
    lines.append("")
    lines.append(
        "CRITICAL: If the customer expresses frustration, anger, complains about the bot, "
        "or explicitly requests a human operator/agent, you MUST hand over the conversation. "
        "To do this, respond with this exact JSON tool call on its own line at the END of your response:\n"
        '{"tool": "human_handover"}\n'
        "Before the tool call, write a polite, reassuring message, such as: "
        "'I apologize for the frustration. I am handing you over to a human representative right away.'"
    )
    return "\n".join(lines)


def _parse_tool_call(response_text: str, media_library: dict[str, Any]) -> dict | None:
    """
    Check if the LLM response contains a send_media tool call.
    Returns the matched MediaItem dict if found, None otherwise.

    Supports two patterns:
    1. Structured tool_calls from LangChain (if the LLM supports native tool calling)
    2. JSON in the response text: {"tool": "send_media", "media_key": "..."}
    """
    # Try to find JSON tool call in the text
    # Look for the pattern anywhere in the response
    import re
    pattern = r'\{[^{}]*"tool"\s*:\s*"send_media"[^{}]*"media_key"\s*:\s*"([^"]+)"[^{}]*\}'
    match = re.search(pattern, response_text)
    if not match:
        # Try alternate key order
        pattern2 = r'\{[^{}]*"media_key"\s*:\s*"([^"]+)"[^{}]*"tool"\s*:\s*"send_media"[^{}]*\}'
        match = re.search(pattern2, response_text)

    if match:
        media_key = match.group(1)
        if media_key in media_library:
            logger.info("LLM tool call detected: send_media('%s')", media_key)
            return media_library[media_key]
        else:
            logger.warning(
                "LLM called send_media with unknown key '%s'. Available: %s",
                media_key, list(media_library.keys()),
            )

    return None


def _clean_tool_call_from_text(text: str) -> str:
    """Remove the JSON tool call from the response text so we send clean text to the user."""
    import re
    # Remove the JSON tool call line
    cleaned = re.sub(
        r'\{[^{}]*"tool"\s*:\s*"(?:send_media|human_handover)"[^{}]*\}',
        "",
        text,
    )
    return cleaned.strip()


async def llm_reasoning_node(state: AgentState) -> dict:
    """
    Invoke the LLM to decide the next conversational step.

    The LLM sees:
    - The tenant's system prompt (brand personality, instructions)
    - Available media assets it can dispatch
    - Last 5 messages of conversation history
    - The current customer message

    It decides: reply with plain text, or trigger send_media(key) for a media asset.
    """
    system_prompt = state.get("system_prompt", "You are a helpful assistant.")
    media_library = state.get("media_library", {})
    chat_history = state.get("chat_history", [])
    message_text = state.get("message_text", "")
    tenant_id = state.get("tenant_id", "unknown")

    logger.info("LLM reasoning: tenant=%s, message='%s...'", tenant_id, message_text[:50])

    # ── Build the system message with media tool instructions ────────────────
    media_instructions = _build_media_tool_description(media_library)
    full_system_prompt = f"{system_prompt}\n\n{media_instructions}"

    # ── Build messages array ─────────────────────────────────────────────────
    messages = [SystemMessage(content=full_system_prompt)]

    # Add chat history (skip the current message which is the last inbound)
    # The history already includes the current inbound from the acknowledge node,
    # but we add it explicitly as the final HumanMessage below for clarity
    for msg in chat_history[:-1]:  # Exclude last one (it's the current message)
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    # Add the current customer message
    message_type = state.get("message_type", "text")
    media_url = state.get("media_url")

    if message_type == "image" and media_url:
        img_url = media_url if media_url.startswith("http") else f"https://mock.whatsapp.api/media/{media_url}"
        content_list = [
            {
                "type": "text",
                "text": message_text or "The customer sent an image. Please describe and analyze it, and respond to the customer's request using your tenant instructions.",
            },
            {
                "type": "image_url",
                "image_url": {"url": img_url},
            },
        ]
        messages.append(HumanMessage(content=content_list))
        logger.info("Multimodal HumanMessage constructed for LLM: url=%s", img_url)
    else:
        messages.append(HumanMessage(content=message_text))

    # ── Invoke LLM ───────────────────────────────────────────────────────────
    llm = _build_llm()

    if llm is None:
        # Fallback when LLM is not available — return a default response
        logger.warning("LLM not available — generating fallback response")
        return {
            "response_type": "text",
            "response_text": (
                "Thank you for your message! I'm currently unable to process "
                "requests, but a team member will assist you shortly."
            ),
            "response_media_url": None,
            "response_media_filename": None,
        }

    try:
        response = await llm.ainvoke(messages)
        response_text = response.content if hasattr(response, "content") else str(response)
        logger.info("LLM response received (%d chars)", len(response_text))

        # Check for JSON human_handover tool call in text
        if "human_handover" in response_text:
            import re
            pattern_handover = r'\{[^{}]*"tool"\s*:\s*"human_handover"[^{}]*\}'
            if re.search(pattern_handover, response_text):
                clean_text = _clean_tool_call_from_text(response_text)
                logger.info("LLM human_handover tool call detected")
                return {
                    "response_type": "handover",
                    "response_text": clean_text or "I apologize for the frustration. Handing you over to a human assistant.",
                    "response_media_url": None,
                    "response_media_filename": None,
                }

        # ── Check for native tool calls (if LLM supports structured tool calling)
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                tool_args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})

                if tool_name == "send_media":
                    media_key = tool_args.get("media_key", "")
                    if media_key in media_library:
                        item = media_library[media_key]
                        media_type = item.get("media_type", "document")
                        logger.info("Native tool call: send_media('%s') -> %s", media_key, media_type)
                        return {
                            "response_type": media_type,
                            "response_text": _clean_tool_call_from_text(response_text) or None,
                            "response_media_url": item["url"],
                            "response_media_filename": item.get("filename"),
                        }

        # ── Check for JSON tool call in text response ────────────────────────
        tool_match = _parse_tool_call(response_text, media_library)
        if tool_match is not None:
            media_type = tool_match.get("media_type", "document")
            clean_text = _clean_tool_call_from_text(response_text)
            return {
                "response_type": media_type,
                "response_text": clean_text or None,
                "response_media_url": tool_match["url"],
                "response_media_filename": tool_match.get("filename"),
            }

        # ── Plain text response ──────────────────────────────────────────────
        return {
            "response_type": "text",
            "response_text": response_text,
            "response_media_url": None,
            "response_media_filename": None,
        }

    except Exception as exc:
        logger.error("LLM invocation failed: %s", exc, exc_info=True)
        return {
            "response_type": "text",
            "response_text": (
                "I apologize, but I'm experiencing a temporary issue. "
                "Please try again in a moment, or a team member will assist you."
            ),
            "response_media_url": None,
            "response_media_filename": None,
            "error": f"LLM error: {exc}",
        }
