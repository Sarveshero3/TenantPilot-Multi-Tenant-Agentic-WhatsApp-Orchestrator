"""
LangGraph agent graph — wires the 4-node pipeline.

Graph: acknowledge -> context_retriever -> llm_reasoning -> dispatcher -> END

This module builds and compiles the graph once, then exposes it as `agent_graph`
for use by the webhook handler.

Usage:
    from app.agent.graph import agent_graph

    result = await agent_graph.ainvoke({
        "inbound_message_id": "wamid.xxx",
        "customer_phone": "+919876543210",
        "tenant_id": "luxury-furniture",
        "message_text": "Can you send me your catalog?",
        "message_type": "text",
    })
"""

from __future__ import annotations

import logging

from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.nodes.acknowledge import acknowledge_node
from app.agent.nodes.context_retriever import context_retriever_node
from app.agent.nodes.llm_reasoning import llm_reasoning_node
from app.agent.nodes.dispatcher import dispatcher_node

logger = logging.getLogger(__name__)


def build_agent_graph() -> StateGraph:
    """
    Construct the 4-node LangGraph processing pipeline.

    Pipeline flow:
        [START]
           |
        acknowledge        → read receipt, typing ON, session upsert, inbound log
           |
        context_retriever  → tenant prompt, media library, last 5 messages
           |
        llm_reasoning      → invoke LLM, decide text vs. media tool call
           |
        dispatcher         → send WhatsApp message, typing OFF, outbound log
           |
        [END]
    """
    graph = StateGraph(AgentState)

    # ── Add nodes ────────────────────────────────────────────────────────────
    graph.add_node("acknowledge", acknowledge_node)
    graph.add_node("context_retriever", context_retriever_node)
    graph.add_node("llm_reasoning", llm_reasoning_node)
    graph.add_node("dispatcher", dispatcher_node)

    def route_after_acknowledge(state: AgentState) -> str:
        """Determine whether to proceed or end immediately if the session is human-monitored."""
        if state.get("skip_agent"):
            return END
        return "context_retriever"

    # ── Add edges ────────────────────────────────────────────────────────────
    graph.add_edge(START, "acknowledge")
    graph.add_conditional_edges(
        "acknowledge",
        route_after_acknowledge,
        {
            "context_retriever": "context_retriever",
            END: END,
        }
    )
    graph.add_edge("context_retriever", "llm_reasoning")
    graph.add_edge("llm_reasoning", "dispatcher")
    graph.add_edge("dispatcher", END)

    logger.info("Agent graph built: START -> acknowledge -> context_retriever -> llm_reasoning -> dispatcher -> END")
    return graph


# ── Compiled graph (module-level singleton) ──────────────────────────────────
# The compiled graph is the runnable that the webhook handler invokes.
agent_graph = build_agent_graph().compile()
