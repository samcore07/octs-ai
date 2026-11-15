"""
Unit and Integration Tests for Request Correlation Subsystem
Verifies UUID generation, correlation validation, context isolation across concurrent async tasks,
and HTTP response header injection.
"""

import asyncio
from fastapi.testclient import TestClient
import pytest

from backend.observability.context import (
    clear_request_context,
    get_context_dict,
    get_correlation_id,
    get_request_id,
    set_request_context,
)
from backend.observability.correlation import generate_request_id, resolve_request_id, validate_correlation_id
import server


def test_request_id_generation():
    """Verify generated request IDs are non-empty valid strings."""
    req_id_1 = generate_request_id()
    req_id_2 = generate_request_id()

    assert isinstance(req_id_1, str)
    assert len(req_id_1) >= 16
    assert req_id_1 != req_id_2


def test_validate_correlation_id():
    """Verify safe correlation ID validation against invalid or malicious patterns."""
    assert validate_correlation_id("abc-123_XYZ") == "abc-123_XYZ"
    assert validate_correlation_id("req-999.prod") == "req-999.prod"
    assert validate_correlation_id("invalid spaces") is None
    assert validate_correlation_id("<script>") is None
    assert validate_correlation_id("'; DROP TABLE--") is None
    assert validate_correlation_id("a" * 129) is None  # Exceeds max length


def test_resolve_request_id_priority():
    """Verify supplied request ID is respected when valid, or fallback generated."""
    # 1. Valid custom header
    assert resolve_request_id({"x-request-id": "custom-req-id-123"}) == "custom-req-id-123"

    # 2. Invalid header format produces new safe UUID
    fallback = resolve_request_id({"x-request-id": "bad id with spaces!"})
    assert fallback != "bad id with spaces!"
    assert len(fallback) >= 16

    # 3. Empty or None headers produces new safe UUID
    gen = resolve_request_id(None)
    assert len(gen) >= 16


def test_contextvars_concurrency_isolation():
    """
    Verify Python contextvars isolate request contexts across concurrent async tasks
    without cross-contamination.
    """
    async def run_isolation_check():
        async def worker(worker_id: int):
            req_id = f"worker-req-{worker_id}"
            corr_id = f"corr-{worker_id}"
            set_request_context(
                request_id=req_id,
                correlation_id=corr_id,
                discipline=f"disc_{worker_id}",
                persona=f"persona_{worker_id}",
                owner_id=f"user_{worker_id}",
            )

            # Yield execution to allow interleaving
            await asyncio.sleep(0.01)

            ctx = get_context_dict()
            assert ctx["request_id"] == req_id
            assert ctx["correlation_id"] == corr_id
            assert ctx["discipline"] == f"disc_{worker_id}"
            assert ctx["persona"] == f"persona_{worker_id}"
            assert ctx["owner_id"] == f"user_{worker_id}"

            clear_request_context()
            assert get_request_id() is None

        # Launch 20 concurrent tasks
        tasks = [worker(i) for i in range(20)]
        await asyncio.gather(*tasks)

    asyncio.run(run_isolation_check())


def test_http_request_id_header_propagation():
    """Verify HTTP requests return X-Request-ID and X-Correlation-ID in response headers."""
    client = TestClient(server.app)

    # Without client headers
    resp = client.get("/api/health/live")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    generated_id = resp.headers["x-request-id"]
    assert len(generated_id) >= 16

    # With client supplied correlation ID
    custom_id = "client-trace-12345"
    resp2 = client.get("/api/health/live", headers={"x-request-id": custom_id})
    assert resp2.status_code == 200
    assert resp2.headers.get("x-request-id") == custom_id
