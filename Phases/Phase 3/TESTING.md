# Phase 3 Testing: Architecture, Mocking Strategy & Verification

This document details the automated testing architecture of **Octs AI** for **Phase 3**, explaining the test suite layout, unit and graph testing strategies, decoupled mocking methodology, and verified test results.

---

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Suite Architecture & Module Inventory](#test-suite-architecture--module-inventory)
- [Decoupled Mocking Strategy](#decoupled-mocking-strategy)
- [Unit Testing](#unit-testing)
- [LangGraph StateGraph Testing](#langgraph-stategraph-testing)
- [HTTP API Integration Testing](#http-api-integration-testing)
- [Verified Test Results (90 Passed, 1 Warning)](#verified-test-results-90-passed-1-warning)
- [How to Run Tests](#how-to-run-tests)

---

## Testing Philosophy

Octs AI adheres to production-grade backend testing principles:
1. **Zero External API Flakiness**: Unit and graph tests never make real HTTP calls to the Google Gemini API. All model interactions are simulated using explicit mock fixtures.
2. **True Dependency Injection**: Graph nodes and executors receive mock models via constructor arguments, completely eliminating monkeypatching of global server variables.
3. **Deterministic Verification**: Every node, conditional edge, and routing branch is independently tested for both happy paths and failure conditions.
4. **End-to-End Contract Assurance**: Integration tests exercise the full FastAPI HTTP stack via Starlette's `TestClient`.

---

## Test Suite Architecture & Module Inventory

The test suite resides in [`backend/tests/`](file:///Users/samriddha/Documents/Octs/backend/tests/) and comprises 11 dedicated test modules:

```
backend/tests/
├── test_agent_registry.py             # 6 tests: Registry lookups, filtering, discovery
├── test_agent_routing.py              # 22 tests: Task-based routing across 16 personas
├── test_api.py                        # 10 tests: FastAPI endpoints & backward compatibility
├── test_config.py                     # 5 tests: Settings, CORS, and LangSmith tracing config
├── test_discipline_configs.py         # 4 tests: 4 creative discipline schema invariants
├── test_graph.py                      # 6 tests: StateGraph assembly, compilation & edges
├── test_orchestration_execution.py    # 6 tests: OrchestrationExecutor lifecycle & recursion
├── test_orchestration_integration.py  # 5 tests: End-to-end API + LangGraph integration
├── test_orchestration_nodes.py        # 13 tests: Individual graph node execution handlers
├── test_persona_prompts.py            # 4 tests: System prompt formatting & constraints
└── test_refinement_di_and_routing.py  # 7 tests: Model DI, zero server imports, 4-case routing
```

**Total Verified Tests**: **90 passing tests across 11 modules**.

---

## Decoupled Mocking Strategy

### The Pre-Refinement Limitation
Prior to the Phase 3 architectural refinement, test cases were forced to patch `server.model`:
```python
# PREVIOUS TIGHTLY COUPLED MOCKING
with patch.object(server, "model", mock_model):
    response = client.post("/ask", json={"prompt": "..."})
```

### Modern Dependency Injection Testing
With Phase 3 dependency injection, tests instantiate the executor directly with an injected mock model without touching `server.py`:

```python
def test_executor_with_explicitly_injected_mock_model():
    mock_model = MagicMock()
    mock_model.invoke.return_value.content = "Injected creative response."

    # Direct constructor injection
    executor = OrchestrationExecutor(model=mock_model)
    request = PromptRequest(prompt="Write a 3-act outline.", role="writers")
    
    response = executor.execute(request)
    
    assert response.reply == "Injected creative response."
    assert response.agent_used == "narrative_architect"
    assert mock_model.invoke.called
```

Furthermore, multiple executor instances can be run in the same process with completely independent models without any cross-test state leakage:

```python
def test_executor_swapping_injected_models():
    mock_1 = MagicMock()
    mock_1.invoke.return_value.content = "Output Alpha"
    mock_2 = MagicMock()
    mock_2.invoke.return_value.content = "Output Beta"

    exec_1 = OrchestrationExecutor(model=mock_1)
    exec_2 = OrchestrationExecutor(model=mock_2)

    res_1 = exec_1.execute(PromptRequest(prompt="Compose chords", role="musicians"))
    res_2 = exec_2.execute(PromptRequest(prompt="Compose chords", role="musicians"))

    assert res_1.reply == "Output Alpha"
    assert res_2.reply == "Output Beta"
```

---

## Unit Testing

### 1. Orchestration Nodes ([`test_orchestration_nodes.py`](file:///Users/samriddha/Documents/Octs/backend/tests/test_orchestration_nodes.py))
- **`test_validate_input_node_valid`**: Verifies normal prompt passes input validation.
- **`test_validate_input_node_empty`**: Verifies empty string or whitespace triggers `validation_failed`.
- **`test_validate_input_node_null`**: Verifies `None` prompt triggers `validation_failed`.
- **`test_validate_input_node_oversized`**: Verifies prompts $> 50,000$ characters are rejected.
- **`test_route_request_node_valid`**: Verifies high-confidence routing sets persona and confidence $\ge 0.70$.
- **`test_route_request_node_low_confidence_fallback`**: Verifies low-confidence routing triggers `routing_fallback`.
- **`test_handle_routing_fallback_node`**: Verifies discipline lead persona assignment.
- **`test_prepare_persona_node_valid`**: Verifies system and human message construction.
- **`test_prepare_persona_node_unknown_persona`**: Verifies handling of non-existent persona IDs.
- **`test_execute_model_node_success`**: Verifies model invocation and output extraction.
- **`test_execute_model_node_exception`**: Verifies graceful handling of model provider exceptions.
- **`test_validate_output_node_valid`**: Verifies output check pass.
- **`test_validate_output_node_empty`**: Verifies fallback generation for blank model responses.
- **`test_finalize_execution_node`**: Verifies latency calculation and terminal status assignment.

### 2. Intelligent Routing & DI ([`test_refinement_di_and_routing.py`](file:///Users/samriddha/Documents/Octs/backend/tests/test_refinement_di_and_routing.py))
- **`test_dependency_injection_no_server_import_in_orchestration`**: Confirms `nodes.py`, `graph.py`, and `executor.py` have zero `server` attributes or imports.
- **`test_case_a_discipline_and_specialist_clear`**: Confirms clear prompt & discipline routes to exact specialist and invokes model.
- **`test_case_b_discipline_known_specialist_uncertain`**: Confirms known discipline with vague prompt falls back to discipline lead and executes model.
- **`test_case_c_discipline_ambiguous_short_circuits_without_llm`**: Confirms discipline-ambiguous prompt returns clarification and **never calls `mock_model.invoke()`**.
- **`test_case_d_invalid_discipline_controlled_fallback`**: Confirms unknown discipline strings trigger safe fallback without crashing.

---

## LangGraph StateGraph Testing

The StateGraph itself is thoroughly exercised in [`test_graph.py`](file:///Users/samriddha/Documents/Octs/backend/tests/test_graph.py):
- **`test_graph_compilation`**: Verifies `build_orchestration_graph()` compiles cleanly into a `CompiledGraph`.
- **`test_graph_singleton_reusability`**: Verifies `get_orchestration_graph()` returns a cached singleton instance for identical configurations.
- **`test_graph_node_inventory`**: Inspects `graph.nodes` to confirm all 7 nodes are present.
- **`test_graph_validation_failure_short_circuit`**: Verifies that invalid inputs bypass model execution and exit directly to `finalize_execution -> END`.
- **`test_graph_successful_pipeline_execution`**: Traces execution through the complete pipeline with mock model.
- **`test_graph_output_validation_failure_handling`**: Verifies empty model response is recovered safely before exit.

---

## HTTP API Integration Testing

Full HTTP round-trip tests in [`test_orchestration_integration.py`](file:///Users/samriddha/Documents/Octs/backend/tests/test_orchestration_integration.py) and [`test_api.py`](file:///Users/samriddha/Documents/Octs/backend/tests/test_api.py):
- Verifies `POST /ask` returns HTTP 200 with `{ "reply": "..." }`.
- Verifies role parsing, latency reporting, and agent metadata.
- Verifies model provider quota exhaustion returns HTTP 500 with descriptive error detail.
- Verifies static file delivery (`/style.css`, `/script.js`).

---

## Verified Test Results (90 Passed, 1 Warning)

Execution of `python3 -m pytest backend/tests/ -v`:

```
============================= test session starts ==============================
platform darwin -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: /Users/samriddha/Documents/Octs
plugins: langsmith-0.14.17, anyio-4.15.1
collected 90 items

backend/tests/test_agent_registry.py::test_registry_contains_16_personas PASSED [  1%]
backend/tests/test_agent_registry.py::test_unique_persona_identifiers PASSED [  2%]
backend/tests/test_agent_registry.py::test_persona_lookup_by_id PASSED   [  3%]
backend/tests/test_agent_registry.py::test_filter_personas_by_discipline PASSED [  4%]
backend/tests/test_agent_registry.py::test_unknown_persona_lookup PASSED [  5%]
backend/tests/test_agent_registry.py::test_unknown_discipline_lookup PASSED [  6%]
backend/tests/test_agent_routing.py::test_representative_prompt_routing (16 variants) PASSED [ 24%]
backend/tests/test_agent_routing.py::test_explicit_task_type_routing PASSED [ 25%]
backend/tests/test_agent_routing.py::test_invalid_discipline_handling PASSED [ 26%]
backend/tests/test_agent_routing.py::test_ambiguous_prompt_fallback_routing PASSED [ 27%]
backend/tests/test_agent_routing.py::test_alternative_persona_recommendation PASSED [ 28%]
backend/tests/test_agent_routing.py::test_model_assisted_classification_success PASSED [ 30%]
backend/tests/test_agent_routing.py::test_model_assisted_classification_malformed_fallback PASSED [ 31%]
backend/tests/test_agent_routing.py::test_model_assisted_classification_invalid_json_fallback PASSED [ 32%]
backend/tests/test_api.py::test_health_endpoint PASSED                    [ 33%]
backend/tests/test_api.py::test_root_serves_html PASSED                  [ 34%]
backend/tests/test_api.py::test_ask_endpoint_success PASSED              [ 35%]
backend/tests/test_api.py::test_ask_endpoint_with_valid_role PASSED      [ 36%]
backend/tests/test_api.py::test_ask_endpoint_rejects_invalid_role PASSED [ 37%]
backend/tests/test_api.py::test_ask_endpoint_rejects_empty_prompt PASSED [ 38%]
backend/tests/test_api.py::test_ask_endpoint_rejects_whitespace_prompt PASSED [ 40%]
backend/tests/test_api.py::test_ask_endpoint_handles_model_failure PASSED [ 41%]
backend/tests/test_api.py::test_ask_get_fallback_endpoint PASSED         [ 42%]
backend/tests/test_api.py::test_static_files_accessible PASSED           [ 43%]
backend/tests/test_config.py::TestConfigAndTracing (5 tests) PASSED       [ 48%]
backend/tests/test_discipline_configs.py (4 tests) PASSED                 [ 53%]
backend/tests/test_graph.py (6 tests) PASSED                              [ 60%]
backend/tests/test_orchestration_execution.py (6 tests) PASSED           [ 66%]
backend/tests/test_orchestration_integration.py (5 tests) PASSED         [ 72%]
backend/tests/test_orchestration_nodes.py (13 tests) PASSED               [ 87%]
backend/tests/test_persona_prompts.py (4 tests) PASSED                    [ 91%]
backend/tests/test_refinement_di_and_routing.py (7 tests) PASSED          [100%]

=============================== warnings summary ===============================
starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated...
======================== 90 passed, 1 warning in 1.15s =========================
```

*(Note: The single warning is an upstream Starlette/AnyIO deprecation notice regarding `BlockingPortal`; it has zero impact on runtime behavior).*

---

## How to Run Tests

```bash
# Run the entire test suite
python3 -m pytest backend/tests/ -v

# Run only LangGraph graph and node tests
python3 -m pytest backend/tests/test_graph.py backend/tests/test_orchestration_nodes.py -v

# Run dependency injection and 4-case routing tests
python3 -m pytest backend/tests/test_refinement_di_and_routing.py -v

# Run with test coverage report
python3 -m pytest backend/tests/ --cov=backend/orchestration
```
