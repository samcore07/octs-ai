"""
OCTS AI - LangGraph Orchestration State (Refined Phase 3)
Strongly typed state definition with support for intelligent clarification workflows.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class OrchestrationState(TypedDict, total=False):
    """
    Strongly typed state container passed between nodes in the LangGraph workflow.
    Minimal, explicit, and free of sensitive API keys or redundant copies.
    """

    # Request Identity & Input
    request_id: str
    original_prompt: str
    discipline_id: Optional[str]
    task_type: Optional[str]
    session_id: Optional[str]

    # Routing Resolution & Clarification
    selected_persona_id: Optional[str]
    alternative_persona_id: Optional[str]
    routing_confidence: Optional[float]
    routing_rationale: Optional[str]
    needs_clarification: bool
    clarification_question: Optional[str]

    # Persona & Model Preparation
    persona_system_prompt: Optional[str]
    model_input: Optional[List[Any]]  # Formatted LangChain BaseMessage instances

    # Model Execution & Validation
    generated_output: Optional[str]
    model_name: Optional[str]

    # Execution Lifecycle & Telemetry
    execution_status: str  # "initialized" | "validated" | "routed" | "needs_clarification" | "prepared" | "executed" | "completed" | "failed"
    execution_error: Optional[str]
    started_at: Optional[float]
    completed_at: Optional[float]
    latency_ms: Optional[int]

    # Additional execution metadata
    metadata: Optional[Dict[str, Any]]
