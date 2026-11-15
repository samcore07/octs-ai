# Phase 7 — Architectural Decision Records (ADRs)

## ADR-001: SQLite Database Separation for Telemetry
- **Status**: Accepted
- **Context**: OCTS AI uses SQLite for creative memory persistence (`octs_memory.db`). High-frequency telemetry writes (every request and event) sharing the same SQLite database would introduce write-lock contention.
- **Decision**: Introduce a distinct telemetry database file (`octs_telemetry.db`) managed by `TelemetryStore`.
- **Consequences**: Telemetry writes never block creative memory transactions or session persistence.

## ADR-002: Context Isolation via Python Contextvars
- **Status**: Accepted
- **Context**: In an asynchronous ASGI server (FastAPI/Uvicorn), global variables or thread-local storage can leak state across concurrent requests.
- **Decision**: Use Python's standard `contextvars` module to bind `request_id`, `correlation_id`, `discipline`, and `persona`.
- **Consequences**: Zero context cross-contamination across concurrent requests without passing context objects manually into every internal helper function.

## ADR-003: Non-Fatal Observability Errors
- **Status**: Accepted
- **Context**: Observability is an operational harness, not the primary application purpose.
- **Decision**: All event emissions and telemetry recordings are wrapped in defensive exception handlers. If writing telemetry to disk fails, primary creative generation succeeds and returns normally.
- **Consequences**: Telemetry storage degradation cannot trigger user-facing generation failures.

## ADR-004: Strict Anti-Fabrication for Token Usage
- **Status**: Accepted
- **Context**: Some systems estimate token usage or compute approximate costs when providers do not return exact usage metadata.
- **Decision**: Never fabricate token counts or costs. If the model provider does not return `usage_metadata`, the values remain `None` (`null` in API and UI).
- **Consequences**: Metric integrity is preserved with zero false data presented to users.
