"""
OCTS AI - Telemetry Storage & Persistence Repository
Manages SQLite engine lifecycle, session pooling, and persistence for operational telemetry and events.
Guarantees that telemetry persistence failures are non-fatal to primary execution.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from typing import Generator, List, Optional
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, sessionmaker

from backend.observability.events import ExecutionEvent
from backend.observability.models import ExecutionEventORM, ObservabilityBase, RequestTelemetryORM
from backend.observability.schemas import RequestTelemetrySchema

logger = logging.getLogger("octs.observability.storage")

DEFAULT_TELEMETRY_DB = "sqlite:///./octs_telemetry.db"


class TelemetryStore:
    """
    Data store for operational telemetry and lifecycle events.
    Isolates operational telemetry from user creative memory.
    """

    def __init__(self, database_url: Optional[str] = None):
        self.db_url = database_url or os.getenv("TELEMETRY_DATABASE_URL", DEFAULT_TELEMETRY_DB)

        connect_args = {}
        if self.db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self.engine = create_engine(
            self.db_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,
        )
        self.init_db()

    def init_db(self) -> None:
        """Initializes tables and indexes."""
        try:
            ObservabilityBase.metadata.create_all(bind=self.engine)
            logger.debug(f"Telemetry store initialized at '{self.db_url}'.")
        except Exception as e:
            logger.warning(f"Failed to initialize telemetry database tables: {e}", exc_info=True)

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provides transactional session scope."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def record_request(self, telemetry: RequestTelemetrySchema) -> bool:
        """Persists a completed request telemetry entry. Non-blocking and non-fatal."""
        try:
            with self.session_scope() as session:
                orm_obj = RequestTelemetryORM(
                    request_id=telemetry.request_id,
                    timestamp=telemetry.timestamp,
                    duration_ms=telemetry.duration_ms,
                    status=telemetry.status,
                    discipline=telemetry.discipline,
                    persona_id=telemetry.persona_id,
                    model_name=telemetry.model_name,
                    quality_score=telemetry.quality_score,
                    reliability_score=telemetry.reliability_score,
                    trust_score=telemetry.trust_score,
                    refinement_triggered=telemetry.refinement_triggered,
                    recovery_attempts=telemetry.recovery_attempts,
                    refinement_accepted=telemetry.refinement_accepted,
                    refinement_reverted=telemetry.refinement_reverted,
                    memories_used=telemetry.memories_used,
                    memories_extracted=telemetry.memories_extracted,
                    prompt_tokens=telemetry.prompt_tokens,
                    completion_tokens=telemetry.completion_tokens,
                    total_tokens=telemetry.total_tokens,
                    error_type=telemetry.error_type,
                    needs_clarification=telemetry.needs_clarification,
                )
                session.merge(orm_obj)
            return True
        except Exception as e:
            logger.error(f"Failed to record request telemetry [req_id={telemetry.request_id}]: {e}")
            return False

    def record_event(self, event: ExecutionEvent) -> bool:
        """Persists an operational execution event. Non-fatal."""
        try:
            with self.session_scope() as session:
                orm_event = ExecutionEventORM(
                    event_id=event.event_id,
                    request_id=event.request_id,
                    event_name=event.event_name.value if hasattr(event.event_name, "value") else str(event.event_name),
                    timestamp=event.timestamp,
                    component=event.component,
                    duration_ms=event.duration_ms,
                    discipline=event.discipline,
                    persona=event.persona,
                    metadata_json=json.dumps(event.metadata, default=str),
                )
                session.add(orm_event)
            return True
        except Exception as e:
            logger.error(f"Failed to record execution event [event={event.event_name}]: {e}")
            return False

    def prune_older_than(self, days: int = 30) -> int:
        """Prunes historical telemetry older than configured retention window."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        deleted_count = 0
        try:
            with self.session_scope() as session:
                res1 = session.query(RequestTelemetryORM).filter(RequestTelemetryORM.timestamp < cutoff).delete()
                res2 = session.query(ExecutionEventORM).filter(ExecutionEventORM.timestamp < cutoff).delete()
                deleted_count = (res1 or 0) + (res2 or 0)
            logger.info(f"Pruned {deleted_count} telemetry records older than {days} days.")
            return deleted_count
        except Exception as e:
            logger.error(f"Error pruning telemetry records: {e}")
            return 0
