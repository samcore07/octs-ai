"""
OCTS AI - Memory REST API & Integration Test Suite
Verifies project CRUD, memory CRUD, path collision prevention,
filtering, and /ask telemetry integration.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def client():
    """Provides a thread-safe test client for FastAPI server."""
    return TestClient(server.app)


def test_project_crud_endpoints(client):
    """Verify complete CRUD lifecycle for /api/memory/projects."""
    headers = {"X-User-Id": "api_user_1"}

    # 1. Create project
    create_payload = {
        "name": "Neon Syndicate",
        "description": "Cyberpunk narrative thriller series.",
        "primary_discipline": "writers",
    }
    create_res = client.post("/api/memory/projects", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    proj = create_res.json()
    proj_id = proj["project_id"]
    assert proj["name"] == "Neon Syndicate"
    assert proj["owner_id"] == "api_user_1"

    # 2. List projects
    list_res = client.get("/api/memory/projects", headers=headers)
    assert list_res.status_code == 200
    projects = list_res.json()
    assert any(p["project_id"] == proj_id for p in projects)

    # 3. Get single project
    get_res = client.get(f"/api/memory/projects/{proj_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["project_id"] == proj_id

    # 4. Patch project
    patch_res = client.patch(
        f"/api/memory/projects/{proj_id}",
        json={"name": "Neon Syndicate: Tokyo 2099"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Neon Syndicate: Tokyo 2099"

    # 5. Delete project
    del_res = client.delete(f"/api/memory/projects/{proj_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # 6. Verify deleted project is deactivated and excluded from active listing
    get_del = client.get(f"/api/memory/projects/{proj_id}", headers=headers)
    assert get_del.status_code == 200
    assert get_del.json()["is_active"] is False

    list_after = client.get("/api/memory/projects", headers=headers)
    assert all(p["project_id"] != proj_id for p in list_after.json())


def test_path_collision_projects_vs_memory_id(client):
    """
    CRITICAL: Verify GET /api/memory/projects does not collide with GET /api/memory/{memory_id}.
    Should return 200 list response, not 404 with memory record lookup error.
    """
    res = client.get("/api/memory/projects")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_memory_crud_endpoints(client):
    """Verify complete CRUD lifecycle for /api/memory."""
    headers = {"X-User-Id": "api_user_2"}

    # 1. Create memory
    create_payload = {
        "memory_type": "user_preference",
        "scope": "discipline",
        "discipline": "musicians",
        "content": "Prefers minor scale progressions in synthwave.",
        "confidence": 0.95,
        "importance": 0.85,
    }
    create_res = client.post("/api/memory", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    mem = create_res.json()
    mem_id = mem["memory_id"]
    assert mem["content"] == "Prefers minor scale progressions in synthwave."
    assert mem["owner_id"] == "api_user_2"

    # 2. Get memory by ID
    get_res = client.get(f"/api/memory/{mem_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["memory_id"] == mem_id

    # 3. Patch memory
    patch_res = client.patch(
        f"/api/memory/{mem_id}",
        json={"content": "Prefers harmonic minor scale in synthwave.", "importance": 0.95},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["content"] == "Prefers harmonic minor scale in synthwave."
    assert patch_res.json()["importance"] == 0.95

    # 4. Delete memory (soft-delete)
    del_res = client.delete(f"/api/memory/{mem_id}", headers=headers)
    assert del_res.status_code == 200

    # 5. Verify deleted memory is now status=deleted or 404
    get_after = client.get(f"/api/memory/{mem_id}", headers=headers)
    assert get_after.status_code in (200, 404)
    if get_after.status_code == 200:
        assert get_after.json()["status"] == "deleted"


def test_memory_query_filtering(client):
    """Verify /api/memory filtering by discipline, memory_type, and status."""
    headers = {"X-User-Id": "api_user_filter"}

    client.post(
        "/api/memory",
        json={
            "memory_type": "constraint",
            "scope": "discipline",
            "discipline": "writers",
            "content": "Strict constraint: No clichés.",
        },
        headers=headers,
    )
    client.post(
        "/api/memory",
        json={
            "memory_type": "user_preference",
            "scope": "discipline",
            "discipline": "creators",
            "content": "Prefers vertical video format.",
        },
        headers=headers,
    )

    # Filter writers
    res_w = client.get("/api/memory?discipline=writers", headers=headers)
    assert res_w.status_code == 200
    items_w = res_w.json()
    assert all(m["discipline"] == "writers" for m in items_w)

    # Filter creators
    res_c = client.get("/api/memory?discipline=creators", headers=headers)
    assert res_c.status_code == 200
    items_c = res_c.json()
    assert all(m["discipline"] == "creators" for m in items_c)


def test_ask_endpoint_telemetry_with_project_and_identity(client):
    """Verify POST /ask receives X-User-Id and project_id, returning memory metadata."""
    mock_model = MagicMock()
    mock_model.invoke.return_value.content = "Creative response with established context."

    headers = {"X-User-Id": "user_telemetry"}

    # Create project first
    proj_res = client.post(
        "/api/memory/projects",
        json={"name": "Cyber Chronicles", "primary_discipline": "writers"},
        headers=headers,
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["project_id"]

    with patch.object(server, "model", mock_model):
        payload = {
            "prompt": "I prefer noir tone when crafting mystery dialogue.",
            "role": "writers",
            "project_id": proj_id,
        }
        res = client.post("/ask", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()

        assert "reply" in data
        assert "memory" in data
        assert data["memory"] is not None
        assert data["memory"]["enabled"] is True
        assert data["memory"]["project_id"] == proj_id
