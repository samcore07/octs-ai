"""
OCTS AI - Request Correlation Identifier Management
Generates, validates, and normalizes correlation and request IDs across API boundaries.
"""

import re
from typing import Dict, Optional
import uuid

# Valid ID pattern: alphanumeric, dashes, underscores, dots, between 4 and 64 characters
_SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{4,64}$")


def generate_request_id() -> str:
    """Generates a secure, standard UUID4 request identifier."""
    return str(uuid.uuid4())


def validate_correlation_id(candidate: Optional[str]) -> Optional[str]:
    """
    Validates and sanitizes an externally supplied correlation ID.
    Returns sanitized string if safe, otherwise None.
    """
    if not candidate or not isinstance(candidate, str):
        return None
    trimmed = candidate.strip()
    if _SAFE_ID_REGEX.match(trimmed):
        return trimmed
    return None


def resolve_request_id(headers: Optional[Dict[str, str]] = None) -> str:
    """
    Resolves request ID from request headers (X-Request-ID or X-Correlation-ID).
    Generates a new UUID4 if missing or invalid.
    """
    if not headers:
        return generate_request_id()

    # Case-insensitive header lookup
    normalized_headers = {k.lower(): v for k, v in headers.items()}

    # Check X-Request-ID first, then X-Correlation-ID
    for header_key in ("x-request-id", "x-correlation-id"):
        val = normalized_headers.get(header_key)
        valid = validate_correlation_id(val)
        if valid:
            return valid

    return generate_request_id()
