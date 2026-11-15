# OCTS AI — Phase 5: Architecture Decisions & Trade-Offs

## ADR-01: Single Shared StateGraph vs Multiple Persona Subgraphs
- **Context:** OCTS AI supports 16 specialized personas across 4 disciplines. Refinement and peer review require coordination between different personas.
- **Decision:** Maintain a single shared LangGraph `StateGraph`. The author and reviewer personas are injected dynamically via persona definitions and state parameters.
- **Rationale:** Creating 16 independent StateGraphs would multiply compilation overhead, fragment telemetry, and complicate conditional routing. A single shared graph with explicit dependency injection maintains architectural simplicity and zero code duplication.

---

## ADR-02: Deterministic Best-Output Selection vs Blind Recency Acceptance
- **Context:** LLMs executing self-correction can degrade output quality, introduce new errors, or hallucinate.
- **Decision:** Every refined candidate is re-evaluated using the Phase 4 `EvaluationEngine`. The `ImprovementAnalyzer` compares criteria deltas; if the candidate regresses, the system reverts to the previous best output and flags `regressed_reverted`.
- **Rationale:** A creative harness must protect output quality. Blindly accepting the latest generation violates reliability guarantees.

---

## ADR-03: Triple-Layer Recursion Bounding & Dynamic Recursion Limit
- **Context:** Autonomous refinement loops can enter infinite cycles if criteria repeatedly fail to meet thresholds.
- **Decision:** Implement strict bounding at 3 layers:
  1. `RecoveryManager.max_attempts` validated between 0 and 5 (`MAX_SAFETY_CAP = 5`).
  2. `RefinementController` checks `attempts < max_attempts` prior to granting `should_refine = True`.
  3. Dynamic LangGraph recursion limit: $\text{safe\_recursion\_limit} = \max(\text{max\_recursion\_limit},\ 15 + 8 \times \text{max\_attempts})$.
- **Rationale:** Ensures guaranteed graph termination in all failure scenarios without manual cancellation, while dynamically allocating sufficient graph steps for multi-attempt loops.

---

## ADR-04: XML Delimiter Isolation & Adversarial Prompt-Injection Defense
- **Context:** The peer reviewer receives candidate text that may contain untrusted user inputs or ambiguous content that could prompt-inject the reviewer.
- **Decision:** Escape embedded candidate tags, wrap candidate text within `<untrusted_candidate_output>` delimiters, and provide hardened system instructions forbidding instruction execution.
- **Rationale:** Standard defense-in-depth practice preventing adversarial hijacking of peer review nodes.

---

## ADR-05: Backward Compatible Schema Extension
- **Context:** Frontends and existing integrations depend on the `PromptResponse` structure.
- **Decision:** Add optional `refinement: Optional[Dict[str, Any]] = None` and preserve `reply`, `role`, `agent_used`, `trust_score`, and `latency_ms`.
- **Rationale:** Zero downtime, zero breaking changes, and full backward compatibility across all existing clients.

---

## ADR-06: Multi-Dimensional Selection Policy vs Simple Delta Quality
- **Context:** A refined candidate could gain $+2.0$ points in stylistic nuance while failing a critical execution integrity check or dropping instruction adherence.
- **Decision:** Implement a multi-dimensional selection policy prioritizing critical execution checks, instruction adherence stability ($> 15.0$ pt drop guard), evaluation coverage, and composite TrustScore over raw quality score.
- **Rationale:** True creative harness reliability requires protecting both stylistic craft and structural/systemic execution integrity.

---

## ADR-07: Reviewer Fallback Transparency vs Silent Degradation
- **Context:** When a peer review model times out or encounters a provider exception, naive architectures mask the failure as a successful review.
- **Decision:** Explicitly capture and return `review_method="heuristic"`, `fallback_triggered=True`, and `fallback_reason` in `PeerReviewResult`.
- **Rationale:** Transparency allows operators and clients to distinguish between genuine specialist critiques and heuristic safety nets.
