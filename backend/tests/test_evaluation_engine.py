"""
OCTS AI - Evaluation Engine Coordinator Tests (Phase 4)
Verifies orchestration evaluation coordination, disabled evaluation mode,
clarification handling, upstream failure resilience, and defensive error containment.
"""

from unittest.mock import MagicMock
from backend.config import Settings
from backend.evaluation.engine import EvaluationEngine
from backend.evaluation.schemas import EvaluationMode


def test_evaluation_engine_completed_execution():
    """Verify EvaluationEngine evaluates valid execution state with quality, reliability, and TrustScore."""
    engine = EvaluationEngine()
    state = {
        "original_prompt": "Write a three-act outline for a sci-fi novel.",
        "generated_output": (
            "### Act I: The Discovery\n"
            "Astronomers detect an unnatural signal.\n\n"
            "### Act II: The Journey\n"
            "The crew launches toward the source.\n\n"
            "### Act III: The Convergence\n"
            "They encounter the remnants of an ancient beacon."
        ),
        "discipline_id": "writers",
        "selected_persona_id": "narrative_architect",
        "execution_status": "output_validated",
        "latency_ms": 500,
    }

    result = engine.evaluate_execution(state, mode_override=EvaluationMode.DETERMINISTIC)

    assert result.evaluation_status == "completed"
    assert result.quality_score is not None
    assert result.reliability_score is not None
    assert result.trust_score is not None
    assert result.trust_breakdown is not None
    assert len(result.criteria_breakdown) == 6
    assert len(result.reliability_checks) == 7
    assert result.evaluation_coverage == 1.0
    assert result.evaluation_duration_ms >= 0


def test_evaluation_engine_disabled_via_config():
    """Verify EvaluationEngine skips evaluation cleanly when EVALUATION_ENABLED is False."""
    settings = Settings(evaluation_enabled=False)
    engine = EvaluationEngine(settings=settings)
    state = {
        "original_prompt": "Some prompt",
        "generated_output": "Some output",
        "discipline_id": "writers",
        "selected_persona_id": "narrative_architect",
        "execution_status": "output_validated",
    }

    result = engine.evaluate_execution(state)

    assert result.evaluation_status == "skipped"
    assert result.quality_score is None
    assert result.reliability_score is None
    assert result.trust_score is None
    assert "disabled" in result.evaluation_summary.lower()


def test_evaluation_engine_clarification_no_fabricated_trust_score():
    """Verify clarification state skips evaluation completely without fabricating checks or scores."""
    engine = EvaluationEngine()
    state = {
        "original_prompt": "Help me make something amazing",
        "discipline_id": None,
        "selected_persona_id": None,
        "needs_clarification": True,
        "clarification_question": "Which creative area are you working in?",
        "generated_output": "Which creative area are you working in?",
        "execution_status": "needs_clarification",
    }

    result = engine.evaluate_execution(state)

    assert result.evaluation_status == "skipped"
    assert result.quality_score is None
    assert result.reliability_score is None
    assert result.trust_score is None
    assert result.trust_breakdown is None
    assert len(result.criteria_breakdown) == 0
    assert len(result.reliability_checks) == 0
    assert result.evaluation_coverage == 0.0
    assert result.evaluation_method == "skipped"
    assert "clarification" in result.evaluation_summary.lower()


def test_evaluation_engine_judge_fallback_transparency():
    """Verify fallback from failed LLM judge to deterministic heuristics preserves metadata."""
    mock_judge = MagicMock()
    from backend.evaluation.schemas import JudgeStatus
    # Judge fails with timeout
    mock_judge.evaluate.return_value = (None, JudgeStatus.TIMEOUT, "Model API timeout after 10s")

    engine = EvaluationEngine(judge=mock_judge)
    state = {
        "original_prompt": "Write a three-act outline for a fantasy tale.",
        "generated_output": (
            "### Act I: The Summoning\n"
            "A mage calls upon the ancient elemental forces.\n\n"
            "### Act II: The Treason\n"
            "The elemental turns against the kingdom.\n\n"
            "### Act III: The Binding\n"
            "The rift is sealed with blood and sorrow."
        ),
        "discipline_id": "writers",
        "selected_persona_id": "narrative_architect",
        "execution_status": "output_validated",
        "latency_ms": 450,
    }

    result = engine.evaluate_execution(state, mode_override=EvaluationMode.LLM_JUDGE)

    assert result.evaluation_status == "completed"
    assert result.evaluation_method == "deterministic"
    assert result.judge_status == JudgeStatus.TIMEOUT
    assert result.fallback_triggered is True
    assert "timeout" in result.fallback_reason.lower()
    assert result.quality_score is not None
    assert result.reliability_score is not None
    assert result.trust_score is not None
    assert any("fallback" in lim.lower() for lim in result.limitations)


def test_evaluation_engine_upstream_execution_failure():
    """Verify upstream execution failure records reliability failure without fabricating quality score."""
    engine = EvaluationEngine()
    state = {
        "original_prompt": "Prompt causing failure",
        "generated_output": "Execution Error: The model provider failed.",
        "discipline_id": "writers",
        "selected_persona_id": "narrative_architect",
        "execution_status": "execution_failed",
        "execution_error": "Model provider timeout.",
    }

    result = engine.evaluate_execution(state)

    assert result.evaluation_status == "failed"
    assert result.quality_score is None
    assert result.trust_score is None
    assert result.reliability_score is not None
    # Execution failed check should be FAILED in reliability checks
    exec_chk = next(c for c in result.reliability_checks if c.check_id == "execution_successful")
    assert exec_chk.status.value == "failed"


def test_evaluation_engine_defensive_error_containment():
    """Verify unexpected evaluator crash returns failed status rather than raising unhandled exception."""
    mock_reg = MagicMock()
    mock_reg.get_evaluator.side_effect = RuntimeError("Database connection corrupted")

    engine = EvaluationEngine(evaluator_registry=mock_reg)
    state = {
        "original_prompt": "Prompt",
        "generated_output": "Output text",
        "discipline_id": "writers",
        "selected_persona_id": "narrative_architect",
        "execution_status": "output_validated",
    }

    result = engine.evaluate_execution(state)

    assert result.evaluation_status == "failed"
    assert "Database connection corrupted" in result.evaluation_summary
