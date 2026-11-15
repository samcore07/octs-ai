"""
OCTS AI - Metrics Collector & Percentile Calculations
Provides mathematical aggregation, latency distribution percentiles, and provider token usage extraction.
Guarantees that missing data is never fabricated.
"""

from typing import Any, Dict, List, Optional, Tuple


def calculate_percentiles(values: List[float]) -> Tuple[float, float, float]:
    """
    Computes (P50, P95, P99) latency percentiles from a list of numerical values.
    Returns (0.0, 0.0, 0.0) if empty.
    """
    if not values:
        return 0.0, 0.0, 0.0

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 1:
        v = round(float(sorted_vals[0]), 2)
        return v, v, v

    def _get_p(p: float) -> float:
        k = (n - 1) * p
        f = int(k)
        c = min(f + 1, n - 1)
        if f == c:
            return round(float(sorted_vals[f]), 2)
        d0 = sorted_vals[f] * (c - k)
        d1 = sorted_vals[c] * (k - f)
        return round(float(d0 + d1), 2)

    return _get_p(0.50), _get_p(0.95), _get_p(0.99)


def extract_model_usage(response: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Safely extracts real prompt_tokens, completion_tokens, and total_tokens from an LLM response.
    Never fabricates values; returns (None, None, None) if provider metadata is absent.
    """
    if response is None:
        return None, None, None

    # Check LangChain usage_metadata attribute
    usage = getattr(response, "usage_metadata", None)
    if isinstance(usage, dict):
        p = usage.get("input_tokens") or usage.get("prompt_tokens")
        c = usage.get("output_tokens") or usage.get("completion_tokens")
        t = usage.get("total_tokens") or ((p + c) if (p is not None and c is not None) else None)
        return p, c, t

    # Check response_metadata dict
    resp_meta = getattr(response, "response_metadata", None)
    if isinstance(resp_meta, dict):
        token_usage = resp_meta.get("token_usage") or resp_meta.get("usage_metadata") or resp_meta.get("usage")
        if isinstance(token_usage, dict):
            p = token_usage.get("prompt_token_count") or token_usage.get("prompt_tokens") or token_usage.get("input_tokens")
            c = token_usage.get("candidates_token_count") or token_usage.get("completion_tokens") or token_usage.get("output_tokens")
            t = token_usage.get("total_token_count") or token_usage.get("total_tokens") or ((p + c) if (p is not None and c is not None) else None)
            return p, c, t

    return None, None, None
