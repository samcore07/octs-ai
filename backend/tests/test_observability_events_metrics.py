"""
Unit Tests for Execution Events, Metrics & Percentile Calculations
Verifies event emission, rolling buffer bounds, percentile math, and safe token usage extraction.
"""

from unittest.mock import MagicMock
import pytest

from backend.observability.collector import TelemetryCollector
from backend.observability.events import ExecutionEvent, ExecutionEventType
from backend.observability.metrics import calculate_percentiles, extract_model_usage


def test_percentile_calculations():
    """Verify P50, P95, and P99 latency percentiles across edge cases."""
    # 1. Empty list
    assert calculate_percentiles([]) == (0.0, 0.0, 0.0)

    # 2. Single value
    assert calculate_percentiles([150.0]) == (150.0, 150.0, 150.0)

    # 3. Known distribution [10, 20, 30, ... 1000]
    latencies = [10.0 * i for i in range(1, 101)]
    p50, p95, p99 = calculate_percentiles(latencies)

    assert p50 == pytest.approx(505.0, 1.0)
    assert p95 == pytest.approx(950.5, 1.0)
    assert p99 == pytest.approx(990.1, 1.0)


def test_extract_model_usage_langchain_object():
    """Verify extract_model_usage extracts real provider usage when present."""
    mock_resp = MagicMock()
    mock_resp.usage_metadata = {
        "input_tokens": 120,
        "output_tokens": 350,
        "total_tokens": 470,
    }

    p_tokens, c_tokens, t_tokens = extract_model_usage(mock_resp)
    assert p_tokens == 120
    assert c_tokens == 350
    assert t_tokens == 470


def test_extract_model_usage_response_metadata_fallback():
    """Verify extract_model_usage falls back to response_metadata['usage_metadata']."""
    mock_resp = MagicMock()
    mock_resp.usage_metadata = None
    mock_resp.response_metadata = {
        "usage_metadata": {
            "prompt_token_count": 80,
            "candidates_token_count": 210,
            "total_token_count": 290,
        }
    }

    p_tokens, c_tokens, t_tokens = extract_model_usage(mock_resp)
    assert p_tokens == 80
    assert c_tokens == 210
    assert t_tokens == 290


def test_extract_model_usage_never_fabricates_when_absent():
    """Verify extract_model_usage returns None rather than inventing tokens."""
    mock_resp = MagicMock()
    mock_resp.usage_metadata = None
    mock_resp.response_metadata = {}

    p_tokens, c_tokens, t_tokens = extract_model_usage(mock_resp)
    assert p_tokens is None
    assert c_tokens is None
    assert t_tokens is None


def test_telemetry_collector_buffer_bounds():
    """Verify TelemetryCollector enforces maximum rolling buffer capacity."""
    collector = TelemetryCollector(store=None, max_recent_events=10)

    for i in range(25):
        collector.emit_event(
            event_name=ExecutionEventType.REQUEST_STARTED,
            component="test_runner",
            request_id=f"req-{i}",
            metadata={"index": i},
        )

    # Buffer must be bounded to max_recent_events
    buffered = collector.get_recent_events(limit=50)
    assert len(buffered) == 10
    # Most recent event is index 24
    assert buffered[0]["metadata"]["index"] == 24
