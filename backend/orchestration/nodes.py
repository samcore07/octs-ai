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
        return {
            "execution_status": "routing_fallback",
            "selected_persona_id": None,
            "routing_confidence": 0.30,
            "routing_rationale": f"Unregistered persona identifier '{routing_result.persona_id}'.",
            "needs_clarification": False,
        }

    # Case B: Discipline is known, but specialist is uncertain
    if routing_result.routing_method == "discipline_default_fallback" or routing_result.confidence < 0.40:
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
        messages: List[BaseMessage] = prompt_template.format_messages(input=state["original_prompt"])

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
        response = active_model.invoke(model_input)

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
            "generated_output": reply_text,
            "model_name": settings.model_name,
            "execution_status": "executed",
        }
    except Exception as e:
        logger.error(f"LLM execution error during node invocation: {e}")
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

    return {
        "execution_status": "output_validated",
    }


def finalize_execution_node(state: OrchestrationState) -> Dict[str, Any]:
    """
    Node F: Finalization
    Calculates execution duration, populates execution timestamps, and finalizes metadata.
    Preserves clarification responses without overwriting them.
    """
    started_at = state.get("started_at")
    now_perf = time.perf_counter()
    elapsed_ms = int((now_perf - started_at) * 1000) if started_at else 0

    current_status = state.get("execution_status", "unknown")

    if current_status == "needs_clarification":
        final_status = "completed_clarification_required"
    elif current_status == "output_validated":
        final_status = "completed"
    else:
        final_status = "failed"

    return {
        "completed_at": time.time(),
        "latency_ms": elapsed_ms,
        "execution_status": final_status,
    }
