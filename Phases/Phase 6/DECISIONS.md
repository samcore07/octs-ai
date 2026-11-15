# OCTS AI — Phase 6: Architecture Decision Records (ADRs)

## ADR 001: SQLite with SQLAlchemy over External Vector Database

### Status: Accepted
### Context:
Phase 6 requires persistent memory across sessions. A common proposal in modern LLM systems is to immediately deploy a vector database (e.g. Chroma, Qdrant, Pinecone, pgvector) with dense embeddings.

### Decision:
We implemented structured metadata retrieval using SQLite and SQLAlchemy ORM, combined with explicit multi-factor ranking (project match, discipline match, token overlap, importance, and exponential recency decay).

### Rationale:
1. **Determinism & Explainability**: Vector similarity often matches surface phrasing rather than structural constraints or project lore. Explicit multi-factor scoring provides complete visibility into why a memory was chosen.
2. **Zero Deployment Overhead**: SQLite requires zero background daemons, zero external API keys, and runs in-memory or single-file in all environments.
3. **Cross-Project Scope Safety**: Metadata-based scope filtering guarantees that cross-project leakage cannot occur, whereas vector search without hard filtering frequently leaks embeddings across boundaries.
4. **Extensibility**: The SQLAlchemy models and repository interface allow adding vector embeddings later as an optional ranking factor without altering the core pipeline.

---

## ADR 002: Passive Background Context Injection vs Active Prompt Mutation

### Status: Accepted
### Context:
Retrieved memories must be provided to specialist personas. Mutating the raw task prompt (`state["original_prompt"]`) causes downstream issues for prompt evaluation, metric scoring, and user history.

### Decision:
We preserve `state["original_prompt"]` completely unchanged throughout the graph lifecycle. Memory context is formatted as an isolated `<retrieved_memory_context>` block and prepended strictly to the model prompt messages inside `prepare_persona_node`.

### Rationale:
1. **Preserves Evaluation Integrity**: Phase 4 evaluation rubrics assess instruction adherence against what the user actually typed, not against injected system context.
2. **Zero Contamination**: The model clearly distinguishes between passive background guidelines and active instructions.
3. **Audit Clarity**: Telemetry in `PromptResponse.memory` records exactly which memories were injected without altering user request records.

---

## ADR 003: Extraction Exclusivity to Winning Artifacts

### Status: Accepted
### Context:
Phase 5 introduced autonomous self-correction and refinement loops. During an interaction turn, multiple draft candidates may be produced (initial draft, peer review critique, refined candidate, or fallback revert).

### Decision:
Memory extraction runs exclusively after `finalize_execution_node`, which selects the verified `best_output`. Extraction never reads intermediate or rejected candidates.

### Rationale:
1. **Quality Guarantee**: Only craft elements that passed Phase 4 evaluation and Phase 5 refinement criteria can become permanent memories.
2. **Reversion Safety**: If a refined candidate regressed and was rejected, memory is extracted from the winning baseline, never the broken revision.
3. **Clarification Protection**: Clarification flows produce no winning creative output and therefore generate zero permanent memories.

---

## ADR 004: Non-Destructive Versioning over In-Place Mutation

### Status: Accepted
### Context:
When a user updates a preference or establishes a contradictory constraint, the system must handle the conflict.

### Decision:
Rather than overwriting or hard-deleting the previous memory, the existing record is transitioned to `status="superseded"` with a pointer (`superseded_by`) to the new memory ID. The new record increments `version = old_version + 1`.

### Rationale:
1. **Auditability**: Preserves creative evolution history across projects.
2. **Rollback Potential**: Archived or superseded memories can be inspected or restored if a user reverts a creative choice.
3. **Precedence Protection**: Prevents lower-precedence AI inferences from silently destroying explicit user directives.
