# Phase 7 — Observability & Correlation Specification

## Request Correlation Subsystem
Request correlation ensures every log line, operational event, metrics point, and database record can be mapped back to a specific client invocation.

### Correlation ID Lifecycle
1. **Ingress**: `RequestCorrelationMiddleware` checks incoming request headers for:
   - `X-Request-ID`
   - `X-Correlation-ID`
2. **Validation**: The identifier is evaluated against `^[a-zA-Z0-9_\-\.]{4,64}$` to guarantee safety against header injection or malformed strings. If absent or invalid, a standard UUID4 is generated.
3. **Context Binding**: The validated ID is set into Python `contextvars` (`request_id` and `correlation_id`).
4. **Graph Propagation**: The ID is injected into `OrchestrationState["request_id"]` and LangGraph configuration metadata.
5. **Egress**: The resolved ID is stamped into the HTTP response header `X-Request-ID`.
6. **Cleanup**: Context is cleared after request processing to guarantee zero memory leakage.

### ContextVars Safety
Python `contextvars` natively isolate execution contexts across asynchronous tasks (`asyncio`). Unlike thread-local storage or mutable global dicts, concurrent requests cannot interleave or overwrite each other's IDs.

---

## Structured JSON Logging
Default human-readable logging is supplemented by `StructuredJSONFormatter` adhering to RFC 8259.

### Log Entry Structure
```json
{
  "timestamp": "2026-11-15T11:45:00.123456+00:00",
  "level": "INFO",
  "logger": "octs.orchestration.executor",
  "message": "Invoking LangGraph pipeline [req_id=f893b123, role=writers, prompt_len=84]",
  "request_id": "f893b123-5e29-4a92-9683-1df250882e3c",
  "correlation_id": "f893b123-5e29-4a92-9683-1df250882e3c",
  "discipline": "writers",
  "persona": "novelist"
}
```

### Automatic Credential Scrubbing
To ensure no credentials or tokens leak into production log aggregators, the log formatter runs pre-compiled regular expressions against every log record message and sanitized payload:
- Google AI Studio API Keys: `AIza[0-9A-Za-z-_]{35}` -> `[REDACTED_SECRET]`
- OpenAI & API Provider Keys: `sk-[a-zA-Z0-9]{20,}` -> `[REDACTED_SECRET]`
- HTTP Bearer Tokens: `bearer\s+[a-zA-Z0-9_\-\.]{20,}` -> `[REDACTED_SECRET]`
- Password & Secret Parameters: `(password|passwd|secret)\s*[:=]\s*\S+` -> `[REDACTED_SECRET]`
- Sensitive Dictionary Keys: Any payload containing keys such as `api_key`, `token`, `authorization` are masked with `"[REDACTED]"`.
