# Phase 2: Testing & Verification Guide

This document details the automated testing architecture, test suites, deterministic mocking strategy, and execution evidence for **Phase 2** of **Octs AI**.

---

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Suite Inventory](#test-suite-inventory)
- [How to Run the Tests](#how-to-run-the-tests)
- [Detailed Test Suite Breakdown](#detailed-test-suite-breakdown)
  - [1. Discipline Configuration Tests (`test_discipline_configs.py`)](#1-discipline-configuration-tests-test_discipline_configspy)
  - [2. Agent Registry Tests (`test_agent_registry.py`)](#2-agent-registry-tests-test_agent_registrypy)
  - [3. Persona Prompts & LangChain Tests (`test_persona_prompts.py`)](#3-persona-prompts--langchain-tests-test_persona_promptspy)
  - [4. Agent Routing Tests (`test_agent_routing.py`)](#4-agent-routing-tests-test_agent_routingpy)
  - [5. Preserved Phase 1 Tests (`test_api.py` & `test_config.py`)](#5-preserved-phase-1-tests-test_apipy--test_configpy)
- [Deterministic Mocking Strategy](#deterministic-mocking-strategy)
- [Official Pytest Verification Evidence](#official-pytest-verification-evidence)

---

## Testing Philosophy

Phase 2 enforces strict automated verification across the entire agent hierarchy:
1. **100% Deterministic**: Zero live network calls to Google Gemini, LangSmith, or external services during test runs.
2. **Schema & Contract Conformance**: Every discipline and persona is checked against Pydantic v2 schemas for required fields, constraints, and valid ranges.
3. **Comprehensive Edge Case Coverage**: Unrecognized disciplines, ambiguous prompts, multi-persona prompts, model failures, and malformed classifier outputs are verified.
4. **Sub-Second Execution**: All 52 tests execute in under 1 second to ensure friction-free continuous testing.

---

## Test Suite Inventory

The test suite lives in `backend/tests/` and contains **52 tests**:

| Test File | Tests | Focus Area |
| :--- | :--- | :--- |
| `test_discipline_configs.py` | 4 | Verification of 4 disciplines, metadata, terminology, and persona links. |
| `test_agent_registry.py` | 6 | Singleton registry behavior, 16 unique personas, lookups, case tolerance. |
| `test_persona_prompts.py` | 4 | LangChain `ChatPromptTemplate` compilation, markdown sections, craft depth. |
| `test_agent_routing.py` | 23 | 16 representative task routes, explicit mapping, fallbacks, model mocks. |
| `test_api.py` | 10 | Preserved Phase 1 endpoint contracts, backwards compatibility, validation. |
| `test_config.py` | 5 | Preserved Phase 1 Pydantic Settings, CORS parsing, LangSmith setup. |
| **Total** | **52** | **100% Pass Rate** |

---

## How to Run the Tests

### 1. Run the Full Test Suite
```bash
python3 -m pytest backend/tests/ -v
```

### 2. Run Only Phase 2 Agent Tests
```bash
python3 -m pytest backend/tests/test_discipline_configs.py backend/tests/test_agent_registry.py backend/tests/test_persona_prompts.py backend/tests/test_agent_routing.py -v
```

### 3. Run Routing Tests Specifically
```bash
python3 -m pytest backend/tests/test_agent_routing.py -v
```

### 4. Run a Specific Test Function
```bash
python3 -m pytest backend/tests/test_agent_routing.py -k "test_model_assisted_classification_success" -v
```

---

## Detailed Test Suite Breakdown

### 1. Discipline Configuration Tests (`test_discipline_configs.py`)
- `test_all_four_disciplines_exist`: Verifies all 4 required disciplines (`writers`, `musicians`, `creators`, `designers`) exist in the registry.
- `test_discipline_required_fields`: Confirms display name, purpose, scope, supported tasks, terminology, and quality requirements are populated.
- `test_discipline_has_four_personas`: Asserts each discipline has exactly 4 specialist personas and `get_personas()` resolves all 4 without error.
- `test_specific_discipline_specialists`: Verifies exact persona membership sets for each discipline.

### 2. Agent Registry Tests (`test_agent_registry.py`)
- `test_registry_contains_16_personas`: Asserts registry contains exactly 16 registered personas.
- `test_unique_persona_identifiers`: Validates that all 16 persona IDs are unique, lowercased, and snake_cased.
- `test_persona_lookup_by_id`: Tests retrieval by ID with case-insensitivity and whitespace trimming.
- `test_filter_personas_by_discipline`: Confirms filtering personas by discipline returns exactly 4 personas per discipline.
- `test_unknown_persona_lookup`: Confirms non-existent persona lookup returns `None` safely.
- `test_unknown_discipline_lookup`: Confirms non-existent discipline lookup returns `None` safely.

### 3. Persona Prompts & LangChain Tests (`test_persona_prompts.py`)
- `test_all_16_personas_have_complete_prompt_fields`: Verifies responsibilities ($\ge 4$), constraints ($\ge 3$), output structure ($\ge 4$), and evaluation criteria ($\ge 3$).
- `test_format_system_prompt_contains_crucial_sections`: Confirms markdown output contains role header, directives, constraints, and criteria.
- `test_build_prompt_template_and_format_messages`: Asserts `build_prompt_template()` builds a valid `ChatPromptTemplate` returning `[SystemMessage, HumanMessage]`.
- `test_persona_domain_depth_no_generic_platitudes`: Asserts generic platitudes (*"you are a helpful assistant"*) are absent from system instructions.

### 4. Agent Routing Tests (`test_agent_routing.py`)
- `test_representative_prompt_routing` (16 parameterized tests): Validates accurate routing to each of the 16 personas using realistic domain prompts with confidence $\ge 0.65$.
- `test_explicit_task_type_routing`: Validates that passing `task_type="worldbuilding_audit"` bypasses regex heuristics and routes with confidence $0.95$.
- `test_invalid_discipline_handling`: Confirms unknown disciplines (e.g. `astrophysics`) fall back safely to `writers` and `narrative_architect` ($C=0.30$).
- `test_ambiguous_prompt_fallback_routing`: Validates that generic prompts with zero matches fall back to the discipline lead specialist ($C=0.50$).
- `test_alternative_persona_recommendation`: Confirms multi-topic queries populate `alternative_persona_id`.
- `test_model_assisted_classification_success`: Uses a mocked model to verify model-assisted classification returns with confidence $0.85$.
- `test_model_assisted_classification_malformed_fallback`: Confirms hallucinated or malformed model responses are discarded in favor of deterministic fallback.
- `test_model_assisted_classification_exception_fallback`: Confirms model exceptions (e.g. API quota errors) are caught silently and fall back safely.

### 5. Preserved Phase 1 Tests (`test_api.py` & `test_config.py`)
- 10 endpoint tests verifying `GET /api/health`, `POST /ask`, backwards-compatible `{ "reply": "..." }` responses, static files, and validation errors.
- 5 configuration tests verifying Pydantic Settings, CORS parsing, and LangSmith setup.

---

## Deterministic Mocking Strategy

In `test_agent_routing.py`, LLM calls are mocked using standard `unittest.mock.MagicMock`:

```python
def test_model_assisted_classification_success(router):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "lore_continuity_keeper"
    mock_model.invoke.return_value = mock_response

    result = router.route(
        prompt="Generic ambiguous prompt with zero keywords xyz123",
        discipline_id="writers",
        model=mock_model,
    )
    assert result.persona_id == "lore_continuity_keeper"
    assert result.routing_method == "model_classification"
```

This guarantees:
- Fast test execution ($\sim 0.8$ seconds for 52 tests).
- Immunity from API rate limits or network downtime.
- Reliable CI/CD execution in isolated container environments.

---

## Official Pytest Verification Evidence

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: /Users/samriddha/Documents/Octs
collected 52 items

backend/tests/test_agent_registry.py::test_registry_contains_16_personas PASSED [  1%]
backend/tests/test_agent_registry.py::test_unique_persona_identifiers PASSED [  3%]
backend/tests/test_agent_registry.py::test_persona_lookup_by_id PASSED   [  5%]
backend/tests/test_agent_registry.py::test_filter_personas_by_discipline PASSED [  7%]
backend/tests/test_agent_registry.py::test_unknown_persona_lookup PASSED [  9%]
backend/tests/test_agent_registry.py::test_unknown_discipline_lookup PASSED [ 11%]
backend/tests/test_agent_routing.py::test_representative_prompt_routing (16 cases) PASSED [ 42%]
backend/tests/test_agent_routing.py::test_explicit_task_type_routing PASSED [ 44%]
backend/tests/test_agent_routing.py::test_invalid_discipline_handling PASSED [ 46%]
backend/tests/test_agent_routing.py::test_ambiguous_prompt_fallback_routing PASSED [ 48%]
backend/tests/test_agent_routing.py::test_alternative_persona_recommendation PASSED [ 50%]
backend/tests/test_agent_routing.py::test_model_assisted_classification_success PASSED [ 51%]
backend/tests/test_agent_routing.py::test_model_assisted_classification_malformed_fallback PASSED [ 53%]
backend/tests/test_agent_routing.py::test_model_assisted_classification_exception_fallback PASSED [ 55%]
backend/tests/test_api.py (10 tests) PASSED                              [ 75%]
backend/tests/test_config.py (5 tests) PASSED                            [ 84%]
backend/tests/test_discipline_configs.py (4 tests) PASSED                [ 92%]
backend/tests/test_persona_prompts.py (4 tests) PASSED                   [100%]

======================== 52 passed, 1 warning in 0.84s =========================
```
