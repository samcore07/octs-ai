# Phase 2: Architectural Decision Records (ADRs)

This document formalizes the architectural decisions made during **Phase 2: Discipline Hierarchy & Agent Persona Layer** of **Octs AI**, capturing the context, evaluated alternatives, rationale, and consequences for each choice.

---

## Index of Decisions

- [ADR-006: Unified Pydantic v2 Schema for Specialist Personas](#adr-006-unified-pydantic-v2-schema-for-specialist-personas)
- [ADR-007: Central Singleton Registry Pattern for Disciplines and Personas](#adr-007-central-singleton-registry-pattern-for-disciplines-and-personas)
- [ADR-008: Multi-Stage Deterministic-First Routing with Fail-Safe Model Classification](#adr-008-multi-stage-deterministic-first-routing-with-fail-safe-model-classification)
- [ADR-009: Decoupled Prompt Templates via LangChain `ChatPromptTemplate`](#adr-009-decoupled-prompt-templates-via-langchain-chatprompttemplate)
- [ADR-010: Backward-Compatible Gateway Integration via `agent_used`](#adr-010-backward-compatible-gateway-integration-via-agent_used)

---

## ADR-006: Unified Pydantic v2 Schema for Specialist Personas

### Status
**Accepted**

### Context
Octs AI supports 16 specialized personas across 4 distinct disciplines. If each persona were implemented as an ad-hoc class or freeform dictionary, maintaining consistency in prompt formatting, evaluation criteria, model hyperparameters, and tool permissions would become unmanageable. We required a single, typed schema that enforces domain rigor while preventing code duplication.

### Decision
Define a unified `PersonaDefinition` schema in `backend/agents/base.py` using **Pydantic v2**. Every specialist persona must be an instantiated instance of this schema, containing explicit fields for ID, display name, discipline, description, responsibilities, task types, system instructions, domain constraints, output structure, evaluation criteria, and recommended hyperparameters (`ModelConfig`).

### Rationale
- **Schema Validation**: Pydantic v2 validates all 16 personas at import time, preventing runtime errors caused by missing attributes or typos.
- **Uniform Prompt Compilation**: The shared `.format_system_prompt()` method compiles markdown system instructions identically across all personas, ensuring structural consistency.
- **Zero Inheritance Bloat**: Avoids complex class hierarchies; personas are declarative data instances rather than subclass implementations.

### Consequences
- **Positive**: Strict type safety, auto-generated documentation, uniform serialization, and predictable behavior.
- **Negative**: Adding a new persona field requires updating all 16 persona instances.
- **Alternatives Considered**:
  - Independent Python classes per persona: Rejected due to severe code duplication and fragmented prompt generation.
  - Raw JSON/YAML persona files: Rejected because Python modules allow programmatic prompt compilation and tight IDE type-checking.

---

## ADR-007: Central Singleton Registry Pattern for Disciplines and Personas

### Status
**Accepted**

### Context
Components across the backend (routing engines, API endpoints, future LangGraph state graphs, and test suites) need to look up discipline configurations and specialist personas by their unique string identifiers. Scattered imports or hardcoded dictionaries would cause circular dependencies and fragmented state.

### Decision
Implement a central `AgentRegistry` singleton accessed via `get_registry()` in `backend/agents/registry.py`. The registry lazily registers all 4 disciplines and 16 personas upon initialization.

### Rationale
- **Single Source of Truth**: Guarantees that persona IDs are unique and reference identical instances throughout the application lifecycle.
- **Circular Dependency Elimination**: Deferred registration routines (`_initialize_registry()`) allow disciplines and personas to reference each other without triggering circular import errors.
- **Case & Whitespace Normalization**: The registry normalizes lookup strings (e.g., `'  Narrative_Architect  '` $\rightarrow$ `'narrative_architect'`), improving system resilience.

### Consequences
- **Positive**: Clean $O(1)$ lookups, clear dependency boundaries, and easy mocking in unit tests.
- **Negative**: Memory footprint for keeping 16 persona instances in memory (negligible in Python, < 2 MB).
- **Alternatives Considered**:
  - Global module-level dictionaries: Rejected due to circular import fragility and lack of encapsulation.
  - Dependency injection container: Rejected as an unnecessary operational abstraction for this scale.

---

## ADR-008: Multi-Stage Deterministic-First Routing with Fail-Safe Model Classification

### Status
**Accepted**

### Context
Directing user queries to the appropriate specialist persona is critical. Using an LLM call for every routing decision introduces high latency (500–1500 ms), consumes API quotas, incurs operational costs, and risks returning hallucinated persona names. However, simple keyword matching alone cannot handle ambiguous queries.

### Decision
Implement a **4-stage hybrid routing pipeline** in `backend/agents/routing/classifier.py`:
1. **Explicit Task Mapping**: High-confidence direct mapping ($C=0.95$) if `task_type` is supplied.
2. **Deterministic Pattern Scoring**: Regex heuristics across curated craft patterns ($C=0.65-0.92$).
3. **Model-Assisted Classification**: Structured classification prompt used only when heuristics score 0 and a model is provided, with strict validation against registered persona IDs.
4. **Discipline Default Fallback**: Deterministic fallback to the discipline's lead persona ($C=0.50$) if all previous stages fail or if external models raise exceptions.

### Rationale
- **Sub-Millisecond Execution**: Over 95% of typical domain tasks route in $< 1\text{ ms}$ without making external network calls.
- **Zero Hallucination Guarantee**: An unvetted or hallucinated persona ID can never escape the router; model outputs are strictly validated against registered personas.
- **Fault-Tolerant**: Network outages, rate limits, or API errors during Stage 3 fail over silently to Stage 4 without raising 500 errors to the user.

### Consequences
- **Positive**: Extremely fast, zero API costs during routing tests, highly reliable, and predictable.
- **Negative**: Heuristic regexes must be maintained as creative vocabulary expands.
- **Alternatives Considered**:
  - Pure LLM-based classification: Rejected due to latency, costs, and hallucination risks.
  - Embedding vector cosine similarity: Rejected because regex heuristics offer zero cold-start latency and require no local vector store dependencies.

---

## ADR-009: Decoupled Prompt Templates via LangChain `ChatPromptTemplate`

### Status
**Accepted**

### Context
Prompts must be structured to support both the current single-model execution in Phase 2 and the future LangGraph multi-agent execution nodes in Phase 3. Hardcoding strings directly into model invocation calls would hinder future workflow integration.

### Decision
Use LangChain's official `ChatPromptTemplate` abstraction in `PersonaDefinition.build_prompt_template()`. The system message compiles the persona's instructions, craft constraints, output architecture, and evaluation criteria, while the human message accepts `{input}`.

### Rationale
- **Standardized Messaging**: Generates typed `[SystemMessage, HumanMessage]` objects ready for any LangChain-compatible chat model.
- **Preparation for Phase 3**: In LangGraph, state graph nodes can directly bind to `persona.build_prompt_template() | model`.
- **Decoupled Craft Rules**: Allows prompt engineering updates without touching routing, server, or execution code.

### Consequences
- **Positive**: Forward-compatible with LangGraph, reusable across models, and cleanly testable.
- **Negative**: Requires `langchain_core` as a core dependency (already present in the repository).
- **Alternatives Considered**:
  - Raw string concatenation (f-strings): Rejected due to lack of role separation (system vs human) and inability to integrate cleanly with LangGraph pipelines.

---

## ADR-010: Backward-Compatible Gateway Integration via `agent_used`

### Status
**Accepted**

### Context
In Phase 1, `POST /ask` returned `PromptResponse` with `agent_used="direct_model"`. The existing frontend UI relies on the `{ "reply": "..." }` response contract. In Phase 2, we must introduce the routed specialist persona without breaking existing clients or prematurely migrating to LangGraph.

### Decision
Instantiate `AgentRouter` in `server.py`. In `ask_gemini()`, route incoming requests based on `request.role` and `request.prompt`, then assign `agent_used=routing.persona_id` in the `PromptResponse`. Keep the underlying `model.invoke(request.prompt)` execution intact until Phase 3.

### Rationale
- **Zero Breaking Changes**: The frontend continues to receive the exact JSON structure it expects.
- **Immediate Telemetry & Visibility**: Server logs and API responses now reflect the active specialist persona (`narrative_architect`, `lyricist_meter_engine`, etc.).
- **Incremental Architecture**: Follows clean evolutionary architecture principles by verifying routing in production before swapping execution engines in Phase 3.

### Consequences
- **Positive**: Zero frontend regressions, complete observability into routing decisions, seamless progression.
- **Negative**: The model does not yet execute the persona's specialized system prompt in live inference (planned for Phase 3).
- **Alternatives Considered**:
  - Immediately replacing `model.invoke()` with a complex multi-agent loop: Rejected because Phase 2's explicit scope is the agent persona and routing layer.
