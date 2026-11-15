# OCTS AI — Phase 4: Evaluation Engine, Quality Assessment & TrustScore

## Executive Overview
Phase 4 introduces a production-grade, extensible, dual-dimension evaluation system into OCTS AI. Prior to Phase 4, the platform orchestrated requests across 4 creative disciplines and 16 specialist personas, validating inputs and outputs structurally. Phase 4 transforms OCTS AI into a measurable, observable creative harness by decoupling **Creative Output Quality** from **Execution Reliability**, introducing normalized domain rubrics, deterministic health checks, an optional LLM-as-a-Judge, and a composite **TrustScore**.

---

## Core Objectives & Achievements
- **Dual Independent Dimensions:** Evaluates *Creative Output Quality* (domain craft, coherence, adherence) separately from *Execution Reliability* (schema compliance, non-empty outputs, persona-discipline alignment, latency telemetry).
- **Four Specialized Quality Rubrics:** Custom rubric matrices for **Writers & Storytellers**, **Musicians & Singers**, **Content Creators**, and **Visual Artists & Designers**, with weights strictly normalized to 1.0.
- **Explicit Domain Constraints:** Enforces truth-in-advertising constraints—no fabricated claims of hearing acoustic audio for musician text or visual inspection of pixel graphics for designer tokens.
- **Composite TrustScore:** Calculates a transparent composite score:
  $$\text{TrustScore} = (\text{Quality Score} \times 0.70) + (\text{Reliability Score} \times 0.30)$$
  Preserves underlying dimensions, exposes calculation formulas, and refuses to fabricate scores on clarification or execution failures.
- **Deterministic & LLM-as-a-Judge Hybrid Modes:** Operates in `deterministic`, `llm_judge`, or `hybrid` modes. Evaluates without extra LLM calls when configured deterministically.
- **Injection-Resistant LLM Judge:** Encapsulates untrusted candidate outputs and user prompts inside isolated XML delimiters with strict system directives and Pydantic validation.
- **LangGraph Integration:** Placed cleanly into the StateGraph between `validate_output` and `finalize_execution`. Defensively handles evaluation errors so user responses are never dropped.
- **100% Backward Compatibility:** Preserves all existing `POST /ask` response properties (`reply`, `role`, `agent_used`, `latency_ms`) while attaching strongly typed evaluation payloads.

---

## Directory & Package Structure
```text
backend/
├── evaluation/
│   ├── __init__.py                  # Package exports
│   ├── engine.py                    # Unified EvaluationEngine coordinator
│   ├── schemas.py                   # Pydantic v2 evaluation schemas
│   ├── evaluator_registry.py        # Central registry for discipline evaluators
│   ├── quality/
│   │   ├── __init__.py              # Quality evaluators package
│   │   ├── base.py                  # Abstract QualityEvaluator base class
│   │   ├── writers.py               # Writers & Storytellers evaluator (6 criteria)
│   │   ├── musicians.py             # Musicians & Singers evaluator (7 criteria)
│   │   ├── creators.py              # Content Creators evaluator (7 criteria)
│   │   └── designers.py             # Visual Artists & Designers evaluator (7 criteria)
│   ├── reliability/
│   │   ├── __init__.py              # Reliability package
│   │   ├── checks.py                # Concrete deterministic execution checks
│   │   └── evaluator.py             # ReliabilityEvaluator runner
│   ├── scoring/
│   │   ├── __init__.py              # Scoring package
│   │   ├── calculator.py            # ScoringCalculator (Quality, Reliability, TrustScore)
│   │   └── weights.py               # Weight matrices and validation routines
│   └── judges/
│       ├── __init__.py              # Judges package
│       ├── llm_judge.py             # Structured LLM-as-a-Judge implementation
│       └── prompts.py               # Injection-resistant prompt framing & delimiters
└── tests/
    ├── test_evaluation_engine.py    # Coordinator lifecycle tests
    ├── test_evaluation_quality.py   # Discipline rubrics & weights tests
    ├── test_evaluation_reliability.py# Deterministic check tests
    ├── test_evaluation_scoring.py   # Mathematical formulas & coverage tests
    ├── test_evaluation_judge.py     # LLM judge parsing & security tests
    └── test_evaluation_integration.py# End-to-end pipeline & API contract tests
```

---

## Phase 4 Documentation Index
1. [ARCHITECTURE.md](file:///Users/samriddha/Documents/Octs/Phases/Phase%204/ARCHITECTURE.md): Structural overview, component boundaries, and Mermaid diagrams.
2. [EVALUATION_ENGINE.md](file:///Users/samriddha/Documents/Octs/Phases/Phase%204/EVALUATION_ENGINE.md): Deep dive into `EvaluationEngine`, `ReliabilityEvaluator`, and `LLMJudge`.
3. [SCORING_MODEL.md](file:///Users/samriddha/Documents/Octs/Phases/Phase%204/SCORING_MODEL.md): Mathematical formulas, rubrics, weights, TrustScore calculation, and coverage rules.
4. [API_REFERENCE.md](file:///Users/samriddha/Documents/Octs/Phases/Phase%204/API_REFERENCE.md): API contracts for `POST /ask`, `GET /api/health`, response schemas, and payload examples.
5. [TESTING.md](file:///Users/samriddha/Documents/Octs/Phases/Phase%204/TESTING.md): Complete test suite breakdown, coverage, mock strategy, and 130 passing tests.
6. [IMPLEMENTATION_LOG.md](file:///Users/samriddha/Documents/Octs/Phases/Phase%204/IMPLEMENTATION_LOG.md): Chronological engineering milestones, challenges encountered, and solutions.
7. [DECISIONS.md](file:///Users/samriddha/Documents/Octs/Phases/Phase%204/DECISIONS.md): Architectural Decision Records (ADRs) for Phase 4 design choices.

---

## Quickstart & Verification
Run the complete automated test suite (144 tests across 16 test modules):
```bash
python3 -m pytest backend/tests/ -v
```

Inspect health and evaluation status via API:
```bash
curl -s http://127.0.0.1:8000/api/health | jq .
```

Submit a creative task with full quality assessment and TrustScore:
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a high-retention video hook for YouTube Shorts", "role": "creators"}' | jq .
```
