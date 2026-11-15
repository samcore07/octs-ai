"""
OCTS AI - Refinement Feedback Builder Unit Tests
Verifies weak criteria extraction, gap sorting, and prompt compilation.
"""

from backend.evaluation.schemas import CriterionResult, CriterionStatus
from backend.refinement.feedback_builder import FeedbackBuilder
from backend.refinement.schemas import PeerReviewResult


def test_extract_weak_criteria_below_threshold():
    """Verify criteria with score < 70.0 are extracted and sorted descending by gap."""
    builder = FeedbackBuilder(threshold=70.0)

    criteria = [
        CriterionResult(
            criterion_id="narrative_coherence",
            criterion_name="Narrative Coherence",
            score=55.0,
            weight=0.25,
            evidence="Pacing slowed significantly in middle chapter.",
            status=CriterionStatus.PASSED,
        ),
        CriterionResult(
            criterion_id="style_tone_consistency",
            criterion_name="Style and Tone Consistency",
            score=88.0,
            weight=0.20,
            evidence="Atmospheric prose maintained.",
            status=CriterionStatus.PASSED,
        ),
        CriterionResult(
            criterion_id="character_consistency",
            criterion_name="Character Consistency",
            score=62.0,
            weight=0.20,
            evidence="Voice shifted unexpectedly in dialogue.",
            status=CriterionStatus.PASSED,
        ),
    ]

    weak = builder.extract_weak_criteria(criteria, threshold=70.0)

    assert len(weak) == 2
    # First item should have largest gap (55.0 score -> 45.0 gap)
    assert weak[0].criterion_id == "narrative_coherence"
    assert weak[0].gap == 45.0
    assert "causal logic" in weak[0].actionable_recommendation.lower()

    # Second item (62.0 score -> 38.0 gap)
    assert weak[1].criterion_id == "character_consistency"
    assert weak[1].gap == 38.0


def test_extract_weak_criteria_empty_when_all_above_threshold():
    """Verify no criteria extracted when all criteria meet or exceed threshold."""
    builder = FeedbackBuilder(threshold=70.0)

    criteria = [
        CriterionResult(
            criterion_id="c1",
            criterion_name="Criterion 1",
            score=75.0,
            weight=0.5,
            evidence="Good",
        ),
        CriterionResult(
            criterion_id="c2",
            criterion_name="Criterion 2",
            score=90.0,
            weight=0.5,
            evidence="Excellent",
        ),
    ]

    weak = builder.extract_weak_criteria(criteria)
    assert len(weak) == 0


def test_build_refinement_prompt_format():
    """Verify build_refinement_prompt creates structured markdown directives."""
    builder = FeedbackBuilder(threshold=70.0)

    criteria = [
        CriterionResult(
            criterion_id="narrative_coherence",
            criterion_name="Narrative Coherence",
            score=60.0,
            weight=0.5,
            evidence="Plot hole in Act II.",
        )
    ]
    weak = builder.extract_weak_criteria(criteria)

    peer_review = PeerReviewResult(
        reviewer_persona_id="lore_continuity_keeper",
        reviewer_persona_name="Lore & Continuity Keeper",
        reviewer_discipline="writers",
        strengths=["Strong initial protagonist motivation."],
        actionable_critique=["Chronology error in flashback timeline."],
        suggested_improvements=["Anchor the flashback to a specific lunar eclipse."],
    )

    prompt = builder.build_refinement_prompt(
        original_prompt="Write a mystery scene.",
        previous_output="The detective walked into the room.",
        weak_criteria=weak,
        persona_name="Narrative Architect",
        peer_review=peer_review,
    )

    assert "# AUTONOMOUS CRAFT REFINEMENT DIRECTIVE" in prompt
    assert "Original Client Prompt" in prompt or "Original Creative Request" in prompt
    assert "Previous Candidate Draft" in prompt
    assert "Narrative Coherence" in prompt
    assert "Lore & Continuity Keeper" in prompt
    assert "Strong initial protagonist motivation." in prompt
    assert "Chronology error in flashback timeline." in prompt
    assert "DO NOT output partial fragments" in prompt
