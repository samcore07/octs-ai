"""
OCTS AI - Agent Persona & Discipline Layer (Phase 2)
Provides unified models, central registry, 4 disciplines, 16 specialist personas, and task routing.
"""

from backend.agents.base import DisciplineConfig, ModelConfig, PersonaDefinition, RoutingResult
from backend.agents.registry import AgentRegistry, get_registry

__all__ = [
    "DisciplineConfig",
    "ModelConfig",
    "PersonaDefinition",
    "RoutingResult",
    "AgentRegistry",
    "get_registry",
]
