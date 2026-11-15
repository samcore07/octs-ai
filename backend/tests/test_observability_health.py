"""
Unit and Integration Tests for Comprehensive Health, Liveness & Readiness Probes
Verifies operational checks, dependency failure handling, and zero secret leakage.
"""

from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from backend.observability.health import HealthChecker
import server


@pytest.fixture
def client():
    return TestClient(server.app)


def test_liveness_endpoint(client):
    """Verify GET /api/health/live returns HTTP 200 and status=alive."""
    resp = client.get("/api/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_endpoint_healthy(client):
    """Verify GET /api/health/ready returns HTTP 200 when system dependencies are ready."""
    resp = client.get("/api/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database_ready"] is True
    assert data["model_ready"] is True


def test_readiness_endpoint_dependency_failure(monkeypatch):
    """Verify GET /api/health/ready returns HTTP 503 when critical dependency fails."""
    # Simulate database connection failure
    monkeypatch.setattr(server.health_checker, "_verify_database", lambda: False)

    client = TestClient(server.app)
    resp = client.get("/api/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "not_ready"
    assert data["database_ready"] is False


def test_detailed_health_sanitization(client):
    """Verify GET /api/health returns detailed dependencies without leaking connection strings or keys."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] in ("ok", "unhealthy")
    assert "dependencies" in data
    assert isinstance(data["dependencies"], list)

    # Validate that sensitive substrings do not appear anywhere in JSON response
    raw_text = resp.text
    assert "password" not in raw_text.lower()
    assert "secret" not in raw_text.lower()
    assert "sqlite:///" not in raw_text
