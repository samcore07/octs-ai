"""
OCTS AI - Observability & Telemetry Relational Database Models
SQLAlchemy ORM schemas with composite indexing for operational metrics and execution events.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

ObservabilityBase = declarative_base()


class RequestTelemetryORM(ObservabilityBase):
    """Stores operational lifecycle metrics for every completed or failed request."""
    __tablename__ = "telemetry_requests"

    request_id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    duration_ms = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, index=True)  # 'completed', 'failed', 'clarification'
    discipline = Column(String(64), nullable=True, index=True)
    persona_id = Column(String(64), nullable=True, index=True)
    model_name = Column(String(64), nullable=True)

    # Evaluation Scores
    quality_score = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    trust_score = Column(Float, nullable=True)

    # Autonomous Refinement Metrics
    refinement_triggered = Column(Boolean, nullable=False, default=False)
    recovery_attempts = Column(Integer, nullable=False, default=0)
    refinement_accepted = Column(Boolean, nullable=False, default=False)
    refinement_reverted = Column(Boolean, nullable=False, default=False)

    # Memory Subsystem Metrics
    memories_used = Column(Integer, nullable=False, default=0)
    memories_extracted = Column(Integer, nullable=False, default=0)

    # Model Token Usage (when available from provider response)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Error Tracking
    error_type = Column(String(64), nullable=True, index=True)
    needs_clarification = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_telemetry_status_time", "status", "timestamp"),
        Index("ix_telemetry_disc_time", "discipline", "timestamp"),
        Index("ix_telemetry_persona_time", "persona_id", "timestamp"),
    )


class ExecutionEventORM(ObservabilityBase):
    """Stores granular operational lifecycle events across orchestration stages."""
    __tablename__ = "telemetry_events"

    event_id = Column(String(64), primary_key=True)
    request_id = Column(String(64), nullable=False, index=True)
    event_name = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    component = Column(String(64), nullable=False)
    duration_ms = Column(Float, nullable=True)
    discipline = Column(String(64), nullable=True)
    persona = Column(String(64), nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")

    __table_args__ = (
        Index("ix_event_req_name", "request_id", "event_name"),
        Index("ix_event_name_time", "event_name", "timestamp"),
    )
