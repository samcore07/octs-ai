"""
OCTS AI - LangGraph Workflow Compilation & Structural Tests
Verifies that the StateGraph compiles, contains all required nodes/edges, and branches correctly.
"""

from unittest.mock import MagicMock
import pytest
from backend.orchestration.graph import build_orchestration_graph, get_orchestration_graph
from backend.orchestration.state import OrchestrationState


def test_graph_compilation():
    """Verify that the orchestration graph builds and compiles without errors."""
    workflow = build_orchestration_graph()
    compiled = workflow.compile()
    assert compiled is not None


def test_graph_singleton_reusability():
    """Verify get_orchestration_graph() returns a compiled singleton graph."""
    graph1 = get_orchestration_graph()
    graph2 = get_orchestration_graph()
    assert graph1 is graph2


def test_graph_node_inventory():
    """Verify all 7 logical nodes are present in the workflow graph."""
    workflow = build_orchestration_graph()
    nodes = workflow.nodes
    expected_nodes = [
        "validate_input",
        "route_request",
        "handle_routing_fallback",
        "prepare_persona",
        "execute_model",
        "validate_output",
        "finalize_execution",
    ]
    for node in expected_nodes:
        assert node in nodes


def test_graph_validation_failure_short_circuit():
    """Verify that an invalid input (empty prompt) short-circuits directly to finalize_execution without invoking the model."""
    mock_model = MagicMock()
    graph = get_orchestration_graph(model_override=mock_model)

    initial_state: OrchestrationState = {
        "request_id": "test-val-short-circuit",
        "original_prompt": "   ",
        "discipline_id": "writers",
        "execution_status": "initialized",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["execution_status"] == "failed"
    assert "validation" in final_state.get("execution_error", "").lower()
    # Model should NEVER be invoked on validation failure
    mock_model.invoke.assert_not_called()


def test_graph_successful_pipeline_execution():
    """Verify that a valid prompt flows through all nodes to completion."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Verified story architecture output."
    mock_model.invoke.return_value = mock_response

    graph = get_orchestration_graph(model_override=mock_model)

    initial_state: OrchestrationState = {
        "request_id": "test-success-pipeline",
        "original_prompt": "Design a 3-act narrative outline with high stakes.",
        "discipline_id": "writers",
        "execution_status": "initialized",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["execution_status"] == "completed"
    assert final_state["selected_persona_id"] == "narrative_architect"
    assert final_state["generated_output"] == "Verified story architecture output."
    assert mock_model.invoke.called


def test_graph_output_validation_failure_handling():
    """Verify that if the model returns an empty string, output validation catches it."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "   "  # Empty whitespace output
    mock_model.invoke.return_value = mock_response

    graph = get_orchestration_graph(model_override=mock_model)

    initial_state: OrchestrationState = {
        "request_id": "test-empty-output",
        "original_prompt": "Tell me a joke",
        "discipline_id": "writers",
        "execution_status": "initialized",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["execution_status"] == "failed"
    assert "empty" in final_state.get("execution_error", "").lower()
