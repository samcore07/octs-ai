"""
OCTS AI - Orchestration Graph Nodes (Refined Phase 3)
Executable task nodes with explicit dependency injection and intelligent ambiguous routing clarification.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage

from backend.config import get_settings
from backend.agents.registry import get_registry
from backend.agents.routing.classifier import AgentRouter
from backend.orchestration.state import OrchestrationState
from backend.observability.collector import get_collector
from backend.observability.events import ExecutionEventType
from backend.observability.metrics import extract_model_usage

logger = logging.getLogger("octs.orchestration.nodes")


def validate_input_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Node A: Input Validation
    Enforces string constraints, whitespace checks, and length bounds on incoming user prompts.
    Does NOT arbitrarily force discipline to 'writers' when omitted.
    """
    prompt = state.get("original_prompt")
    settings = get_settings()

    if prompt is None or not isinstance(prompt, str):
        return {
            "execution_status": "validation_failed",
            "execution_error": "Input validation failed: Prompt must be a non-null string.",
            "generated_output": "Validation Error: Prompt must be a valid text string.",
        }

    trimmed = prompt.strip()
    if not trimmed:
        return {
            "execution_status": "validation_failed",
            "execution_error": "Input validation failed: Prompt cannot be empty or solely whitespace.",
            "generated_output": "Validation Error: Prompt cannot be empty or solely whitespace.",
        }

    if len(trimmed) > settings.max_prompt_length:
        return {
            "execution_status": "validation_failed",
            "execution_error": f"Input validation failed: Prompt length ({len(trimmed)}) exceeds max allowed limit ({settings.max_prompt_length}).",
            "generated_output": f"Validation Error: Prompt exceeds maximum character limit of {settings.max_prompt_length}.",
        }

    # Normalize discipline identifier only if explicitly provided
    raw_discipline = state.get("discipline_id")
    normalized_discipline = None
    if raw_discipline and isinstance(raw_discipline, str):
        clean = raw_discipline.strip().lower()
        if clean in settings.allowed_disciplines:
            normalized_discipline = clean

    return {
        "original_prompt": trimmed,
        "discipline_id": normalized_discipline,
        "execution_status": "validated",
    }


def route_request_node(
    state: OrchestrationState,
    router: Optional[AgentRouter] = None,
    registry=None,
) -> Dict[str, Any]:
    """
    Node B: Task Routing with Intelligent Clarification
    Differentiates between:
      Case A: Clear discipline and specialist
      Case B: Known discipline, uncertain specialist (safe specialist fallback)
      Case C: Ambiguous discipline (structured clarification required)
      Case D: Routing failure
    """
    active_router = router or AgentRouter(registry=registry)
    active_registry = registry or get_registry()

    prompt = state["original_prompt"]
    discipline_id = state.get("discipline_id")
    task_type = state.get("task_type")

    routing_result = active_router.route(
        prompt=prompt,
        discipline_id=discipline_id,
        task_type=task_type,
    )

    # Case C: Ambiguous discipline -> requires user clarification
    if getattr(routing_result, "needs_clarification", False) is True:
        logger.info("Routing determined prompt is ambiguous across disciplines. Triggering clarification.")
        get_collector().emit_event(
            event_name=ExecutionEventType.REQUEST_CLARIFICATION_REQUIRED,
            component="route_request_node",
            request_id=state.get("request_id"),
            metadata={"question": getattr(routing_result, "clarification_question", None)},
        )
        return {
            "discipline_id": None,
            "selected_persona_id": None,
            "routing_confidence": 0.0,
            "routing_rationale": getattr(routing_result, "rationale", "Clarification required."),
            "needs_clarification": True,
            "clarification_question": getattr(routing_result, "clarification_question", None),
            "generated_output": getattr(routing_result, "clarification_question", None),
            "execution_status": "needs_clarification",
        }

    # Validate persona against registry
    persona = active_registry.get_persona(routing_result.persona_id)
    if not persona:
        logger.warning(f"Router returned unregistered persona '{routing_result.persona_id}'. Requiring safe fallback.")
        get_collector().emit_event(
            event_name=ExecutionEventType.ROUTING_FALLBACK,
            component="route_request_node",
            request_id=state.get("request_id"),
            discipline=routing_result.discipline_id,
            metadata={"reason": "unregistered_persona", "persona_attempted": routing_result.persona_id},
        )
        return {
            "execution_status": "routing_fallback",
            "selected_persona_id": None,
            "routing_confidence": 0.30,
            "routing_rationale": f"Unregistered persona identifier '{routing_result.persona_id}'.",
            "needs_clarification": False,
        }

    # Case B: Discipline is known, but specialist is uncertain
    if routing_result.routing_method == "discipline_default_fallback" or routing_result.confidence < 0.40:
        get_collector().emit_event(
            event_name=ExecutionEventType.ROUTING_FALLBACK,
            component="route_request_node",
            request_id=state.get("request_id"),
            discipline=routing_result.discipline_id,
            persona=routing_result.persona_id,
            metadata={"confidence": routing_result.confidence, "method": routing_result.routing_method},
        )
        return {
            "discipline_id": routing_result.discipline_id,
            "selected_persona_id": routing_result.persona_id,
            "alternative_persona_id": routing_result.alternative_persona_id,
            "routing_confidence": routing_result.confidence,
            "routing_rationale": routing_result.rationale,
            "execution_status": "routing_fallback",
            "needs_clarification": False,
        }

    # Case A: Both discipline and specialist are clear
    get_collector().emit_event(
        event_name=ExecutionEventType.ROUTING_COMPLETED,
        component="route_request_node",
        request_id=state.get("request_id"),
        discipline=routing_result.discipline_id,
        persona=routing_result.persona_id,
        metadata={"confidence": routing_result.confidence, "method": routing_result.routing_method},
    )
    return {
        "discipline_id": routing_result.discipline_id,
        "selected_persona_id": routing_result.persona_id,
        "alternative_persona_id": routing_result.alternative_persona_id,
        "routing_confidence": routing_result.confidence,
        "routing_rationale": routing_result.rationale,
        "execution_status": "routed",
        "needs_clarification": False,
    }


