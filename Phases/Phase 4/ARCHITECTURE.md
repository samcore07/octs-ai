# OCTS AI — Phase 4: System Architecture & Design

## 1. Architectural Evolution (Phases 1 to 4)

```mermaid
flowchart TD
    subgraph P1["Phase 1: Foundation"]
        A[FastAPI Gateway] --> B[Configuration & CORS]
        B --> C[Gemini LLM Provider]
        C --> D[LangSmith Tracing]
    end

    subgraph P2["Phase 2: Personas & Routing"]
        E[4 Disciplines] --> F[16 Specialist Personas]
        F --> G[Deterministic AgentRouter]
        G --> H[AgentRegistry Singleton]
    end

    subgraph P3["Phase 3: LangGraph Orchestration"]
        I[StateGraph Pipeline] --> J[Dependency Injection]
        J --> K[Intelligent Clarification Case C]
        K --> L[Single Shared Graph]
    end

    subgraph P4["Phase 4: Evaluation & TrustScore"]
        M[Dual-Dimension Evaluation] --> N[4 Discipline Rubrics]
        N --> O[Deterministic Reliability Checks]
        O --> P[ScoringCalculator & TrustScore]
        P --> Q[Optional LLM-as-a-Judge]
    end

    P1 --> P2 --> P3 --> P4
```

---

## 2. Dual-Dimension Evaluation Architecture

The cornerstone of Phase 4 is the strict separation between **Creative Output Quality** and **Execution Reliability**.

```mermaid
graph TD
    A[Orchestration State] --> B{Execution Status?}
    B -->|needs_clarification| C[Clarification Short-Circuit]
    C --> D[Quality: None | Reliability: None | TrustScore: None | Status: skipped]
    
    B -->|execution_failed| E[Failure Handling]
    E --> F[Quality: None | Reliability: Evaluated | TrustScore: None]

    B -->|output_validated| G[Dual Dimension Evaluator]
    
    subgraph DimA["Dimension A: Creative Output Quality"]
        G --> H[Discipline Rubric Evaluator]
        H --> I[Heuristic Baseline or LLM Judge]
        I --> J[Normalized Quality Score: 0 - 100]
    end

    subgraph DimB["Dimension B: Execution Reliability"]
        G --> K[Deterministic Checks Runner]
        K --> L[Schema, Persona, Latency Invariants]
        L --> M[Deterministic Reliability Score: 0 - 100]
    end

    J --> N[ScoringCalculator]
    M --> N
    N --> O["Composite TrustScore = (Quality * 0.70) + (Reliability * 0.30)"]
```

### Why Independent Dimensions Matter
1. **Technical Success $\neq$ High Quality:** A model can return a syntactically valid JSON payload in 200 ms that contains generic, uninspired creative text. Conflating execution with quality would falsely assign high marks to poor creative work.
2. **Creative Value $\neq$ Technical Flawlessness:** A compelling script returned despite a non-critical telemetry warning or degraded retry loop is still creatively valuable, but its reliability deficit must remain visible to operators.
3. **No Fabricated Trust:** If an execution fails or user clarification is requested, creative quality is not evaluated and `trust_score` remains strictly `None`.

---

## 3. LangGraph Pipeline Integration

Evaluation is integrated directly into the compiled StateGraph as a dedicated node (`evaluate_execution`) positioned between `validate_output` and `finalize_execution`.

```mermaid
sequenceDiagram
    autonumber
    actor User as Client / UI
    participant Server as FastAPI (server.py)
    participant Exec as OrchestrationExecutor
    participant Graph as LangGraph StateGraph
    participant Eval as EvaluationEngine
    participant Calc as ScoringCalculator

    User->>Server: POST /ask {"prompt": "...", "role": "writers"}
    Server->>Exec: execute_prompt(prompt, role)
    Exec->>Graph: invoke(initial_state)
    
    rect rgb(240, 248, 255)
        Note over Graph: validate_input -> route_request -> prepare_persona -> execute_model -> validate_output
    end

    Graph->>Eval: evaluate_execution_node(state)
    activate Eval
    Eval->>Eval: ReliabilityEvaluator.evaluate(state)
    Eval->>Eval: QualityEvaluator.evaluate(prompt, output)
    Eval->>Calc: calculate_quality_score(criteria)
    Eval->>Calc: calculate_reliability_score(checks)
    Eval->>Calc: calculate_trust_score(quality, reliability)
    Calc-->>Eval: TrustScore, TrustBreakdown
    Eval-->>Graph: Updates state with evaluation_result & trust_score
    deactivate Eval

    Graph->>Graph: finalize_execution_node(state)
    Graph-->>Exec: final_state
    Exec-->>Server: PromptResponse(reply, trust_score, evaluation, ...)
    Server-->>User: JSON Response (200 OK)
```

---

## 4. Module Boundaries & Responsibilities

| Module | Responsibility | Injected Dependencies |
| :--- | :--- | :--- |
| `backend.evaluation.engine.EvaluationEngine` | Coordinates quality assessment, reliability evaluation, mode routing, and defensive exception containment. | `EvaluatorRegistry`, `ScoringCalculator`, `ReliabilityEvaluator`, `LLMJudge`, `Settings` |
| `backend.evaluation.evaluator_registry.EvaluatorRegistry` | O(1) lookup of discipline quality evaluators; singleton provider. | None |
| `backend.evaluation.quality.base.QualityEvaluator` | Abstract base defining criterion weights, normalization, and domain constraints. | `weights_override` |
| `backend.evaluation.reliability.evaluator.ReliabilityEvaluator` | Runs 7 deterministic pipeline health checks against orchestration state. | `AgentRegistry` |
| `backend.evaluation.scoring.calculator.ScoringCalculator` | Calculates normalized Quality Score, Reliability Score, coverage, and composite TrustScore. | Configured weights (`0.70 / 0.30`) |
| `backend.evaluation.judges.llm_judge.LLMJudge` | Model-based structured evaluation with prompt-injection containment. | `BaseChatModel`, `timeout_seconds`, `max_retries` |
