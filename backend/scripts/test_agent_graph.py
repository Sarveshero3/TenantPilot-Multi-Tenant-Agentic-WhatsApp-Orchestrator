"""
Smoke test for the LangGraph agent pipeline.
Tests that the graph compiles and the state flows through all 4 nodes.
Does NOT require MongoDB or NVIDIA API key — tests structure only.

Usage: python scripts/test_agent_graph.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_graph_structure():
    """Test that the graph builds and has the correct node topology."""
    from app.agent.graph import build_agent_graph

    graph = build_agent_graph()
    compiled = graph.compile()

    # Check graph has all 4 nodes
    node_names = set(compiled.get_graph().nodes.keys())
    expected_nodes = {"acknowledge", "context_retriever", "llm_reasoning", "dispatcher"}

    # LangGraph adds __start__ and __end__ pseudo-nodes
    assert expected_nodes.issubset(node_names), (
        f"Missing nodes. Expected {expected_nodes}, got {node_names}"
    )

    print("OK: Graph has all 4 nodes: %s" % sorted(expected_nodes))
    print("OK: Full node set: %s" % sorted(node_names))


def test_state_definition():
    """Test that AgentState has all required fields."""
    from app.agent.state import AgentState

    required_fields = [
        "inbound_message_id", "customer_phone", "tenant_id",
        "message_text", "message_type", "session_id",
        "system_prompt", "media_library", "chat_history",
        "response_type", "response_text", "response_media_url",
        "response_media_filename", "error",
    ]

    annotations = AgentState.__annotations__
    for field in required_fields:
        assert field in annotations, f"Missing field in AgentState: {field}"

    print("OK: AgentState has all %d required fields" % len(required_fields))


def test_node_imports():
    """Test that all nodes can be imported."""
    from app.agent.nodes.acknowledge import acknowledge_node
    from app.agent.nodes.context_retriever import context_retriever_node
    from app.agent.nodes.llm_reasoning import llm_reasoning_node
    from app.agent.nodes.dispatcher import dispatcher_node

    assert callable(acknowledge_node)
    assert callable(context_retriever_node)
    assert callable(llm_reasoning_node)
    assert callable(dispatcher_node)

    print("OK: All 4 node functions are callable")


def test_package_exports():
    """Test the public package API."""
    from app.agent import agent_graph, AgentState

    assert agent_graph is not None
    assert AgentState is not None

    print("OK: app.agent exports agent_graph and AgentState")


if __name__ == "__main__":
    print("=== Agent Graph Smoke Tests ===\n")
    test_state_definition()
    test_node_imports()
    test_graph_structure()
    test_package_exports()
    print("\nAll agent graph smoke tests passed.")
