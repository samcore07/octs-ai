"""
OCTS AI - Orchestration Execution Tests
Verifies that all 4 creative disciplines execute through the single shared LangGraph pipeline.
"""

from unittest.mock import MagicMock
import pytest
from backend.orchestration.executor import OrchestrationExecutor


@pytest.fixture
def mock_gemini():
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Verified craft response from specialist agent."
    mock_model.invoke.return_value = mock_response
    return mock_model


def test_shared_execution_writers(mock_gemini):
    """Verify writers task executes through narrative_architect."""
    executor = OrchestrationExecutor(model_override=mock_gemini)
    res = executor.execute_prompt(
        prompt="Design a 3-act narrative outline with high stakes.",
        role="writers",
    )
    assert res.role == "writers"
    assert res.agent_used == "narrative_architect"
    assert res.reply == "Verified craft response from specialist agent."
    assert res.latency_ms is not None

    # Verify that the specialist's system prompt reached the model
    call_args = mock_gemini.invoke.call_args[0][0]
    assert "ROLE: Narrative Architect" in call_args[0].content


def test_shared_execution_musicians(mock_gemini):
    """Verify musicians task executes through lyricist_meter_engine."""
    executor = OrchestrationExecutor(model_override=mock_gemini)
    res = executor.execute_prompt(
        prompt="Help me write lyrics with a tight rhyme scheme and meter.",
        role="musicians",
    )
    assert res.role == "musicians"
    assert res.agent_used == "lyricist_meter_engine"
    assert res.reply == "Verified craft response from specialist agent."

    call_args = mock_gemini.invoke.call_args[0][0]
    assert "ROLE: Lyricist & Meter Engine" in call_args[0].content


def test_shared_execution_creators(mock_gemini):
    """Verify creators task executes through hook_retention_architect."""
    executor = OrchestrationExecutor(model_override=mock_gemini)
    res = executor.execute_prompt(
        prompt="Create a high-retention video hook for the first 3 seconds.",
        role="creators",
    )
    assert res.role == "creators"
    assert res.agent_used == "hook_retention_architect"
    assert res.reply == "Verified craft response from specialist agent."

    call_args = mock_gemini.invoke.call_args[0][0]
    assert "ROLE: Hook & Retention Architect" in call_args[0].content


def test_shared_execution_designers(mock_gemini):
    """Verify designers task executes through design_token_palette_architect."""
    executor = OrchestrationExecutor(model_override=mock_gemini)
    res = executor.execute_prompt(
        prompt="Generate a semantic design tokens color palette that passes WCAG 2.2 AAA.",
        role="designers",
    )
    assert res.role == "designers"
    assert res.agent_used == "design_token_palette_architect"
    assert res.reply == "Verified craft response from specialist agent."

    call_args = mock_gemini.invoke.call_args[0][0]
    assert "ROLE: Design Token & Palette Architect" in call_args[0].content


def test_model_provider_failure_handling():
    """Verify model provider error raises graceful exception without crashing."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = RuntimeError("Resource Exhausted (Quota exceeded)")

    executor = OrchestrationExecutor(model_override=mock_model)
    with pytest.raises(RuntimeError) as exc_info:
        executor.execute_prompt(
            prompt="Outline a story",
            role="writers",
        )
    assert "Resource Exhausted" in str(exc_info.value)


def test_recursion_limit_configured():
    """Verify graph invocation config contains bounded recursion limit."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Response"
    mock_model.invoke.return_value = mock_response

    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "execution_status": "completed",
        "generated_output": "Success",
        "selected_persona_id": "narrative_architect",
        "discipline_id": "writers",
        "latency_ms": 10,
    }

    executor = OrchestrationExecutor(graph=mock_graph)
    executor.execute_prompt(prompt="Test prompt", role="writers")

    invoked_config = mock_graph.invoke.call_args[1].get("config", {})
    assert "recursion_limit" in invoked_config
    assert invoked_config["recursion_limit"] == executor.settings.max_recursion_limit
