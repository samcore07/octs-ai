"""
OCTS AI - Orchestration Individual Nodes Unit Tests
Unit tests for isolated logical nodes: validation, routing, preparation, execution, and finalization.
"""

from unittest.mock import MagicMock
import pytest
from backend.orchestration.nodes import (
    execute_model_node,
    finalize_execution_node,
    handle_routing_fallback_node,
    prepare_persona_node,
    route_request_node,
    validate_input_node,
    validate_output_node,
)
from backend.orchestration.state import OrchestrationState


# ---------------------------------------------------------------------------
# Node A: Input Validation Tests
# ---------------------------------------------------------------------------

def test_validate_input_node_valid():
    """Verify valid prompt passes and is trimmed."""
    state: OrchestrationState = {
        "original_prompt": "   How to write a hero journey?   ",
        "discipline_id": "writers",
    }
    result = validate_input_node(state)
    assert result["execution_status"] == "validated"
    assert result["original_prompt"] == "How to write a hero journey?"
    assert result["discipline_id"] == "writers"


def test_validate_input_node_empty():
    """Verify empty or whitespace-only prompt is rejected."""
    state: OrchestrationState = {"original_prompt": "   "}
    result = validate_input_node(state)
    assert result["execution_status"] == "validation_failed"
    assert "whitespace" in result["execution_error"].lower()


def test_validate_input_node_null():
    """Verify None prompt is rejected."""
    state: OrchestrationState = {"original_prompt": None}
    result = validate_input_node(state)
    assert result["execution_status"] == "validation_failed"


def test_validate_input_node_oversized():
    """Verify oversized prompts exceeding limit are rejected."""
    state: OrchestrationState = {"original_prompt": "a" * 50001}
    result = validate_input_node(state)
    assert result["execution_status"] == "validation_failed"
    assert "exceeds" in result["execution_error"].lower()


# ---------------------------------------------------------------------------
# Node B: Routing Tests
# ---------------------------------------------------------------------------

def test_route_request_node_valid():
    """Verify high-confidence routing sets persona and confidence."""
    state: OrchestrationState = {
        "original_prompt": "Help me design chords with modal interchange.",
        "discipline_id": "musicians",
    }
    result = route_request_node(state)
    assert result["execution_status"] == "routed"
    assert result["selected_persona_id"] == "harmonic_arranger"
    assert result["routing_confidence"] >= 0.70


def test_route_request_node_low_confidence_fallback():
    """Verify low-confidence or ambiguous queries trigger routing_fallback status."""
    mock_router = MagicMock()
    mock_result = MagicMock()
    mock_result.persona_id = "narrative_architect"
    mock_result.confidence = 0.35  # Below 0.40 threshold
    mock_result.rationale = "Ambiguous craft inquiry."
    mock_result.alternative_persona_id = None
    mock_router.route.return_value = mock_result

    state: OrchestrationState = {
        "original_prompt": "Ambiguous query",
        "discipline_id": "writers",
    }
    result = route_request_node(state, router=mock_router)
    assert result["execution_status"] == "routing_fallback"


def test_handle_routing_fallback_node():
    """Verify fallback node assigns the discipline lead persona with safe explanation."""
    state: OrchestrationState = {
        "original_prompt": "Something generic",
        "discipline_id": "designers",
    }
    result = handle_routing_fallback_node(state)
    assert result["execution_status"] == "routed"
    assert result["selected_persona_id"] == "concept_ideation_engine"
    assert "primary lead" in result["routing_rationale"]


# ---------------------------------------------------------------------------
# Node C: Persona Preparation Tests
# ---------------------------------------------------------------------------

def test_prepare_persona_node_valid():
    """Verify prompt template compilation and BaseMessage construction."""
    state: OrchestrationState = {
        "original_prompt": "How do I build tension in Act 2?",
        "selected_persona_id": "narrative_architect",
    }
    result = prepare_persona_node(state)
    assert result["execution_status"] == "prepared"
    assert "persona_system_prompt" in result
    assert "ROLE: Narrative Architect" in result["persona_system_prompt"]
    assert len(result["model_input"]) == 2
    # Ensure human input is separated
    assert result["model_input"][1].content == "How do I build tension in Act 2?"


def test_prepare_persona_node_unknown_persona():
    """Verify handling of unknown persona ID."""
    state: OrchestrationState = {
        "original_prompt": "Test prompt",
        "selected_persona_id": "non_existent_persona_123",
    }
    result = prepare_persona_node(state)
    assert result["execution_status"] == "preparation_failed"


# ---------------------------------------------------------------------------
# Node D: Model Execution Tests
# ---------------------------------------------------------------------------

def test_execute_model_node_success():
    """Verify model invocation extracts content and populates generated_output."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Synthesized response from Gemini."
    mock_model.invoke.return_value = mock_response

    state: OrchestrationState = {
        "model_input": ["msg1", "msg2"],
    }
    result = execute_model_node(state, model_override=mock_model)
    assert result["execution_status"] == "executed"
    assert result["generated_output"] == "Synthesized response from Gemini."


def test_execute_model_node_exception():
    """Verify provider exceptions are caught and recorded."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = RuntimeError("Quota exhausted")

    state: OrchestrationState = {
        "model_input": ["msg1", "msg2"],
    }
    result = execute_model_node(state, model_override=mock_model)
    assert result["execution_status"] == "execution_failed"
    assert "Quota exhausted" in result["execution_error"]


# ---------------------------------------------------------------------------
# Node E: Output Validation Tests
# ---------------------------------------------------------------------------

def test_validate_output_node_valid():
    """Verify non-empty output passes structural validation."""
    state: OrchestrationState = {
        "generated_output": "Non-empty output text.",
    }
    result = validate_output_node(state)
    assert result["execution_status"] == "output_validated"


def test_validate_output_node_empty():
    """Verify empty output triggers output_validation_failed."""
    state: OrchestrationState = {
        "generated_output": "   ",
    }
    result = validate_output_node(state)
    assert result["execution_status"] == "output_validation_failed"


# ---------------------------------------------------------------------------
# Node F: Finalization Tests
# ---------------------------------------------------------------------------

def test_finalize_execution_node():
    """Verify latency calculation and timestamp population."""
    import time
    started = time.perf_counter() - 0.05  # 50 ms ago
    state: OrchestrationState = {
        "started_at": started,
        "execution_status": "output_validated",
    }
    result = finalize_execution_node(state)
    assert result["execution_status"] == "completed"
    assert result["latency_ms"] >= 40
    assert result["completed_at"] is not None
