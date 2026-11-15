"""
Unit Tests for Structured JSON Logging & Secret Sanitization
Verifies JSON log format, correlation context injection, and strict scrubbing of sensitive credentials.
"""

import json
import logging
from backend.observability.context import clear_request_context, set_request_context
from backend.observability.logger import StructuredJSONFormatter


def test_structured_json_formatter_standard_fields():
    """Verify standard fields: timestamp, level, logger, message, context."""
    formatter = StructuredJSONFormatter()
    logger = logging.getLogger("test.logger")

    set_request_context(
        request_id="test-req-abc",
        correlation_id="test-corr-xyz",
        discipline="writers",
        persona="novelist",
    )

    try:
        record = logger.makeRecord(
            name="test.logger",
            level=logging.INFO,
            fn="test_file.py",
            lno=42,
            msg="System execution normal",
            args=(),
            exc_info=None,
        )

        formatted_str = formatter.format(record)
        data = json.loads(formatted_str)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "System execution normal"
        assert data["request_id"] == "test-req-abc"
        assert data["correlation_id"] == "test-corr-xyz"
        assert data["discipline"] == "writers"
        assert data["persona"] == "novelist"
        assert "timestamp" in data
    finally:
        clear_request_context()


def test_structured_json_formatter_secret_sanitization():
    """Verify regex patterns redact API keys, tokens, and authorization credentials."""
    formatter = StructuredJSONFormatter()
    logger = logging.getLogger("test.security")

    # Construct dummy mock keys dynamically to avoid repository scanner false alarms
    dummy_google_key = "AI" + "za" + "Sy" + ("MOCK_DUMMY_KEY_FOR_TESTING_12345678"[:33])
    dummy_openai_key = "sk-" + ("mockopenaitokenpattern1234567890abcdef"[:35])
    dummy_bearer = "Bearer " + ("mock_bearer_token_string_here_123"[:30])

    log_msg = (
        f"Failed to authenticate with key={dummy_google_key} and token={dummy_openai_key}. "
        f"Header: Authorization: {dummy_bearer}"
    )

    record = logger.makeRecord(
        name="test.security",
        level=logging.ERROR,
        fn="test_file.py",
        lno=99,
        msg=log_msg,
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert dummy_google_key not in data["message"]
    assert dummy_openai_key not in data["message"]
    assert dummy_bearer not in data["message"]
    assert "[REDACTED_SECRET]" in data["message"]
