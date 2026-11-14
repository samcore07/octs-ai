"""
OCTS AI - Central Agent Registry
Singleton registry managing the 4 creative disciplines and 16 specialist agent personas.
"""

from typing import Dict, List, Optional
from backend.agents.base import DisciplineConfig, PersonaDefinition


class AgentRegistry:
    """Central store for disciplines and specialized personas."""

    def __init__(self):
        self._disciplines: Dict[str, DisciplineConfig] = {}
        self._personas: Dict[str, PersonaDefinition] = {}

    def register_discipline(self, discipline: DisciplineConfig) -> None:
        """Registers a discipline configuration."""
        if discipline.id in self._disciplines:
            # Idempotent registration
            self._disciplines[discipline.id] = discipline
            return
        self._disciplines[discipline.id] = discipline

    def register_persona(self, persona: PersonaDefinition) -> None:
        """Registers a persona definition."""
        self._personas[persona.id] = persona

    def get_discipline(self, discipline_id: str) -> Optional[DisciplineConfig]:
        """Retrieves a discipline configuration by ID."""
        return self._disciplines.get(discipline_id.lower().strip())

    def get_persona(self, persona_id: str) -> Optional[PersonaDefinition]:
        """Retrieves a persona definition by ID."""
        return self._personas.get(persona_id.lower().strip())

    def list_disciplines(self) -> List[DisciplineConfig]:
        """Lists all registered disciplines."""
        return list(self._disciplines.values())

    def list_personas(self, discipline_id: Optional[str] = None) -> List[PersonaDefinition]:
        """Lists registered personas, optionally filtered by discipline ID."""
        if discipline_id:
            normalized = discipline_id.lower().strip()
            return [p for p in self._personas.values() if p.discipline_id == normalized]
        return list(self._personas.values())

    def get_personas_for_discipline(self, discipline_id: str) -> List[PersonaDefinition]:
        """Convenience method to retrieve personas for a specific discipline."""
        return self.list_personas(discipline_id)


_GLOBAL_REGISTRY: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Returns the initialized global AgentRegistry singleton."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = AgentRegistry()
        _initialize_registry(_GLOBAL_REGISTRY)
    return _GLOBAL_REGISTRY


def _initialize_registry(registry: AgentRegistry) -> None:
    """
    Imports and registers all 4 disciplines and 16 specialist personas.
    Ensures zero duplicate or circular import side-effects.
    """
    # Import and register Personas
    from backend.agents.personas.narrative_architect import narrative_architect
    from backend.agents.personas.lore_continuity_keeper import lore_continuity_keeper
    from backend.agents.personas.prose_stylist import prose_stylist
    from backend.agents.personas.research_scout import research_scout

    from backend.agents.personas.lyricist_meter_engine import lyricist_meter_engine
    from backend.agents.personas.harmonic_arranger import harmonic_arranger
    from backend.agents.personas.track_structure_architect import track_structure_architect
    from backend.agents.personas.sonic_palette_curator import sonic_palette_curator

    from backend.agents.personas.hook_retention_architect import hook_retention_architect
    from backend.agents.personas.multi_platform_transmuter import multi_platform_transmuter
    from backend.agents.personas.editorial_cadence_planner import editorial_cadence_planner
    from backend.agents.personas.audience_friction_auditor import audience_friction_auditor

    from backend.agents.personas.concept_ideation_engine import concept_ideation_engine
    from backend.agents.personas.visual_system_auditor import visual_system_auditor
    from backend.agents.personas.art_direction_critic import art_direction_critic
    from backend.agents.personas.design_token_palette_architect import design_token_palette_architect

    all_personas = [
        narrative_architect,
        lore_continuity_keeper,
        prose_stylist,
        research_scout,
        lyricist_meter_engine,
        harmonic_arranger,
        track_structure_architect,
        sonic_palette_curator,
        hook_retention_architect,
        multi_platform_transmuter,
        editorial_cadence_planner,
        audience_friction_auditor,
        concept_ideation_engine,
        visual_system_auditor,
        art_direction_critic,
        design_token_palette_architect,
    ]

    for p in all_personas:
        registry.register_persona(p)

    # Import and register Disciplines
    from backend.agents.disciplines.writers import writers_discipline
    from backend.agents.disciplines.musicians import musicians_discipline
    from backend.agents.disciplines.creators import creators_discipline
    from backend.agents.disciplines.designers import designers_discipline

    all_disciplines = [
        writers_discipline,
        musicians_discipline,
        creators_discipline,
        designers_discipline,
    ]

    for d in all_disciplines:
        registry.register_discipline(d)
