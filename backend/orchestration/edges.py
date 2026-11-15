"""
OCTS AI - Orchestration Graph Conditional Edges (Refined Phase 4)
Defines edge routing predicates for the LangGraph state graph including Evaluation Engine routing.
"""

from backend.orchestration.state import OrchestrationState


def route_after_input_validation(state: OrchestrationState) -> str:
    """
    Decides whether to proceed to context identification or short-circuit to finalization on validation error.
    """
    if state.get("execution_status") == "validation_failed":
        return "finalize_execution"
    return "identify_context"


def route_after_task_routing(state: OrchestrationState) -> str:
    """
    Decides routing branch:
      - If discipline is ambiguous (Case C) -> short-circuit to finalization (bypasses LLM & evaluation).
      - If discipline is known but specialist uncertain (Case B) -> safe specialist fallback.
      - If specialist is verified (Case A) -> prepare persona.
    """
    status = state.get("execution_status")
    if status == "needs_clarification":
        return "finalize_execution"
    if status == "routing_fallback":
        return "handle_routing_fallback"
    return "prepare_persona"


def route_after_persona_preparation(state: OrchestrationState) -> str:
    """
    Decides whether to execute the model or terminate early on prompt compilation error.
    """
    if state.get("execution_status") == "preparation_failed":
        return "finalize_execution"
    return "execute_model"


def route_after_model_execution(state: OrchestrationState) -> str:
    """
    Decides whether to validate model output or proceed to evaluation on provider execution failure.
    Provider failure proceeds to evaluation so deterministic reliability checks record the failure.
    """
    if state.get("execution_status") == "execution_failed":
        return "evaluate_execution"
    return "validate_output"


def route_after_output_validation(state: OrchestrationState) -> str:
    """
    Routes output to evaluation engine so that reliability and quality checks assess the result.
    """
    return "evaluate_execution"


def route_after_evaluation(state: OrchestrationState) -> str:
    """
    Decides whether to enter refinement loop or proceed directly to finalization.
    Clarifications, validation failures, or provider execution errors bypass refinement.
    """
    status = state.get("execution_status")
    has_error = bool(state.get("execution_error"))

    if status == "needs_clarification" or has_error:
        return "finalize_execution"

    if status in ("validation_failed", "preparation_failed", "execution_failed", "output_validation_failed"):
        return "finalize_execution"

    return "refinement_controller"


def route_after_refinement_controller(state: OrchestrationState) -> str:
    """
    Decides refinement branch based on controller decision:
      - If should_refine is False -> finalize_execution.
      - If peer_reviewer_id is set -> peer_review.
      - If peer review not assigned -> synthesize_feedback directly.
    """
    decision = state.get("refinement_decision") or {}
    if not decision.get("should_refine"):
        return "finalize_execution"

    if decision.get("peer_reviewer_id"):
        return "peer_review"

    return "synthesize_feedback"