def handle_routing_fallback_node(state: OrchestrationState, registry=None) -> Dict[str, Any]:
    """
    Node: Safe Specialist Fallback (Case B)
    Used when discipline is known, but specific craft task is general.
    Ensures the lead persona of the KNOWN discipline is assigned with a clear explanation.
    """
    active_registry = registry or get_registry()
    discipline_id = state.get("discipline_id") or "writers"
    discipline = active_registry.get_discipline(discipline_id) or active_registry.get_discipline("writers")

    # Use already assigned persona or lead persona for this known discipline
    persona_id = state.get("selected_persona_id") or discipline.specialist_persona_ids[0]
    persona = active_registry.get_persona(persona_id)

    rationale = (
        f"Discipline confirmed as {discipline.display_name}. Assigned primary lead specialist "
        f"({persona.display_name}) for general craft guidance."
    )

    return {
        "discipline_id": discipline.id,
        "selected_persona_id": persona.id,
        "routing_confidence": state.get("routing_confidence", 0.50),
        "routing_rationale": rationale,
        "execution_status": "routed",
        "needs_clarification": False,
    }


def prepare_persona_node(state: OrchestrationState, registry=None) -> Dict[str, Any]:
    """
    Node C: Persona Preparation
    Loads the specialist PersonaDefinition and compiles the LangChain ChatPromptTemplate with craft constraints.
    """
    active_registry = registry or get_registry()
    persona_id = state.get("selected_persona_id")

    persona = active_registry.get_persona(persona_id) if persona_id else None
    if not persona:
        return {
            "execution_status": "preparation_failed",
            "execution_error": f"Failed to load persona definition for '{persona_id}'.",
            "generated_output": f"Internal Error: Persona definition '{persona_id}' could not be resolved.",
        }

    try:
        system_prompt = persona.format_system_prompt()
        prompt_template = persona.build_prompt_template()

        # Phase 6: Inject retrieved memory context if present
        memory_ctx = state.get("memory_context")
        if memory_ctx and memory_ctx.strip():
            input_text = f"{memory_ctx.strip()}\n\nTask:\n{state['original_prompt']}"
        else:
            input_text = state["original_prompt"]

        messages: List[BaseMessage] = prompt_template.format_messages(input=input_text)

        return {
            "persona_system_prompt": system_prompt,
            "model_input": messages,
            "execution_status": "prepared",
        }
    except Exception as e:
        logger.error(f"Error compiling prompt template for persona '{persona_id}': {e}")
        return {
            "execution_status": "preparation_failed",
            "execution_error": f"Template compilation error: {str(e)}",
            "generated_output": "Internal Error: Could not compile persona prompt template.",
        }


