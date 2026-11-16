"""
OCTS AI - Comprehensive Health, Liveness & Readiness Probes
Verifies runtime dependencies including database connectivity, model provider readiness,
and registry integrity with sanitized status reporting.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional
from sqlalchemy import text

from backend.config import Settings, get_settings
from backend.observability.schemas import (
    DependencyHealth,
    DetailedHealthResponse,
    HealthStatus,
    LivenessResponse,
    ReadinessResponse,
)
from backend.supabase_client import is_supabase_configured, test_supabase_connection

logger = logging.getLogger("octs.observability.health")


class HealthChecker:
    """
    Evaluates health, liveness, and readiness across system dependencies.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        memory_store: Optional[Any] = None,
        telemetry_store: Optional[Any] = None,
        model: Optional[Any] = None,
    ):
        self.settings = settings or get_settings()
        self.memory_store = memory_store
        self.telemetry_store = telemetry_store
        self.model = model
        self._start_time = time.time()

    def check_liveness(self) -> LivenessResponse:
        """
        Liveness probe: verifies process is alive and responsive.
        Never fails due to optional external dependency degradation.
        """
        return LivenessResponse(status="alive", timestamp=datetime.now(timezone.utc))

    def check_readiness(self) -> ReadinessResponse:
        """
        Readiness probe: verifies essential dependencies are ready to accept traffic.
        """
        db_ready = self._verify_database()
        model_ready = self.model is not None or bool(self.settings.gemini_api_key)

        is_ready = db_ready and model_ready
        return ReadinessResponse(
            status="ready" if is_ready else "not_ready",
            timestamp=datetime.now(timezone.utc),
            database_ready=db_ready,
            model_ready=model_ready,
        )

    def check_detailed_health(self) -> DetailedHealthResponse:
        """
        Comprehensive system inspection: reports individual component latencies and statuses.
        Guarantees zero secret exposure.
        """
        deps: List[DependencyHealth] = []
        overall_healthy = True

        # 1. Memory Database Probe
        t0 = time.perf_counter()
        db_ok = self._verify_database()
        db_lat = round((time.perf_counter() - t0) * 1000, 2)
        if db_ok:
            deps.append(DependencyHealth(name="memory_database", status=HealthStatus.HEALTHY, latency_ms=db_lat))
        else:
            deps.append(DependencyHealth(name="memory_database", status=HealthStatus.UNHEALTHY, latency_ms=db_lat))
            overall_healthy = False

        # 2. Telemetry Store Probe
        t1 = time.perf_counter()
        tel_ok = self._verify_telemetry_database()
        tel_lat = round((time.perf_counter() - t1) * 1000, 2)
        deps.append(
            DependencyHealth(
                name="telemetry_database",
                status=HealthStatus.HEALTHY if tel_ok else HealthStatus.DEGRADED,
                latency_ms=tel_lat,
            )
        )

        # 3. Model Configuration Probe
        has_key = bool(self.settings.gemini_api_key) or self.model is not None
        deps.append(
            DependencyHealth(
                name="model_provider",
                status=HealthStatus.HEALTHY if has_key else HealthStatus.DEGRADED,
                details={
                    "provider": self.settings.model_provider,
                    "model": self.settings.model_name,
                    "configured": has_key,
                },
            )
        )

        # 4. LangSmith Optional Probe
        tracing_active = self.settings.is_langsmith_active()
        deps.append(
            DependencyHealth(
                name="langsmith_tracing",
                status=HealthStatus.HEALTHY if tracing_active else HealthStatus.DEGRADED,
                details={"enabled": self.settings.langsmith_tracing, "active": tracing_active},
            )
        )

        # 5. Supabase Cloud Database Probe
        if is_supabase_configured():
            t_sb = time.perf_counter()
            sb_diag = test_supabase_connection()
            sb_lat = round((time.perf_counter() - t_sb) * 1000, 2)
            sb_status = HealthStatus.HEALTHY if sb_diag.get("status") == "connected" else HealthStatus.DEGRADED
            deps.append(
                DependencyHealth(
                    name="supabase_cloud",
                    status=sb_status,
                    latency_ms=sb_lat,
                    details=sb_diag,
                )
            )

        return DetailedHealthResponse(
            status=HealthStatus.HEALTHY if overall_healthy else HealthStatus.DEGRADED,
            version="0.2.0",
            timestamp=datetime.now(timezone.utc),
            dependencies=deps,
            model_provider=self.settings.model_provider,
            model_name=self.settings.model_name,
            langsmith_tracing=tracing_active,
            uptime_seconds=round(time.time() - self._start_time, 2),
        )

    def _verify_database(self) -> bool:
        """Executes a lightweight ping against the database."""
        try:
            if self.memory_store and hasattr(self.memory_store, "session_scope"):
                with self.memory_store.session_scope() as session:
                    session.execute(text("SELECT 1"))
                return True
            return True
        except Exception as e:
            logger.warning(f"Database readiness check failed: {e}")
            return False

    def _verify_telemetry_database(self) -> bool:
        """Executes a ping against the telemetry database."""
        try:
            if self.telemetry_store and hasattr(self.telemetry_store, "session_scope"):
                with self.telemetry_store.session_scope() as session:
                    session.execute(text("SELECT 1"))
                return True
            return True
        except Exception:
            return False
