# Phase 3 Architectural Decision Records (ADRs)

This document formalizes the key architectural and design decisions established during **Phase 3** of **Octs AI**, recording context, evaluated options, chosen strategies, and operational consequences.

---

## Index of Decisions

- [ADR-001: Single Shared StateGraph vs. Per-Agent Workflows](#adr-001-single-shared-stategraph-vs-per-agent-workflows)
- [ADR-002: Typed Graph State via TypedDict](#adr-002-typed-graph-state-via-typeddict)
- [ADR-003: Model Dependency Injection vs. Global Module Lookups](#adr-003-model-dependency-injection-vs-global-module-lookups)
- [ADR-004: Intelligent 4-Case Routing with Non-LLM Clarification Short-Circuit](#adr-004-intelligent-4-case-routing-with-non-llm-clarification-short-circuit)
- [ADR-005: Bounded Stateless Pipeline with Checkpointer-Ready State](#adr-005-bounded-stateless-pipeline-with-checkpointer-ready-state)
- [ADR-006: Separation of Routing Logic from Graph Execution](#adr-006-separation-of-routing-logic-from-graph-execution)
- [ADR-007: Centralized Dual-Theme CSS Variables with Anti-FOUC Guard](#adr-007-centralized-dual-theme-css-variables-with-anti-fouc-guard)

---

## ADR-001: Single Shared StateGraph vs. Per-Agent Workflows

### Context
Octs AI supports 16 specialized personas across 4 disciplines. We evaluated whether to compile 16 independent LangGraph workflows or one shared orchestration graph parameterized at runtime.

### Evaluated Options
1. **Option A: 16 Independent Workflows**: A discrete `StateGraph` for every specialist (e.g. `NarrativeArchitectGraph`, `LyricistGraph`).
2. **Option B: 4 Discipline Graphs**: One graph per discipline with 4 sub-branches.
3. **Option C: Single Shared Parameterized StateGraph**: One single graph pipeline that dynamically loads persona definitions from `AgentRegistry`.

### Decision
**Option C (Single Shared StateGraph)** was selected.

### Rationale
- All personas share identical workflow stages: input validation, specialist routing, prompt synthesis, model invocation, output verification, and finalization.
- Graph compilation overhead is $O(1)$ instead of $O(N)$.
- Adding new personas requires zero modification to graph topology or orchestration code.

### Consequences
- **Positive**: Extremely maintainable, predictable memory footprint, uniform observability across all 16 agents.
- **Negative**: Graph nodes must remain generic enough to handle all domain prompt variations.

---

## ADR-002: Typed Graph State via TypedDict

### Context
LangGraph requires a state definition schema. Options include Python dictionaries, `typing.TypedDict`, or Pydantic `BaseModel`.

### Decision
Use **Python `TypedDict` (`OrchestrationState`)** with `total=False`.

### Rationale
- LangGraph natively supports `TypedDict` for fast, lightweight state merging without validation overhead on every node transition.
- Pydantic models introduce serialization and parsing overhead inside graph loops.
- `total=False` allows nodes to return partial state dictionaries containing only the keys they update.

### Consequences
- **Positive**: High execution speed, strong IDE autocompletion, type safety.
- **Negative**: Validation of internal state transitions is manual rather than automatically coerced by Pydantic.

---

## ADR-003: Model Dependency Injection vs. Global Module Lookups

### Context
The initial Phase 3 implementation resolved the model dynamically in `nodes.py` via `getattr(server, "model", None)`. This coupled orchestration to the web framework.

### Evaluated Options
1. **Option A: Dynamic Global Lookup**: Keep `getattr(server, "model", None)`.
2. **Option B: Thread-Local / ContextVar**: Store model in a global context variable.
3. **Option C: Explicit Top-Down Dependency Injection**: Pass model instance into `OrchestrationExecutor` constructor and bind it to node closures.

### Decision
**Option C (Explicit Dependency Injection)** was selected.

### Rationale
- Eliminates circular dependencies and decouples `backend/orchestration/` completely from `server.py`.
- Enables unit tests to pass mock models directly without patching global server attributes.
- Allows running multiple executor instances simultaneously with different models (e.g., A/B testing).

### Consequences
- **Positive**: Clean architectural boundaries, hermetic unit tests, zero global state.
- **Negative**: Requires passing dependencies through graph builder functions.

---

## ADR-004: Intelligent 4-Case Routing with Non-LLM Clarification Short-Circuit

### Context
When user intent was ambiguous, the previous system arbitrarily defaulted to `writers` and `narrative_architect`, erroneously invoking the Gemini API and consuming tokens for non-actionable queries.

### Decision
Implement a **4-Case Routing Decision Tree** in `AgentRouter`:
- **Case A**: High confidence -> route to specialist, call model.
- **Case B**: Known discipline, vague specialist query -> route to discipline primary lead, call model.
- **Case C**: Ambiguous discipline without explicit role -> set `needs_clarification = True`, short-circuit directly to `finalize_execution -> END`.
- **Case D**: Invalid input -> controlled fallback.

### Rationale
- Protects Gemini token quota and reduces latency for non-actionable prompts from ~3000ms to **7ms**.
- Asks the user an intelligent, concise clarification question rather than guessing their profession incorrectly.

### Consequences
- **Positive**: Zero LLM cost for ambiguous queries, instant response, better UX.
- **Negative**: Requires careful heuristic keyword tuning to prevent false clarification triggers.

---

## ADR-005: Bounded Stateless Pipeline with Checkpointer-Ready State

### Context
Phase 3 requires establishing execution boundaries without introducing unnecessary database dependencies prematurely before Phase 4.

### Decision
Operate the graph **statelessly per request** while enforcing a strict **recursion limit (25)**, while designing `OrchestrationState` with `session_id` and `request_id` attributes ready for Phase 4 persistent checkpointing (`SqliteSaver` / `PostgresSaver`).

### Rationale
- Keeps Phase 3 dependencies lightweight and focused on orchestration mechanics.
- Bounded recursion guarantees execution will never enter runaway infinite loops.

### Consequences
- **Positive**: Zero database setup required for Phase 3; graph is resilient against memory exhaustion.
- **Negative**: Multi-turn conversational memory is deferred to Phase 4.

---

## ADR-006: Separation of Routing Logic from Graph Execution

### Context
Should routing heuristics be implemented inside graph nodes or delegated to an external component?

### Decision
Keep routing classification inside [`AgentRouter`](file:///Users/samriddha/Documents/Octs/backend/agents/routing/classifier.py) and have `route_request_node` invoke the router as a specialized dependency.

### Rationale
- Single Responsibility Principle: Graph nodes orchestrate workflow; classification modules own domain heuristics.
- Allows independent unit testing of routing rules without invoking graph machinery.

---

## ADR-007: Centralized Dual-Theme CSS Variables with Anti-FOUC Guard

### Context
Implementing Dark Mode required choosing between scattered per-component CSS class overrides or a centralized CSS custom property (variable) system.

### Decision
Implement a **centralized CSS custom property system**:
- `:root` defines Swiss Tech Light Mode (default).
- `[data-theme="dark"]` overrides colors with deep charcoal panels (`#0F1117`, `#161922`, `#262B37`).
- Anti-FOUC inline script placed in `<head>` before stylesheets render.
- State persisted in `localStorage` under `octs_ai_theme`.

### Rationale
- Completely eliminates visual theme flashing during page load.
- Single source of truth for color tokens across all pages.
- Zero external CSS libraries or frameworks required.

### Consequences
- **Positive**: Accessible contrast (WCAG AA), instant theme switching, consistent across all 8 HTML files.
- **Negative**: All legacy styles had to be audited to ensure no hardcoded hex values bypass variables.
