# OCTS AI — Phase 5: Multi-Dimensional Improvement Analysis & Regression Reversion

## 1. Overview
In multi-turn autonomous refinement, a naive selection policy assuming $\Delta\text{Quality} > 0$ is inherently dangerous for production systems. A candidate may gain $+2.0$ points in prose flow while failing a critical reliability check, dropping execution reliability by $-40$ points, losing evaluation coverage, or severely regressing on explicit prompt constraints.

OCTS AI Phase 5 implements a robust, **multi-dimensional candidate evaluation policy** that assesses Quality, Execution Reliability, Rubric Coverage, and composite TrustScore before accepting a candidate as the winning artifact.

---

## 2. Multi-Dimensional Selection Architecture

```
                       [Candidate Evaluation]
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [Critical Checks]                [Instruction Adherence]
   (Did any critical check fail        (Did prompt adherence drop
    or reliability drop > 25 pts?)       more than 15.0 points?)
                 │                               │
            YES ──► REJECT                  YES ──► REJECT
                 │                               │
                 └─── NO ────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [Evaluation Coverage]            [Composite TrustScore]
     (Did coverage drop > 25%?        (Did TrustScore gain > 0.05
      Or partial -> comprehensive?)     with stable reliability?)
                 │                               │
            YES ──► REJECT / ACCEPT         YES ──► ACCEPT
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                    [Standard Quality Comparison]
                 (Quality gain + stable reliability
                   + positive criterion balance)
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
                 ACCEPT                    REJECT
            (New Best Artifact)     (Revert to Baseline)
```

---

## 3. Strict Deterministic Policy Rules

The `ImprovementAnalyzer` evaluates candidates through the following sequential criteria:

### Rule 1: Missing or Failed Evaluation Guard
If either the candidate evaluation or previous evaluation is unavailable or un-scorable:
- Candidate is **rejected**.
- Selection Reason: `"Candidate evaluation failed or produced no valid quality score; preserved previous best."`

### Rule 2: Critical Execution Reliability Check Guard
If candidate introduced a critical execution failure ($N_{\text{crit\_cand}} > N_{\text{crit\_prev}}$), or candidate reliability score dropped by more than $25.0$ points:
- Candidate is **strictly rejected**, regardless of Quality Score.
- `critical_regression_detected = True`
- Selection Reason: `"Candidate suffered a critical execution reliability check failure... preserved previous best despite quality score."`

### Rule 3: Instruction Adherence Regression Guard
Even when overall quality score rises, if `instruction_adherence` dropped by $> 15.0$ points:
- Candidate is **rejected** to prevent persona drift or failure to satisfy core user constraints.
- `critical_regression_detected = True`
- Selection Reason: `"Candidate instruction adherence regressed significantly... preserved previous best."`

### Rule 4: Coverage Delta Handling
Evaluation coverage ($C \in [0.0, 1.0]$) represents rubric completeness:
- **Comprehensive Promotion:** If previous coverage was partial ($C_{\text{prev}} < 0.60$) and candidate coverage is comprehensive ($C_{\text{cand}} \ge 0.85$) with comparable quality ($\text{Quality}_{\text{cand}} \ge \text{Quality}_{\text{prev}} - 5.0$): Candidate is **accepted**.
- **Coverage Regression Guard:** If candidate coverage dropped by more than $0.25$ ($C_{\text{cand}} < C_{\text{prev}} - 0.25$): Candidate is **rejected**.

### Rule 5: TrustScore Dominance
When both candidate and previous best possess valid composite TrustScores and candidate reliability is stable ($\Delta\text{Reliability} \ge -10.0$):
- If $\Delta\text{Trust} > 0.05$: Candidate is **accepted**.
- If $\Delta\text{Trust} < -0.05$: Candidate is **rejected**.

### Rule 6: Primary Quality Gain with Reliability Stability
When TrustScore is equal or unavailable:
- If $\Delta\text{Quality} > 0.05$ AND $\Delta\text{Reliability} \ge -10.0$: Candidate is **accepted**.
- If $\Delta\text{Quality} < -0.05$: Candidate is **rejected**.

### Rule 7: Criteria Count Tie-Breaking
When Quality, Reliability, and TrustScores are within $[ -0.05, +0.05 ]$:
- If $|\text{Improved Criteria}| > |\text{Regressed Criteria}|$: Candidate is **accepted**.
- Otherwise: Candidate is **rejected** and baseline is preserved.

---

## 4. Regression Reversion Invariant

Whenever a candidate is rejected:
1. `best_output` retains the previous best text verbatim.
2. `best_evaluation` retains the previous best evaluation result verbatim.
3. `best_output_selected` retains the previous winning iteration identifier (`"initial"`, `"attempt_1"`, etc.).
4. `refinement_status = "regressed_reverted"`.
5. The rejection reason, deltas, and movement counts are logged in an immutable `ImprovementRecord`.

---

## 5. Telemetry Schema (`ImprovementRecord`)

```json
{
  "attempt_number": 1,
  "selection_reason": "Candidate demonstrated composite TrustScore improvement (+8.9 pts: 80.8 -> 89.7).",
  "candidate_accepted": true,
  "is_improvement": true,
  "previous_best_score": 80.83,
  "candidate_score": 89.74,
  "previous_quality_score": 76.9,
  "new_quality_score": 85.35,
  "quality_delta": 8.45,
  "previous_reliability_score": 90.0,
  "new_reliability_score": 100.0,
  "reliability_delta": 10.0,
  "previous_coverage": 1.0,
  "new_coverage": 1.0,
  "coverage_delta": 0.0,
  "previous_trust_score": 80.83,
  "new_trust_score": 89.74,
  "trust_delta": 8.91,
  "improved_criteria": ["instruction_adherence", "narrative_coherence", "structural_quality"],
  "regressed_criteria": [],
  "unchanged_criteria": ["character_consistency", "originality_creativity", "style_tone_consistency"],
  "critical_regression_detected": false,
  "rationale": "Candidate demonstrated composite TrustScore improvement (+8.9 pts: 80.8 -> 89.7)."
}
```
