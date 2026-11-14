"""
OCTS AI - LangGraph StateGraph Definition & Compilation (Refined Phase 3)
Constructs and compiles the single shared orchestration graph with explicit dependency injection.
"""

from typing import Any, Optional
from langgraph.graph import END, START, StateGraph

from backend.orchestration.edges import (
    route_after_input_validation,
    route_after_model_execution,
    route_after_persona_preparation,
    route_after_task_routing,
)
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


def build_orchestration_graph(
    model: Optional[Any] = None,
    router: Optional[Any] = None,
    registry: Optional[Any] = None,
    model_override: Optional[Any] = None,
    router_override: Optional[Any] = None,
) -> StateGraph:
    """
    Constructs the uncompiled StateGraph for creative task orchestration.
    Receives injected dependencies explicitly (no global server lookups).
    """
    workflow = StateGraph(OrchestrationState)
    active_model = model if model is not None else model_override
    active_router = router if router is not None else router_override

    def _route_node(state: OrchestrationState):
        return route_request_node(state, router=active_router, registry=registry)

    def _fallback_node(state: OrchestrationState):
        return handle_routing_fallback_node(state, registry=registry)

    def _prep_node(state: OrchestrationState):
        return prepare_persona_node(state, registry=registry)

    def _model_node(state: OrchestrationState):
        return execute_model_node(state, model=active_model)

    # Register workflow nodes
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("route_request", _route_node)
    workflow.add_node("handle_routing_fallback", _fallback_node)
    workflow.add_node("prepare_persona", _prep_node)
    workflow.add_node("execute_model", _model_node)
    workflow.add_node("validate_output", validate_output_node)
    workflow.add_node("finalize_execution", finalize_execution_node)

    # 1. Entry point into validation
    workflow.add_edge(START, "validate_input")

    # 2. Input validation conditional branch
    workflow.add_conditional_edges(
        "validate_input",
        route_after_input_validation,
        {
            "route_request": "route_request",
            "finalize_execution": "finalize_execution",
        },
    )

    # 3. Routing conditional branch (supports Case A, B, and C clarification)
    workflow.add_conditional_edges(
        "route_request",
        route_after_task_routing,
        {
            "prepare_persona": "prepare_persona",
            "handle_routing_fallback": "handle_routing_fallback",
            "finalize_execution": "finalize_execution",  # Case C: Ambiguous discipline
        },
    )

    # 4. Fallback recovery transitions into persona preparation
    workflow.add_edge("handle_routing_fallback", "prepare_persona")

    # 5. Persona preparation conditional branch
    workflow.add_conditional_edges(
        "prepare_persona",
        route_after_persona_preparation,
        {
            "execute_model": "execute_model",
            "finalize_execution": "finalize_execution",
        },
    )

    # 6. Model execution conditional branch
    workflow.add_conditional_edges(
        "execute_model",
        route_after_model_execution,
        {
            "validate_output": "validate_output",
            "finalize_execution": "finalize_execution",
        },
    )

    # 7. Output validation leads to finalization
    workflow.add_edge("validate_output", "finalize_execution")

    # 8. Finalization terminates graph execution
    workflow.add_edge("finalize_execution", END)

    return workflow


_COMPILED_GRAPH = None


def get_orchestration_graph(
    model: Optional[Any] = None,
    router: Optional[Any] = None,
    registry: Optional[Any] = None,
    model_override: Optional[Any] = None,
    router_override: Optional[Any] = None,
):
    """
    Returns a compiled LangGraph executable for production or test environments.
    Caches default singleton instance when no dependency overrides are supplied.
    """
    global _COMPILED_GRAPH
    active_model = model if model is not None else model_override
    active_router = router if router is not None else router_override

    if active_model is not None or active_router is not None or registry is not None:
        graph = build_orchestration_graph(
            model=active_model,
            router=active_router,
            registry=registry,
        )
        return graph.compile()

    if _COMPILED_GRAPH is None:
        graph = build_orchestration_graph()
        _COMPILED_GRAPH = graph.compile()
    return _COMPILED_GRAPH
