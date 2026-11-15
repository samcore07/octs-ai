# Phase 7 — Execution Event Taxonomy

## Event Model
All operational events adhere to the `ExecutionEvent` dataclass and `ExecutionEventSchema` Pydantic model:

| Field | Type | Description |
|---|---|---|
| `event_id` | `str` (UUID) | Unique identifier for the individual lifecycle event |
| `request_id` | `str` | Correlated request identifier |
| `event_name` | `ExecutionEventType` | Canonical lifecycle event name from taxonomy |
| `timestamp` | `datetime` (UTC) | Monotonically generated ISO 8601 UTC timestamp |
| `component` | `str` | Generating component (e.g. `execute_model_node`) |
| `duration_ms` | `Optional[float]` | Stage execution duration in milliseconds |
| `discipline` | `Optional[str]` | Active creative discipline (e.g. `writers`) |
| `persona` | `Optional[str]` | Active specialist persona (e.g. `novelist`) |
| `metadata` | `Dict[str, Any]` | Sanitized diagnostic context (lengths, tokens, scores) |

---

## Complete 24-Event Lifecycle Taxonomy

```text
# 1. Request Lifecycle
request_started
request_completed
request_failed
request_clarification_required

# 2. Memory Intelligence
context_identified
memory_retrieval_started
memory_retrieval_completed
memory_persistence_completed

# 3. Request Routing
routing_started
routing_completed
routing_fallback

# 4. Specialist Persona Preparation
persona_prepared

# 5. Model Generation
model_execution_started
model_execution_completed
model_execution_failed

# 6. Structural Output Validation
output_validation_completed

# 7. Quality & Reliability Evaluation
evaluation_started
evaluation_completed
evaluation_failed

# 8. Specialist Peer Review
peer_review_started
peer_review_completed
peer_review_fallback

# 9. Autonomous Refinement & Self-Correction
refinement_started
refinement_completed
refinement_rejected
refinement_reverted
```
