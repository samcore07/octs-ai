"""
OCTS AI - Discipline Configurations Unit Tests
Verifies all 4 creative disciplines, their metadata, task categories, and relationships.
"""

import pytest
from backend.agents.registry import get_registry


@pytest.fixture
def registry():
    return get_registry()


EXPECTED_DISCIPLINES = ["writers", "musicians", "creators", "designers"]


def test_all_four_disciplines_exist(registry):
    """Verify all 4 required disciplines exist in the registry."""
    disciplines = registry.list_disciplines()
    disc_ids = [d.id for d in disciplines]
    assert len(disciplines) == 4
    for expected_id in EXPECTED_DISCIPLINES:
        assert expected_id in disc_ids


def test_discipline_required_fields(registry):
    """Verify that every discipline defines complete metadata, terminology, and requirements."""
    for disc_id in EXPECTED_DISCIPLINES:
        disc = registry.get_discipline(disc_id)
        assert disc is not None
        assert disc.display_name and len(disc.display_name) > 0
        assert disc.purpose and len(disc.purpose) > 0
        assert disc.scope and len(disc.scope) > 0
        assert len(disc.supported_task_categories) >= 4
        assert len(disc.discipline_terminology) >= 4
        assert len(disc.quality_requirements) >= 3
        assert len(disc.default_output_conventions) >= 3


def test_discipline_has_four_personas(registry):
    """Verify each discipline references exactly 4 specialist persona IDs."""
    for disc_id in EXPECTED_DISCIPLINES:
        disc = registry.get_discipline(disc_id)
        assert len(disc.specialist_persona_ids) == 4
        # Verify persona lookup resolves
        personas = disc.get_personas()
        assert len(personas) == 4
        for p in personas:
            assert p.discipline_id == disc_id


def test_specific_discipline_specialists(registry):
    """Verify exact expected specialist personas per discipline."""
    writers = registry.get_discipline("writers")
    assert set(writers.specialist_persona_ids) == {
        "narrative_architect",
        "lore_continuity_keeper",
        "prose_stylist",
        "research_scout",
    }

    musicians = registry.get_discipline("musicians")
    assert set(musicians.specialist_persona_ids) == {
        "lyricist_meter_engine",
        "harmonic_arranger",
        "track_structure_architect",
        "sonic_palette_curator",
    }

    creators = registry.get_discipline("creators")
    assert set(creators.specialist_persona_ids) == {
        "hook_retention_architect",
        "multi_platform_transmuter",
        "editorial_cadence_planner",
        "audience_friction_auditor",
    }

    designers = registry.get_discipline("designers")
    assert set(designers.specialist_persona_ids) == {
        "concept_ideation_engine",
        "visual_system_auditor",
        "art_direction_critic",
        "design_token_palette_architect",
    }
