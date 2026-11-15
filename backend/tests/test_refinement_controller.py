"""
OCTS AI - Refinement Controller Unit Tests
Verifies decision engine, threshold evaluation, clarification bypass, and bounded retry loops.
"""

from backend.config import Settings
from backend.refinement.controller import RefinementController


def test_controller_bypasses_when_refinement_disabled():
    """Verify refinement is not triggered when refinement_enabled is False."""
    settings = Settings(refinement_enabled=False)
    controller = RefinementController(settings=settings)

    state = {
        "quality_score": 50.0,
        "selected_persona_id": "narrative_architect",
        "recovery_attempts": 0,
    }

    decision = controller.evaluate_state(state)
    assert decision.should_refine is False
    assert "disabled" in decision.trigger_reason.lower()


def test_controller_bypasses_on_clarification():
    """Verify refinement is bypassed when request requires user clarification."""
    controller = RefinementController()

    state = {
        "needs_clarification": True,
        "quality_score": 40.0,
        "recovery_attempts": 0,
    }

    decision = controller.evaluate_state(state)
    assert decision.should_refine is False
    assert "clarification" in decision.trigger_reason.lower()


def test_controller_bypasses_when_threshold_met():
    """Verify refinement is not triggered when quality score meets threshold."""
    controller = RefinementController()

    state = {
        "quality_score": 75.0,
        "selected_persona_id": "narrative_architect",
        "recovery_attempts": 0,
    }

    decision = controller.evaluate_state(state)
    assert decision.should_refine is False
    assert "meets or exceeds" in decision.trigger_reason.lower()


def test_controller_triggers_when_score_below_threshold():
    """Verify refinement is triggered with peer review when quality score is below threshold."""
    controller = RefinementController()

    state = {
        "quality_score": 62.0,
        "selected_persona_id": "narrative_architect",
        "recovery_attempts": 0,
        "best_evaluation": {
            "quality_score": 62.0,
            "criteria_breakdown": [
                {
                    "criterion_id": "narrative_coherence",
                    "criterion_name": "Narrative Coherence",
                    "score": 55.0,
                    "max_score": 100.0,
                    "weight": 0.5,
                    "evidence": "Pacing sag in middle.",
                    "status": "passed",
                }
            ],
        },
    }

    decision = controller.evaluate_state(state)
    assert decision.should_refine is True
    assert decision.attempt_number == 1
    assert decision.target_persona_id == "narrative_architect"
    assert decision.peer_reviewer_id == "lore_continuity_keeper"
    assert len(decision.weak_criteria) == 1


def test_controller_terminates_at_max_recovery_attempts():
    """Verify refinement is terminated once max_recovery_attempts (2) is reached."""
    controller = RefinementController()

    state = {
        "quality_score": 65.0,
        "selected_persona_id": "narrative_architect",
        "recovery_attempts": 2,
    }

    decision = controller.evaluate_state(state)
    assert decision.should_refine is False
    assert "maximum recovery attempts" in decision.trigger_reason.lower()
