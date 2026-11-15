# OCTS AI — Phase 4: API Reference

## 1. Primary Execution Endpoint: `POST /ask`

Submits creative tasks for persona routing, LangGraph execution, and Phase 4 dual-dimension evaluation.

### Endpoint Details
* **Method:** `POST`
* **Path:** `/ask`
* **Content-Type:** `application/json`

### Request Schema (`PromptRequest`)
```json
{
  "prompt": "Create an opening hook and retention strategy for a documentary video.",
  "role": "creators",
  "session_id": "optional-session-id",
  "task_type": "optional-task-override"
}
```

---

### Response Schema (`PromptResponse`) — Deterministic Execution
```json
{
  "reply": "Stop scrolling! Here is the documentary retention framework:\n1. Hook: Start at the climax.\n2. Body: Unfold the mystery.\n3. CTA: Subscribe for part two.",
  "role": "creators",
  "agent_used": "hook_retention_architect",
  "trust_score": 91.5,
  "trust_breakdown": {
    "quality_score": 87.86,
    "reliability_score": 100.0,
    "quality_weight": 0.70,
    "reliability_weight": 0.30,
    "formula_explanation": "TrustScore (91.5) = (QualityScore [87.86] * 0.70) + (ReliabilityScore [100.0] * 0.30)"
  },
  "evaluation": {
    "evaluation_id": "c1f7b5e4-2391-49b8-a764-927164998792",
    "evaluation_status": "completed",
    "discipline": "creators",
    "agent_used": "hook_retention_architect",
    "evaluation_mode": "deterministic",
    "evaluation_method": "deterministic",
    "judge_status": "not_used",
    "fallback_triggered": false,
    "fallback_reason": null,
    "quality_score": 87.86,
    "reliability_score": 100.0,
    "trust_score": 91.5,
    "evaluation_coverage": 1.0,
    "evaluation_summary": "Evaluated via deterministic craft heuristics.",
    "criteria_breakdown": [
      {
        "criterion_id": "hook_effectiveness",
        "criterion_name": "Hook Effectiveness",
        "score": 92.0,
        "max_score": 100.0,
        "weight": 0.20,
        "weighted_score": 18.4,
        "evidence": "Opening establishes an immediate curiosity gap or pattern interrupt.",
        "status": "passed"
      }
    ],
    "reliability_checks": [
      {
        "check_id": "output_exists",
        "check_name": "Output Presence Verification",
        "status": "passed",
        "severity": "critical",
        "explanation": "Generated output exists and is a valid string payload."
      }
    ],
    "limitations": [
      "Evaluates editorial pacing, hook psychology, and platform structure from script text.",
      "Does not predict or guarantee audience retention rates, viral reach, or platform algorithmic distribution."
    ],
    "evaluated_at": 1794723000.12,
    "evaluation_duration_ms": 2
  },
  "latency_ms": 480,
  "recovery_triggered": false,
  "model_used": "gemini-3.5-flash-lite",
  "needs_clarification": false,
  "clarification_question": null,
  "routing_confidence": 0.95,
  "execution_status": "completed"
}
```

---

### Response Schema — LLM Judge Fallback
When the LLM judge times out or produces invalid JSON, the system transparently falls back to deterministic heuristics:
```json
{
  "evaluation": {
    "evaluation_status": "completed",
    "evaluation_mode": "llm_judge",
    "evaluation_method": "deterministic",
    "judge_status": "timeout",
    "fallback_triggered": true,
    "fallback_reason": "Model API call timed out after 10000ms",
    "quality_score": 88.0,
    "reliability_score": 100.0,
    "trust_score": 91.6,
    "evaluation_summary": "Evaluated via deterministic fallback (Judge status: timeout)."
  }
}
```

---

### Response Schema — Clarification Path (Case C)
```json
{
  "reply": "Your request touches multiple creative disciplines. To give you the best assistance, which creative area are you focusing on?\n\n1. Writers & Storytellers\n2. Musicians & Singers\n3. Content Creators\n4. Visual Artists & Designers",
  "role": null,
  "agent_used": null,
  "trust_score": null,
  "trust_breakdown": null,
  "evaluation": {
    "evaluation_status": "skipped",
    "evaluation_method": "skipped",
    "judge_status": "not_used",
    "quality_score": null,
    "reliability_score": null,
    "trust_score": null,
    "criteria_breakdown": [],
    "reliability_checks": [],
    "evaluation_coverage": 0.0,
    "evaluation_summary": "Evaluation skipped: Request required clarification across disciplines; no generation occurred."
  },
  "latency_ms": 7,
  "recovery_triggered": false,
  "model_used": "gemini-3.5-flash-lite",
  "needs_clarification": true,
  "clarification_question": "Your request touches multiple creative disciplines...",
  "routing_confidence": 0.0,
  "execution_status": "completed_clarification_required"
}
```

---

## 2. Diagnostics & Health: `GET /api/health`
```bash
curl -s http://127.0.0.1:8000/api/health | jq .
```
```json
{
  "status": "ok",
  "version": "0.2.0",
  "model_provider": "google_genai",
  "model_name": "gemini-3.5-flash-lite",
  "langsmith_tracing": false
}
```
