"""
OCTS AI - Quality Evaluators Tests (Phase 4)
Verifies rubric definitions, criterion weights, normalization, domain limitations,
and deterministic heuristic evaluations across all four disciplines.
"""

import pytest
from backend.evaluation.quality.base import QualityEvaluator
from backend.evaluation.quality.writers import WritersQualityEvaluator
from backend.evaluation.quality.musicians import MusiciansQualityEvaluator
from backend.evaluation.quality.creators import CreatorsQualityEvaluator
from backend.evaluation.quality.designers import DesignersQualityEvaluator
from backend.evaluation.scoring.weights import (
    WRITERS_WEIGHTS,
    MUSICIANS_WEIGHTS,
    CREATORS_WEIGHTS,
    DESIGNERS_WEIGHTS,
    validate_weights,
)


# ---------------------------------------------------------------------------
# Weight & Interface Integrity Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "evaluator_cls,expected_discipline,expected_criteria_count",
    [
        (WritersQualityEvaluator, "writers", 6),
        (MusiciansQualityEvaluator, "musicians", 7),
        (CreatorsQualityEvaluator, "creators", 7),
        (DesignersQualityEvaluator, "designers", 7),
    ],
)
def test_evaluator_weights_and_criteria(evaluator_cls, expected_discipline, expected_criteria_count):
    """Verify that every discipline evaluator has valid weights summing to 1.0 and correct criteria."""
    evaluator = evaluator_cls()
    assert evaluator.discipline_id == expected_discipline
    assert len(evaluator.limitations) > 0

    # Ensure metadata matches criteria count
    metadata = evaluator.get_criteria_metadata()
    assert len(metadata) == expected_criteria_count

    # Ensure weights are valid and sum to 1.0
    weights = evaluator.get_default_weights()
    assert len(weights) == expected_criteria_count
    assert validate_weights(weights) is True


def test_invalid_weights_validation():
    """Verify weight validation raises ValueError for negative weights or sums != 1.0."""
    with pytest.raises(ValueError, match="cannot be negative"):
        validate_weights({"crit_a": -0.1, "crit_b": 1.1})

    with pytest.raises(ValueError, match="must sum to 1.0"):
        validate_weights({"crit_a": 0.5, "crit_b": 0.3})

    with pytest.raises(ValueError, match="cannot be empty"):
        validate_weights({})


# ---------------------------------------------------------------------------
# Discipline-Specific Evaluation Tests
# ---------------------------------------------------------------------------

def test_writers_quality_evaluator():
    """Verify WritersQualityEvaluator produces normalized criteria and respects persona adaptation."""
    evaluator = WritersQualityEvaluator()
    prompt = "Design a three-act narrative outline about a forgotten kingdom."
    output = (
        "### Act I: The Awakening\n"
        "Princess Lyra uncovers a hidden vault beneath the citadel.\n\n"
        "### Act II: The Descent\n"
        "Betrayed by her mentor, she journeys across the ashlands.\n\n"
        "### Act III: The Climax\n"
        "Lyra reclaims the crown at great personal sacrifice."
    )

    results = evaluator.evaluate(
        prompt=prompt,
        output=output,
        persona_id="narrative_architect",
    )

    assert len(results) == 6
    for crit in results:
        assert 0.0 <= crit.score <= 100.0
        assert 0.0 <= crit.weighted_score <= 100.0
        assert crit.evidence
        assert crit.status.value == "passed"

    # Narrative Architect with clear Act markers should achieve high structural score
    struct_crit = next(c for c in results if c.criterion_id == "structural_quality")
    assert struct_crit.score >= 85.0


def test_musicians_quality_evaluator_text_boundaries():
    """Verify MusiciansQualityEvaluator explicitly documents text limitations and evaluates structure."""
    evaluator = MusiciansQualityEvaluator()
    assert any("acoustic audio" in lim.lower() for lim in evaluator.limitations)

    prompt = "Write a pop-rock song about late-night city driving."
    output = (
        "[Verse 1]\n"
        "Neon lights reflecting on the wet asphalt\n"
        "Cmaj7 - G - Am - F\n\n"
        "[Chorus]\n"
        "Driving into midnight, leaving all the ghosts behind\n"
        "C - G - Dm - Am"
    )

    results = evaluator.evaluate(
        prompt=prompt,
        output=output,
        persona_id="harmonic_arranger",
    )

    assert len(results) == 7
    struct_crit = next(c for c in results if c.criterion_id == "song_structure")
    harm_crit = next(c for c in results if c.criterion_id == "harmonic_reasoning")
    assert struct_crit.score >= 85.0
    assert harm_crit.score >= 85.0


def test_creators_quality_evaluator_no_viral_guarantee():
    """Verify CreatorsQualityEvaluator enforces no viral reach guarantees and evaluates hooks."""
    evaluator = CreatorsQualityEvaluator()
    assert any("guarantee" in lim.lower() for lim in evaluator.limitations)

    prompt = "Create a 30-second TikTok script on productivity."
    output = (
        "Stop making this 1 morning mistake if you want deep focus!\n"
        "Step 1: Put your phone in another room.\n"
        "Step 2: Do 25 minutes of deep work before checking notifications.\n"
        "Follow for daily focus routines!"
    )

    results = evaluator.evaluate(
        prompt=prompt,
        output=output,
        persona_id="hook_retention_architect",
    )

    assert len(results) == 7
    hook_crit = next(c for c in results if c.criterion_id == "hook_effectiveness")
    assert hook_crit.score >= 85.0


def test_designers_quality_evaluator_text_design_reasoning():
    """Verify DesignersQualityEvaluator evaluates token and design reasoning in text."""
    evaluator = DesignersQualityEvaluator()
    assert any("pixel" in lim.lower() or "canvas" in lim.lower() for lim in evaluator.limitations)

    prompt = "Generate a semantic color palette with WCAG AAA accessibility."
    output = (
        "### Semantic Color Tokens\n"
        "- --color-primary: #1E40AF (Contrast ratio 7.2:1 against white, WCAG AAA compliant)\n"
        "- --color-surface: #F8FAFC\n"
        "- --color-text-main: #0F172A (Contrast ratio 14.1:1)\n"
        "Spatial grid uses 8px base increment with 16px touch target padding."
    )

    results = evaluator.evaluate(
        prompt=prompt,
        output=output,
        persona_id="design_token_palette_architect",
    )

    assert len(results) == 7
    ds_crit = next(c for c in results if c.criterion_id == "design_system_coherence")
    usability_crit = next(c for c in results if c.criterion_id == "usability_reasoning")
    assert ds_crit.score >= 85.0
    assert usability_crit.score >= 85.0
