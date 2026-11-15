# OCTS AI — Phase 4: Scoring Model & TrustScore

## 1. Overview of Scoring Formulas

OCTS AI evaluates executions across two distinct dimensions, combining them into a single composite **TrustScore** while preserving the underlying component scores.

$$\text{TrustScore} = (\text{Quality Score} \times W_Q) + (\text{Reliability Score} \times W_R)$$

* **Default Quality Weight ($W_Q$):** $0.70$ (70%)
* **Default Reliability Weight ($W_R$):** $0.30$ (30%)
* **Scale:** Normalized to $0.0 - 100.0$
* **Weight Invariants:** $W_Q \ge 0, W_R \ge 0$, and $(W_Q + W_R) > 0$. Weights are normalized to sum to $1.0$.

---

## 2. Dimension A: Quality Score & Criterion Statuses

The Quality Score measures adherence to discipline-specific craft standards.

### Criterion Statuses
Every criterion is assigned an explicit evaluation status:
- **`PASSED`:** Evaluated and satisfactory ($\text{score} \ge 70.0$).
- **`FAILED`:** Evaluated and unsatisfactory ($\text{score} < 70.0$, including an actual evaluated score of $0.0$).
- **`SKIPPED`:** Intentionally not evaluated (e.g. not applicable to the current task).
- **`UNAVAILABLE`:** Could not be evaluated or omitted by the evaluator/judge.

### Mathematical Formula & Re-normalization
Criteria with status `SKIPPED` or `UNAVAILABLE` have `score = None` and `weighted_score = None`. Their weights are **strictly excluded from the active denominator**.

$$\text{Quality Score} = \frac{\sum_{i \in \text{Active}} (\text{Score}_i \times \text{Weight}_i)}{\sum_{i \in \text{Active}} \text{Weight}_i}$$

* $\text{Active} = \{i \mid \text{Status}_i \in \{\text{PASSED}, \text{FAILED}\} \land \text{Score}_i \neq \text{None}\}$
* If all criteria are `UNAVAILABLE` or `SKIPPED` ($\sum_{i \in \text{Active}} \text{Weight}_i = 0$), then $\text{Quality Score} = \text{None}$.

### Evaluation Coverage
Coverage explicitly tracks the fraction of total rubric criteria that were successfully evaluated:

$$\text{Evaluation Coverage} = \frac{N_{\text{evaluated}}}{N_{\text{total}}} \times 100\% = \frac{N_{\text{total}} - N_{\text{skipped}} - N_{\text{unavailable}}}{N_{\text{total}}} \times 100\%$$

* Consistently calculated across all four disciplines (6 criteria for writers, 7 for musicians, creators, and designers).

---

## 3. Dimension B: Reliability Score Calculation

The Reliability Score evaluates technical execution health and pipeline invariants. Deductions are calculated from unique, deduplicated checks:

$$\text{Reliability Score} = \max\left(0.0, 100.0 - (40.0 \times F_{\text{critical}}) - (10.0 \times F_{\text{warning}})\right)$$

| Severity | Deduction | Check Types |
| :--- | :--- | :--- |
| **CRITICAL** | $40.0$ pts | `output_exists`, `output_not_empty`, `persona_resolved`, `execution_successful` |
| **WARNING** | $10.0$ pts | `persona_discipline_match`, `substantive_length` ($\ge 25$ chars) |
| **INFO** | $0.0$ pts | `latency_recorded` (Informational only; never reduces reliability score) |

### Invariants:
1. **Deduplication:** Duplicate checks with the same `check_id` are ignored and never cause duplicate deductions.
2. **Skipped/Unavailable:** Checks marked `SKIPPED` or `UNAVAILABLE` do not count as passes.
3. **No Evaluation:** If no checks were evaluated (e.g. clarification flow), $\text{Reliability Score} = \text{None}$.

---

## 4. TrustScore Validation Table

| Quality Score | Reliability Score | TrustScore | Explanation |
|---:|---:|---:|:--- |
| **90.0** | **100.0** | **93.00** | $(90.0 \times 0.70) + (100.0 \times 0.30) = 63.0 + 30.0 = 93.0$ |
| **80.0** | **90.0** | **83.00** | $(80.0 \times 0.70) + (90.0 \times 0.30) = 56.0 + 27.0 = 83.0$ |
| **None** | **100.0** | **None** | Missing Quality dimension (e.g. clarification or failure). |
| **90.0** | **None** | **None** | Missing Reliability dimension. |
| **None** | **None** | **None** | Evaluation skipped or disabled. |

---

## 5. Concrete Worked Examples

### Example 1: Specification Example (One Unavailable Criterion)
* Criterion A: Weight = $0.33$, Score = $80.0$, Status = `PASSED`
* Criterion B: Weight = $0.33$, Score = $90.0$, Status = `PASSED`
* Criterion C: Weight = $0.34$, Score = `None`, Status = `UNAVAILABLE`
* **Calculation:**
  $$\text{Active Weight} = 0.33 + 0.33 = 0.66$$
  $$\text{Weighted Sum} = (80.0 \times 0.33) + (90.0 \times 0.33) = 26.4 + 29.7 = 56.1$$
  $$\text{Quality Score} = \frac{56.1}{0.66} = \mathbf{85.00}$$
  $$\text{Evaluation Coverage} = \frac{2}{3} = \mathbf{66.67\%}$$
* *Note: The score is correctly $85.00$, NOT $56.67$ (which would occur if C were incorrectly treated as zero).*

### Example 2: Actual Evaluated Zero vs Unavailable
* Criterion A: Weight = $0.50$, Score = $80.0$, Status = `PASSED`
* Criterion B: Weight = $0.50$, Score = $0.0$, Status = `FAILED`
* **Calculation:**
  $$\text{Active Weight} = 0.50 + 0.50 = 1.00$$
  $$\text{Quality Score} = (80.0 \times 0.50) + (0.0 \times 0.50) = \mathbf{40.00}$$
  $$\text{Evaluation Coverage} = \mathbf{100.0\%}$$

### Example 3: Clarification Path (Case C)
* `needs_clarification = True`
* `evaluation_status = "skipped"`
* $\text{Quality Score} = \text{None}$, $\text{Reliability Score} = \text{None}$, $\text{TrustScore} = \text{None}$.
* Reliability checks list is empty `[]` (no fabricated checks).
