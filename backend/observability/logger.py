"""
OCTS AI - Structured Logging & Secret Redaction
Provides structured JSON logging with contextvar injection and automatic credential scrubbing.
Guarantees that logging failures never interrupt application execution.
"""

from datetime import datetime, timezone
import json
import logging
import os
import re
from typing import Any, Dict

from backend.observability.context import get_context_dict

# Regexes for scrubbing secrets in log payloads
_SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"),
    re.compile(r"(?i)(password|passwd|secret)\s*[:=]\s*\S+"),
]

# Sensitive dictionary keys to redact
_SENSITIVE_KEYS = {
    "api_key", "gemini_api_key", "langsmith_api_key", "password", "secret",
    "token", "authorization", "x-api-key", "access_token",
}


def sanitize_data(data: Any) -> Any:
    """Recursively redacts secrets and sensitive keys from log payloads."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if str(k).lower() in _SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_data(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, str):
        cleaned = data
        for pat in _SECRET_PATTERNS:
            cleaned = pat.sub("[REDACTED_SECRET]", cleaned)
        return cleaned
    return data


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured JSON entries with request context."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = get_context_dict()
        msg = record.getMessage()

        # Sanitize text
        for pat in _SECRET_PATTERNS:
            msg = pat.sub("[REDACTED_SECRET]", msg)

        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": msg,
            "request_id": ctx.get("request_id"),
            "correlation_id": ctx.get("correlation_id"),
            "discipline": ctx.get("discipline"),
            "persona": ctx.get("persona"),
        }

        # Include structured extra fields if provided
        if hasattr(record, "structured_data") and isinstance(record.structured_data, dict):
            log_entry["data"] = sanitize_data(record.structured_data)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_observability_logging(
    level: Any = "INFO",
    json_format: bool = True,
) -> None:
    """
    Configures root logging with structured JSON formatting and secret scrubbing.
    Accepts a log level string, or a Settings configuration instance.
    """
    if hasattr(level, "log_level"):
        lvl_str = getattr(level, "log_level", "INFO")
    elif isinstance(level, str):
        lvl_str = level
    else:
        lvl_str = "INFO"

    root_logger = logging.getLogger("octs")
    root_logger.setLevel(getattr(logging, lvl_str.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler()
    if json_format:
        stream_handler.setFormatter(StructuredJSONFormatter())
    else:
        fmt = "%(asctime)s [%(levelname)s] [req_id=%(request_id)s] %(name)s: %(message)s"
        stream_handler.setFormatter(logging.Formatter(fmt))

    root_logger.addHandler(stream_handler)
