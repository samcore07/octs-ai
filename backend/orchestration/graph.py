"""
OCTS AI - LangGraph StateGraph Definition & Compilation (Refined Phase 5)
Constructs and compiles the single shared orchestration graph with explicit dependency injection
for Model, Router, Registry, EvaluationEngine, and RefinementEngine.
"""

from typing import Any, Optional
from langgraph.graph import END, START, StateGraph

from backend.orchestration.edges import (
    route_after_evaluation,
    route_after_input_validation,
    route_after_model_execution,
    route_after_persona_preparation,
    route_after_refinement_controller,
    route_after_task_routing,
)
from backend.orchestration.nodes import (
    build_context_node,
    evaluate_execution_node,
    evaluate_refinement_node,
    execute_model_node,
    extract_memory_node,
    finalize_execution_node,
    handle_routing_fallback_node,
    identify_context_node,
    improvement_analyzer_node,
    peer_review_node,
    persist_memory_node,
    prepare_persona_node,
    refine_output_node,
    refinement_controller_node,
    retrieve_memory_node,
    route_request_node,
    synthesize_feedback_node,
    validate_input_node,
    validate_output_node,
)
from backend.orchestration.state import OrchestrationState


def build_orchestration_graph(
    model: Optional[Any] = None,
    router: Optional[Any] = None,
    registry: Optional[Any] = None,
    evaluator_engine: Optional[Any] = None,
    refinement_engine: Optional[Any] = None,
    memory_manager: Optional[Any] = None,
    model_override: Optional[Any] = None,
    router_override: Optional[Any] = None,
    evaluator_engine_override: Optional[Any] = None,
    refinement_engine_override: Optional[Any] = None,
    memory_manager_override: Optional[Any] = None,
) -> StateGraph:
    """
    Constructs the uncompiled StateGraph for creative task orchestration.
    Receives injected dependencies explicitly (no global server lookups).
    """
    workflow = StateGraph(OrchestrationState)
    active_model = model if model is not None else model_override
    active_router = router if router is not None else router_override
    active_engine = evaluator_engine if evaluator_engine is not None else evaluator_engine_override
    active_refinement = refinement_engine if refinement_engine is not None else refinement_engine_override
    active_memory = memory_manager if memory_manager is not None else memory_manager_override

    if active_refinement is None:
        from backend.refinement.engine import RefinementEngine
        active_refinement = RefinementEngine(model=active_model)

    if active_memory is None:
        from backend.memory.memory_manager import MemoryManager
        active_memory = MemoryManager()

    def _identify_context_node(state: OrchestrationState):
        return identify_context_node(state)

    def _retrieve_memory_node(state: OrchestrationState):
        return retrieve_memory_node(state, memory_manager=active_memory)

    def _build_context_node(state: OrchestrationState):
        return build_context_node(state)

    def _route_node(state: OrchestrationState):
        return route_request_node(state, router=active_router, registry=registry)

    def _fallback_node(state: OrchestrationState):
        return handle_routing_fallback_node(state, registry=registry)

    def _prep_node(state: OrchestrationState):
        return prepare_persona_node(state, registry=registry)

    def _model_node(state: OrchestrationState):
        return execute_model_node(state, model=active_model)

    def _eval_node(state: OrchestrationState):
        return evaluate_execution_node(state, engine=active_engine)

    def _refinement_controller_node(state: OrchestrationState):
        return refinement_controller_node(state, refinement_engine=active_refinement)

    def _peer_review_node(state: OrchestrationState):
        return peer_review_node(state, refinement_engine=active_refinement)

    def _synthesize_feedback_node(state: OrchestrationState):
        return synthesize_feedback_node(state, refinement_engine=active_refinement, registry=registry)

    def _refine_output_node(state: OrchestrationState):
        return refine_output_node(state, model=active_model)

    def _evaluate_refinement_node(state: OrchestrationState):
        return evaluate_refinement_node(state, evaluator_engine=active_engine)

    def _improvement_analyzer_node(state: OrchestrationState):
        return improvement_analyzer_node(state, refinement_engine=active_refinement)

    def _extract_memory_node(state: OrchestrationState):
        return extract_memory_node(state, memory_manager=active_memory)

    def _persist_memory_node(state: OrchestrationState):
        return persist_memory_node(state, memory_manager=active_memory)

    # Register workflow nodes
    workflow.add_node("validate_input", validate_input_node)

    # Phase 6: Memory & Context nodes
    workflow.add_node("identify_context", _identify_context_node)
    workflow.add_node("retrieve_memory", _retrieve_memory_node)
    workflow.add_node("build_context", _build_context_node)

    workflow.add_node("route_request", _route_node)
    workflow.add_node("handle_routing_fallback", _fallback_node)
    workflow.add_node("prepare_persona", _prep_node)
    workflow.add_node("execute_model", _model_node)
    workflow.add_node("validate_output", validate_output_node)
    workflow.add_node("evaluate_execution", _eval_node)

    # Phase 5: Autonomous Refinement & Peer Review nodes
    workflow.add_node("refinement_controller", _refinement_controller_node)
    workflow.add_node("peer_review", _peer_review_node)
    workflow.add_node("synthesize_feedback", _synthesize_feedback_node)
    workflow.add_node("refine_output", _refine_output_node)
    workflow.add_node("evaluate_refinement", _evaluate_refinement_node)
    workflow.add_node("improvement_analyzer", _improvement_analyzer_node)

    workflow.add_node("finalize_execution", finalize_execution_node)

    # Phase 6: Post-execution Memory Extraction & Persistence nodes
    workflow.add_node("extract_memory", _extract_memory_node)
    workflow.add_node("persist_memory", _persist_memory_node)

    # 1. Entry point into validation
    workflow.add_edge(START, "validate_input")

    # 2. Input validation conditional branch
    workflow.add_conditional_edges(
        "validate_input",
        route_after_input_validation,
        {
            "identify_context": "identify_context",
            "finalize_execution": "finalize_execution",
        },
    )

    # Phase 6: Context & Memory Retrieval Pipeline
    workflow.add_edge("identify_context", "retrieve_memory")
    workflow.add_edge("retrieve_memory", "build_context")
    workflow.add_edge("build_context", "route_request")

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

    # 6. Model execution conditional branch (provider failure proceeds to evaluation for reliability tracking)
    workflow.add_conditional_edges(
        "execute_model",
        route_after_model_execution,
        {
            "validate_output": "validate_output",
            "evaluate_execution": "evaluate_execution",
        },
    )

    # 7. Output validation transitions into Evaluation Engine
    workflow.add_edge("validate_output", "evaluate_execution")

    # 8. Evaluation Engine transitions conditionally (into Refinement or Finalization)
    workflow.add_conditional_edges(
        "evaluate_execution",
        route_after_evaluation,
        {
            "refinement_controller": "refinement_controller",
            "finalize_execution": "finalize_execution",
        },
    )

    # 9. Refinement Controller branches to Peer Review, Synthesize Feedback, or Finalize
    workflow.add_conditional_edges(
        "refinement_controller",
        route_after_refinement_controller,
        {
            "peer_review": "peer_review",
            "synthesize_feedback": "synthesize_feedback",
            "finalize_execution": "finalize_execution",
        },
    )

    # 10. Peer Review transitions to feedback synthesis
    workflow.add_edge("peer_review", "synthesize_feedback")

    # 11. Synthesize Feedback transitions to refine output
    workflow.add_edge("synthesize_feedback", "refine_output")

    # 12. Refine Output transitions to evaluation of refined candidate
    workflow.add_edge("refine_output", "evaluate_refinement")

    # 13. Evaluate Refinement transitions to improvement analyzer
    workflow.add_edge("evaluate_refinement", "improvement_analyzer")

    # 14. Improvement Analyzer loops back to Refinement Controller for bounded termination checks
    workflow.add_edge("improvement_analyzer", "refinement_controller")

    # 15. Finalization transitions into Memory Extraction & Persistence
    workflow.add_edge("finalize_execution", "extract_memory")
    workflow.add_edge("extract_memory", "persist_memory")
    workflow.add_edge("persist_memory", END)

    return workflow


