# Phase 1: Backend Foundation & Infrastructure

Welcome to the engineering documentation for **Phase 1** of **Octs AI**, a professional AI Creative Harness designed to assist creative professionals across four core disciplines: **Writers**, **Musicians**, **Content Creators**, and **Visual Artists & Designers**.

Phase 1 establishes a production-grade backend foundation, modularizing the server architecture, implementing typed configuration management, introducing structured Pydantic schemas, setting up safe and optional LangSmith observability, enforcing security and CORS controls, and delivering a comprehensive automated test suite.

---

## Table of Contents

- [Phase Overview](#phase-overview)
- [Objectives & Scope](#objectives--scope)
- [Key Accomplishments](#key-accomplishments)
- [Technology Stack](#technology-stack)
- [Implementation Status](#implementation-status)
- [Documentation Index](#documentation-index)
- [Prerequisites](#prerequisites)
- [Quickstart: Run and Verify](#quickstart-run-and-verify)
- [Next Phase Preview](#next-phase-preview)

---

## Phase Overview

Prior to Phase 1, the backend consisted of a monolithic script (`server.py`) with unvalidated dictionary payloads, wildcard CORS configurations (`allow_origins=["*"]`), no telemetry or health monitoring endpoints, and no automated testing.

Phase 1 refactors this architecture into a maintainable, clean backend package (`backend/`) without altering the existing frontend application, user interface, or API backwards compatibility.

---

## Objectives & Scope

### In-Scope (Delivered)
1. **Modular Backend Package**: Created `backend/` directory with distinct modules for configuration (`config.py`), request/response schemas (`schemas.py`), and observability (`tracing.py`).
2. **Type-Safe Configuration**: Replaced unstructured environment reads with Pydantic Settings (`backend/config.py`), supporting default values, type coercion, and comma-separated CORS parsing.
3. **Structured Validation**: Defined explicit Pydantic models for incoming and outgoing payloads while strictly preserving `{ "reply": "..." }` contract compatibility for the existing frontend.
4. **Resilient Tracing**: Implemented non-blocking LangSmith initialization (`backend/tracing.py`) that degrades gracefully if API keys are absent or disabled.
5. **System Health & Telemetry**: Added `GET /api/health` providing real-time status of server version, active model provider, model name, and tracing configuration.
6. **HTTP Method Guards**: Added an explicit handler for `GET /ask` returning HTTP 405 Method Not Allowed with clear guidance.
7. **Comprehensive Unit Testing**: Created a dedicated automated test suite (`backend/tests/`) with 15 passing tests covering configuration parsing and API endpoints.

### Out-of-Scope (Deferred to Phase 2 & Beyond)
- Multi-agent LangGraph workflow execution and state graphs (Phase 2).
- Discipline-specific specialist personas and task routing (Phase 2).
- Dynamic TrustScore calculation engine and reflection loops (Phase 2).
- Persistent checkpointing with SQLite/PostgreSQL (Phase 2).
- Frontend modifications or UI redesigns (strictly preserved).

---

## Key Accomplishments

| Area | Prior State | Phase 1 State |
| :--- | :--- | :--- |
| **Server Architecture** | Monolithic `server.py` | Modular `server.py` + `backend/` package |
| **Config Management** | Raw `os.getenv` with minimal fallbacks | Strict Pydantic `BaseSettings` with validation |
| **CORS Policy** | Wildcard `["*"]` allowing all origins | Configurable origin whitelist parsed via settings |
| **API Contracts** | Raw dictionaries (`request.json()`) | Validated Pydantic models with legacy preservation |
| **Health Monitoring** | None (only root HTML route) | Standardized `GET /api/health` endpoint |
| **Observability** | Untraced LLM execution | Safe, optional LangSmith integration |
| **Test Coverage** | 0 tests | 15 unit and integration tests passing (`pytest`) |

---

## Technology Stack

- **Runtime**: Python 3.10+
- **Web Framework**: FastAPI `>= 0.115.0`
- **ASGI Server**: Uvicorn `>= 0.32.0`
- **Configuration & Validation**: Pydantic `>= 2.9.0`, Pydantic Settings `>= 2.5.0`
- **LLM Integration**: LangChain Google GenAI (`langchain-google-genai >= 2.0.0`)
- **Observability**: LangSmith (`langsmith >= 0.1.100`)
- **Testing**: Pytest (`pytest >= 8.0.0`), HTTPX (`httpx >= 0.27.0`)

---

## Implementation Status

- [x] **Modular Backend Structure**: Complete (`backend/__init__.py`, `backend/config.py`, `backend/schemas.py`, `backend/tracing.py`).
- [x] **Pydantic Settings & Defaults**: Complete and verified against `.env.example`.
- [x] **Optional LangSmith Telemetry**: Complete with zero crashes when unconfigured.
- [x] **Strict CORS Whitelist**: Complete with environment-based override capability.
- [x] **Health Endpoint (`GET /api/health`)**: Complete and reporting live system telemetry.
- [x] **Safe `GET /ask` Handler**: Complete, returning 405 with structured message.
- [x] **Automated Test Suite**: 15/15 tests passing in `backend/tests/`.
- [x] **Zero Frontend Regressions**: All static pages, stylesheets, and client scripts preserved.

---

## Documentation Index

Explore the detailed Phase 1 documentation:

1. [**Architecture & System Design**](ARCHITECTURE.md) — Comprehensive explanation of backend modularization, request lifecycle, and Mermaid architectural diagrams.
2. [**API Reference**](API_REFERENCE.md) — Specification of all active endpoints, request/response schemas, validation constraints, and curl examples.
3. [**Configuration Guide**](CONFIGURATION.md) — Environment variables reference, default values, Pydantic Settings validation rules, and local setup.
4. [**Testing Documentation**](TESTING.md) — Automated test suite structure, execution guide, test fixtures, mocking strategy, and verification results.
5. [**Implementation Log**](IMPLEMENTATION_LOG.md) — Detailed technical log of files created/modified, architectural refactorings, and resolved technical debt.
6. [**Architectural Decision Records (ADRs)**](DECISIONS.md) — Formal records documenting rationale, context, and consequences of key architectural choices.

---

## Prerequisites

Before running the backend, ensure you have:
1. Python 3.10 or higher installed.
2. A virtual environment created and activated:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Required dependencies installed:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
4. A valid `.env` file created from `.env.example`:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY to .env
   ```

---

## Quickstart: Run and Verify

### 1. Run the Test Suite
Execute all automated unit and integration tests:
```bash
python3 -m pytest backend/tests/ -v
```
Expected output:
```text
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

### 2. Start the Development Server
```bash
python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Verify Health Check
In a separate terminal or browser:
```bash
curl -X GET http://127.0.0.1:8000/api/health
```
Response:
```json
{
  "status": "ok",
  "version": "0.2.0",
  "model_provider": "google_genai",
  "model_name": "gemini-3.5-flash-lite",
  "langsmith_tracing": false
}
```

### 4. Verify Static Frontend
Open `http://127.0.0.1:8000` in your web browser to access the Octs AI Creative Harness interface.

---

## Next Phase Preview

With Phase 1 infrastructure verified and stable, the project is prepared for **Phase 2: Agent Architecture & Graph Orchestration**:
- Implementation of `backend/agents/` containing the four discipline agents (`writers`, `musicians`, `creators`, `designers`).
- Construction of `backend/orchestrator/` featuring LangGraph state graphs and recovery engines.
- Integration of persistent checkpointing via SQLite.
- Implementation of realistic TrustScore evaluation.
