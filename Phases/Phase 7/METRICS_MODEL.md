# Phase 7 — Metrics Model & Percentile Math

## Operational Metrics Overview
OCTS AI collects metrics across six operational dimensions:
1. Request Throughput & Health
2. Graph Execution Latency (P50, P95, P99)
3. Creative Quality & TrustScore Distributions
4. Autonomous Refinement & Peer Review Efficacy
5. Persistent Memory Utilization
6. Real Model Token Usage

---

## Percentile Calculation Formulas
To avoid external dependencies on heavy analytics packages (like NumPy or SciPy), percentiles are calculated mathematically using standard linear interpolation:

For an ordered list of values $V = [v_0, v_1, \dots, v_{n-1}]$ of size $n$, the percentile position $k$ for percentile $p \in [0, 1]$ is:

$$k = (n - 1) \times p$$

Let $f = \lfloor k \rfloor$ (integer index) and $c = \min(f + 1, n - 1)$.
If $f = c$, the percentile is:

$$P(p) = v_f$$

Otherwise, linear interpolation yields:

$$P(p) = v_f \times (c - k) + v_c \times (k - f)$$

- **P50 (Median)**: $p = 0.50$
- **P95**: $p = 0.95$
- **P99**: $p = 0.99$

---

## Model Usage & Token Accounting
Token accounting strictly relies on data provided by the active model provider:
- **LangChain `usage_metadata`**: Extracted directly when available (`input_tokens`, `output_tokens`, `total_tokens`).
- **Response Metadata Fallback**: Extracted from `response_metadata["usage_metadata"]` (Google GenAI SDK schema: `prompt_token_count`, `candidates_token_count`, `total_token_count`).
- **Strict Anti-Fabrication Rule**: If token counts are not reported by the model provider (e.g. mock models during testing, offline fallbacks), the fields remain `None` (`null` in JSON). Under no circumstances are token counts or operational costs estimated or fabricated.
