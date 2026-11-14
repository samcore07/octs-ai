"""
OCTS AI - Agent Routing Package
Exports AgentRouter and deterministic rule helpers.
"""

from backend.agents.routing.classifier import AgentRouter
from backend.agents.routing.rules import (
    DEFAULT_PERSONAS,
    TASK_TYPE_MAPPING,
    score_prompt_for_discipline,
)

__all__ = [
    "AgentRouter",
    "DEFAULT_PERSONAS",
    "TASK_TYPE_MAPPING",
    "score_prompt_for_discipline",
]
