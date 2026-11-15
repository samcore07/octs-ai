"""
OCTS AI - Deterministic Reliability Checks
Concrete execution checks verifying pipeline integrity, schema validity, and execution invariants.
"""

from typing import Any, Dict, List, Optional
from backend.agents.registry import AgentRegistry, get_registry
from backend.evaluation.schemas import (
    CheckSeverity,
    CriterionStatus,
    ReliabilityCheckResult,
)


def check_output_exists(state: Dict[str, Any]) -> ReliabilityCheckResult:
    """Verifies that the generated output is not None."""
    output = state.get("generated_output")
    if output is not None and isinstance(output, str):
        return ReliabilityCheckResult(
            check_id="output_exists",
            check_name="Output Presence Verification",
            status=CriterionStatus.PASSED,
            severity=CheckSeverity.CRITICAL,
            explanation="Generated output exists and is a valid string payload.",
        )
    return ReliabilityCheckResult(
        check_id="output_exists",
        check_name="Output Presence Verification",
        status=CriterionStatus.FAILED,
        severity=CheckSeverity.CRITICAL,
        explanation="Generated output is missing or null.",
    )


def check_output_not_empty(state: Dict[str, Any]) -> ReliabilityCheckResult:
    """Verifies that the generated output contains non-whitespace content."""
    output = state.get("generated_output")
    if output and isinstance(output, str) and output.strip():
        return ReliabilityCheckResult(
            check_id="output_not_empty",
            check_name="Non-Empty Payload Verification",
            status=CriterionStatus.PASSED,
            severity=CheckSeverity.CRITICAL,
            explanation=f"Generated output contains substantive content ({len(output.strip())} chars).",
        )
    return ReliabilityCheckResult(
        check_id="output_not_empty",
        check_name="Non-Empty Payload Verification",
        status=CriterionStatus.FAILED,
        severity=CheckSeverity.CRITICAL,
        explanation="Generated output is empty or solely whitespace.",
    )


def check_persona_resolved(
    state: Dict[str, Any],
    registry: Optional[AgentRegistry] = None,
) -> ReliabilityCheckResult:
    """Verifies that the assigned specialist persona exists in the AgentRegistry."""
    active_reg = registry or get_registry()
    persona_id = state.get("selected_persona_id")

    if not persona_id:
        return ReliabilityCheckResult(
            check_id="persona_resolved",
            check_name="Persona Registry Resolution",
            status=CriterionStatus.FAILED,
            severity=CheckSeverity.CRITICAL,
            explanation="No persona ID was recorded in orchestration state.",
        )

    persona = active_reg.get_persona(persona_id)
    if persona:
        return ReliabilityCheckResult(
            check_id="persona_resolved",
            check_name="Persona Registry Resolution",
            status=CriterionStatus.PASSED,
            severity=CheckSeverity.CRITICAL,
            explanation=f"Persona '{persona_id}' successfully resolved in AgentRegistry.",
        )

    return ReliabilityCheckResult(
        check_id="persona_resolved",
        check_name="Persona Registry Resolution",
        status=CriterionStatus.FAILED,
        severity=CheckSeverity.CRITICAL,
        explanation=f"Persona '{persona_id}' is not registered in the system.",
    )


def check_persona_discipline_match(
    state: Dict[str, Any],
    registry: Optional[AgentRegistry] = None,
) -> ReliabilityCheckResult:
    """Verifies that the selected persona aligns with the routed discipline."""
    active_reg = registry or get_registry()
    persona_id = state.get("selected_persona_id")
    discipline_id = state.get("discipline_id")

    if not persona_id or not discipline_id:
        return ReliabilityCheckResult(
            check_id="persona_discipline_match",
            check_name="Discipline-Persona Alignment",
            status=CriterionStatus.FAILED,
            severity=CheckSeverity.WARNING,
            explanation="Missing persona or discipline identifier in orchestration state.",
        )

    persona = active_reg.get_persona(persona_id)
    if persona and persona.discipline_id == discipline_id:
        return ReliabilityCheckResult(
            check_id="persona_discipline_match",
            check_name="Discipline-Persona Alignment",
            status=CriterionStatus.PASSED,
            severity=CheckSeverity.WARNING,
            explanation=f"Persona '{persona_id}' strictly matches discipline '{discipline_id}'.",
        )

    return ReliabilityCheckResult(
        check_id="persona_discipline_match",
        check_name="Discipline-Persona Alignment",
        status=CriterionStatus.FAILED,
        severity=CheckSeverity.WARNING,
        explanation=(
            f"Persona '{persona_id}' discipline mismatch. "
            f"Expected '{discipline_id}', found '{getattr(persona, 'discipline_id', None)}'."
        ),
    )


def check_execution_successful(state: Dict[str, Any]) -> ReliabilityCheckResult:
    """Verifies that orchestration completed without unhandled node errors."""
    status = state.get("execution_status")
    error = state.get("execution_error")

    valid_success_statuses = (
        "output_validated",
        "completed",
        "executed",
        "refinement_executed",
        "refining",
        "refinement_complete",
    )

    if status in valid_success_statuses and not error:
        return ReliabilityCheckResult(
            check_id="execution_successful",
            check_name="Workflow Execution Health",
            status=CriterionStatus.PASSED,
            severity=CheckSeverity.CRITICAL,
            explanation=f"Workflow completed successfully without unhandled node errors (status='{status}').",
        )

    return ReliabilityCheckResult(
        check_id="execution_successful",
        check_name="Workflow Execution Health",
        status=CriterionStatus.FAILED,
        severity=CheckSeverity.CRITICAL,
        explanation=f"Execution did not cleanly complete (status='{status}', error='{error}').",
    )


def check_latency_recorded(state: Dict[str, Any]) -> ReliabilityCheckResult:
    """Verifies that request latency was measured."""
    latency = state.get("latency_ms")
    started_at = state.get("started_at")

    if latency is not None and latency >= 0:
        return ReliabilityCheckResult(
            check_id="latency_recorded",
            check_name="Execution Telemetry Verification",
            status=CriterionStatus.PASSED,
            severity=CheckSeverity.INFO,
            explanation=f"Execution latency was accurately captured ({latency} ms).",
        )
    elif started_at is not None:
        return ReliabilityCheckResult(
            check_id="latency_recorded",
            check_name="Execution Telemetry Verification",
            status=CriterionStatus.PASSED,
            severity=CheckSeverity.INFO,
            explanation="Execution start timestamp captured; latency calculation in progress.",
        )

    return ReliabilityCheckResult(
        check_id="latency_recorded",
        check_name="Execution Telemetry Verification",
        status=CriterionStatus.FAILED,
        severity=CheckSeverity.INFO,
        explanation="No latency or timestamp metrics were recorded.",
    )


def check_substantive_length(
    state: Dict[str, Any],
    min_length: int = 25,
) -> ReliabilityCheckResult:
    """Verifies that the generated output meets minimum length threshold for creative content."""
    output = state.get("generated_output", "")
    length = len(output.strip()) if isinstance(output, str) else 0

    if length >= min_length:
        return ReliabilityCheckResult(
            check_id="substantive_length",
            check_name="Substantive Response Length",
            status=CriterionStatus.PASSED,
            severity=CheckSeverity.WARNING,
            explanation=f"Response length ({length} chars) satisfies substantive threshold ({min_length} chars).",
        )

    return ReliabilityCheckResult(
        check_id="substantive_length",
        check_name="Substantive Response Length",
        status=CriterionStatus.FAILED,
        severity=CheckSeverity.WARNING,
        explanation=f"Response length ({length} chars) is below expected threshold ({min_length} chars).",
    )
