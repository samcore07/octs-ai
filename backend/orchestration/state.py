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

    # Phase 4: Evaluation Engine & TrustScore
    evaluation_result: Optional[Dict[str, Any]]
    quality_score: Optional[float]
    reliability_score: Optional[float]
    trust_score: Optional[float]
    trust_breakdown: Optional[Dict[str, Any]]

    # Phase 5: Autonomous Refinement & Specialist Collaboration
    initial_output: Optional[str]
    current_output: Optional[str]
    best_output: Optional[str]
    best_output_selected: Optional[str]
    initial_evaluation: Optional[Dict[str, Any]]
    current_evaluation: Optional[Dict[str, Any]]
    best_evaluation: Optional[Dict[str, Any]]
    recovery_attempts: int
    max_recovery_attempts: int
    peer_review_result: Optional[Dict[str, Any]]
    refinement_feedback: Optional[str]
    improvement_history: Optional[List[Dict[str, Any]]]
    refinement_status: Optional[str]
    refinement_metadata: Optional[Dict[str, Any]]
    refinement_decision: Optional[Dict[str, Any]]

    # Phase 5 Telemetry & Call Counting
    initial_generation_latency_ms: Optional[int]
    peer_review_latency_ms: Optional[int]
    refinement_generation_latency_ms: Optional[int]
    evaluation_latency_ms: Optional[int]
    model_call_count: Optional[int]
    reviewer_call_count: Optional[int]

    # Phase 6: Memory & Persistent Intelligence
    owner_id: Optional[str]
    project_id: Optional[str]
    memory_context: Optional[str]
    retrieved_memories: Optional[List[Dict[str, Any]]]
    extracted_memories: Optional[List[Dict[str, Any]]]
    memory_metadata: Optional[Dict[str, Any]]
    memory_status: Optional[str]

    # Phase 7: Observability, Metrics & Token Usage
    correlation_id: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    agent_pipeline: Optional[List[Dict[str, Any]]]
