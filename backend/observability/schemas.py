"""
OCTS AI - Observability & Telemetry Pydantic Schemas
Strict data contracts for operational events, metric records, analytics summaries, and health probes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    name: str
    status: HealthStatus
    details: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None


class DetailedHealthResponse(BaseModel):
    status: HealthStatus
    version: str = "0.2.0"
    timestamp: datetime = Field(default_factory=utc_now)
    dependencies: List[DependencyHealth]
    model_provider: str
    model_name: str
    langsmith_tracing: bool
    active_requests: int = 0
    uptime_seconds: float = 0.0


class LivenessResponse(BaseModel):
    status: str = "alive"
    timestamp: datetime = Field(default_factory=utc_now)


class ReadinessResponse(BaseModel):
    status: str = "ready"
    timestamp: datetime = Field(default_factory=utc_now)
    database_ready: bool
    model_ready: bool


class ExecutionEventSchema(BaseModel):
    event_id: str
    request_id: str
    event_name: str
    timestamp: datetime = Field(default_factory=utc_now)
    component: str
    duration_ms: Optional[float] = None
    discipline: Optional[str] = None
    persona: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RequestTelemetrySchema(BaseModel):
    request_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    duration_ms: int
    status: str
    discipline: Optional[str] = None
    persona_id: Optional[str] = None
    model_name: Optional[str] = None
    quality_score: Optional[float] = None
    reliability_score: Optional[float] = None
    trust_score: Optional[float] = None
    refinement_triggered: bool = False
    recovery_attempts: int = 0
    refinement_accepted: bool = False
    refinement_reverted: bool = False
    memories_used: int = 0
    memories_extracted: int = 0
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    error_type: Optional[str] = None
    needs_clarification: bool = False


# Analytics Responses
class AnalyticsOverviewResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    clarification_requests: int
    success_rate_pct: float
    failure_rate_pct: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_trust_score: Optional[float] = None
    avg_quality_score: Optional[float] = None
    total_refinement_attempts: int
    total_reversions: int
    total_model_calls: int
    total_tokens_used: Optional[int] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class DisciplineAnalyticsItem(BaseModel):
    discipline: str
    request_count: int
    success_rate_pct: float
    avg_latency_ms: float
    avg_trust_score: Optional[float] = None
    avg_quality_score: Optional[float] = None
    refinement_rate_pct: float


class PersonaAnalyticsItem(BaseModel):
    persona_id: str
    discipline: str
    request_count: int
    avg_latency_ms: float
    avg_quality_score: Optional[float] = None
    avg_trust_score: Optional[float] = None
    failure_count: int


class RefinementAnalyticsSummary(BaseModel):
    total_refinements_attempted: int
    refinement_acceptance_count: int
    refinement_rejection_count: int
    reversion_count: int
    acceptance_rate_pct: float
    avg_trust_delta: Optional[float] = None
    avg_quality_delta: Optional[float] = None


class MemoryAnalyticsSummary(BaseModel):
    retrieval_requests: int
    avg_memories_retrieved: float
    total_memories_extracted: int
    persistence_success_rate_pct: float
