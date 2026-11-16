"""
Unit and Integration Tests for Supabase Cloud Database Module
Verifies:
1. Environment detection and configuration defaults.
2. Graceful fallback to SQLite when Supabase is unconfigured.
3. Client initialization and connection testing with mock Supabase client.
4. Memory, Project, and Telemetry synchronization functions.
5. FastAPI /api/supabase/status and /api/supabase/test endpoints.
"""

from unittest.mock import MagicMock, patch
import pytest
from starlette.testclient import TestClient

from backend.supabase_client import (
    delete_memory_record,
    delete_project_record,
    get_supabase_client,
    get_supabase_config,
    is_supabase_configured,
    reset_supabase_client,
    sync_execution_event,
    sync_memory_record,
    sync_project_record,
    sync_telemetry_record,
    test_supabase_connection as run_supabase_connection_test,
)
from server import app


@pytest.fixture(autouse=True)
def clean_supabase_state(monkeypatch):
    """Ensures Supabase client singleton is reset before each test."""
    reset_supabase_client()
    yield
    reset_supabase_client()


def test_supabase_unconfigured_defaults(monkeypatch):
    """When no Supabase env variables are provided, should report not configured."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert is_supabase_configured() is False
    assert get_supabase_client() is None

    result = run_supabase_connection_test()
    assert result["status"] == "not_configured"
    assert result["mode"] == "sqlite_fallback"


def test_supabase_detection_with_env(monkeypatch):
    """Detects configuration when SUPABASE_URL and SUPABASE_KEY are set."""
    monkeypatch.setenv("SUPABASE_URL", "https://xyzexample.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key-12345")

    cfg = get_supabase_config()
    assert cfg["url"] == "https://xyzexample.supabase.co"
    assert cfg["key"] == "test-key-12345"
    assert is_supabase_configured() is True


def test_supabase_connection_test_with_mock_client(monkeypatch):
    """Verifies connection test probe when mock Supabase client is present."""
    monkeypatch.setenv("SUPABASE_URL", "https://xyzexample.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key-12345")

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_limit = MagicMock()

    mock_limit.execute.return_value = MagicMock(data=[{"id": "1"}])
    mock_select.limit.return_value = mock_limit
    mock_table.select.return_value = mock_select
    mock_client.table.return_value = mock_table

    with patch("backend.supabase_client.get_supabase_client", return_value=mock_client):
        res = run_supabase_connection_test()
        assert res["status"] == "connected"
        assert res["mode"] == "supabase_cloud"
        assert res["latency_ms"] is not None
        assert res["tables"]["projects"] == "available"
        assert res["tables"]["memory_records"] == "available"


def test_supabase_sync_memory_record():
    """Verifies memory record upsert call to Supabase client."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_upsert = MagicMock()

    mock_upsert.execute.return_value = MagicMock(data=[])
    mock_table.upsert.return_value = mock_upsert
    mock_client.table.return_value = mock_table

    with patch("backend.supabase_client.get_supabase_client", return_value=mock_client):
        success = sync_memory_record({
            "memory_id": "mem-100",
            "owner_id": "user-1",
            "content": "Craft constraint: no passive voice.",
            "memory_type": "craft_rule",
            "scope": "discipline",
            "discipline": "writers",
        })

        assert success is True
        mock_client.table.assert_called_with("memory_records")
        mock_table.upsert.assert_called_once()


def test_supabase_delete_memory_record():
    """Verifies memory deletion call to Supabase client."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_del = MagicMock()
    mock_eq = MagicMock()

    mock_eq.execute.return_value = MagicMock(data=[])
    mock_del.eq.return_value = mock_eq
    mock_table.delete.return_value = mock_del
    mock_client.table.return_value = mock_table

    with patch("backend.supabase_client.get_supabase_client", return_value=mock_client):
        success = delete_memory_record("mem-100")
        assert success is True
        mock_client.table.assert_called_with("memory_records")
        mock_table.delete.assert_called_once()
        mock_del.eq.assert_called_with("memory_id", "mem-100")


def test_supabase_sync_project_record():
    """Verifies project record upsert call to Supabase client."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_upsert = MagicMock()

    mock_upsert.execute.return_value = MagicMock(data=[])
    mock_table.upsert.return_value = mock_upsert
    mock_client.table.return_value = mock_table

    with patch("backend.supabase_client.get_supabase_client", return_value=mock_client):
        success = sync_project_record({
            "project_id": "proj-1",
            "owner_id": "user-1",
            "name": "Neon Dreams",
            "discipline": "musicians",
        })

        assert success is True
        mock_client.table.assert_called_with("projects")
        mock_table.upsert.assert_called_once()


def test_supabase_sync_telemetry_record():
    """Verifies telemetry insertion call to Supabase client."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_insert = MagicMock()

    mock_insert.execute.return_value = MagicMock(data=[])
    mock_table.insert.return_value = mock_insert
    mock_client.table.return_value = mock_table

    with patch("backend.supabase_client.get_supabase_client", return_value=mock_client):
        success = sync_telemetry_record({
            "request_id": "req-123",
            "duration_ms": 350.2,
            "status": "success",
            "discipline": "writers",
            "persona_id": "narrative_architect",
        })

        assert success is True
        mock_client.table.assert_called_with("request_telemetry")
        mock_table.insert.assert_called_once()


def test_supabase_status_endpoint():
    """Verifies GET /api/supabase/status returns valid schema."""
    client = TestClient(app)
    res = client.get("/api/supabase/status")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "mode" in data
    assert "has_direct_postgres" in data
    assert "has_rest_api" in data


def test_supabase_test_endpoint():
    """Verifies POST /api/supabase/test endpoint responds."""
    client = TestClient(app)
    res = client.post("/api/supabase/test")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "mode" in data


def test_api_health_includes_database_provider():
    """Verifies GET /api/health includes database provider metadata."""
    client = TestClient(app)
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "database_provider" in data
    assert "supabase_configured" in data
    assert data["database_provider"] in ("sqlite_local", "supabase_cloud")
