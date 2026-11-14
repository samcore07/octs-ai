# Phase 3 Execution Engine: Unified Multi-Agent Runtime

This document explains the runtime execution engine of **Octs AI**, detailing how 16 distinct specialist personas share a single, unified execution harness without code duplication, and how prompt synthesis, model invocation, output verification, and error recovery operate at runtime.

---

## Table of Contents

- [The Single Shared Execution Engine Paradigm](#the-single-shared-execution-engine-paradigm)
- [AgentRegistry Discovery & Integration](#agentregistry-discovery--integration)
- [AgentRouter Dynamic Classification](#agentrouter-dynamic-classification)
- [Persona Prompt Preparation Subsystem](#persona-prompt-preparation-subsystem)
- [Gemini Model Invocation & Configuration](#gemini-model-invocation--configuration)
- [Output Validation & Verification Gate](#output-validation--verification-gate)
- [Telemetry & Execution Metadata](#telemetry--execution-metadata)
- [Error Handling & Failure Recovery](#error-handling--failure-recovery)

---

## The Single Shared Execution Engine Paradigm

A naive multi-agent architecture compiles separate execution graphs for every persona (e.g., 16 independent workflows for 16 specialists). In Octs AI, this anti-pattern is deliberately rejected.

### The Unified Engine
All 16 personas execute through **one single LangGraph StateGraph** managed by the [`OrchestrationExecutor`](file:///Users/samriddha/Documents/Octs/backend/orchestration/executor.py).

```
                            Single Orchestration Pipeline
     Input
       │
       ▼
 ┌───────────────┐      Dynamic Lookup     ┌────────────────────────┐
 │ route_request │ ──────────────────────> │ AgentRouter            │
 └───────┬───────┘                         └────────────────────────┘
         │ (Selected: Persona ID)
         ▼
 ┌─────────────────┐    Dynamic Compile    ┌────────────────────────┐
 │ prepare_persona │ ────────────────────> │ AgentRegistry (1 of 16)│
 └───────┬─────────┘                       └────────────────────────┘
         │ (Compiled Messages)
         ▼
 ┌───────────────┐      Injected Invocation┌────────────────────────┐
 │ execute_model │ ──────────────────────> │ Injected Gemini Model  │
 └───────┬───────┘                         └────────────────────────┘
         │ (AIMessage)
         ▼
 ┌─────────────────┐    Verification
 │ validate_output │
 └───────┬─────────┘
         │
         ▼
       Output
```

### Architectural Advantages
1. **Zero Graph Proliferation**: Maintenance overhead is $O(1)$ instead of $O(N)$. Adding a 17th persona requires only adding a configuration file in `backend/agents/personas/`; zero changes are needed in the graph or executor.
2. **Unified Observability**: Every execution follows identical lifecycle hooks, telemetry aggregation, and error handling paths.
3. **Optimized Resource Consumption**: A single compiled graph is cached and reused across requests.

---

## AgentRegistry Discovery & Integration

The [`AgentRegistry`](file:///Users/samriddha/Documents/Octs/backend/agents/registry.py) acts as the single source of truth for all persona definitions:

- **Lazy Auto-Discovery**: Automatically discovers and registers all 16 persona modules on first access.
- **Lookup Operations**:
  - `registry.get_persona(persona_id) -> Optional[PersonaDefinition]`
  - `registry.get_discipline(discipline_id) -> Optional[DisciplineConfig]`
  - `registry.get_personas_by_discipline(discipline_id) -> List[PersonaDefinition]`
- **Runtime Integration**: In `prepare_persona_node`, the registry is queried:
  ```python
  persona = registry.get_persona(selected_persona_id)
  if not persona:
      return {
          "execution_status": "persona_preparation_failed",
          "execution_error": f"Persona '{selected_persona_id}' not found in registry."
      }
  ```

---

## AgentRouter Dynamic Classification

The [`AgentRouter`](file:///Users/samriddha/Documents/Octs/backend/agents/routing/classifier.py) evaluates user intent and maps it to the most qualified specialist.

### 4-Case Decision Logic

```python
result = router.route(prompt=prompt, discipline_id=discipline_id)
```

1. **Case A (Discipline and Specialist Clear)**:
   - High confidence ($\ge 0.70$).
   - Returns exact specialist persona (e.g. `"lyricist_meter_engine"`).
   - Execution proceeds directly to `prepare_persona -> execute_model`.
2. **Case B (Discipline Known, Specialist Vague)**:
   - User provided `role="musicians"`, but prompt is generic (*"I'm stuck on my song"*).
   - Router detects ambiguity within discipline and falls back to discipline lead (e.g. `track_structure_architect`) with confidence $0.50$.
   - Execution proceeds to model execution.
3. **Case C (Discipline Ambiguous, No Role Given)**:
   - Prompt contains mixed or zero domain craft signals (*"Help me create something impactful"*).
   - Returns `needs_clarification = True` and sets `clarification_question`.
   - Pipeline short-circuits directly to `finalize_execution`. **Zero LLM tokens are consumed**.
4. **Case D (Invalid Input / Unknown String)**:
   - Sanitizes input, logs warning, and executes safe controlled fallback.

---

## Persona Prompt Preparation Subsystem

In [`backend/orchestration/nodes.py:prepare_persona_node`](file:///Users/samriddha/Documents/Octs/backend/orchestration/nodes.py), the raw prompt is transformed into a rich domain prompt:

1. **System Prompt Construction**:
   - Persona Identity & Mission.
   - Core Responsibilities.
   - Craft-Specific Technical Constraints (e.g. WCAG 2.2 AA contrast ratios for designers; syllabic meter stress contours for lyricists).
   - Anti-Patterns & Banned Generic Platitudes.
   - Required Output Architecture (e.g. 5 mandatory numbered sections).
2. **Message Assembly**:
   ```python
   messages = [
       SystemMessage(content=persona.prompt_template.format_system_prompt()),
       HumanMessage(content=state["original_prompt"])
   ]
   ```
3. **Output**: Stored in `state["formatted_messages"]`.

---

## Gemini Model Invocation & Configuration

The model execution node ([`backend/orchestration/nodes.py:execute_model_node`](file:///Users/samriddha/Documents/Octs/backend/orchestration/nodes.py)) executes the compiled prompt:

### Explicit Model Dependency
The model instance is passed as an explicit argument:
```python
def execute_model_node(state: OrchestrationState, model: Optional[Any] = None) -> Dict[str, Any]:
    active_model = model or getattr(state, "model", None)
    if not active_model:
        raise RuntimeError("AI model dependency was not provided to execute_model_node.")
    
    response = active_model.invoke(state["formatted_messages"])
    raw_content = response.content if hasattr(response, "content") else str(response)
    
    return {
        "raw_response": raw_content,
        "generated_output": raw_content,
        "execution_status": "model_executed"
    }
```

### Provider Configuration
- **Model**: `gemini-3.5-flash-lite` (via `langchain-google-genai`).
- **Temperature / Sampling**: Gemini 3.5 Flash Lite utilizes fixed sampling defaults. The system logs a graceful warning and ignores client-side overrides to avoid API errors.

---

## Output Validation & Verification Gate

The [`validate_output_node`](file:///Users/samriddha/Documents/Octs/backend/orchestration/nodes.py) functions as a quality gate before output is finalized:

1. **Completeness Verification**: Confirms `raw_response` is non-empty and contains substantive text ($> 10$ characters).
2. **Whitespace Check**: Rejects responses containing only whitespace.
3. **Safe Fallback**: If an empty response is received from the LLM provider, an intelligent domain recovery message is constructed rather than returning a blank screen.

---

## Telemetry & Execution Metadata

Every execution records comprehensive telemetry in `OrchestrationState` and maps it to `PromptResponse`:

- `latency_ms`: Execution latency in milliseconds measured with high-precision monotonic clock (`time.perf_counter`).
- `selected_persona_id`: Machine identifier of the specialist persona (e.g. `hook_retention_architect`).
- `role`: Creative discipline utilized (`writers`, `musicians`, `creators`, `designers`).
- `routing_confidence`: Heuristic routing confidence score ($0.0$ to $1.0$).
- `execution_status`: Lifecycle status (`completed`, `completed_clarification_required`, `validation_failed`, `failed`).
- `model_used`: Name of the generative AI model that produced the output.

---

## Error Handling & Failure Recovery

The execution engine implements layered error handling:

| Error Category | Handling Mechanism | User Impact |
| :--- | :--- | :--- |
| **Input Validation Failure** | Short-circuit via `validate_input -> finalize_execution` | Returns HTTP 422 or friendly validation explanation in `reply`. |
| **Discipline Ambiguity (Case C)** | Short-circuit via `route_request -> finalize_execution` | Returns HTTP 200 with clear clarification question in `reply`. Zero LLM tokens wasted. |
| **Model API Quota / Rate Limit** | Catches `Exception` in `execute_model_node`, sets `execution_status = "model_failed"` | Returns HTTP 500 with descriptive error detail in JSON. |
| **Empty Model Output** | Handled in `validate_output_node` with domain recovery template | User receives a polite retry directive instead of empty output. |
| **Graph Recursion Exceeded** | Bounded by `recursion_limit: 25` | Execution terminates safely without server memory starvation. |
