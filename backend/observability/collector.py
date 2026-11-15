"""
OCTS AI - Telemetry Collector
Central facade for event emission, request recording, and integration with storage.
"""

from collections import deque
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from backend.observability.context import get_correlation_id, get_discipline, get_persona, get_request_id
from backend.observability.events import ExecutionEvent, ExecutionEventType
from backend.observability.schemas import RequestTelemetrySchema
from backend.observability.storage import TelemetryStore

logger = logging.getLogger("octs.observability.collector")


class TelemetryCollector:
    """
    Coordinates operational telemetry recording, event emission, and persistence.
    Keeps a rolling in-memory buffer of recent events for quick diagnostics.
    """

    def __init__(self, store: Optional[TelemetryStore] = None, max_recent_events: int = 100):
        self.store = store or TelemetryStore()
        self.recent_events: deque = deque(maxlen=max_recent_events)

    def emit_event(
        self,
        event_name: ExecutionEventType,
        component: str,
        request_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        discipline: Optional[str] = None,
        persona: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionEvent:
        """
        Emits and persists an operational lifecycle event.
        Automatically resolves request_id and active context if not explicitly provided.
        """
        req_id = request_id or get_request_id() or "unknown_req"
        disc = discipline or get_discipline()
        pers = persona or get_persona()

        event = ExecutionEvent(
            event_id=str(uuid.uuid4()),
            event_name=event_name,
            request_id=req_id,
            component=component,
            duration_ms=duration_ms,
            discipline=disc,
            persona=pers,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
        )

        # Store in rolling in-memory buffer
        self.recent_events.append(event)

        # Persist to database asynchronously/non-blocking
        if self.store is not None:
            self.store.record_event(event)

        logger.debug(
            f"Event emitted: {event.event_name.value} [req_id={req_id[:8]}, comp={component}, dur={duration_ms}ms]"
        )
        return event

    def record_request_telemetry(self, telemetry: RequestTelemetrySchema) -> bool:
        """Persists completed request telemetry."""
        if self.store is not None:
            return self.store.record_request(telemetry)
        return True

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent in-memory operational events."""
        events_list = list(self.recent_events)
        events_list.reverse()
        return [e.to_dict() for e in events_list[:limit]]


_GLOBAL_COLLECTOR: Optional[TelemetryCollector] = None


def get_collector() -> TelemetryCollector:
    """Returns singleton TelemetryCollector instance."""
    global _GLOBAL_COLLECTOR
    if _GLOBAL_COLLECTOR is None:
        _GLOBAL_COLLECTOR = TelemetryCollector()
    return _GLOBAL_COLLECTOR


def set_collector(collector: TelemetryCollector) -> None:
    """Sets the global collector instance (useful for testing overrides)."""
    global _GLOBAL_COLLECTOR
    _GLOBAL_COLLECTOR = collector
