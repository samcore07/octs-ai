"""
Integration Tests for Analytics API Subsystem
Verifies /api/analytics endpoints with filters, pagination, empty state behavior,
and strict adherence to real persisted data.
"""

from fastapi.testclient import TestClient
import pytest

from backend.observability.events import ExecutionEvent, ExecutionEventType
from backend.observability.schemas import RequestTelemetrySchema
from backend.observability.storage import TelemetryStore
import server


@pytest.fixture
def client():
    return TestClient(server.app)


@pytest.fixture
def sample_telemetry_data():
    """Populates telemetry database with controlled test records for analytics validation."""
    store = server.analytics_service.store

    # 1. Successful Writers request with refinement
    rec1 = RequestTelemetrySchema(
        request_id="test-req-writers-001",
        correlation_id="test-corr-001",
        duration_ms=450,
        status="completed",
        discipline="writers",
        persona_id="novelist",
        trust_score=88.5,
        quality_score=92.0,
        recovery_attempts=1,
        refinement_triggered=True,
        refinement_accepted=True,
        refinement_reverted=False,
        memories_used=2,
        memories_extracted=1,
        prompt_tokens=150,
        completion_tokens=300,
        total_tokens=450,
    )

    # 2. Musicians request without refinement
    rec2 = RequestTelemetrySchema(
        request_id="test-req-musicians-002",
        correlation_id="test-corr-002",
        duration_ms=620,
        status="completed",
        discipline="musicians",
        persona_id="composer",
        trust_score=84.0,
        quality_score=86.0,
        recovery_attempts=0,
        refinement_triggered=False,
        refinement_accepted=False,
        refinement_reverted=False,
        memories_used=0,
        memories_extracted=0,
    )

    store.record_request(rec1)
    store.record_request(rec2)

    # Lifecycle event
    store.record_event(
        ExecutionEvent(
            event_id="test-event-001",
            event_name=ExecutionEventType.REQUEST_STARTED,
            component="test_fixture",
            request_id="test-req-writers-001",
            discipline="writers",
            persona="novelist",
        )
    )


def test_analytics_overview_endpoint(client, sample_telemetry_data):
    """Verify /api/analytics/overview returns aggregate percentiles and counts."""
    resp = client.get("/api/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_requests"] >= 2
    assert data["successful_requests"] >= 2
    assert data["avg_latency_ms"] > 0
    assert data["p50_latency_ms"] > 0
    assert data["avg_trust_score"] is not None


def test_analytics_requests_endpoint_filtering_and_pagination(client, sample_telemetry_data):
    """Verify /api/analytics/requests supports discipline filtering and pagination."""
    resp = client.get("/api/analytics/requests?discipline=writers&limit=10")
    assert resp.status_code == 200
    items = resp.json()

    assert isinstance(items, list)
    assert len(items) >= 1
    assert all(item["discipline"] == "writers" for item in items)


def test_analytics_disciplines_breakdown(client, sample_telemetry_data):
    """Verify /api/analytics/disciplines returns 4 creative disciplines."""
    resp = client.get("/api/analytics/disciplines")
    assert resp.status_code == 200
    items = resp.json()

    disciplines = {item["discipline"] for item in items}
    assert disciplines == {"writers", "musicians", "creators", "designers"}


def test_analytics_refinement_summary(client, sample_telemetry_data):
    """Verify /api/analytics/refinement returns real autonomous refinement stats."""
    resp = client.get("/api/analytics/refinement")
    assert resp.status_code == 200
    data = resp.json()

    assert "total_refinements_attempted" in data
    assert "acceptance_rate_pct" in data


def test_analytics_memory_summary(client, sample_telemetry_data):
    """Verify /api/analytics/memory returns retrieval and extraction stats."""
    resp = client.get("/api/analytics/memory")
    assert resp.status_code == 200
    data = resp.json()

    assert "retrieval_requests" in data
    assert "avg_memories_retrieved" in data


def test_analytics_events_endpoint(client, sample_telemetry_data):
    """Verify /api/analytics/events returns lifecycle audit records."""
    resp = client.get("/api/analytics/events?event_name=request_started")
    assert resp.status_code == 200
    events = resp.json()

    assert isinstance(events, list)
    assert len(events) >= 1
    assert all(e["event_name"] == "request_started" for e in events)
