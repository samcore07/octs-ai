# Phase 7 — Error Taxonomy & Production Fault Handling

## Error Taxonomy
OCTS AI classifies all exceptions and operational failures into a standardized enum `ErrorTaxonomy`:

| Error Code | HTTP Status | Description |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Client payload validation failure |
| `ROUTING_ERROR` | 500 | Persona router failure |
| `MODEL_PROVIDER_ERROR` | 502 | LLM provider runtime exception |
| `MODEL_TIMEOUT` | 504 | LLM provider timeout threshold exceeded |
| `MODEL_RATE_LIMIT` | 429 | Upstream rate limit encountered |
| `OUTPUT_VALIDATION_ERROR` | 502 | Model generated empty or malformed payload |
| `EVALUATION_ERROR` | 500 | Quality or reliability evaluator runtime error |
| `PEER_REVIEW_ERROR` | 500 | Specialist peer review generation error |
| `REFINEMENT_ERROR` | 500 | Autonomous refinement loop failure |
| `MEMORY_RETRIEVAL_ERROR` | 500 | Context retrieval query failure |
| `MEMORY_PERSISTENCE_ERROR` | 500 | Consolidation write failure |
| `DATABASE_ERROR` | 500 | SQLite transactional failure |
| `INTERNAL_ERROR` | 500 | Unhandled internal exception |

---

## Safe Client Responses
Production clients must never receive unhandled stack traces, internal paths, or database schemas.

The `build_safe_error_response()` helper constructs uniform JSON responses:
```json
{
  "error": {
    "code": "MODEL_PROVIDER_ERROR",
    "message": "The generative model provider experienced an operational error.",
    "request_id": "f893b123-5e29-4a92-9683-1df250882e3c",
    "status_code": 502
  }
}
```

Internal logs retain full exception details and stack traces tagged with the `request_id` for SRE investigation.
