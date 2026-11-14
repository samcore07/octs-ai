# Phase 1: Testing & Verification Guide

This document describes the testing architecture, test suites, mocking strategy, and verification procedures established in **Phase 1** of **Octs AI**.

---

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Framework & Tooling](#test-framework--tooling)
- [Test Directory Structure](#test-directory-structure)
- [How to Run the Tests](#how-to-run-the-tests)
- [Detailed Test Suite Breakdown](#detailed-test-suite-breakdown)
  - [1. Configuration Tests (`test_config.py`)](#1-configuration-tests-test_configpy)
  - [2. API & Endpoint Tests (`test_api.py`)](#2-api--endpoint-tests-test_apipy)
- [Mocking Strategy & Isolation](#mocking-strategy--isolation)
- [Test Results & Verification Evidence](#test-results--verification-evidence)
- [Adding New Tests](#adding-new-tests)

---

## Testing Philosophy

Prior to Phase 1, the repository contained no automated tests. Validation relied entirely on manual browser clicking.

Phase 1 establishes a comprehensive automated testing standard centered on three core principles:
1. **Zero External Dependency on LLM Quotas**: Unit tests must execute reliably in CI/CD and offline environments without incurring real Google Gemini API calls or quota consumption.
2. **Strict Contract Verification**: All request payloads, response schemas, and status codes are checked against explicit Pydantic models.
3. **Comprehensive Edge-Case Testing**: Invalid roles, oversized inputs, empty prompts, whitespace strings, and method guards are systematically validated.

---

## Test Framework & Tooling

- **Test Runner**: `pytest >= 8.0.0`
- **HTTP Client**: `starlette.testclient.TestClient` (built on `httpx`)
- **Mocking**: `unittest.mock.MagicMock`, `unittest.mock.patch.object`
- **Assertions**: Standard Python assertions with descriptive pytest failure output.

---

## Test Directory Structure

```text
backend/tests/
├── __init__.py           # Package indicator
├── test_config.py        # Configuration, environment parsing & validation (5 tests)
└── test_api.py           # Endpoints, schemas, validation & CORS headers (10 tests)
```

---

## How to Run the Tests

### 1. Run the Full Suite
Execute all tests from the repository root:
```bash
python3 -m pytest backend/tests/ -v
```

### 2. Run Only Configuration Tests
```bash
python3 -m pytest backend/tests/test_config.py -v
```

### 3. Run Only API Tests
```bash
python3 -m pytest backend/tests/test_api.py -v
```

### 4. Run a Specific Test Case
```bash
python3 -m pytest backend/tests/test_api.py -k "test_ask_endpoint_with_role" -v
```

---

## Detailed Test Suite Breakdown

### 1. Configuration Tests (`test_config.py`)

This suite validates the Pydantic Settings class and LangSmith tracing setup:

| Test Name | Purpose / Assertion | Status |
| :--- | :--- | :--- |
| `test_default_settings` | Verifies default values for model name (`gemini-3.5-flash-lite`), provider (`google_genai`), temperature, and allowed disciplines (`writers`, `musicians`, `creators`, `designers`). | **PASSED** |
| `test_cors_origins_parsing` | Validates that a comma-separated string (e.g., `"https://app.octs.ai, https://admin.octs.ai"`) is parsed into a clean list of trimmed strings. | **PASSED** |
| `test_tracing_disabled_by_default` | Confirms `setup_tracing()` returns `False` and sets `LANGSMITH_TRACING="false"` when tracing is disabled. | **PASSED** |
| `test_tracing_missing_api_key_graceful` | Confirms graceful fallback to `False` and `LANGSMITH_TRACING="false"` when `langsmith_tracing=True` but the API key is empty. | **PASSED** |
| `test_tracing_enabled_with_valid_key` | Confirms `setup_tracing()` exports `LANGSMITH_TRACING="true"`, `LANGSMITH_PROJECT`, and `LANGSMITH_API_KEY` when configured with a valid key. | **PASSED** |

### 2. API & Endpoint Tests (`test_api.py`)

This suite tests the FastAPI application endpoints via `TestClient`:

| Test Name | Purpose / Assertion | Status |
| :--- | :--- | :--- |
| `test_health_endpoint` | Asserts `GET /api/health` returns HTTP 200 with JSON matching `HealthResponse` (`status="ok"`, `version="0.2.0"`, model provider, and model name). | **PASSED** |
| `test_serve_home` | Asserts `GET /` returns HTTP 200 with HTML content type (`text/html`) containing "Octs AI". | **PASSED** |
| `test_ask_endpoint_backward_compatibility` | **CRITICAL**: Submits `{ "prompt": "..." }`, asserts HTTP 200 and response contains top-level `"reply"` key for frontend compatibility. | **PASSED** |
| `test_ask_endpoint_with_valid_role` | Submits `{ "prompt": "...", "role": "writers" }`, asserts HTTP 200 and `"role": "writers"` in response. | **PASSED** |
| `test_ask_endpoint_rejects_invalid_role` | Submits `{ "prompt": "...", "role": "unsupported_discipline" }`, asserts HTTP 400 Bad Request. | **PASSED** |
| `test_ask_endpoint_rejects_empty_prompt` | Submits `{ "prompt": "" }`, asserts HTTP 422 Unprocessable Entity. | **PASSED** |
| `test_ask_endpoint_rejects_whitespace_prompt` | Submits `{ "prompt": "   " }`, asserts HTTP 422 Unprocessable Entity. | **PASSED** |
| `test_ask_endpoint_handles_model_failure` | Simulates downstream model failure, asserts HTTP 500 with proper error message. | **PASSED** |
| `test_ask_get_fallback_endpoint` | Requests `GET /ask`, asserts HTTP 405 Method Not Allowed with JSON error message. | **PASSED** |
| `test_static_files_accessible` | Requests `/index.html` via static files mount, asserts HTTP 200. | **PASSED** |

---

## Mocking Strategy & Isolation

To isolate the test environment from external Google API services, `test_api.py` utilizes `patch.object` on the `server.model` object:

```python
from unittest.mock import MagicMock, patch
import server

def test_ask_endpoint_with_role():
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Mocked creative response for writer."
    mock_model.invoke.return_value = mock_response

    with patch.object(server, "model", mock_model):
        response = client.post("/ask", json={
            "prompt": "Create a character flaw for a protagonist.",
            "role": "writers"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Mocked creative response for writer."
        assert data["role"] == "writers"
```

### Why `patch.object`?
Because `ChatGoogleGenerativeAI` is a Pydantic v2 `BaseModel`, conventional attribute path patching (e.g. `patch("server.model.invoke")`) can fail due to Pydantic attribute interception. Patching the top-level `server.model` reference cleanly intercepts the call across all endpoint invocations without altering the underlying class.

---

## Test Results & Verification Evidence

The full test suite was executed and verified:

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: /Users/samriddha/Documents/Octs
collected 15 items

backend/tests/test_api.py::test_health_endpoint PASSED                   [  6%]
backend/tests/test_api.py::test_serve_home PASSED                        [ 13%]
backend/tests/test_api.py::test_ask_endpoint_backward_compatibility PASSED [ 20%]
backend/tests/test_api.py::test_ask_endpoint_with_valid_role PASSED      [ 26%]
backend/tests/test_api.py::test_ask_endpoint_rejects_invalid_role PASSED [ 33%]
backend/tests/test_api.py::test_ask_endpoint_rejects_empty_prompt PASSED [ 40%]
backend/tests/test_api.py::test_ask_endpoint_rejects_whitespace_prompt PASSED [ 46%]
backend/tests/test_api.py::test_ask_endpoint_handles_model_failure PASSED [ 53%]
backend/tests/test_api.py::test_ask_get_fallback_endpoint PASSED         [ 60%]
backend/tests/test_api.py::test_static_files_accessible PASSED           [ 66%]
backend/tests/test_config.py::TestConfigAndTracing::test_cors_origins_parsing PASSED [ 73%]
backend/tests/test_config.py::TestConfigAndTracing::test_default_settings PASSED [ 80%]
backend/tests/test_config.py::TestConfigAndTracing::test_tracing_disabled_by_default PASSED [ 86%]
backend/tests/test_config.py::TestConfigAndTracing::test_tracing_enabled_with_valid_key PASSED [ 93%]
backend/tests/test_config.py::TestConfigAndTracing::test_tracing_missing_api_key_graceful PASSED [100%]

============================== 15 passed in 0.69s ==============================
```

- **Total Tests**: 15
- **Passed**: 15 (100%)
- **Failed**: 0
- **Execution Time**: 0.55 seconds

---

## Adding New Tests

When contributing new features in subsequent phases:
1. **Place tests in `backend/tests/`**: Name test files with prefix `test_*.py`.
2. **Maintain deterministic mocking**: Mock external network calls to LangSmith or Gemini.
3. **Assert response schemas**: Use Pydantic schemas to validate output structure (`HealthResponse.model_validate(response.json())`).
4. **Run the suite before pushing**: Ensure all existing tests remain green.
