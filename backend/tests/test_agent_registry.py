"""
OCTS AI - Agent Registry Unit Tests
Verifies persona registration, uniqueness, lookup mechanics, and error tolerance.
"""

import pytest
from backend.agents.registry import AgentRegistry, get_registry


@pytest.fixture
def registry():
    return get_registry()


ALL_16_PERSONAS = [
    # Writers
    "narrative_architect",
    "lore_continuity_keeper",
    "prose_stylist",
    "research_scout",
    # Musicians
    "lyricist_meter_engine",
    "harmonic_arranger",
    "track_structure_architect",
    "sonic_palette_curator",
    # Creators
    "hook_retention_architect",
    "multi_platform_transmuter",
    "editorial_cadence_planner",
    "audience_friction_auditor",
    # Designers
    "concept_ideation_engine",
    "visual_system_auditor",
    "art_direction_critic",
    "design_token_palette_architect",
]


def test_registry_contains_16_personas(registry):
    """Verify exactly 16 specialist personas are registered."""
    personas = registry.list_personas()
    assert len(personas) == 16


def test_unique_persona_identifiers(registry):
    """Verify that all 16 persona IDs are unique and snake_case."""
    personas = registry.list_personas()
    ids = [p.id for p in personas]
    assert len(ids) == len(set(ids)) == 16
    for pid in ids:
        assert pid.islower()
        assert " " not in pid
        assert pid in ALL_16_PERSONAS


def test_persona_lookup_by_id(registry):
    """Verify lookup by ID, including whitespace and case normalization."""
    for pid in ALL_16_PERSONAS:
        persona = registry.get_persona(pid)
        assert persona is not None
        assert persona.id == pid
        # Test case/whitespace tolerance
        assert registry.get_persona(f"  {pid.upper()}  ") == persona


def test_filter_personas_by_discipline(registry):
    """Verify filtering personas by discipline returns exactly 4 personas per discipline."""
    for disc_id in ["writers", "musicians", "creators", "designers"]:
        discipline_personas = registry.get_personas_for_discipline(disc_id)
        assert len(discipline_personas) == 4
        for p in discipline_personas:
            assert p.discipline_id == disc_id


def test_unknown_persona_lookup(registry):
    """Verify non-existent persona lookup returns None without error."""
    assert registry.get_persona("non_existent_persona") is None
    assert registry.get_persona("") is None


def test_unknown_discipline_lookup(registry):
    """Verify non-existent discipline lookup returns None without error."""
    assert registry.get_discipline("unknown_discipline") is None
