"""
OCTS AI - Structured Execution Event Model
Defines the standard operational lifecycle events emitted throughout request processing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class ExecutionEventType(str, Enum):
    """Operational lifecycle event identifiers across all orchestration stages."""
    # Request lifecycle
    REQUEST_STARTED = "request_started"
    REQUEST_COMPLETED = "request_completed"
    REQUEST_FAILED = "request_failed"
    REQUEST_CLARIFICATION_REQUIRED = "request_clarification_required"

    # Context & Memory
    CONTEXT_IDENTIFIED = "context_identified"
    MEMORY_RETRIEVAL_STARTED = "memory_retrieval_started"
    MEMORY_RETRIEVAL_COMPLETED = "memory_retrieval_completed"
    MEMORY_PERSISTENCE_COMPLETED = "memory_persistence_completed"

    # Routing
    ROUTING_STARTED = "routing_started"
    ROUTING_COMPLETED = "routing_completed"
    ROUTING_FALLBACK = "routing_fallback"

    # Persona Preparation
    PERSONA_PREPARED = "persona_prepared"

    # Model Execution
    MODEL_EXECUTION_STARTED = "model_execution_started"
    MODEL_EXECUTION_COMPLETED = "model_execution_completed"
    MODEL_EXECUTION_FAILED = "model_execution_failed"

    # Validation
    OUTPUT_VALIDATION_COMPLETED = "output_validation_completed"

    # Evaluation
    EVALUATION_STARTED = "evaluation_started"
    EVALUATION_COMPLETED = "evaluation_completed"
    EVALUATION_FAILED = "evaluation_failed"

    # Peer Review
    PEER_REVIEW_STARTED = "peer_review_started"
    PEER_REVIEW_COMPLETED = "peer_review_completed"
    PEER_REVIEW_FALLBACK = "peer_review_fallback"

    # Refinement
    REFINEMENT_STARTED = "refinement_started"
    REFINEMENT_COMPLETED = "refinement_completed"
    REFINEMENT_REJECTED = "refinement_rejected"
    REFINEMENT_REVERTED = "refinement_reverted"


@dataclass
class ExecutionEvent:
    """Represents an atomic operational event recorded in the system."""
    event_name: ExecutionEventType
    request_id: str
    component: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[float] = None
    discipline: Optional[str] = None
    persona: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes event to clean dictionary for persistence and analytics."""
        return {
            "event_id": self.event_id,
            "request_id": self.request_id,
            "event_name": self.event_name.value,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "duration_ms": self.duration_ms,
            "discipline": self.discipline,
            "persona": self.persona,
            "metadata": self.metadata,
        }