_COMPILED_GRAPH = None


def get_orchestration_graph(
    model: Optional[Any] = None,
    router: Optional[Any] = None,
    registry: Optional[Any] = None,
    evaluator_engine: Optional[Any] = None,
    refinement_engine: Optional[Any] = None,
    memory_manager: Optional[Any] = None,
    model_override: Optional[Any] = None,
    router_override: Optional[Any] = None,
    evaluator_engine_override: Optional[Any] = None,
    refinement_engine_override: Optional[Any] = None,
    memory_manager_override: Optional[Any] = None,
):
    """
    Returns a compiled LangGraph executable for production or test environments.
    Caches default singleton instance when no dependency overrides are supplied.
    """
    global _COMPILED_GRAPH
    active_model = model if model is not None else model_override
    active_router = router if router is not None else router_override
    active_engine = evaluator_engine if evaluator_engine is not None else evaluator_engine_override
    active_refinement = refinement_engine if refinement_engine is not None else refinement_engine_override
    active_memory = memory_manager if memory_manager is not None else memory_manager_override

    has_overrides = (
        active_model is not None
        or active_router is not None
        or registry is not None
        or active_engine is not None
        or refinement_engine is not None
        or refinement_engine_override is not None
        or active_memory is not None
    )

    if has_overrides:
        graph = build_orchestration_graph(
            model=active_model,
            router=active_router,
            registry=registry,
            evaluator_engine=active_engine,
            refinement_engine=active_refinement,
            memory_manager=active_memory,
        )
        return graph.compile()

    if _COMPILED_GRAPH is None:
        graph = build_orchestration_graph()
        _COMPILED_GRAPH = graph.compile()
    return _COMPILED_GRAPH
