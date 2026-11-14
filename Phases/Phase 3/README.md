# Phase 3: LangGraph Multi-Agent Orchestration Layer

Welcome to the engineering documentation for **Phase 3** of **Octs AI**, a professional AI Creative Harness designed to assist creative professionals across four core disciplines: **Writers & Storytellers**, **Musicians & Singers**, **Content Creators**, and **Visual Artists & Designers**.

Phase 3 transforms the Phase 1 backend foundation and Phase 2 persona definitions into an executable, production-grade **LangGraph multi-agent orchestration pipeline**. It establishes a single shared execution harness, decoupled model dependency injection, intelligent 4-case routing with non-LLM clarification short-circuiting, and a polished dual-theme (Light/Dark) frontend workspace.

---

## Table of Contents

- [Phase Overview](#phase-overview)
- [Objectives & Scope](#objectives--scope)
- [Architecture Summary](#architecture-summary)
- [Key Accomplishments](#key-accomplishments)
- [Technology Stack](#technology-stack)
- [Implementation Status](#implementation-status)
- [Documentation Index](#documentation-index)
- [Prerequisites](#prerequisites)
- [Quickstart: Run and Verify](#quickstart-run-and-verify)
- [Next Phase Preview](#next-phase-preview)

---

## Phase Overview

Prior to Phase 3, the application possessed 16 rich specialist persona configurations and deterministic routing rules (Phase 2), but executed tasks via a direct model invocation without pipeline stages, validation gates, or orchestration lifecycle management.

Phase 3 delivers the complete orchestration and presentation layer:
1. **Unified LangGraph Execution Pipeline**: One shared `StateGraph` executing input validation, persona routing, fallback resolution, prompt preparation, model execution, output verification, and finalization across all 16 specialist personas.
2. **Decoupled Model Dependency Injection**: Complete architectural elimination of server global lookups; all nodes, graphs, and the `OrchestrationExecutor` receive their model and router dependencies explicitly.
3. **Intelligent 4-Case Routing Engine**: Ambiguous discipline queries now trigger a structured clarification prompt and short-circuit directly to `finalize_execution -> END` in under **10ms**, bypassing persona preparation and the Gemini LLM entirely.
4. **Production Frontend Workspace & Dark Mode**: A refined Linear/Vercel-inspired UI with an elevated deep charcoal Dark Mode, light mode default, anti-FOUC loading guards, real-time telemetry, and safe markdown output rendering.
5. **Zero-Regression API Contract**: Preserved 100% backward compatibility for existing clients (`POST /ask` returning `{ "reply": "..." }`) while exposing rich orchestration telemetry.

---

## Objectives & Scope

### In-Scope (Delivered)
1. **Typed State Architecture (`backend/orchestration/state.py`)**: Defined `OrchestrationState` TypedDict tracking 16 execution attributes from request initiation to telemetry reporting.
2. **Orchestration Nodes (`backend/orchestration/nodes.py`)**: Built 7 deterministic graph nodes with explicit dependency injection for model and router instances.
3. **Conditional Routing Edges (`backend/orchestration/edges.py`)**: Implemented 4 conditional edge decision routers managing validation failures, specialist fallbacks, Case C clarification short-circuits, and output recovery.
4. **StateGraph Compilation (`backend/orchestration/graph.py`)**: Singleton graph compiler assembling nodes and edges into an executable LangGraph `CompiledGraph`.
5. **High-Level Execution Harness (`backend/orchestration/executor.py`)**: `OrchestrationExecutor` orchestrating graph execution, bounded recursion limits, and schema translation.
6. **API Layer Decoupling (`server.py`)**: Initialized Gemini chat model in FastAPI application lifecycle and injected it cleanly into the executor without circular imports.
7. **Refined UI & Dark Mode (`style.css`, `script.js`, `pages/`)**: Implemented a centralized CSS variable theme system (`[data-theme="dark"]`), topbar toggle button, anti-FOUC head scripts, and truthful telemetry.
8. **Automated Test Suite (`backend/tests/`)**: Expanded test suite to **90 unit and integration tests** passing with 100% reliability.

### Out-of-Scope (Deferred to Phase 4 & Beyond)
- Multi-agent dialectical debate and automated reflection loops (Phase 4).
- Dynamic TrustScore evaluation rubrics and heuristic grading (Phase 4).
- Persistent SQLite / PostgreSQL checkpointers for multi-turn conversational memory (Phase 4).
- Cloud deployment and remote GitHub pushes (held locally per instruction).

---

## Architecture Summary

```
                      +--------------------------------------------------+
                      |                   FastAPI Server                 |
                      |                    (server.py)                   |
                      +-------------------------+------------------------+
                                                |
                                      POST /ask | PromptRequest
                                                v
                      +--------------------------------------------------+
                      |             OrchestrationExecutor                |
                      |       (backend/orchestration/executor.py)        |
                      +-------------------------+------------------------+
                                                | Injects: Model, Router, Registry
                                                v
                      +--------------------------------------------------+
                      |             Compiled StateGraph                  |
                      |        (backend/orchestration/graph.py)          |
                      +-------------------------+------------------------+
                                                |
         +--------------------------------------+--------------------------------------+
         |                                      |                                      |
         v                                      v                                      v
+------------------+                  +------------------+                   +--------------------+
|  validate_input  |                  |  route_request   |                   |  prepare_persona   |
+--------+---------+                  +--------+---------+                   +---------+----------+
         |                                     |                                       |
         | Pass                                | Discovered                            | Compiled
         v                                     v                                       v
+------------------+                  +------------------+                   +--------------------+
|  route_request   |                  | prepare_persona  |                   |   execute_model    |
+------------------+                  +------------------+                   |   (Injected LLM)   |
         |                                     |                                       |
         | Case C (Ambiguous)                  | Low Confidence                        v
         v                                     v                             +--------------------+
+------------------+                  +------------------+                   |  validate_output   |
| finalize_exec    |                  | routing_fallback |                   +---------+----------+
+--------+---------+                  +--------+---------+                             |
         |                                     |                                       v
         v                                     +---------------------------->+--------------------+
        END                                                                  |   finalize_exec    |
                                                                             +---------+----------+
                                                                                       |
                                                                                       v
                                                                                      END
```

---

## Key Accomplishments

1. **Production LangGraph Integration**: Replaced direct Gemini SDK invocations with an industry-standard StateGraph pipeline using LangGraph 0.2+.
2. **True Dependency Injection**: Eliminated `getattr(server, "model", None)`. All orchestration modules are 100% decoupled from the web server and testable in total isolation.
3. **Zero-Token Ambiguity Clarification**: Prompts lacking creative discipline context short-circuit in **~7ms**, saving API costs and asking the user for their discipline before calling the LLM.
4. **Single Shared Engine for 16 Personas**: Zero duplicate graphs. All 16 specialists across Writers, Musicians, Creators, and Designers share the exact same execution pipeline.
5. **Modern Minimalist UI & Dark Mode**: Elevated the frontend to match Linear, Notion, and Vercel aesthetic standards with seamless light/dark mode switching and zero theme flashing.
6. **Robust Test Suite**: 90 verified automated tests covering schemas, routing trees, nodes, graph compilation, dependency injection, and end-to-end HTTP integration.

---

## Technology Stack

| Layer | Component | Version / Library |
| :--- | :--- | :--- |
| **Orchestration** | LangGraph StateGraph | `langgraph >= 0.2.0` |
| **Model Integration**| LangChain Google GenAI | `langchain-google-genai >= 2.0.0` |
| **Model Provider** | Google Gemini | `gemini-3.5-flash-lite` |
| **API Framework** | FastAPI & Uvicorn | `fastapi >= 0.115.0`, `uvicorn >= 0.32.0` |
| **Data Validation** | Pydantic v2 | `pydantic >= 2.10.0` |
| **Telemetry** | LangSmith (Optional) | `langsmith >= 0.1.0` |
| **Frontend** | Vanilla ES6+ HTML/CSS | Swiss Tech + Industrial Lab Aesthetic |
| **Testing** | Pytest & AnyIO | `pytest >= 9.2.0`, `starlette.testclient` |

---

## Implementation Status

| Feature / Component | Status | Verified Evidence |
| :--- | :--- | :--- |
| **Typed State Schema** | **Complete** | [`backend/orchestration/state.py`](file:///Users/samriddha/Documents/Octs/backend/orchestration/state.py) |
| **Graph Nodes (7 nodes)** | **Complete** | [`backend/orchestration/nodes.py`](file:///Users/samriddha/Documents/Octs/backend/orchestration/nodes.py) |
| **Conditional Edges (4 edges)** | **Complete** | [`backend/orchestration/edges.py`](file:///Users/samriddha/Documents/Octs/backend/orchestration/edges.py) |
| **Graph Builder & Factory** | **Complete** | [`backend/orchestration/graph.py`](file:///Users/samriddha/Documents/Octs/backend/orchestration/graph.py) |
| **Orchestration Executor** | **Complete** | [`backend/orchestration/executor.py`](file:///Users/samriddha/Documents/Octs/backend/orchestration/executor.py) |
| **Model Dependency Injection** | **Complete** | Injected via constructor; zero `server.py` imports |
| **4-Case Routing Engine** | **Complete** | Cases A, B, C, D handled deterministically |
| **Frontend Refinement & Dark Mode** | **Complete** | Centralized CSS variables, anti-FOUC, live telemetry |
| **Unit & Integration Tests** | **Complete** | **90/90 tests passing** in `backend/tests/` |

---

## Documentation Index

Explore the complete Phase 3 engineering documentation:

1. [**ARCHITECTURE.md**](./ARCHITECTURE.md): Comprehensive system architecture, module boundaries, dependency injection, and Phase 1-2-3 relationship.
2. [**GRAPH_WORKFLOW.md**](./GRAPH_WORKFLOW.md): Complete StateGraph structure, node inventory, conditional edges, routing tree, and Mermaid execution diagrams.
3. [**EXECUTION_ENGINE.md**](./EXECUTION_ENGINE.md): Single shared execution engine, persona prompt preparation, Gemini configuration, and error recovery.
4. [**API_REFERENCE.md**](./API_REFERENCE.md): API contract, endpoint schemas, request/response examples for all 4 routing cases, and error codes.
5. [**TESTING.md**](./TESTING.md): Test architecture, module breakdown, mocking strategy, and verified test results.
6. [**IMPLEMENTATION_LOG.md**](./IMPLEMENTATION_LOG.md): Complete chronological record of files modified, decisions made, and verified milestones.
7. [**DECISIONS.md**](./DECISIONS.md): Architectural Decision Records (ADRs) covering graph topology, typing, dependency injection, and theme state.
8. [**FRONTEND.md**](./FRONTEND.md): Detailed documentation of UI/UX improvements, design language preservation, dark mode system, and telemetry.

---

## Prerequisites

- **Python**: 3.10, 3.11, or 3.12 (developed and verified on Python 3.12.10).
- **Environment**: Virtual environment with dependencies from `requirements.txt`.
- **API Key**: Valid `GEMINI_API_KEY` configured in `.env`.
- **Optional**: `LANGSMITH_API_KEY` if LangSmith distributed tracing is enabled.

---

## Quickstart: Run and Verify

### 1. Run Automated Test Suite
Execute the complete test suite across all 11 test modules:
```bash
python3 -m pytest backend/tests/ -v
```
Expected output:
```
======================== 90 passed, 1 warning in 1.15s =========================
```

### 2. Launch Local Development Server
Start the FastAPI server on `127.0.0.1:8000`:
```bash
python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Verify System Health
```bash
curl -s http://127.0.0.1:8000/api/health | jq
```
Expected output:
```json
{
  "status": "ok",
  "version": "0.2.0",
  "model_provider": "google_genai",
  "model_name": "gemini-3.5-flash-lite",
  "langsmith_tracing": false
}
```

### 4. Test Case C: Ambiguous Prompt (Zero-Token Clarification)
```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I want to create something interesting today"}' | jq
```
Expected output:
```json
{
  "reply": "Which creative discipline are you working in? (Writers & Storytellers, Musicians & Singers, Content Creators, or Visual Artists & Designers)",
  "role": null,
  "agent_used": null,
  "needs_clarification": true,
  "clarification_question": "Which creative discipline are you working in? (Writers & Storytellers, Musicians & Singers, Content Creators, or Visual Artists & Designers)",
  "routing_confidence": 0.0,
  "latency_ms": 7,
  "execution_status": "completed_clarification_required"
}
```

### 5. Test Case A: Creative Specialist Execution
```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Give me a 2-line lyric with an AABB rhyme scheme about neon rain.", "role": "musicians"}' | jq
```

---

## Next Phase Preview

Phase 3 establishes a solid, decoupled orchestration pipeline. Phase 4 will introduce:
- **TrustScore Evaluation Engine**: Rubric-based scoring analyzing craft adherence, constraint compliance, and domain depth.
- **Autonomous Multi-Agent Reflection**: Automated revision loops when a specialist output fails quality rubrics.
- **Persistent State Checkpointing**: Replacing stateless execution with SQLite/PostgreSQL checkpointing for multi-turn conversational memory.
