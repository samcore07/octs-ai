# Phase 1: Architectural Decision Records (ADRs)

This document formalizes the architectural decisions made during **Phase 1: Backend Foundation & Infrastructure** of **Octs AI**, capturing the context, evaluated alternatives, rationale, and consequences for each choice.

---

## Index of Decisions

- [ADR-001: Pydantic Settings for Configuration Management](#adr-001-pydantic-settings-for-configuration-management)
- [ADR-002: Optional & Non-Blocking LangSmith Tracing Initialization](#adr-002-optional--non-blocking-langsmith-tracing-initialization)
- [ADR-003: Strict & Configurable CORS Origins Policy](#adr-003-strict--configurable-cors-origins-policy)
- [ADR-004: Preservation of Legacy `POST /ask` Response Contract](#adr-004-preservation-of-legacy-post-ask-response-contract)
- [ADR-005: Separation of Backend Concerns into Modular Packages](#adr-005-separation-of-backend-concerns-into-modular-packages)

---

## ADR-001: Pydantic Settings for Configuration Management

### Status
**Accepted**

### Context
Prior to Phase 1, the backend read environment variables ad-hoc using `os.getenv("GEMINI_API_KEY")`. There were no type checks, no validation for ranges (such as model temperature), and no clear defaults for settings like model names or timeout limits. As the system prepares for LangGraph agents, multi-model support, and telemetry, unstructured configuration would lead to runtime failures and hidden bugs.

### Decision
Implement configuration management via `pydantic-settings` (`BaseSettings`), encapsulated in `backend/config.py`.

### Rationale
- **Declarative Typing**: Variables are cast to explicit Python types (`int`, `float`, `bool`, `list[str]`).
- **Automatic `.env` Parsing**: Seamlessly reads `.env` files while ignoring extraneous operating system variables.
- **Fail-Fast Validation**: Erroneous values (e.g. invalid temperature floats or corrupted numbers) are caught at application boot time rather than during user requests.
- **Test Overridability**: Settings instances can be instantiated directly with keyword arguments during unit testing without modifying host environment variables.

### Consequences
- **Positive**: Clean centralized configuration, immutable settings objects, self-documenting parameters.
- **Negative**: Adds `pydantic-settings` dependency.
- **Alternatives Considered**:
  - Raw `python-dotenv` with manual `os.getenv`: Rejected due to lack of type coercion, validation, and testing friction.
  - JSON/YAML configuration files: Rejected to maintain 12-factor application compatibility where environment variables drive runtime config.

---

## ADR-002: Optional & Non-Blocking LangSmith Tracing Initialization

### Status
**Accepted**

### Context
Observability into agent execution, latency, and token consumption is critical for production AI systems. LangSmith provides this capability for LangChain applications. However, requiring LangSmith API keys would break local development, CI pipelines, and offline evaluation for developers who do not have an active LangSmith subscription.

### Decision
Implement LangSmith tracing as an **optional, non-blocking** service in `backend/tracing.py`. Tracing is enabled only if `LANGSMITH_TRACING=true` and a valid `LANGSMITH_API_KEY` is present. If missing or invalid, tracing is safely disabled, an informational warning is logged, and server initialization proceeds unimpeded.

### Rationale
- **Zero Local Friction**: Developers can clone the repository, provide only a `GEMINI_API_KEY`, and immediately run tests or local servers.
- **CI/CD Reliability**: Automated test runners do not need external observability credentials.
- **Production Readiness**: When deployed to staging or production, simply setting the environment variables activates end-to-end tracing without code modifications.

### Consequences
- **Positive**: High developer ergonomics, resilient startup, no runtime exceptions due to missing telemetry keys.
- **Negative**: Traces may be inadvertently skipped if an invalid key is supplied and the log warning is ignored.
- **Alternatives Considered**:
  - Mandatory LangSmith initialization: Rejected because it blocks local development and unit tests.
  - Custom logging middleware: Rejected because LangSmith provides automatic, deep-trace graph visualization specifically designed for LangChain and LangGraph.

---

## ADR-003: Strict & Configurable CORS Origins Policy

### Status
**Accepted**

### Context
The original implementation of `server.py` used wildcard CORS origins:
```python
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
...
```
This configuration is insecure for production systems as it allows arbitrary external websites to execute authenticated requests against the API from a user's browser.

### Decision
Replace wildcard origins with a configurable whitelist managed via `backend.config.Settings.cors_origins`.
- Default to standard local development ports:
  - `http://127.0.0.1:8000`
  - `http://localhost:8000`
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- Allow override via the `CORS_ORIGINS` environment variable, supporting comma-separated origin strings.

### Rationale
- **Security Compliance**: Adheres to modern web security standards by preventing untrusted cross-origin requests.
- **Deployment Flexibility**: Production domains (e.g. `https://app.octsai.com`) can be injected via `.env` without modifying Python code.
- **Convenience**: Includes a Pydantic field validator that strips whitespace and parses comma-separated strings automatically.

### Consequences
- **Positive**: Closes the security hole created by `allow_origins=["*"]`.
- **Negative**: If a developer runs the frontend on an unusual port (e.g., `8080`), they must explicitly update `CORS_ORIGINS` in `.env`.
- **Alternatives Considered**:
  - Keeping wildcard `["*"]`: Rejected due to serious security vulnerabilities.
  - Hardcoded localhost-only origins: Rejected because it prevents production hosting on custom domains.

---

## ADR-004: Preservation of Legacy `POST /ask` Response Contract

### Status
**Accepted**

### Context
The existing frontend (`js/main.js` and `js/dashboard.js`) parses responses from `POST /ask` with the expectation of a JSON object containing a `"reply"` key:
```javascript
const data = await response.json();
displayMessage(data.reply);
```
Rewriting the frontend at this stage would violate the project's strict architectural constraints and risk introducing client regressions. However, the backend needs to return richer metadata (such as latency, agent role, and TrustScore).

### Decision
Extend the `PromptResponse` Pydantic schema to include all new metadata while **strictly maintaining the top-level `"reply"` field**:
```json
{
  "reply": "Model generated response text...",
  "role": "writers",
  "agent_used": "direct_model",
  "trust_score": null,
  "trust_breakdown": null,
  "latency_ms": 1142.85,
  "recovery_triggered": false,
  "model_used": "gemini-3.5-flash-lite"
}
```

### Rationale
- **100% Backward Compatibility**: Existing frontend scripts continue functioning seamlessly without needing changes.
- **Forward Extensibility**: Modern frontend features or debugging tools can inspect `latency_ms`, `agent_used`, and `trust_score` as they are developed.
- **Single Source of Truth**: The schema is formally defined and validated in `backend/schemas.py`.

### Consequences
- **Positive**: Zero frontend breaking changes; existing UX works without disruption.
- **Negative**: Backend carries the legacy `reply` field alongside newer metadata fields.
- **Alternatives Considered**:
  - Renaming `reply` to `content` or `output`: Rejected because it breaks the current frontend without user consent.
  - Creating a separate `/api/v2/ask` endpoint: Rejected at Phase 1 to avoid duplicating endpoint logic prior to LangGraph integration.

---

## ADR-005: Separation of Backend Concerns into Modular Packages

### Status
**Accepted**

### Context
Prior to Phase 1, `server.py` combined routing, model instantiation, environment variable loading, and static file serving in a single file. As Phase 2 will introduce multi-agent graph workflows, checkpointing, and evaluation engines, continuing with a monolithic structure would make the codebase unmaintainable and impossible to test thoroughly.

### Decision
Establish a dedicated `backend/` package and decompose the backend into single-responsibility modules:
- `backend/config.py`: Environment configuration and validation.
- `backend/schemas.py`: Pydantic data contracts for requests and responses.
- `backend/tracing.py`: LangSmith observability hooks.
- `server.py`: FastAPI route assembly, middleware configuration, and static file serving.
- `backend/tests/`: Automated unit and integration test suite.

### Rationale
- **High Cohesion, Low Coupling**: Each module has a single reason to change.
- **Testability**: Components such as `config` and `schemas` can be unit tested without starting the ASGI web server.
- **Smooth Phase 2 Progression**: Creates clean integration points for `backend/agents/` and `backend/orchestrator/` in the next phase.

### Consequences
- **Positive**: Clean architecture, clear import hierarchies, easy onboarding for developers.
- **Negative**: Increases the number of files in the project.
- **Alternatives Considered**:
  - Keeping everything in `server.py`: Rejected due to severe maintainability and scalability limitations.
  - Over-architecting into multiple microservices: Rejected as an unnecessary operational overhead for this stage of the project.
