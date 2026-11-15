# OCTS AI — Phase 6: Testing & Verification Suite

## 1. Test Architecture & Coverage

Phase 6 introduces five dedicated automated test suites in `backend/tests/`, expanding total test coverage to **234 automated tests**:

```text
Test Suite Breakdown:
├── Phase 1-5 Baseline Tests: 187 passing
└── Phase 6 Memory Tests:     47 passing
    ├── test_memory_schemas.py (6 tests)
    ├── test_memory_repository.py (6 tests)
    ├── test_memory_scoping.py (4 tests)
    ├── test_memory_extraction.py (8 tests)
    ├── test_memory_retrieval.py (7 tests)
    ├── test_memory_consolidation.py (5 tests)
    ├── test_memory_orchestration.py (6 tests)
    └── test_memory_api.py (5 tests)
```

---

## 2. Test Suite Descriptions

### 1. `test_memory_schemas.py`
- Validates field constraints, enum values, confidence bounds ($0.0 \le c \le 1.0$), and Pydantic serialization for `MemoryRecord`, `ProjectRecord`, and `MemoryMetadata`.

### 2. `test_memory_repository.py`
- Tests transactional SQLite CRUD, restart persistence across SQLite connections, soft delete, archiving, version increments, and cascading project deactivation.

### 3. `test_memory_scoping.py`
- Verifies strict multi-tenant user isolation, project leakage prevention across distinct `project_id` values, discipline boundary containment, and header-based identity resolution.

### 4. `test_memory_extraction.py`
- Verifies extraction heuristics for explicit preferences, project lore, decisions, and constraints.
- Confirms rejection of ephemeral commands ("Please write a story") and scrubbing of PII / API keys.
- Confirms turn bounding ($\le 3$ items).

### 5. `test_memory_retrieval.py`
- Verifies multi-factor ranking weights and ordering.
- Verifies project match boosting and discipline match boosting.
- Tests token budget truncation ($\le 2000$ tokens / 8,000 characters).
- Tests access tracking (`access_count` increments and `last_accessed_at` timestamps).

### 6. `test_memory_consolidation.py`
- Verifies precedence hierarchy (explicit user preference supersedes AI inferred preference).
- Verifies non-destructive version incrementing ($v1 \rightarrow v2$) and `superseded_by` linkage.
- Verifies duplicate content skipping.
- Verifies lower precedence candidates cannot overwrite established memories.

### 7. `test_memory_orchestration.py`
- Verifies memory context injection into persona prompt before model execution while preserving `original_prompt`.
- Verifies memory disabled toggle (`memory_enabled=False`) cleanly bypasses retrieval and extraction.
- Verifies clarification path skips extraction (`memory_status="skipped"`).
- Verifies model failure aborts extraction.
- Verifies refinement reversion extracts from the winning baseline artifact.

### 8. `test_memory_api.py`
- Tests FastAPI REST endpoints for `/api/memory/projects` and `/api/memory`.
- Verifies path collision prevention (`/api/memory/projects` returns 200 list, not 404).
- Tests `/ask` integration with `project_id` and verifies `PromptResponse.memory` telemetry.

---

## 3. Verification Command

Execute the complete test suite with:

```bash
python3 -m pytest backend/tests/ -v
```

Expected result: **234 passed, 1 warning (starlette AnyIO testclient warning) in ~10s**.
