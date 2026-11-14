"""
Octs AI - API Endpoint & Backward Compatibility Tests
Uses FastAPI TestClient with deterministic mocked model responses.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
import server


@pytest.fixture
def client():
    """Provides a thread-safe test client."""
    return TestClient(server.app)


def test_health_endpoint(client):
    """Verify system diagnostics endpoint returns valid health payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.2.0"
    assert "model_provider" in data
    assert "model_name" in data


def test_serve_home(client):
    """Verify root GET / serves index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Octs AI" in response.text


def test_ask_endpoint_backward_compatibility(client):
    """
    CRITICAL: Verify POST /ask accepts exact existing payload {'prompt': '...'}
    and returns exact expected key {'reply': '...'} for frontend compatibility.
    """
    mock_model = MagicMock()
    mock_model.invoke.return_value.content = "Simulated creative guidance for testing."

    with patch.object(server, "model", mock_model):
        payload = {"prompt": "Write a 3-act story outline"}
        response = client.post("/ask", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Primary backward compatibility invariant:
        assert "reply" in data
        assert data["reply"] == "Simulated creative guidance for testing."
        assert "latency_ms" in data


def test_ask_endpoint_with_valid_role(client):
    """Verify valid discipline is accepted and returned."""
    mock_model = MagicMock()
    mock_model.invoke.return_value.content = "Verse and chorus structure."

    with patch.object(server, "model", mock_model):
        payload = {"prompt": "Compose chords", "role": "musicians"}
        response = client.post("/ask", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Verse and chorus structure."
        assert data["role"] == "musicians"


def test_ask_endpoint_rejects_invalid_role(client):
    """Verify invalid discipline is rejected with 422 validation error."""
    payload = {"prompt": "Test prompt", "role": "invalid_astrology_role"}
    response = client.post("/ask", json=payload)
    assert response.status_code == 422


def test_ask_endpoint_rejects_empty_prompt(client):
    """Verify empty prompt is rejected with 422."""
    payload = {"prompt": ""}
    response = client.post("/ask", json=payload)
    assert response.status_code == 422


def test_ask_endpoint_rejects_whitespace_prompt(client):
    """Verify prompt containing only whitespace is rejected."""
    payload = {"prompt": "     \n\t   "}
    response = client.post("/ask", json=payload)
    assert response.status_code == 422


def test_ask_endpoint_handles_model_failure(client):
    """Verify model invocation failures return HTTP 500 gracefully."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = RuntimeError("Google GenAI API Quota Exceeded")

    with patch.object(server, "model", mock_model):
        payload = {"prompt": "Write a story to trigger simulated failure", "role": "writers"}
        response = client.post("/ask", json=payload)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Quota Exceeded" in data["detail"]


def test_ask_get_fallback_endpoint(client):
    """Verify accidental GET /ask returns friendly informative error instead of 405."""
    response = client.get("/ask")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "HTTP POST" in data["message"]


def test_static_files_accessible(client):
    """Verify static assets remain fully accessible through gateway."""
    css_res = client.get("/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers.get("content-type", "")

    js_res = client.get("/script.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers.get("content-type", "")