def execute_model_node(
    state: OrchestrationState,
    model: Optional[Any] = None,
    model_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Node D: Model Execution with Explicit Dependency Injection
    Uses the directly injected model dependency. Does NOT import server.py or use global lookups.
    """
    model_input = state.get("model_input")
    settings = get_settings()
    active_model = model if model is not None else model_override

    if active_model is None:
        logger.error("execute_model_node called without an injected model instance.")
        return {
            "execution_status": "execution_failed",
            "execution_error": "No LLM model dependency injected into orchestration node.",
            "generated_output": "Execution Error: AI model dependency was not provided.",
        }

    try:
        t0 = time.perf_counter()
        response = active_model.invoke(model_input)
        duration_ms = int((time.perf_counter() - t0) * 1000)

        raw_content = getattr(response, "content", response)
        if isinstance(raw_content, str):
            reply_text = raw_content
        elif isinstance(raw_content, list):
            reply_text = "".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in raw_content
            )
        else:
            reply_text = str(raw_content)

        p_tokens, c_tokens, t_tokens = extract_model_usage(response)

        get_collector().emit_event(
            event_name=ExecutionEventType.MODEL_EXECUTION_COMPLETED,
            component="execute_model_node",
            request_id=state.get("request_id"),
            duration_ms=duration_ms,
            discipline=state.get("discipline_id"),
            persona=state.get("selected_persona_id"),
            metadata={
                "model": settings.model_name,
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "total_tokens": t_tokens,
            },
        )

        return {
            "generated_output": reply_text,
            "model_name": settings.model_name,
            "execution_status": "executed",
            "initial_generation_latency_ms": duration_ms,
            "model_call_count": 1,
            "prompt_tokens": p_tokens,
            "completion_tokens": c_tokens,
            "total_tokens": t_tokens,
        }
    except Exception as e:
        logger.error(f"LLM execution error during node invocation: {e}")
        get_collector().emit_event(
            event_name=ExecutionEventType.MODEL_EXECUTION_FAILED,
            component="execute_model_node",
            request_id=state.get("request_id"),
            discipline=state.get("discipline_id"),
            persona=state.get("selected_persona_id"),
            metadata={"error": str(e)},
        )
        return {
            "execution_status": "execution_failed",
            "execution_error": f"Model execution error: {str(e)}",
            "generated_output": f"Execution Error: The model provider failed during generation ({str(e)}).",
        }


def validate_output_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Node E: Output Structural Validation
    Confirms that the model returned a non-empty, non-whitespace string payload.
    Avoids claiming craft quality has been verified when only structural validation occurred.
    """
    output = state.get("generated_output")

    if output is None or not isinstance(output, str):
        return {
            "execution_status": "output_validation_failed",
            "execution_error": "Model produced a null or non-string response object.",
            "generated_output": "Output Validation Error: Malformed response received from model provider.",
        }

    if not output.strip():
        return {
            "execution_status": "output_validation_failed",
            "execution_error": "Model produced an empty or whitespace-only response string.",
            "generated_output": "Output Validation Error: The model returned an empty response.",
        }

    get_collector().emit_event(
        event_name=ExecutionEventType.OUTPUT_VALIDATION_COMPLETED,
        component="validate_output_node",
        request_id=state.get("request_id"),
        discipline=state.get("discipline_id"),
        persona=state.get("selected_persona_id"),
        metadata={"output_length": len(output)},
    )

    return {
        "execution_status": "output_validated",
    }


def evaluate_execution_node(
    state: OrchestrationState,
    engine: Optional[Any] = None,
    engine_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Node G: Evaluation Engine & Scoring Calculator
    Assesses creative output quality and execution reliability as independent dimensions.
    Calculates composite TrustScore. Defensive against evaluation exceptions so creative output
    is never destroyed if evaluation fails.
    """
    from backend.evaluation.engine import EvaluationEngine

    active_engine = engine if engine is not None else engine_override
    if active_engine is None:
        active_engine = EvaluationEngine()

    try:
        eval_result = active_engine.evaluate_execution(dict(state))
        dumped = eval_result.model_dump()
        get_collector().emit_event(
            event_name=ExecutionEventType.EVALUATION_COMPLETED,
            component="evaluate_execution_node",
            request_id=state.get("request_id"),
            discipline=state.get("discipline_id"),
            persona=state.get("selected_persona_id"),
            metadata={
                "quality_score": eval_result.quality_score,
                "reliability_score": eval_result.reliability_score,
                "trust_score": eval_result.trust_score,
            },
        )
        return {
            "evaluation_result": dumped,
            "quality_score": eval_result.quality_score,
            "reliability_score": eval_result.reliability_score,
            "trust_score": eval_result.trust_score,
            "trust_breakdown": eval_result.trust_breakdown.model_dump() if eval_result.trust_breakdown else None,
            "execution_status": "evaluated" if not state.get("execution_error") else state.get("execution_status", "failed"),
        }
    except Exception as e:
        logger.error(f"Error executing evaluation node: {e}", exc_info=True)
        get_collector().emit_event(
            event_name=ExecutionEventType.EVALUATION_FAILED,
            component="evaluate_execution_node",
            request_id=state.get("request_id"),
            discipline=state.get("discipline_id"),
            persona=state.get("selected_persona_id"),
            metadata={"error": str(e)},
        )
        return {
            "evaluation_result": {
                "evaluation_status": "unavailable",
                "evaluation_summary": f"Evaluation unavailable: {str(e)}",
            },
            "quality_score": None,
            "reliability_score": None,
            "trust_score": None,
            "trust_breakdown": None,
            "execution_status": "evaluated" if not state.get("execution_error") else state.get("execution_status", "failed"),
        }


def finalize_execution_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Node F: Finalization
    Calculates execution duration, populates execution timestamps, finalizes telemetry,
    and sets best output and RefinementMetadata.
    Preserves clarification responses without overwriting them.
    Guarantees that reply, evaluation, trust_score, and telemetry are strictly consistent.
    """
    from backend.refinement.schemas import RefinementMetadata, RefinementStatus

    started_at = state.get("started_at")
    now_perf = time.perf_counter()
    elapsed_ms = int((now_perf - started_at) * 1000) if started_at else 0
    settings = get_settings()

    current_status = state.get("execution_status", "unknown")
    has_error = bool(state.get("execution_error"))

    if current_status == "needs_clarification":
        final_status = "completed_clarification_required"
    elif (current_status in ("output_validated", "evaluated", "completed", "refinement_complete", "refining", "refinement_evaluated", "refinement_analyzed")) and not has_error:
        final_status = "completed"
    else:
        final_status = "failed"

    # Resolve final selected artifact and evaluation
    final_output = state.get("best_output") or state.get("generated_output")
    final_eval = state.get("best_evaluation") or state.get("evaluation_result")

    # Build RefinementMetadata
    attempts = state.get("recovery_attempts", 0)
    max_attempts = state.get("max_recovery_attempts", getattr(settings, "refinement_max_attempts", 2))
    initial_eval = state.get("initial_evaluation") or state.get("evaluation_result") or {}

    init_q = initial_eval.get("quality_score") if isinstance(initial_eval, dict) else getattr(initial_eval, "quality_score", None)
    final_q = final_eval.get("quality_score") if isinstance(final_eval, dict) else getattr(final_eval, "quality_score", None)
    q_delta = round(final_q - init_q, 2) if (final_q is not None and init_q is not None) else None

    init_t = initial_eval.get("trust_score") if isinstance(initial_eval, dict) else getattr(initial_eval, "trust_score", None)
    final_t = final_eval.get("trust_score") if isinstance(final_eval, dict) else getattr(final_eval, "trust_score", None)
    t_delta = round(final_t - init_t, 2) if (final_t is not None and init_t is not None) else None

    ref_status = state.get("refinement_status")
    if current_status == "needs_clarification" or (has_error and not state.get("initial_output")):
        ref_status = RefinementStatus.SKIPPED.value
        attempts = 0
    elif not ref_status:
        if attempts == 0:
            ref_status = RefinementStatus.NOT_NEEDED.value
        elif attempts >= max_attempts:
            ref_status = RefinementStatus.MAX_ATTEMPTS_REACHED.value
        else:
            ref_status = RefinementStatus.IMPROVED.value

    peer_review_result = state.get("peer_review_result")
    reviewer_id = None
    if isinstance(peer_review_result, dict):
        reviewer_id = peer_review_result.get("reviewer_persona_id")

    peer_lat = state.get("peer_review_latency_ms")
    ref_lat = state.get("refinement_generation_latency_ms")
    total_ref_lat = (peer_lat or 0) + (ref_lat or 0) if (peer_lat is not None or ref_lat is not None) else None

    refinement_metadata = RefinementMetadata(
        refinement_triggered=(attempts > 0),
        recovery_attempts=attempts,
        max_recovery_attempts=max_attempts,
        initial_quality_score=init_q,
        final_quality_score=final_q,
        quality_delta=q_delta,
        initial_trust_score=init_t,
        final_trust_score=final_t,
        trust_delta=t_delta,
        peer_review_conducted=bool(peer_review_result),
        reviewer_persona_id=reviewer_id,
        refinement_status=ref_status,
        improvement_history=state.get("improvement_history") or [],
        best_output_selected=state.get("best_output_selected", "initial"),
        initial_generation_latency_ms=state.get("initial_generation_latency_ms"),
        peer_review_latency_ms=peer_lat,
        refinement_generation_latency_ms=ref_lat,
        evaluation_latency_ms=state.get("evaluation_latency_ms"),
        total_refinement_latency_ms=total_ref_lat,
        model_call_count=state.get("model_call_count", 1 if final_output else 0),
        reviewer_call_count=state.get("reviewer_call_count", 0),
    )

    result = {
        "generated_output": final_output,
        "evaluation_result": final_eval,
        "completed_at": time.time(),
        "latency_ms": elapsed_ms,
        "execution_status": final_status,
        "refinement_metadata": refinement_metadata.model_dump(),
    }

    if isinstance(final_eval, dict):
        if "quality_score" in final_eval:
            result["quality_score"] = final_eval["quality_score"]
        if "reliability_score" in final_eval:
            result["reliability_score"] = final_eval["reliability_score"]
        if "trust_score" in final_eval:
            result["trust_score"] = final_eval["trust_score"]
        if "trust_breakdown" in final_eval:
            result["trust_breakdown"] = final_eval["trust_breakdown"]

    return result


# ============================================================================
# Phase 5: Autonomous Refinement & Specialist Collaboration Nodes
# ============================================================================

def refinement_controller_node(
    state: OrchestrationState,
    refinement_engine: Optional[Any] = None,
    engine_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Phase 5 Node: Refinement Controller
    Evaluates current quality, determines whether to trigger recovery or peer review,
    and initializes tracking structures.
    """
    from backend.refinement.engine import RefinementEngine

    active_engine = refinement_engine if refinement_engine is not None else engine_override
    if active_engine is None:
        active_engine = RefinementEngine()

    # Initialize baseline artifact and evaluation on first arrival
    initial_output = state.get("initial_output") or state.get("generated_output")
    best_output = state.get("best_output") or initial_output
    initial_eval = state.get("initial_evaluation") or state.get("evaluation_result")
    best_eval = state.get("best_evaluation") or initial_eval
    current_attempts = state.get("recovery_attempts", 0)

    state_for_eval = {
        **state,
        "initial_output": initial_output,
        "best_output": best_output,
        "initial_evaluation": initial_eval,
        "best_evaluation": best_eval,
        "recovery_attempts": current_attempts,
    }

    decision = active_engine.decide_refinement(state_for_eval)

    if decision.should_refine:
        return {
            "initial_output": initial_output,
            "best_output": best_output,
            "initial_evaluation": initial_eval,
            "best_evaluation": best_eval,
            "recovery_attempts": decision.attempt_number,
            "refinement_decision": decision.model_dump(),
            "execution_status": "refining",
        }
    else:
        ref_status = state.get("refinement_status")
        if not ref_status:
            if current_attempts == 0:
                ref_status = "not_needed"
            elif current_attempts >= decision.max_attempts:
                ref_status = "max_attempts_reached"
            else:
                ref_status = "improved"

        return {
            "initial_output": initial_output,
            "best_output": best_output,
            "initial_evaluation": initial_eval,
            "best_evaluation": best_eval,
            "refinement_decision": decision.model_dump(),
            "refinement_status": ref_status,
            "execution_status": "refinement_complete",
        }


def peer_review_node(
    state: OrchestrationState,
    refinement_engine: Optional[Any] = None,
    engine_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Phase 5 Node: Specialist Peer Review
    Invokes the assigned peer reviewer specialist to provide structured critique.
    """
    from backend.refinement.engine import RefinementEngine
    from backend.refinement.schemas import CriterionFeedback

    active_engine = refinement_engine if refinement_engine is not None else engine_override
    if active_engine is None:
        active_engine = RefinementEngine()

    decision_data = state.get("refinement_decision") or {}
    peer_reviewer_id = decision_data.get("peer_reviewer_id")
    candidate_output = state.get("best_output") or state.get("generated_output") or ""
    original_prompt = state.get("original_prompt") or ""

    weak_criteria: List[CriterionFeedback] = []
    for item in decision_data.get("weak_criteria", []):
        if isinstance(item, dict):
            weak_criteria.append(CriterionFeedback(**item))
        elif isinstance(item, CriterionFeedback):
            weak_criteria.append(item)

    if not peer_reviewer_id:
        return {"peer_review_result": None}

    get_collector().emit_event(
        event_name=ExecutionEventType.PEER_REVIEW_STARTED,
        component="peer_review_node",
        request_id=state.get("request_id"),
        discipline=state.get("discipline_id"),
        persona=peer_reviewer_id,
        metadata={"author_persona": state.get("selected_persona_id")},
    )

    try:
        t0 = time.perf_counter()
        review_result = active_engine.conduct_peer_review(
            reviewer_persona_id=peer_reviewer_id,
            original_prompt=original_prompt,
            candidate_output=candidate_output,
            weak_criteria=weak_criteria,
        )
        duration_ms = int((time.perf_counter() - t0) * 1000)
        call_inc = 1 if getattr(review_result, "review_method", "llm") == "llm" else 0

        if getattr(review_result, "fallback_triggered", False):
            get_collector().emit_event(
                event_name=ExecutionEventType.PEER_REVIEW_FALLBACK,
                component="peer_review_node",
                request_id=state.get("request_id"),
                duration_ms=duration_ms,
                discipline=state.get("discipline_id"),
                persona=peer_reviewer_id,
                metadata={"reason": getattr(review_result, "fallback_reason", "unknown")},
            )
        else:
            get_collector().emit_event(
                event_name=ExecutionEventType.PEER_REVIEW_COMPLETED,
                component="peer_review_node",
                request_id=state.get("request_id"),
                duration_ms=duration_ms,
                discipline=state.get("discipline_id"),
                persona=peer_reviewer_id,
                metadata={"review_method": getattr(review_result, "review_method", "llm")},
            )

        return {
            "peer_review_result": review_result.model_dump(),
            "peer_review_latency_ms": (state.get("peer_review_latency_ms") or 0) + duration_ms,
            "reviewer_call_count": (state.get("reviewer_call_count") or 0) + 1,
            "model_call_count": (state.get("model_call_count") or 1) + call_inc,
        }
    except Exception as e:
        logger.warning(f"Error executing peer review node: {e}")
        get_collector().emit_event(
            event_name=ExecutionEventType.PEER_REVIEW_FALLBACK,
            component="peer_review_node",
            request_id=state.get("request_id"),
            discipline=state.get("discipline_id"),
            persona=peer_reviewer_id,
            metadata={"reason": "exception", "error": str(e)},
        )
        return {
            "peer_review_result": {
                "reviewer_persona_id": peer_reviewer_id,
                "reviewer_persona_name": "Peer Reviewer",
                "reviewer_discipline": "general",
                "strengths": ["Original creative premise established."],
                "actionable_critique": [f"Peer review error: {str(e)}"],
                "suggested_improvements": ["Remediate rubric deficiencies directly."],
                "status": "fallback",
                "review_method": "heuristic",
                "fallback_triggered": True,
                "fallback_reason": "exception",
            },
            "reviewer_call_count": (state.get("reviewer_call_count") or 0) + 1,
        }


def synthesize_feedback_node(
    state: OrchestrationState,
    refinement_engine: Optional[Any] = None,
    engine_override: Optional[Any] = None,
    registry=None,
) -> Dict[str, Any]:
    """
    Phase 5 Node: Synthesize Feedback & Prepare Refinement Prompt
    Consolidates rubric gaps and peer review feedback into directives for the author persona.
    """
    from backend.refinement.engine import RefinementEngine
    from backend.refinement.schemas import CriterionFeedback, PeerReviewResult
    from langchain_core.messages import HumanMessage, SystemMessage

    active_engine = refinement_engine if refinement_engine is not None else engine_override
    if active_engine is None:
        active_engine = RefinementEngine()

    active_registry = registry or get_registry()
    persona_id = state.get("selected_persona_id")
    persona = active_registry.get_persona(persona_id) if persona_id else None

    decision_data = state.get("refinement_decision") or {}
    weak_criteria: List[CriterionFeedback] = [
        CriterionFeedback(**item) if isinstance(item, dict) else item
        for item in decision_data.get("weak_criteria", [])
    ]

    peer_data = state.get("peer_review_result")
    peer_review: Optional[PeerReviewResult] = None
    if peer_data and isinstance(peer_data, dict):
        peer_review = PeerReviewResult(**peer_data)

    synthesized_text = active_engine.synthesize_feedback(
        weak_criteria=weak_criteria,
        peer_review=peer_review,
    )

    original_prompt = state.get("original_prompt", "")
    previous_draft = state.get("best_output") or state.get("generated_output") or ""
    persona_name = persona.display_name if persona else "Specialist"

    refinement_prompt = active_engine.feedback_builder.build_refinement_prompt(
        original_prompt=original_prompt,
        previous_output=previous_draft,
        weak_criteria=weak_criteria,
        persona_name=persona_name,
        peer_review=peer_review,
    )

    system_prompt = persona.format_system_prompt() if persona else "You are an expert creative specialist."
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=refinement_prompt),
    ]

    get_collector().emit_event(
        event_name=ExecutionEventType.REFINEMENT_STARTED,
        component="synthesize_feedback_node",
        request_id=state.get("request_id"),
        discipline=state.get("discipline_id"),
        persona=state.get("selected_persona_id"),
        metadata={"attempt_number": state.get("recovery_attempts", 1)},
    )

    return {
        "refinement_feedback": synthesized_text,
        "model_input": messages,
        "execution_status": "refining_prompt_prepared",
    }


def refine_output_node(
    state: OrchestrationState,
    model: Optional[Any] = None,
    model_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Phase 5 Node: Execute Refinement Generation
    Invokes the injected model with the synthesized refinement instructions.
    Defensive against provider failures: previous output is never destroyed.
    """
    active_model = model if model is not None else model_override
    model_input = state.get("model_input")

    if active_model is None:
        logger.error("refine_output_node called without an injected model instance.")
        return {
            "current_output": None,
            "execution_status": "refinement_execution_failed",
            "execution_error": "No model injected for refinement generation.",
        }

    try:
        t0 = time.perf_counter()
        response = active_model.invoke(model_input)
        duration_ms = int((time.perf_counter() - t0) * 1000)

        raw_content = getattr(response, "content", response)
        if isinstance(raw_content, str):
            reply_text = raw_content
        elif isinstance(raw_content, list):
            reply_text = "".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in raw_content
            )
        else:
            reply_text = str(raw_content)

        return {
            "current_output": reply_text,
            "generated_output": reply_text,
            "refinement_generation_latency_ms": (state.get("refinement_generation_latency_ms") or 0) + duration_ms,
            "model_call_count": (state.get("model_call_count") or 1) + 1,
            "execution_status": "refinement_executed",
        }
    except Exception as e:
        logger.error(f"Error during refinement generation: {e}")
        return {
            "current_output": None,
            "execution_status": "refinement_execution_failed",
            "execution_error": f"Refinement model provider error: {str(e)}",
        }


def evaluate_refinement_node(
    state: OrchestrationState,
    evaluator_engine: Optional[Any] = None,
    engine_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Phase 5 Node: Re-evaluate Refined Output
    Runs Phase 4 EvaluationEngine on the newly refined output text.
    """
    from backend.evaluation.engine import EvaluationEngine

    candidate_output = state.get("current_output")
    if not candidate_output or not candidate_output.strip():
        logger.warning("evaluate_refinement_node: candidate output is empty or failed.")
        return {
            "current_evaluation": None,
            "execution_status": "refinement_eval_skipped",
        }

    active_eval_engine = evaluator_engine if evaluator_engine is not None else engine_override
    if active_eval_engine is None:
        active_eval_engine = EvaluationEngine()

    state_copy = dict(state)
    state_copy["generated_output"] = candidate_output
    if not state_copy.get("latency_ms") and not state_copy.get("started_at"):
        state_copy["latency_ms"] = state.get("refinement_generation_latency_ms") or 10

    try:
        t0 = time.perf_counter()
        eval_result = active_eval_engine.evaluate_execution(state_copy)
        duration_ms = int((time.perf_counter() - t0) * 1000)

        return {
            "current_evaluation": eval_result.model_dump(),
            "evaluation_latency_ms": (state.get("evaluation_latency_ms") or 0) + duration_ms,
            "execution_status": "refinement_evaluated",
        }
    except Exception as e:
        logger.error(f"Error evaluating refinement output: {e}", exc_info=True)
        return {
            "current_evaluation": None,
            "execution_status": "refinement_eval_failed",
            "execution_error": f"Refinement evaluation error: {str(e)}",
        }


def improvement_analyzer_node(
    state: OrchestrationState,
    refinement_engine: Optional[Any] = None,
    engine_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Phase 5 Node: Improvement Analyzer & Best-Output Selection
    Compares candidate evaluation against previous best, enforces deterministic selection,
    and updates telemetry history.
    """
    from backend.refinement.engine import RefinementEngine
    from backend.refinement.schemas import ImprovementRecord, RefinementStatus

    active_engine = refinement_engine if refinement_engine is not None else engine_override
    if active_engine is None:
        active_engine = RefinementEngine()

    prev_best_output = state.get("best_output") or state.get("initial_output") or state.get("generated_output") or ""
    prev_best_eval = state.get("best_evaluation") or state.get("initial_evaluation") or state.get("evaluation_result")
    cand_output = state.get("current_output")
    cand_eval = state.get("current_evaluation")
    attempt_num = state.get("recovery_attempts", 1)
    prev_label = state.get("best_output_selected", "initial")

    # If candidate failed execution or evaluation, reject and revert
    if not cand_output or not cand_eval:
        fail_reason = "Candidate refinement failed generation or evaluation. Reverting to previous best output."
        get_collector().emit_event(
            event_name=ExecutionEventType.REFINEMENT_REVERTED,
            component="improvement_analyzer_node",
            request_id=state.get("request_id"),
            discipline=state.get("discipline_id"),
            persona=state.get("selected_persona_id"),
            metadata={"reason": fail_reason, "attempt": attempt_num},
        )
        imp_record = ImprovementRecord(
            attempt_number=attempt_num,
            selection_reason=fail_reason,
            candidate_accepted=False,
            is_improvement=False,
            previous_best_score=prev_best_eval.get("quality_score") if isinstance(prev_best_eval, dict) else None,
            new_quality_score=None,
            rationale=fail_reason,
        )
        history = list(state.get("improvement_history") or [])
        history.append(imp_record.model_dump())
        return {
            "best_output": prev_best_output,
            "best_evaluation": prev_best_eval,
            "best_output_selected": prev_label,
            "refinement_status": RefinementStatus.REGRESSED_REVERTED.value,
            "improvement_history": history,
            "execution_status": "refinement_analyzed",
        }

    imp_record = active_engine.analyze_improvement(
        previous_eval=prev_best_eval,
        candidate_eval=cand_eval,
        attempt_number=attempt_num,
    )

    best_out, best_ev, best_lbl, ref_st = active_engine.select_best_artifact(
        previous_output=prev_best_output,
        previous_eval=prev_best_eval,
        candidate_output=cand_output,
        candidate_eval=cand_eval,
        improvement_record=imp_record,
        previous_label=prev_label,
    )

    history = list(state.get("improvement_history") or [])
    history.append(imp_record.model_dump())

    event_type = (
        ExecutionEventType.REFINEMENT_COMPLETED
        if imp_record.candidate_accepted
        else (
            ExecutionEventType.REFINEMENT_REVERTED
            if "revert" in str(ref_st).lower()
            else ExecutionEventType.REFINEMENT_REJECTED
        )
    )
    get_collector().emit_event(
        event_name=event_type,
        component="improvement_analyzer_node",
        request_id=state.get("request_id"),
        discipline=state.get("discipline_id"),
        persona=state.get("selected_persona_id"),
        metadata={
            "attempt": attempt_num,
            "accepted": imp_record.candidate_accepted,
            "is_improvement": imp_record.is_improvement,
            "refinement_status": str(ref_st),
        },
    )

    res = {
        "best_output": best_out,
        "best_evaluation": best_ev,
        "best_output_selected": best_lbl,
        "refinement_status": ref_st.value if hasattr(ref_st, "value") else str(ref_st),
        "improvement_history": history,
        "execution_status": "refinement_analyzed",
    }

    if isinstance(best_ev, dict):
        if "quality_score" in best_ev:
            res["quality_score"] = best_ev["quality_score"]
        if "reliability_score" in best_ev:
            res["reliability_score"] = best_ev["reliability_score"]
        if "trust_score" in best_ev:
            res["trust_score"] = best_ev["trust_score"]
        if "trust_breakdown" in best_ev:
            res["trust_breakdown"] = best_ev["trust_breakdown"]

    return res


# ==============================================================================
# Phase 6: Memory & Persistent Intelligence Nodes
# ==============================================================================

def identify_context_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Phase 6 Node: Identity & Context Resolution
    Normalizes caller identity, project scope, and session continuity tokens.
    """
    owner_id = (state.get("owner_id") or "default_user").strip()
    project_id = state.get("project_id")
    session_id = state.get("session_id")

    get_collector().emit_event(
        event_name=ExecutionEventType.CONTEXT_IDENTIFIED,
        component="identify_context_node",
        request_id=state.get("request_id"),
        metadata={"owner_id": owner_id, "project_id": project_id, "session_id": session_id},
    )

    return {
        "owner_id": owner_id,
        "project_id": project_id,
        "session_id": session_id,
        "execution_status": "context_identified",
    }


def retrieve_memory_node(
    state: OrchestrationState,
    memory_manager: Optional[Any] = None,
    manager_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Phase 6 Node: Context-Aware Memory Retrieval
    Queries the persistent memory repository for active, scope-compliant memories.
    """
    from backend.memory.memory_manager import MemoryManager

    active_manager = memory_manager if memory_manager is not None else manager_override
    if active_manager is None:
        active_manager = MemoryManager()

    prompt = state.get("original_prompt", "")
    owner_id = state.get("owner_id", "default_user")
    project_id = state.get("project_id")
    discipline = state.get("discipline_id")

    get_collector().emit_event(
        event_name=ExecutionEventType.MEMORY_RETRIEVAL_STARTED,
        component="retrieve_memory_node",
        request_id=state.get("request_id"),
        discipline=discipline,
        metadata={"owner_id": owner_id, "project_id": project_id},
    )

    try:
        t0 = time.perf_counter()
        context_str, telemetry_items = active_manager.retrieve_context(
            prompt=prompt,
            owner_id=owner_id,
            project_id=project_id,
            discipline=discipline,
        )
        duration_ms = int((time.perf_counter() - t0) * 1000)

        get_collector().emit_event(
            event_name=ExecutionEventType.MEMORY_RETRIEVAL_COMPLETED,
            component="retrieve_memory_node",
            request_id=state.get("request_id"),
            duration_ms=duration_ms,
            discipline=discipline,
            metadata={"items_retrieved": len(telemetry_items)},
        )

        return {
            "memory_context": context_str,
            "retrieved_memories": [item.model_dump() for item in telemetry_items],
            "execution_status": "memory_retrieved",
        }
    except Exception as e:
        logger.error(f"Error in retrieve_memory_node: {e}", exc_info=True)
        return {
            "memory_context": "",
            "retrieved_memories": [],
            "execution_status": "memory_retrieval_failed",
        }


def build_context_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Phase 6 Node: Context Assembly & Bridge
    Finalizes context container before task routing.
    """
    return {
        "execution_status": "context_built",
    }


def extract_memory_node(
    state: OrchestrationState,
    memory_manager: Optional[Any] = None,
    manager_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Phase 6 Node: Conservative Memory Extraction
    Extracts durable preferences, decisions, and constraints from successful generation.
    Bypasses extraction on clarification paths or failed runs.
    """
    from backend.memory.memory_manager import MemoryManager

    active_manager = memory_manager if memory_manager is not None else manager_override
    if active_manager is None:
        active_manager = MemoryManager()

    if not active_manager.settings.memory_enabled or not active_manager.settings.memory_auto_extraction:
        return {
            "memory_status": "skipped",
        }

    status = state.get("execution_status")
    if state.get("needs_clarification") or status in ("failed", "validation_failed", "execution_failed"):
        return {
            "memory_status": "skipped",
        }

    prompt = state.get("original_prompt", "")
    # Use final selected winning artifact, never an unselected or regressed draft
    output = state.get("best_output") or state.get("generated_output") or ""
    owner_id = state.get("owner_id", "default_user")
    project_id = state.get("project_id")
    discipline = state.get("discipline_id")
    session_id = state.get("session_id")

    try:
        extracted = active_manager.extractor.extract_memories(
            prompt=prompt,
            output=output,
            discipline=discipline,
            project_id=project_id,
            owner_id=owner_id,
            session_id=session_id,
        )

        return {
            "extracted_memories": [m.model_dump() for m in extracted],
            "memory_status": "extracted",
        }
    except Exception as e:
        logger.warning(f"Error in extract_memory_node: {e}", exc_info=True)
        return {
            "extracted_memories": [],
            "memory_status": "extraction_failed",
        }


def persist_memory_node(
    state: OrchestrationState,
    memory_manager: Optional[Any] = None,
    manager_override: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Phase 6 Node: Memory Persistence & Telemetry Assembly
    Consolidates new memories into the database and builds final MemoryMetadata.
    """
    from backend.memory.memory_manager import MemoryManager
    from backend.memory.schemas import MemoryMetadata, MemoryRecord, RetrievedMemoryItem

    active_manager = memory_manager if memory_manager is not None else manager_override
    if active_manager is None:
        active_manager = MemoryManager()

    retrieved_dicts = state.get("retrieved_memories") or []
    retrieved_items = [RetrievedMemoryItem(**d) for d in retrieved_dicts]
    project_id = state.get("project_id")

    mem_status = state.get("memory_status")
    if mem_status == "skipped":
        metadata = MemoryMetadata(
            enabled=active_manager.settings.memory_enabled,
            retrieval_performed=bool(retrieved_items),
            memories_used=len(retrieved_items),
            extraction_performed=False,
            persistence_status="skipped",
            memories_retrieved=retrieved_items,
            project_id=project_id,
        )
        return {"memory_metadata": metadata.model_dump()}

    extracted_dicts = state.get("extracted_memories") or []
    persistence_status = "not_attempted"

    if extracted_dicts:
        try:
            records = [MemoryRecord(**d) for d in extracted_dicts]
            active_manager.consolidator.consolidate_and_save(records)
            persistence_status = "success"
        except Exception as e:
            logger.error(f"Error persisting memories: {e}", exc_info=True)
            persistence_status = "failed"
    else:
        persistence_status = "success" if state.get("execution_status") == "completed" else "not_attempted"

    metadata = MemoryMetadata(
        enabled=active_manager.settings.memory_enabled,
        retrieval_performed=bool(retrieved_items),
        memories_used=len(retrieved_items),
        extraction_performed=bool(extracted_dicts),
        persistence_status=persistence_status,
        memories_retrieved=retrieved_items,
        project_id=project_id,
    )

    get_collector().emit_event(
        event_name=ExecutionEventType.MEMORY_PERSISTENCE_COMPLETED,
        component="persist_memory_node",
        request_id=state.get("request_id"),
        discipline=state.get("discipline_id"),
        metadata={
            "persistence_status": persistence_status,
            "extracted_count": len(extracted_dicts),
            "retrieved_count": len(retrieved_items),
        },
    )

    return {"memory_metadata": metadata.model_dump()}
