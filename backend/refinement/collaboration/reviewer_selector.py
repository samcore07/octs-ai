"""
OCTS AI - Specialist Peer Reviewer Selector
Selects optimal peer reviewer persona based on author identity,
identified weak criteria, and recovery attempt iteration.
"""

from typing import List, Optional
from backend.refinement.collaboration.reviewer_registry import ReviewerRegistry
from backend.refinement.schemas import CriterionFeedback


class ReviewerSelector:
    """
    Intelligently selects a peer reviewer persona using domain pairings
    and rubric deficiency affinity matching.
    """

    CRITERION_AFFINITY_MAP = {
        # Writers
        "lore": "lore_continuity_keeper",
        "continuity": "lore_continuity_keeper",
        "character": "lore_continuity_keeper",
        "structure": "narrative_architect",
        "narrative": "narrative_architect",
        "pacing": "narrative_architect",
        "style": "prose_stylist",
        "tone": "prose_stylist",
        "prose": "prose_stylist",
        "research": "research_scout",
        "historical": "research_scout",

        # Musicians
        "harmony": "harmonic_arranger",
        "chord": "harmonic_arranger",
        "meter": "lyricist_meter_engine",
        "lyrics": "lyricist_meter_engine",
        "rhyme": "lyricist_meter_engine",
        "track_structure": "track_structure_architect",
        "structure_quality": "track_structure_architect",
        "timbre": "sonic_palette_curator",
        "palette": "sonic_palette_curator",
        "sonic": "sonic_palette_curator",

        # Creators
        "hook": "hook_retention_architect",
        "retention": "hook_retention_architect",
        "friction": "audience_friction_auditor",
        "clarity": "audience_friction_auditor",
        "platform": "multi_platform_transmuter",
        "transmute": "multi_platform_transmuter",
        "cadence": "editorial_cadence_planner",
        "calendar": "editorial_cadence_planner",

        # Designers
        "token": "design_token_palette_architect",
        "color": "design_token_palette_architect",
        "contrast": "design_token_palette_architect",
        "hierarchy": "visual_system_auditor",
        "grid": "visual_system_auditor",
        "alignment": "visual_system_auditor",
        "lighting": "art_direction_critic",
        "composition": "art_direction_critic",
        "concept": "concept_ideation_engine",
        "metaphor": "concept_ideation_engine",
    }

    def __init__(self, registry: Optional[ReviewerRegistry] = None):
        self.registry = registry or ReviewerRegistry()

    def select_reviewer(
        self,
        author_persona_id: str,
        weak_criteria: Optional[List[CriterionFeedback]] = None,
        attempt_number: int = 1,
    ) -> Optional[str]:
        """
        Determines the most qualified peer reviewer persona.
        Guarantees reviewer != author_persona_id.
        """
        if not author_persona_id:
            return None

        # 1. Check if a weak criterion strongly demands a specialized reviewer
        if weak_criteria:
            for item in weak_criteria:
                cid = item.criterion_id.lower()
                for keyword, target_persona in self.CRITERION_AFFINITY_MAP.items():
                    if keyword in cid and target_persona != author_persona_id:
                        return target_persona

        # 2. Iteration-based selection from registered pairings
        primary, secondary = self.registry.get_pairings(author_persona_id)

        if attempt_number > 1 and secondary:
            return secondary

        return primary or secondary
