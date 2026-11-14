"""
OCTS AI - Discipline Configurations
Exports all 4 creative discipline configurations.
"""

from backend.agents.disciplines.writers import writers_discipline
from backend.agents.disciplines.musicians import musicians_discipline
from backend.agents.disciplines.creators import creators_discipline
from backend.agents.disciplines.designers import designers_discipline

__all__ = [
    "writers_discipline",
    "musicians_discipline",
    "creators_discipline",
    "designers_discipline",
]
