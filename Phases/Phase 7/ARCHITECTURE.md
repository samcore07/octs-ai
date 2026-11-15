# Phase 7 — Observability Architecture

## Architectural Philosophy
Observability in OCTS AI follows three strict rules:
1. **Instrument, Do Not Rebuild**: The existing LangGraph orchestration, evaluation rubrics, refinement loops, and memory stores remain intact. Observability acts as a non-invasive telemetry overlay.
2. **Failures in Observability Are Non-Fatal**: If telemetry logging or metric recording fails, the user's creative generation request must never crash or degrade.
3. **Strict Separation of Telemetry & Domain State**: Operational metrics and logs are stored in a dedicated SQLite database (`octs_telemetry.db`), completely separate from creative persistence (`octs_memory.db`).

## Package Structure
```text
backend/observability/
├── __init__.py           # Unified exports facade
├── context.py            # Python contextvars for request isolation
├── correlation.py        # UUID generation, validation regex, header resolver
├── events.py             # 24 lifecycle events enum and ExecutionEvent model
├── logger.py             # Structured JSON formatter with credential scrubbing
├── models.py             # SQLAlchemy ORM models with composite indexes
├── storage.py            # TelemetryStore managing SQLite engine and pruning
├── metrics.py            # Math percentiles (P50, P95, P99) and token extraction
├── collector.py          # TelemetryCollector singleton with rolling buffer
├── middleware.py         # Starlette/FastAPI RequestCorrelationMiddleware
├── error_tracking.py     # 14-code ErrorTaxonomy, AppError, exception classifier
├── health.py             # HealthChecker (liveness, readiness, detailed)
├── analytics.py          # AnalyticsService querying persisted telemetry
└── schemas.py            # Pydantic v2 schemas for health, telemetry, analytics
```

## Telemetry Data Flow Diagram

```mermaid
flowchart TD
    Client[HTTP Client / Frontend] -->|HTTP Request| Middleware[RequestCorrelationMiddleware]
    Middleware -->|Attach X-Request-ID & Context| Context[Python ContextVars]
    Middleware -->|POST /ask| Router[FastAPI Route Handler]
    Router -->|Injected Model & ID| Executor[OrchestrationExecutor]
    
    subgraph LangGraph Pipeline
        Executor -->|REQUEST_STARTED| Collector[TelemetryCollector]
        Executor --> NodeRouting[route_request_node]
        NodeRouting --> NodeContext[identify_context_node]
        NodeContext --> NodeMemRet[retrieve_memory_node]
        NodeMemRet --> NodeExec[execute_model_node]
        NodeExec --> NodeVal[validate_output_node]
        NodeVal --> NodeEval[evaluate_execution_node]
        NodeEval --> NodePeer[peer_review_node]
        NodePeer --> NodeRefine[refine_output_node]
        NodeRefine --> NodeAnalyzer[improvement_analyzer_node]
        NodeAnalyzer --> NodeMemPers[persist_memory_node]
        NodeMemPers --> NodeFinal[finalize_execution_node]
    end

    NodeRouting -.->|Events| Collector
    NodeExec -.->|Tokens & Events| Collector
    NodeEval -.->|Scores & Events| Collector
    NodePeer -.->|Critique & Events| Collector
    NodeAnalyzer -.->|Reversion & Events| Collector
    NodeMemPers -.->|Storage & Events| Collector
    
    Collector -->|In-Memory Buffer| MemoryBuffer[Deque 100 Recent Events]
    Collector -->|Non-blocking Merge| TelemetryDB[(octs_telemetry.db)]
    
    TelemetryDB -->|Queries| AnalyticsService[AnalyticsService]
    AnalyticsService -->|REST API| AnalyticsEndpoints[GET /api/analytics/*]
    AnalyticsEndpoints --> Dashboard[Observability Web Dashboard]
```
