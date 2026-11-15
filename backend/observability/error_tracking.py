"""
OCTS AI - Centralized Error Taxonomy & Classification
Maps internal runtime exceptions to stable error codes and safe client error representations.
"""

from enum import Enum
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("octs.observability.errors")


class ErrorTaxonomy(str, Enum):
    """Stable classification codes for all system and operational errors."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ROUTING_ERROR = "ROUTING_ERROR"
    MODEL_PROVIDER_ERROR = "MODEL_PROVIDER_ERROR"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    MODEL_RATE_LIMIT = "MODEL_RATE_LIMIT"
    OUTPUT_VALIDATION_ERROR = "OUTPUT_VALIDATION_ERROR"
    EVALUATION_ERROR = "EVALUATION_ERROR"
    PEER_REVIEW_ERROR = "PEER_REVIEW_ERROR"
    REFINEMENT_ERROR = "REFINEMENT_ERROR"
    MEMORY_RETRIEVAL_ERROR = "MEMORY_RETRIEVAL_ERROR"
    MEMORY_PERSISTENCE_ERROR = "MEMORY_PERSISTENCE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """
    Standard domain exception encapsulating classification, safe client message,
    and diagnostic context.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorTaxonomy = ErrorTaxonomy.INTERNAL_ERROR,
        status_code: int = 500,
        safe_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.safe_message = safe_message or "An internal error occurred while processing the request."
        self.details = details or {}
        self.original_exception = original_exception

    def to_safe_dict(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Produces a sanitized client-facing error payload without leaking stack traces."""
        return {
            "error": True,
            "error_code": self.error_code.value,
            "message": self.safe_message,
            "request_id": request_id,
            "status_code": self.status_code,
        }


def classify_exception(exc: Exception) -> ErrorTaxonomy:
    """
    Classifies arbitrary runtime exceptions into the standard ErrorTaxonomy.
    """
    if isinstance(exc, AppError):
        return exc.error_code

    exc_str = str(exc).lower()
    exc_type = type(exc).__name__.lower()

    if "timeout" in exc_str or "timed out" in exc_str or "timeouterror" in exc_type:
        return ErrorTaxonomy.MODEL_TIMEOUT

    if "rate limit" in exc_str or "429" in exc_str or "quota" in exc_str:
        return ErrorTaxonomy.MODEL_RATE_LIMIT

    if "validation" in exc_str or "valueerror" in exc_type or "pydantic" in exc_str:
        return ErrorTaxonomy.VALIDATION_ERROR

    if "sqlite" in exc_str or "operationalerror" in exc_type or "database" in exc_str or "sqlalchemy" in exc_str:
        return ErrorTaxonomy.DATABASE_ERROR

    if "model" in exc_str or "gemini" in exc_str or "api" in exc_str or "invoke" in exc_str:
        return ErrorTaxonomy.MODEL_PROVIDER_ERROR

    if "routing" in exc_str:
        return ErrorTaxonomy.ROUTING_ERROR

    if "memory" in exc_str:
        return ErrorTaxonomy.MEMORY_RETRIEVAL_ERROR

    return ErrorTaxonomy.INTERNAL_ERROR


def build_safe_error_response(
    exc: Exception,
    request_id: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Builds a secure, consistent HTTP error response. Stack traces are never leaked in production.
    """
    if isinstance(exc, AppError):
        payload = exc.to_safe_dict(request_id=request_id)
        if debug:
            payload["debug_message"] = exc.message
        return payload

    classified_code = classify_exception(exc)
    status_code = 500

    if classified_code == ErrorTaxonomy.VALIDATION_ERROR:
        status_code = 422
        safe_msg = "Request validation failed. Please check your parameters."
    elif classified_code == ErrorTaxonomy.MODEL_RATE_LIMIT:
        status_code = 429
        safe_msg = "AI model rate limit exceeded. Please retry momentarily."
    elif classified_code == ErrorTaxonomy.MODEL_TIMEOUT:
        status_code = 504
        safe_msg = "Upstream AI model provider request timed out."
    elif classified_code == ErrorTaxonomy.ROUTING_ERROR:
        status_code = 400
        safe_msg = "Unable to route request to a valid specialist persona."
    else:
        status_code = 500
        safe_msg = "A server error occurred while executing the creative harness."

    payload = {
        "error": True,
        "error_code": classified_code.value,
        "message": safe_msg,
        "request_id": request_id,
        "status_code": status_code,
    }

    if debug:
        payload["debug_message"] = str(exc)
        payload["exception_type"] = type(exc).__name__

    return payload
