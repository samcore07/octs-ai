# OCTS AI — Phase 5: API Specification & Contracts

## 1. Gateway Overview
OCTS AI preserves strict backward compatibility with existing frontends and legacy integration tests. The response payload structure maintains `reply` as the primary output text, while enriching metadata with Phase 4 evaluation metrics and Phase 5 autonomous refinement telemetry.

---

## 2. POST /ask (Primary Execution Endpoint)

### Request Contract (`PromptRequest`)
```json
{
  "prompt": "Write a three-act plot outline for Elena finding the celestial cipher.",
  "role": "writers",
  "session_id": "session-1234",
  "task_type": "story_outline"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `prompt` | `string` | **Yes** | Creative query or task (1 to 50,000 characters; whitespace validated). |
| `role` | `string` | No | Creative discipline: `writers`, `musicians`, `creators`, `designers`. |
| `session_id` | `string` | No | Optional identifier for thread continuity. |
| `task_type` | `string` | No | Specific task category override. |

---

### Response Contract (`PromptResponse`)
```json
{
  "reply": "### Act I: The Awakening\nElena discovered the ancient manuscript...\n\n### Act II: The Conflict\nShe confronted the guild master...\n\n### Act III: The Climax\nWith decisive action, she shattered the mirror...",
  "role": "writers",
  "agent_used": "narrative_architect",
  "trust_score": 89.74,
  "trust_breakdown": {
    "quality_score": 85.35,
    "reliability_score": 100.0,
    "quality_weight": 0.70,
    "reliability_weight": 0.30,
    "formula_explanation": "TrustScore (89.74) = (QualityScore [85.35] * 0.70) + (ReliabilityScore [100.0] * 0.30)"
  },
  "latency_ms": 342,
  "recovery_triggered": true,
  "model_used": "gemini-3.5-flash-lite",
  "needs_clarification": false,
  "clarification_question": null,
  "routing_confidence": 0.95,
  "execution_status": "completed",
  "evaluation": {
    "evaluation_id": "96b27e4e-0a58-45b6-bc21-6d9b93be81b0",
    "evaluation_status": "completed",
    "discipline": "writers",
    "agent_used": "narrative_architect",
    "evaluation_mode": "deterministic",
    "quality_score": 85.35,
    "reliability_score": 100.0,
    "trust_score": 89.74,
    "criteria_breakdown": [
      {
        "criterion_id": "instruction_adherence",
        "criterion_name": "Instruction Adherence",
        "score": 92.0,
        "max_score": 100.0,
        "weight": 0.15,
        "weighted_score": 13.8,
        "evidence": "Output directly integrates core entities and instructions from the prompt.",
        "status": "passed"
      }
    ]
  },
  "refinement": {
    "refinement_triggered": true,
    "recovery_attempts": 1,
    "max_recovery_attempts": 2,
    "initial_quality_score": 76.9,
    "final_quality_score": 85.35,
    "quality_delta": 8.45,
    "initial_trust_score": 80.83,
    "final_trust_score": 89.74,
    "trust_delta": 8.91,
    "peer_review_conducted": true,
    "reviewer_persona_id": "lore_continuity_keeper",
    "refinement_status": "improved",
    "improvement_history": [
      {
        "attempt_number": 1,
        "selection_reason": "Candidate demonstrated composite TrustScore improvement (+8.9 pts: 80.8 -> 89.7).",
        "candidate_accepted": true,
        "is_improvement": true,
        "previous_best_score": 80.83,
        "candidate_score": 89.74,
        "previous_quality_score": 76.9,
        "new_quality_score": 85.35,
        "quality_delta": 8.45,
        "previous_reliability_score": 90.0,
        "new_reliability_score": 100.0,
        "reliability_delta": 10.0,
        "previous_coverage": 1.0,
        "new_coverage": 1.0,
        "coverage_delta": 0.0,
        "previous_trust_score": 80.83,
        "new_trust_score": 89.74,
        "trust_delta": 8.91,
        "improved_criteria": ["instruction_adherence", "narrative_coherence", "structural_quality"],
        "regressed_criteria": [],
        "unchanged_criteria": ["character_consistency", "originality_creativity", "style_tone_consistency"],
        "critical_regression_detected": false,
        "rationale": "Candidate demonstrated composite TrustScore improvement (+8.9 pts: 80.8 -> 89.7)."
      }
    ],
    "best_output_selected": "attempt_1",
    "initial_generation_latency_ms": 112,
    "peer_review_latency_ms": 84,
    "refinement_generation_latency_ms": 135,
    "evaluation_latency_ms": 11,
    "total_refinement_latency_ms": 219,
    "model_call_count": 3,
    "reviewer_call_count": 1
  }
}
```

---

## 3. Strict Consistency Guarantees
- The `reply`, `agent_used`, `trust_score`, `trust_breakdown`, and `evaluation` fields represent the identical winning artifact.
- When refinement reverts due to regression, all evaluation fields correspond to the baseline draft.
- For clarification paths, `recovery_triggered = False` and `refinement.refinement_status = "skipped"`.
