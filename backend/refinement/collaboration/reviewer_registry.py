"""
OCTS AI - Specialist Peer Reviewer Registry
Maintains domain-aligned primary and secondary peer reviewer pairings for all 16 personas.
"""

from typing import Dict, List, Optional, Tuple


class ReviewerRegistry:
    """
    Registry defining complementary specialist collaboration pairings across
    Writers, Musicians, Creators, and Designers disciplines.
    """

    # Domain-complementary pairings: {author_persona_id: (primary_reviewer, secondary_reviewer)}
    PAIRINGS: Dict[str, Tuple[str, str]] = {
        # Writers & Storytellers
        "narrative_architect": ("lore_continuity_keeper", "prose_stylist"),
        "lore_continuity_keeper": ("narrative_architect", "research_scout"),
        "prose_stylist": ("narrative_architect", "research_scout"),
        "research_scout": ("lore_continuity_keeper", "narrative_architect"),

        # Musicians & Audio Artists
        "lyricist_meter_engine": ("harmonic_arranger", "track_structure_architect"),
        "harmonic_arranger": ("sonic_palette_curator", "track_structure_architect"),
        "track_structure_architect": ("harmonic_arranger", "sonic_palette_curator"),
        "sonic_palette_curator": ("track_structure_architect", "harmonic_arranger"),

        # Creators & Multi-Platform Builders
        "hook_retention_architect": ("audience_friction_auditor", "multi_platform_transmuter"),
        "multi_platform_transmuter": ("editorial_cadence_planner", "hook_retention_architect"),
        "editorial_cadence_planner": ("audience_friction_auditor", "multi_platform_transmuter"),
        "audience_friction_auditor": ("hook_retention_architect", "editorial_cadence_planner"),

        # Designers & Visual Thinkers
        "concept_ideation_engine": ("visual_system_auditor", "art_direction_critic"),
        "visual_system_auditor": ("design_token_palette_architect", "concept_ideation_engine"),
        "art_direction_critic": ("concept_ideation_engine", "visual_system_auditor"),
        "design_token_palette_architect": ("visual_system_auditor", "art_direction_critic"),
    }

    def __init__(self, custom_pairings: Optional[Dict[str, Tuple[str, str]]] = None):
        self._pairings = dict(self.PAIRINGS)
        if custom_pairings:
            self._pairings.update(custom_pairings)

    def get_pairings(self, persona_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Returns (primary_reviewer, secondary_reviewer) for a persona."""
        return self._pairings.get(persona_id, (None, None))

    def get_primary_reviewer(self, persona_id: str) -> Optional[str]:
        """Returns the primary peer reviewer for a persona."""
        pair = self._pairings.get(persona_id)
        return pair[0] if pair else None

    def get_secondary_reviewer(self, persona_id: str) -> Optional[str]:
        """Returns the secondary peer reviewer for a persona."""
        pair = self._pairings.get(persona_id)
        return pair[1] if pair else None

    def is_valid_pairing(self, author_id: str, reviewer_id: str) -> bool:
        """Verifies reviewer is valid and not self-reviewing."""
        if not author_id or not reviewer_id:
            return False
        if author_id == reviewer_id:
            return False
        return True

    def get_all_registered_authors(self) -> List[str]:
        """Returns all 16 registered author persona identifiers."""
        return list(self._pairings.keys())
