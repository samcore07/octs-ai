"""
OCTS AI - Orchestration Layer Exceptions
Typed domain exceptions for the LangGraph orchestration pipeline.
"""


class OrchestrationError(Exception):
    """Base exception for all orchestration errors."""
    pass


class InputValidationError(OrchestrationError):
    """Raised when request input fails validation rules or size limits."""
    pass


class RoutingError(OrchestrationError):
    """Raised when a task cannot be routed or resolved to a valid persona."""
    pass


class PersonaPreparationError(OrchestrationError):
    """Raised when persona prompt compilation or template formatting fails."""
    pass


class ModelExecutionError(OrchestrationError):
    """Raised when the LLM provider fails during invocation."""
    pass


class OutputValidationError(OrchestrationError):
    """Raised when the LLM produces an empty, malformed, or invalid response."""
    pass
