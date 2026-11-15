"""
OCTS AI - Reliability Evaluator Tests (Phase 4)
Verifies deterministic execution integrity checks: output existence, non-empty payload,
persona registry resolution, discipline alignment, execution health, and telemetry capture.
"""

from backend.evaluation.reliability.checks import (
    check_execution_successful,
    check_latency_recorded,
    check_output_exists,
    check_output_not_empty,
    check_persona_discipline_match,
    check_persona_resolved,
    check_substantive_length,
)
from backend.evaluation.reliability.evaluator import ReliabilityEvaluator
from backend.evaluation.schemas import CriterionStatus


def test_check_output_exists():
    """Verify output_exists check handles valid string, None, and non-string outputs."""
    valid_state = {"generated_output": "Sample output text."}
    res_pass = check_output_exists(valid_state)
    assert res_pass.status == CriterionStatus.PASSED

    none_state = {"generated_output": None}
    res_fail = check_output_exists(none_state)
    assert res_fail.status == CriterionStatus.FAILED

    non_str_state = {"generated_output": 12345}
    res_fail_type = check_output_exists(non_str_state)
    assert res_fail_type.status == CriterionStatus.FAILED


def test_check_output_not_empty():
    """Verify output_not_empty check handles substantive text vs whitespace."""
    state_valid = {"generated_output": "Valid text"}
    assert check_output_not_empty(state_valid).status == CriterionStatus.PASSED

    state_empty = {"generated_output": "   \n\t  "}
    assert check_output_not_empty(state_empty).status == CriterionStatus.FAILED


def test_check_persona_resolved():
    """Verify persona_resolved verifies existence in AgentRegistry."""
    state_valid = {"selected_persona_id": "narrative_architect"}
    assert check_persona_resolved(state_valid).status == CriterionStatus.PASSED

    state_invalid = {"selected_persona_id": "non_existent_specialist"}
    assert check_persona_resolved(state_invalid).status == CriterionStatus.FAILED

    state_missing = {}
    assert check_persona_resolved(state_missing).status == CriterionStatus.FAILED


def test_check_persona_discipline_match():
    """Verify persona_discipline_match ensures assigned persona belongs to routed discipline."""
    state_match = {
        "selected_persona_id": "narrative_architect",
        "discipline_id": "writers",
    }
    assert check_persona_discipline_match(state_match).status == CriterionStatus.PASSED

    state_mismatch = {
        "selected_persona_id": "narrative_architect",
        "discipline_id": "musicians",
    }
    assert check_persona_discipline_match(state_mismatch).status == CriterionStatus.FAILED


def test_check_execution_successful():
    """Verify execution_successful checks status and absence of execution errors."""
    state_ok = {
        "execution_status": "output_validated",
        "execution_error": None,
    }
    assert check_execution_successful(state_ok).status == CriterionStatus.PASSED

    state_err = {
        "execution_status": "execution_failed",
        "execution_error": "Connection error",
    }
    assert check_execution_successful(state_err).status == CriterionStatus.FAILED


def test_check_latency_recorded():
    """Verify latency_recorded captures latency or started_at timestamp."""
    state_lat = {"latency_ms": 350}
    assert check_latency_recorded(state_lat).status == CriterionStatus.PASSED

    state_empty = {}
    assert check_latency_recorded(state_empty).status == CriterionStatus.FAILED


def test_check_substantive_length():
    """Verify substantive_length threshold verification."""
    state_long = {"generated_output": "A sufficiently long creative response text that exceeds 25 characters."}
    assert check_substantive_length(state_long, min_length=25).status == CriterionStatus.PASSED

    state_short = {"generated_output": "Too short"}
    assert check_substantive_length(state_short, min_length=25).status == CriterionStatus.FAILED


def test_reliability_evaluator_all_checks():
    """Verify ReliabilityEvaluator runs all 7 deterministic checks."""
    evaluator = ReliabilityEvaluator()
    state = {
        "generated_output": "Comprehensive creative narrative outline.",
        "selected_persona_id": "narrative_architect",
        "discipline_id": "writers",
        "execution_status": "output_validated",
        "execution_error": None,
        "latency_ms": 420,
    }

    results = evaluator.evaluate(state)
    assert len(results) == 7
    assert all(chk.status == CriterionStatus.PASSED for chk in results)
