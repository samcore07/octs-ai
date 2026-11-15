"""
OCTS AI - Request Context Management
Provides thread-safe and async-safe request context propagation using Python contextvars.
Guarantees zero cross-request contamination in concurrent environments.
"""

from contextvars import ContextVar
import os
from typing import Any, Dict, Optional

_REQUEST_ID_CTX: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_CORRELATION_ID_CTX: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_DISCIPLINE_CTX: ContextVar[Optional[str]] = ContextVar("discipline", default=None)
_PERSONA_CTX: ContextVar[Optional[str]] = ContextVar("persona", default=None)
_OWNER_ID_CTX: ContextVar[Optional[str]] = ContextVar("owner_id", default=None)


def set_request_context(
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    discipline: Optional[str] = None,
    persona: Optional[str] = None,
    owner_id: Optional[str] = None,
) -> None:
    """Sets the active request context for the current async task / thread execution."""
    if request_id is not None:
        _REQUEST_ID_CTX.set(request_id)
    if correlation_id is not None:
        _CORRELATION_ID_CTX.set(correlation_id)
    if discipline is not None:
        _DISCIPLINE_CTX.set(discipline)
    if persona is not None:
        _PERSONA_CTX.set(persona)
    if owner_id is not None:
        _OWNER_ID_CTX.set(owner_id)


def get_request_id() -> Optional[str]:
    """Returns the current request ID from context or None."""
    return _REQUEST_ID_CTX.get()


def get_correlation_id() -> Optional[str]:
    """Returns the current correlation ID from context or falls back to request_id."""
    return _CORRELATION_ID_CTX.get() or _REQUEST_ID_CTX.get()


def get_discipline() -> Optional[str]:
    """Returns the active discipline from context."""
    return _DISCIPLINE_CTX.get()


def get_persona() -> Optional[str]:
    """Returns the active specialist persona from context."""
    return _PERSONA_CTX.get()


def get_owner_id() -> Optional[str]:
    """Returns the active caller owner ID from context."""
    return _OWNER_ID_CTX.get()


def get_context_dict() -> Dict[str, Any]:
    """Returns a dictionary snapshot of current request context for logging and telemetry."""
    return {
        "request_id": get_request_id(),
        "correlation_id": get_correlation_id(),
        "discipline": get_discipline(),
        "persona": get_persona(),
        "owner_id": get_owner_id(),
    }


def clear_request_context() -> None:
    """Resets all context variables to None."""
    _REQUEST_ID_CTX.set(None)
    _CORRELATION_ID_CTX.set(None)
    _DISCIPLINE_CTX.set(None)
    _PERSONA_CTX.set(None)
    _OWNER_ID_CTX.set(None)
