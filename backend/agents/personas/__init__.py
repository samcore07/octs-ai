"""
OCTS AI - Specialist Personas Package
Exports all 16 specialist agent personas across the 4 disciplines.
"""

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

__all__ = [
    "narrative_architect",
    "lore_continuity_keeper",
    "prose_stylist",
    "research_scout",
    "lyricist_meter_engine",
    "harmonic_arranger",
    "track_structure_architect",
    "sonic_palette_curator",
    "hook_retention_architect",
    "multi_platform_transmuter",
    "editorial_cadence_planner",
    "audience_friction_auditor",
    "concept_ideation_engine",
    "visual_system_auditor",
    "art_direction_critic",
    "design_token_palette_architect",
]
