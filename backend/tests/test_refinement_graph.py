"""
OCTS AI - LangGraph Refinement Workflow Tests
Verifies full graph structure, refinement node inventory, conditional edges,
and bounded loop execution with mock model and evaluators.
"""

from unittest.mock import MagicMock
from backend.evaluation.engine import EvaluationEngine
from backend.orchestration.graph import build_orchestration_graph, get_orchestration_graph
from backend.orchestration.state import OrchestrationState
from backend.refinement.engine import RefinementEngine


def test_graph_contains_all_phase_5_nodes():
    """Verify that all Phase 5 refinement nodes are registered in the StateGraph."""
    workflow = build_orchestration_graph()
    nodes = workflow.nodes

    phase_5_nodes = [
        "refinement_controller",
        "peer_review",
        "synthesize_feedback",
        "refine_output",
        "evaluate_refinement",
        "improvement_analyzer",
    ]

    for node in phase_5_nodes:
        assert node in nodes, f"Expected node '{node}' not found in graph nodes."


def test_graph_bypasses_refinement_when_quality_high():
    """Verify graph skips refinement when initial generation quality meets or exceeds threshold."""
    mock_model = MagicMock()
    # High-quality response with structural headings and comprehensive content (>150 chars)
    mock_model.invoke.return_value.content = (
        "### Act I: The Awakening\n"
        "Elena discovered the ancient manuscript hidden within the obsidian altar.\n\n"
        "### Act II: The Conflict\n"
        "She confronted the guild master, refusing to surrender the celestial cipher.\n\n"
        "### Act III: The Climax\n"
        "With decisive action, she shattered the mirror, breaking the curse permanently."
    )

    graph = get_orchestration_graph(model_override=mock_model)

    initial_state: OrchestrationState = {
        "request_id": "test-high-quality-bypass",
        "original_prompt": "Write a three-act story outline with Elena and the celestial cipher.",
        "discipline_id": "writers",
        "selected_persona_id": "narrative_architect",
        "execution_status": "initialized",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["execution_status"] == "completed"
    assert final_state.get("quality_score", 0) >= 70.0
    # Refinement should not have run
    assert final_state.get("recovery_attempts", 0) == 0
    ref_meta = final_state.get("refinement_metadata", {})
    assert ref_meta.get("refinement_triggered") is False
    assert ref_meta.get("refinement_status") == "not_needed"


def test_graph_executes_refinement_loop_on_low_score():
    """Verify graph triggers refinement loop, peer review, and terminates when score is low."""
    mock_model = MagicMock()

    # Call 1: initial brief draft (low score)
    # Call 2: peer review JSON
    # Call 3: refined draft (improved with full structure)
    call_counts = {"count": 0}

    def _mock_invoke(messages):
        call_counts["count"] += 1
        count = call_counts["count"]
        mock_resp = MagicMock()
        if count == 1:
            # Short generation that scores low on length/structure
            mock_resp.content = "Short draft."
        elif count == 2:
            # Peer review JSON response
            mock_resp.content = (
                '{"strengths": ["Clear core"], "actionable_critique": ["Too brief"], '
                '"suggested_improvements": ["Expand acts"]}'
            )
        else:
            # Refined generation with full structure
            mock_resp.content = (
                "### Act I: Setup\nThe protagonist accepts the perilous quest.\n\n"
                "### Act II: Confrontation\nObstacles mount as enemies close in.\n\n"
                "### Act III: Resolution\nA hard-won victory restores balance."
            )
        return mock_resp

    mock_model.invoke.side_effect = _mock_invoke

    graph = get_orchestration_graph(model_override=mock_model)

    initial_state: OrchestrationState = {
        "request_id": "test-refinement-loop",
        "original_prompt": "Help me write a three-act plot outline.",
        "discipline_id": "writers",
        "selected_persona_id": "narrative_architect",
        "execution_status": "initialized",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["execution_status"] == "completed"
    assert final_state.get("recovery_attempts", 0) >= 1
    ref_meta = final_state.get("refinement_metadata", {})
    assert ref_meta.get("refinement_triggered") is True
    assert ref_meta.get("peer_review_conducted") is True
    assert ref_meta.get("reviewer_persona_id") == "lore_continuity_keeper"
    assert ref_meta.get("refinement_status") == "improved"
    assert "Act I" in final_state.get("generated_output", "")


def test_graph_strictly_bounds_to_max_recovery_attempts():
    """Verify graph never executes more than max_recovery_attempts even if score remains low."""
    mock_model = MagicMock()
    # Always returns short stub that fails threshold
    mock_model.invoke.return_value.content = "Stub."

    graph = get_orchestration_graph(model_override=mock_model)

    initial_state: OrchestrationState = {
        "request_id": "test-bounded-attempts",
        "original_prompt": "Outline",
        "discipline_id": "writers",
        "selected_persona_id": "narrative_architect",
        "execution_status": "initialized",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["execution_status"] == "completed"
    # Must never exceed max recovery attempts (2)
    assert final_state.get("recovery_attempts", 0) <= 2
    ref_meta = final_state.get("refinement_metadata", {})
    assert ref_meta.get("recovery_attempts") <= 2
