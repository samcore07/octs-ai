# Phase 2: Discipline Hierarchy & Agent Persona Layer

Welcome to the engineering documentation for **Phase 2** of **Octs AI**, a professional AI Creative Harness designed to assist creative professionals across four core disciplines: **Writers & Storytellers**, **Musicians & Singers**, **Content Creators**, and **Visual Artists & Designers**.

Phase 2 builds upon the Phase 1 backend foundation by introducing a modular, typed agent persona layer powered by **Pydantic v2** and **LangChain-compatible prompt structures**. It establishes 4 domain disciplines, 16 deeply specialized agent personas, a centralized singleton registry, and a deterministic 4-stage task router.

---

## Table of Contents

- [Phase Overview](#phase-overview)
- [Objectives & Scope](#objectives--scope)
- [Discipline & Persona Matrix](#discipline--persona-matrix)
- [Key Accomplishments](#key-accomplishments)
- [Technology Stack](#technology-stack)
- [Implementation Status](#implementation-status)
- [Documentation Index](#documentation-index)
- [Prerequisites](#prerequisites)
- [Quickstart: Run and Verify](#quickstart-run-and-verify)
- [Next Phase Preview](#next-phase-preview)

---

## Phase Overview

Prior to Phase 2, prompt execution relied on a generic, unspecialized model invocation that lacked creative craft constraints, discipline-specific terminology, and task-based specialization.

Phase 2 formalizes the core intelligence layer:
1. **Discipline Hierarchy**: 4 distinct creative disciplines configured with domain terminology, quality benchmarks, and output conventions.
2. **Specialist Persona Layer**: 16 dedicated persona definitions with non-generic system prompts, technical craft constraints, expected output architectures, and evaluation criteria.
3. **Central Agent Registry**: A singleton discovery registry providing fast lookups by ID and filtering by discipline.
4. **Deterministic Task Router**: A 4-stage routing engine combining explicit task mapping, regex pattern heuristics, safe model classification with validation, and discipline default fallbacks.
5. **Zero-Regression API Integration**: Seamless connection to `POST /ask` populating the `agent_used` field with the routed specialist while preserving 100% backward compatibility.

---

## Objectives & Scope

### In-Scope (Delivered)
1. **Unified Schema Base (`backend/agents/base.py`)**: Defined typed Pydantic v2 schemas: `PersonaDefinition`, `DisciplineConfig`, `ModelConfig`, and `RoutingResult`.
2. **Central Registry (`backend/agents/registry.py`)**: Singleton `AgentRegistry` with lazy auto-discovery managing all disciplines and personas.
3. **Four Discipline Configs (`backend/agents/disciplines/`)**: Complete definitions for `writers`, `musicians`, `creators`, and `designers`.
4. **Sixteen Specialist Personas (`backend/agents/personas/`)**: 16 dedicated modules with domain-specific craft depth, constraints, and LangChain prompt compilation.
5. **Task-Based Routing Engine (`backend/agents/routing/`)**: Heuristic scoring engine and `AgentRouter` ensuring no invalid persona ID ever reaches execution.
6. **Gateway Integration (`server.py`)**: Connected routing to `POST /ask` returning the active `agent_used` in `PromptResponse`.
7. **Comprehensive Unit Testing (`backend/tests/`)**: Added 37 new tests, bringing the verified test suite to **52/52 passing tests**.

### Out-of-Scope (Deferred to Phase 3 & Beyond)
- Multi-agent LangGraph cyclic graph execution and node state transitions (Phase 3).
- SQLite/PostgreSQL persistent checkpointing across conversation turns (Phase 3).
- Dynamic TrustScore evaluation engine and reflection loops (Phase 4).
- Frontend visual updates or UI modifications (preserved as-is).

---

## Discipline & Persona Matrix

```
Octs AI Creative Harness
├── Writers & Storytellers (writers)
│   ├── Narrative Architect (narrative_architect)
│   ├── Lore & Continuity Keeper (lore_continuity_keeper)
│   ├── Prose Stylist (prose_stylist)
│   └── Research Scout (research_scout)
│
├── Musicians & Singers (musicians)
│   ├── Lyricist & Meter Engine (lyricist_meter_engine)
│   ├── Harmonic Arranger (harmonic_arranger)
│   ├── Track Structure Architect (track_structure_architect)
│   └── Sonic Palette Curator (sonic_palette_curator)
│
├── Content Creators (creators)
│   ├── Hook & Retention Architect (hook_retention_architect)
│   ├── Multi-Platform Transmuter (multi_platform_transmuter)
│   ├── Editorial Cadence Planner (editorial_cadence_planner)
│   └── Audience Friction Auditor (audience_friction_auditor)
│
└── Visual Artists & Designers (designers)
    ├── Concept Ideation Engine (concept_ideation_engine)
    ├── Visual System Auditor (visual_system_auditor)
    ├── Art Direction Critic (art_direction_critic)
    └── Design Token & Palette Architect (design_token_palette_architect)
```

---

## Key Accomplishments

| Area | Phase 1 State | Phase 2 State |
| :--- | :--- | :--- |
| **Agent Personas** | Single fallback identifier (`direct_model`) | 16 deeply specialized, typed personas |
| **Prompt Engineering** | Unconstrained direct prompt pass-through | Structured LangChain `ChatPromptTemplate` with craft constraints |
| **Task Routing** | None (direct execution) | 4-stage deterministic router with confidence scoring & fallbacks |
| **Domain Hierarchy** | String role validation only | 4 formal `DisciplineConfig` instances with terminology and benchmarks |
| **Registry Management** | None | Singleton `AgentRegistry` with zero-overhead discovery |
| **Test Coverage** | 15 passing tests | 52 passing tests (100% pass rate in < 1 second) |

---

## Technology Stack

- **Runtime**: Python 3.10+
- **Data Validation & Schemas**: Pydantic `>= 2.9.0` (v2 `BaseModel`, `ConfigDict`, `Field`)
- **Prompt Abstractions**: LangChain Core (`langchain_core >= 0.3.0`, `ChatPromptTemplate`)
- **Pattern Matching**: Python `re` standard library with pre-compiled regex scoring
- **Web Framework**: FastAPI `>= 0.115.0`
- **Testing**: Pytest `>= 8.0.0`, `unittest.mock`

---

## Implementation Status

- [x] **Unified Schemas**: Complete (`backend/agents/base.py`).
- [x] **Agent Registry**: Complete (`backend/agents/registry.py`).
- [x] **Discipline Configurations**: Complete (`writers`, `musicians`, `creators`, `designers`).
- [x] **16 Specialist Personas**: Complete and registered with deep craft prompts.
- [x] **LangChain Template Compilation**: Complete via `.build_prompt_template()`.
- [x] **Deterministic Routing Engine**: Complete with pattern scoring and safe fallbacks.
- [x] **Server Integration**: Complete in `server.py` (`POST /ask` returns `agent_used`).
- [x] **Automated Test Suite**: 52/52 tests passing in `backend/tests/`.
- [x] **Zero Regressions**: 100% backward compatibility maintained for existing frontend.

---

## Documentation Index

Explore the detailed Phase 2 documentation:

1. [**Architecture & Layer Design**](ARCHITECTURE.md) — Comprehensive explanation of the agent layer, class relationships, request lifecycle, and Mermaid diagrams.
2. [**Disciplines & Specialist Personas Reference**](DISCIPLINE_HIERARCHY.md) — In-depth breakdown of all 4 disciplines and 16 specialist personas, craft constraints, and output structures.
3. [**Routing & Classification Guide**](ROUTING_GUIDE.md) — Detailed specifications of the 4-stage routing pipeline, regex heuristics, task mapping, and model fallback safety.
4. [**Testing & Verification Guide**](TESTING.md) — Documentation for the 52 automated tests, test fixtures, deterministic mocking, and verification results.
5. [**Implementation & Engineering Log**](IMPLEMENTATION_LOG.md) — Chronological engineering log of files created, refactorings, and resolved technical challenges.
6. [**Architectural Decision Records (ADRs)**](DECISIONS.md) — Formal records (ADR-006 through ADR-010) documenting the rationale behind Phase 2 decisions.

---

## Prerequisites

Before running or testing the agent layer, ensure you have:
1. Python 3.10 or higher.
2. Activated virtual environment with installed dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. A configured `.env` file containing `GEMINI_API_KEY`.

---

## Quickstart: Run and Verify

### 1. Run the Full Test Suite
Execute all 52 unit, integration, and routing tests:
```bash
python3 -m pytest backend/tests/ -v
```
Expected output:
```text
======================== 52 passed, 1 warning in 0.84s =========================
```

### 2. Verify Persona Routing via CLI
Test the router with a creative prompt:
```bash
python3 -c "
from backend.agents.routing import AgentRouter
router = AgentRouter()
res = router.route('Write lyrics with tight meter and vocal hooks', discipline_id='musicians')
print(f'Routed to: {res.persona_id} (Confidence: {res.confidence})')
print(f'Rationale: {res.rationale}')
"
```
Expected output:
```text
Routed to: lyricist_meter_engine (Confidence: 0.85)
Rationale: Selected Lyricist & Meter Engine based on domain craft keywords and task pattern matching.
```

### 3. Verify System Health and Live Inference
Start the server:
```bash
python3 -m uvicorn server:app --host 127.0.0.1 --port 8000
```
In another terminal, test inference through the backward-compatible endpoint:
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "How do I structure Act 2 of a screenplay?", "role": "writers"}'
```
Response:
```json
{
  "reply": "...",
  "role": "writers",
  "agent_used": "narrative_architect",
  "trust_score": null,
  "trust_breakdown": null,
  "latency_ms": 1240,
  "recovery_triggered": false,
  "model_used": "gemini-3.5-flash-lite"
}
```

---

## Next Phase Preview

With the agent persona hierarchy, registry, and routing engine thoroughly verified, the system is ready for **Phase 3: LangGraph Orchestration & Checkpointing**:
- Construction of cyclic state graphs in `backend/orchestrator/`.
- Dynamic persona execution nodes using compiled `ChatPromptTemplate` instances.
- SQLite persistence checkpointing scoped by `thread_id`.
- Automated recovery routing on execution faults.
