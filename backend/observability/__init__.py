"""
OCTS AI - Observability, Monitoring & Reliability Subsystem
Exports request correlation, structured logging, error classification,
event tracking, metrics collection, and health probes.
"""

from backend.observability.analytics import AnalyticsService
from backend.observability.collector import TelemetryCollector, get_collector, set_collector
from backend.observability.context import (
    clear_request_context,
    get_context_dict,
    get_correlation_id,
    get_discipline,
    get_owner_id,
    get_persona,
    get_request_id,
    set_request_context,
)
from backend.observability.correlation import generate_request_id, resolve_request_id, validate_correlation_id
from backend.observability.error_tracking import AppError, ErrorTaxonomy, build_safe_error_response, classify_exception
from backend.observability.events import ExecutionEvent, ExecutionEventType
from backend.observability.health import HealthChecker
from backend.observability.logger import StructuredJSONFormatter, setup_observability_logging
from backend.observability.metrics import calculate_percentiles, extract_model_usage
from backend.observability.middleware import RequestCorrelationMiddleware
from backend.observability.models import ExecutionEventORM, ObservabilityBase, RequestTelemetryORM
from backend.observability.schemas import (
    AnalyticsOverviewResponse,
    DetailedHealthResponse,
    DisciplineAnalyticsItem,
    ExecutionEventSchema,
    HealthStatus,
    LivenessResponse,
    MemoryAnalyticsSummary,
    PersonaAnalyticsItem,
    ReadinessResponse,
    RefinementAnalyticsSummary,
    RequestTelemetrySchema,
)
from backend.observability.storage import TelemetryStore

__all__ = [
    # Context & Correlation
    "get_request_id",
    "get_correlation_id",
    "get_discipline",
    "get_persona",
    "get_owner_id",
    "set_request_context",
    "clear_request_context",
    "get_context_dict",
    "generate_request_id",
    "resolve_request_id",
    "validate_correlation_id",
    # Logging
    "setup_observability_logging",
    "StructuredJSONFormatter",
    # Errors
    "ErrorTaxonomy",
    "AppError",
    "classify_exception",
    "build_safe_error_response",
    # Events
    "ExecutionEventType",
    "ExecutionEvent",
    # Metrics & Collector
    "calculate_percentiles",
    "extract_model_usage",
    "TelemetryCollector",
    "get_collector",
    "set_collector",
    # Storage & Models
    "TelemetryStore",
    "ObservabilityBase",
    "RequestTelemetryORM",
    "ExecutionEventORM",
    # Middleware
    "RequestCorrelationMiddleware",
    # Health & Analytics
    "HealthChecker",
    "AnalyticsService",
    # Schemas
    "HealthStatus",
    "LivenessResponse",
    "ReadinessResponse",
    "DetailedHealthResponse",
    "ExecutionEventSchema",
    "RequestTelemetrySchema",
    "AnalyticsOverviewResponse",
    "DisciplineAnalyticsItem",
    "PersonaAnalyticsItem",
    "RefinementAnalyticsSummary",
    "MemoryAnalyticsSummary",
]
