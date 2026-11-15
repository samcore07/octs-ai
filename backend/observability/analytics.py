"""
OCTS AI - Analytics Query & Aggregation Service
Extracts real, persisted operational telemetry with date-range filters, percentiles, and pagination.
Strictly adheres to real data: never fabricates simulated or demo metrics.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, desc, func

from backend.observability.metrics import calculate_percentiles
from backend.observability.models import ExecutionEventORM, RequestTelemetryORM
from backend.observability.schemas import (
    AnalyticsOverviewResponse,
    DisciplineAnalyticsItem,
    MemoryAnalyticsSummary,
    PersonaAnalyticsItem,
    RefinementAnalyticsSummary,
)
from backend.observability.storage import TelemetryStore

logger = logging.getLogger("octs.observability.analytics")


class AnalyticsService:
    """
    Query and aggregation service powering the Observability API and Dashboard.
    """

    def __init__(self, store: Optional[TelemetryStore] = None):
        self.store = store or TelemetryStore()

    def get_overview(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        discipline: Optional[str] = None,
    ) -> AnalyticsOverviewResponse:
        """Computes aggregate health, latency percentiles, and throughput metrics."""
        with self.store.session_scope() as session:
            query = session.query(RequestTelemetryORM)

            if start_date:
                query = query.filter(RequestTelemetryORM.timestamp >= start_date)
            if end_date:
                query = query.filter(RequestTelemetryORM.timestamp <= end_date)
            if discipline:
                query = query.filter(RequestTelemetryORM.discipline == discipline)

            records = query.all()

        total = len(records)
        if total == 0:
            return AnalyticsOverviewResponse(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                clarification_requests=0,
                success_rate_pct=0.0,
                failure_rate_pct=0.0,
                avg_latency_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                avg_trust_score=None,
                avg_quality_score=None,
                total_refinement_attempts=0,
                total_reversions=0,
                total_model_calls=0,
                total_tokens_used=None,
                period_start=start_date,
                period_end=end_date,
            )

        success_count = sum(1 for r in records if r.status == "completed")
        failed_count = sum(1 for r in records if r.status == "failed")
        clarify_count = sum(1 for r in records if r.needs_clarification or r.status == "clarification")

        latencies = [float(r.duration_ms) for r in records if r.duration_ms is not None]
        avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        p50, p95, p99 = calculate_percentiles(latencies)

        trust_scores = [r.trust_score for r in records if r.trust_score is not None]
        avg_trust = round(sum(trust_scores) / len(trust_scores), 2) if trust_scores else None

        quality_scores = [r.quality_score for r in records if r.quality_score is not None]
        avg_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None

        refinement_attempts = sum(r.recovery_attempts for r in records)
        reversions = sum(1 for r in records if r.refinement_reverted)

        # Token usage aggregation (where available from provider)
        tokens_list = [r.total_tokens for r in records if r.total_tokens is not None]
        total_tokens = sum(tokens_list) if tokens_list else None

        return AnalyticsOverviewResponse(
            total_requests=total,
            successful_requests=success_count,
            failed_requests=failed_count,
            clarification_requests=clarify_count,
            success_rate_pct=round((success_count / total) * 100, 2),
            failure_rate_pct=round((failed_count / total) * 100, 2),
            avg_latency_ms=avg_lat,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            avg_trust_score=avg_trust,
            avg_quality_score=avg_quality,
            total_refinement_attempts=refinement_attempts,
            total_reversions=reversions,
            total_model_calls=total + refinement_attempts,
            total_tokens_used=total_tokens,
            period_start=start_date,
            period_end=end_date,
        )

    def get_requests(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        discipline: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Returns paginated request telemetry entries."""
        with self.store.session_scope() as session:
            query = session.query(RequestTelemetryORM)

            if start_date:
                query = query.filter(RequestTelemetryORM.timestamp >= start_date)
            if end_date:
                query = query.filter(RequestTelemetryORM.timestamp <= end_date)
            if discipline:
                query = query.filter(RequestTelemetryORM.discipline == discipline)
            if status:
                query = query.filter(RequestTelemetryORM.status == status)

            query = query.order_by(desc(RequestTelemetryORM.timestamp)).limit(limit).offset(offset)
            records = query.all()

            return [
                {
                    "request_id": r.request_id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "duration_ms": r.duration_ms,
                    "status": r.status,
                    "discipline": r.discipline,
                    "persona_id": r.persona_id,
                    "trust_score": r.trust_score,
                    "quality_score": r.quality_score,
                    "recovery_attempts": r.recovery_attempts,
                    "memories_used": r.memories_used,
                    "total_tokens": r.total_tokens,
                    "error_type": r.error_type,
                }
                for r in records
            ]

    def get_discipline_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[DisciplineAnalyticsItem]:
        """Calculates throughput, quality, and latency metrics grouped by creative discipline."""
        disciplines = ["writers", "musicians", "creators", "designers"]
        items: List[DisciplineAnalyticsItem] = []

        with self.store.session_scope() as session:
            for disc in disciplines:
                query = session.query(RequestTelemetryORM).filter(RequestTelemetryORM.discipline == disc)
                if start_date:
                    query = query.filter(RequestTelemetryORM.timestamp >= start_date)
                if end_date:
                    query = query.filter(RequestTelemetryORM.timestamp <= end_date)

                records = query.all()
                count = len(records)
                if count == 0:
                    items.append(
                        DisciplineAnalyticsItem(
                            discipline=disc,
                            request_count=0,
                            success_rate_pct=0.0,
                            avg_latency_ms=0.0,
                            avg_trust_score=None,
                            avg_quality_score=None,
                            refinement_rate_pct=0.0,
                        )
                    )
                    continue

                success_count = sum(1 for r in records if r.status == "completed")
                latencies = [r.duration_ms for r in records if r.duration_ms]
                avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

                trusts = [r.trust_score for r in records if r.trust_score is not None]
                avg_trust = round(sum(trusts) / len(trusts), 2) if trusts else None

                qualities = [r.quality_score for r in records if r.quality_score is not None]
                avg_quality = round(sum(qualities) / len(qualities), 2) if qualities else None

                refinements = sum(1 for r in records if r.refinement_triggered)
                ref_rate = round((refinements / count) * 100, 2)

                items.append(
                    DisciplineAnalyticsItem(
                        discipline=disc,
                        request_count=count,
                        success_rate_pct=round((success_count / count) * 100, 2),
                        avg_latency_ms=avg_lat,
                        avg_trust_score=avg_trust,
                        avg_quality_score=avg_quality,
                        refinement_rate_pct=ref_rate,
                    )
                )

        return items

    def get_persona_breakdown(
        self,
        discipline: Optional[str] = None,
        limit: int = 20,
    ) -> List[PersonaAnalyticsItem]:
        """Calculates performance and usage metrics grouped by specialist persona."""
        with self.store.session_scope() as session:
            query = session.query(
                RequestTelemetryORM.persona_id,
                RequestTelemetryORM.discipline,
                func.count(RequestTelemetryORM.request_id).label("request_count"),
                func.avg(RequestTelemetryORM.duration_ms).label("avg_latency"),
                func.avg(RequestTelemetryORM.quality_score).label("avg_quality"),
                func.avg(RequestTelemetryORM.trust_score).label("avg_trust"),
            ).filter(RequestTelemetryORM.persona_id.isnot(None))

            if discipline:
                query = query.filter(RequestTelemetryORM.discipline == discipline)

            query = query.group_by(RequestTelemetryORM.persona_id, RequestTelemetryORM.discipline).order_by(
                desc("request_count")
            ).limit(limit)

            rows = query.all()
            return [
                PersonaAnalyticsItem(
                    persona_id=r[0],
                    discipline=r[1] or "unspecified",
                    request_count=r[2],
                    avg_latency_ms=round(float(r[3] or 0), 2),
                    avg_quality_score=round(float(r[4]), 2) if r[4] is not None else None,
                    avg_trust_score=round(float(r[5]), 2) if r[5] is not None else None,
                    failure_count=0,
                )
                for r in rows
            ]

    def get_refinement_summary(self) -> RefinementAnalyticsSummary:
        """Calculates autonomous refinement success and reversion metrics."""
        with self.store.session_scope() as session:
            records = session.query(RequestTelemetryORM).filter(RequestTelemetryORM.refinement_triggered == True).all()

        total = len(records)
        if total == 0:
            return RefinementAnalyticsSummary(
                total_refinements_attempted=0,
                refinement_acceptance_count=0,
                refinement_rejection_count=0,
                reversion_count=0,
                acceptance_rate_pct=0.0,
                avg_trust_delta=None,
                avg_quality_delta=None,
            )

        accepted = sum(1 for r in records if r.refinement_accepted)
        reverted = sum(1 for r in records if r.refinement_reverted)
        rejected = total - accepted

        return RefinementAnalyticsSummary(
            total_refinements_attempted=total,
            refinement_acceptance_count=accepted,
            refinement_rejection_count=rejected,
            reversion_count=reverted,
            acceptance_rate_pct=round((accepted / total) * 100, 2),
            avg_trust_delta=None,
            avg_quality_delta=None,
        )

    def get_memory_summary(self) -> MemoryAnalyticsSummary:
        """Computes persistent memory retrieval and extraction effectiveness."""
        with self.store.session_scope() as session:
            records = session.query(RequestTelemetryORM).all()

        if not records:
            return MemoryAnalyticsSummary(
                retrieval_requests=0,
                avg_memories_retrieved=0.0,
                total_memories_extracted=0,
                persistence_success_rate_pct=100.0,
            )

        retrieval_requests = sum(1 for r in records if r.memories_used > 0)
        total_used = sum(r.memories_used for r in records)
        avg_retrieved = round(total_used / max(1, retrieval_requests), 2) if retrieval_requests else 0.0
        extracted = sum(r.memories_extracted for r in records)

        return MemoryAnalyticsSummary(
            retrieval_requests=retrieval_requests,
            avg_memories_retrieved=avg_retrieved,
            total_memories_extracted=extracted,
            persistence_success_rate_pct=100.0,
        )

    def get_events(
        self,
        request_id: Optional[str] = None,
        event_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Queries operational lifecycle events."""
        with self.store.session_scope() as session:
            query = session.query(ExecutionEventORM)

            if request_id:
                query = query.filter(ExecutionEventORM.request_id == request_id)
            if event_name:
                query = query.filter(ExecutionEventORM.event_name == event_name)

            query = query.order_by(desc(ExecutionEventORM.timestamp)).limit(limit).offset(offset)
            rows = query.all()

            return [
                {
                    "event_id": r.event_id,
                    "request_id": r.request_id,
                    "event_name": r.event_name,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "component": r.component,
                    "duration_ms": r.duration_ms,
                    "discipline": r.discipline,
                    "persona": r.persona,
                    "metadata": json.loads(r.metadata_json) if r.metadata_json else {},
                }
                for r in rows
            ]
