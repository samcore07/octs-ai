"""
OCTS AI - Orchestration Graph Conditional Edges (Refined Phase 4)
Defines edge routing predicates for the LangGraph state graph including Evaluation Engine routing.
"""

from backend.orchestration.state import OrchestrationState


def route_after_input_validation(state: OrchestrationState) -> str:
    """
    Decides whether to proceed to routing or short-circuit to finalization on validation error.
    """
    if state.get("execution_status") == "validation_failed":
        return "finalize_execution"
    return "route_request"


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
