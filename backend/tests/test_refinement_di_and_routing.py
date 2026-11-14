"""Phase 3 Architectural Refinement Tests: Dependency Injection & Routing Logic.

Verifies:
1. Explicit model dependency injection into OrchestrationExecutor and graph nodes.
2. Zero coupling between backend/orchestration and server.py.
3. Intelligent ambiguous-routing handling across Cases A, B, C, and D.
4. Short-circuiting execution without LLM invocation when clarification is required.
"""

from unittest.mock import MagicMock
import pytest

from backend.orchestration.executor import OrchestrationExecutor
from backend.agents.routing.classifier import AgentRouter
from backend.agents.registry import AgentRegistry
from backend.schemas import PromptRequest, PromptResponse


# ===========================================================================
# 1. Dependency Injection Tests (Improvement A)
# ===========================================================================

def test_dependency_injection_no_server_import_in_orchestration():
    """Verify that backend.orchestration modules do NOT import server.py."""
    import backend.orchestration.nodes as nodes
    import backend.orchestration.graph as graph
    import backend.orchestration.executor as executor

    assert not hasattr(nodes, "server")
    assert not hasattr(graph, "server")
    assert not hasattr(executor, "server")


def test_executor_with_explicitly_injected_mock_model():
    """Verify OrchestrationExecutor executes using solely an injected mock model."""
    mock_model = MagicMock()
    mock_model.invoke.return_value.content = "Injected model creative response."

    executor = OrchestrationExecutor(model=mock_model)
    request = PromptRequest(
        prompt="Write a three-act structure outline.",
        role="writers",
        task_type="story_craft",
    )

    response = executor.execute(request)

    assert isinstance(response, PromptResponse)
    assert response.reply == "Injected model creative response."
    assert response.role == "writers"
    assert response.agent_used == "narrative_architect"
    assert response.execution_status == "completed"
    assert response.needs_clarification is False
    assert mock_model.invoke.called


def test_executor_swapping_injected_models():
    """Verify that distinct executor instances use their respective injected models independently."""
    mock_model_1 = MagicMock()
    mock_model_1.invoke.return_value.content = "Response from model Alpha."

    mock_model_2 = MagicMock()
    mock_model_2.invoke.return_value.content = "Response from model Beta."

    executor_1 = OrchestrationExecutor(model=mock_model_1)
    executor_2 = OrchestrationExecutor(model=mock_model_2)

    req = PromptRequest(prompt="Compose a melody with chords.", role="musicians")

    res_1 = executor_1.execute(req)
    res_2 = executor_2.execute(req)

    assert res_1.reply == "Response from model Alpha."
    assert res_2.reply == "Response from model Beta."
    assert mock_model_1.invoke.call_count == 1
    assert mock_model_2.invoke.call_count == 1


# ===========================================================================
# 2. Intelligent Routing Tests (Improvement B)
# ===========================================================================

def test_case_a_discipline_and_specialist_clear():
    """Case A: Discipline and specialist craft signal are clear -> routes normally and calls model."""
    mock_model = MagicMock()
    mock_model.invoke.return_value.content = "Color palette definition."

    executor = OrchestrationExecutor(model=mock_model)
    request = PromptRequest(
        prompt="Generate design tokens and hex color codes for WCAG AA compliance.",
        role="designers",
    )

    response = executor.execute(request)

    assert response.agent_used == "design_token_palette_architect"
    assert response.role == "designers"
    assert response.needs_clarification is False
    assert response.execution_status == "completed"
    assert mock_model.invoke.called


def test_case_b_discipline_known_specialist_uncertain():
    """Case B: Discipline known via role, but specialist inquiry is vague -> falls back to discipline lead, calls model."""
    mock_model = MagicMock()
    mock_model.invoke.return_value.content = "Musician lead creative advice."

    executor = OrchestrationExecutor(model=mock_model)
    # Generic musical creative block - no specific lyrics/chords/structure/sonic tokens
    request = PromptRequest(
        prompt="I have creative block and don't know what to do next with my track.",
        role="musicians",
    )

    response = executor.execute(request)

    assert response.role == "musicians"
    # Should fall back to track_structure_architect or lead without needing user clarification
    assert response.agent_used in ["track_structure_architect", "lyricist_meter_engine", "harmonic_arranger"]
    assert response.needs_clarification is False
    assert response.execution_status == "completed"
    assert mock_model.invoke.called


def test_case_c_discipline_ambiguous_short_circuits_without_llm():
    """Case C: Discipline is ambiguous and no role provided -> short-circuits, returns clarification, NO LLM call."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = AssertionError("LLM should NOT be invoked for ambiguous routing!")

    executor = OrchestrationExecutor(model=mock_model)
    # Ambiguous prompt across disciplines with no explicit role
    request = PromptRequest(
        prompt="I want to create something interesting and impactful today.",
        role=None,
    )

    response = executor.execute(request)

    assert response.needs_clarification is True
    assert response.clarification_question is not None
    assert "creative discipline" in response.clarification_question.lower()
    # Backward compatibility: reply contains clarification question
    assert response.reply == response.clarification_question
    assert response.execution_status == "completed_clarification_required"
    # Verify Gemini LLM was never invoked
    mock_model.invoke.assert_not_called()


def test_case_d_invalid_discipline_controlled_fallback():
    """Case D: Unknown discipline string -> router detects ambiguity or falls back safely."""
    router = AgentRouter()
    result = router.route("Help me write an outline", discipline_id="space_exploration")

    # Either triggers clarification or falls back safely, never crashes
    assert result.discipline_id in [None, "writers", "musicians", "creators", "designers"]
    if result.needs_clarification:
        assert result.clarification_question is not None
    else:
        assert result.persona_id is not None
