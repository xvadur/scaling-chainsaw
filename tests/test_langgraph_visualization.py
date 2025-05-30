"""
Tests for LangGraph Visualization Module
"""
import pytest
from aetheros_protocol.visualization.langgraph_config import AetheroGraphVisualizer, AgentState

@pytest.fixture
def sample_config():
    return {
        "agents": [
            {"agent_id": "planner_agent_001", "description_asl": {"purpose": "planning"}},
            {"agent_id": "scout_agent_001", "description_asl": {"purpose": "discovery"}},
        ]
    }

def test_initialize_graph(sample_config):
    visualizer = AetheroGraphVisualizer(sample_config)
    visualizer.initialize_graph()
    assert len(visualizer.graph.nodes) == 2
    assert "planner_agent_001" in visualizer.graph.nodes
    assert "scout_agent_001" in visualizer.graph.nodes

def test_add_agent_node(sample_config):
    visualizer = AetheroGraphVisualizer(sample_config)
    visualizer.add_agent_node("analyst_agent_001", {"purpose": "analysis"})
    assert "analyst_agent_001" in visualizer.graph.nodes

def test_update_agent_state(sample_config):
    visualizer = AetheroGraphVisualizer(sample_config)
    visualizer.initialize_graph()
    visualizer.update_agent_state("planner_agent_001", AgentState.PROCESSING)
    node_state = visualizer.graph.nodes["planner_agent_001"]["state"]
    assert node_state == AgentState.PROCESSING.value

def test_add_transition(sample_config):
    visualizer = AetheroGraphVisualizer(sample_config)
    visualizer.initialize_graph()
    visualizer.add_transition(
        "planner_agent_001",
        "scout_agent_001",
        {"stage": "planning_to_discovery"}
    )
    assert visualizer.graph.has_edge("planner_agent_001", "scout_agent_001")

def test_generate_mermaid_diagram(sample_config):
    visualizer = AetheroGraphVisualizer(sample_config)
    visualizer.initialize_graph()
    visualizer.add_transition(
        "planner_agent_001",
        "scout_agent_001",
        {"stage": "planning_to_discovery"}
    )
    diagram = visualizer.generate_mermaid_diagram()
    assert "graph TD" in diagram
    assert "planner_agent_001" in diagram
    assert "scout_agent_001" in diagram

def test_export_graph_data(sample_config):
    visualizer = AetheroGraphVisualizer(sample_config)
    visualizer.initialize_graph()
    visualizer.add_transition(
        "planner_agent_001",
        "scout_agent_001",
        {"stage": "planning_to_discovery"}
    )
    data = visualizer.export_graph_data()
    assert "nodes" in data
    assert "edges" in data
    assert any(node["id"] == "planner_agent_001" for node in data["nodes"])
    assert any(edge["source"] == "planner_agent_001" for edge in data["edges"])

if __name__ == "__main__":
    pytest.main(["-v", __file__])
