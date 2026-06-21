"""
LangGraph agent package.

Public API:
    from app.agent import agent_graph

    result = await agent_graph.ainvoke({
        "inbound_message_id": "...",
        "customer_phone": "+91...",
        "tenant_id": "luxury-furniture",
        "message_text": "Show me your catalog",
        "message_type": "text",
    })
"""

from app.agent.graph import agent_graph
from app.agent.state import AgentState

__all__ = ["agent_graph", "AgentState"]
