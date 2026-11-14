"""
OCTS AI - End-to-End Orchestration Integration Tests
Tests FastAPI HTTP endpoints with the real LangGraph pipeline using TestClient and mocked model.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
import server


@pytest.fixture
def client():
    return TestClient(server.app)


def test_integration_ask_endpoint_end_to_end(client):
    """Verify full end-to-end execution of POST /ask through LangGraph pipeline."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Three-act structure outlined with inciting incident and climax."
    mock_model.invoke.return_value = mock_response

    with patch.object(server, "model", mock_model):
        response = client.post("/ask", json={
            "prompt": "Design a 3-act narrative outline with high stakes.",
            "role": "writers",
        })

        assert response.status_code == 200
        data = response.json()

        # Contract guarantees
        assert "reply" in data
        assert data["reply"] == "Three-act structure outlined with inciting incident and climax."
        assert data["role"] == "writers"
        assert data["agent_used"] == "narrative_architect"
        assert "latency_ms" in data
        assert data["latency_ms"] >= 0
        assert data["model_used"] == "gemini-3.5-flash-lite"


def test_integration_ask_endpoint_musicians(client):
    """Verify musicians route executes via lyricist_meter_engine."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Rhyme scheme designed in AABB format."
    mock_model.invoke.return_value = mock_response

    with patch.object(server, "model", mock_model):
        response = client.post("/ask", json={
            "prompt": "Help me write lyrics with a tight rhyme scheme and meter.",
            "role": "musicians",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["agent_used"] == "lyricist_meter_engine"
        assert data["role"] == "musicians"


def test_integration_health_check_operational(client):
    """Verify GET /api/health remains fully operational."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.2.0"
    assert "model_provider" in data


def test_integration_root_route_serves_frontend(client):
    """Verify GET / continues serving index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Octs AI" in response.text


def test_integration_model_failure_returns_500(client):
    """Verify model invocation failures return HTTP 500 cleanly."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = RuntimeError("Google Gemini API Quota Exceeded")

    with patch.object(server, "model", mock_model):
        response = client.post("/ask", json={
            "prompt": "Outline a novel",
            "role": "writers",
        })
        assert response.status_code == 500
        data = response.json()
        assert "Quota Exceeded" in data["detail"]
