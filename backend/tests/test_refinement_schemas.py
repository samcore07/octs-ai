"""
OCTS AI - Refinement & Collaboration Schema Unit Tests
Verifies Pydantic models, validation boundaries, and serialization formats for Phase 5.
"""

import pytest
from pydantic import ValidationError

from backend.refinement.schemas import (
    CriterionFeedback,
    ImprovementRecord,
    PeerReviewResult,
    PeerReviewStatus,
    RefinementDecision,
    RefinementMetadata,
    RefinementStatus,
)


def test_criterion_feedback_valid():
    """Verify CriterionFeedback instantiation and field constraints."""
    fb = CriterionFeedback(
        criterion_id="narrative_coherence",
        criterion_name="Narrative Coherence",
        current_score=60.0,
        gap=40.0,
        deficiency_summary="Causal gaps observed in second act.",
        actionable_recommendation="Strengthen protagonist decision causality.",
    )
    assert fb.criterion_id == "narrative_coherence"
    assert fb.current_score == 60.0
    assert fb.gap == 40.0
    assert fb.max_score == 100.0


def test_criterion_feedback_invalid_scores():
    """Verify CriterionFeedback rejects negative or out-of-bounds scores."""
    with pytest.raises(ValidationError):
        CriterionFeedback(
            criterion_id="c1",
            criterion_name="C1",
            current_score=-5.0,
            gap=105.0,
            deficiency_summary="err",
            actionable_recommendation="fix",
        )


def test_peer_review_result_defaults():
    """Verify PeerReviewResult default attributes and status enum."""
    pr = PeerReviewResult(
        reviewer_persona_id="lore_continuity_keeper",
        reviewer_persona_name="Lore & Continuity Keeper",
        reviewer_discipline="writers",
        strengths=["Clear pacing"],
        actionable_critique=["Magic system contradiction"],
        suggested_improvements=["Establish consistent rune rules"],
    )
    assert pr.status == PeerReviewStatus.COMPLETED
    assert len(pr.strengths) == 1
    assert len(pr.actionable_critique) == 1


def test_refinement_decision_bounding():
    """Verify RefinementDecision attempt and trigger fields."""
    decision = RefinementDecision(
        should_refine=True,
        trigger_reason="Quality below 70.0",
        attempt_number=1,
        max_attempts=2,
    )
    assert decision.should_refine is True
    assert decision.attempt_number == 1
    assert decision.max_attempts == 2


def test_improvement_record_deltas():
    """Verify ImprovementRecord tracks positive and negative deltas correctly."""
    rec = ImprovementRecord(
        attempt_number=1,
        previous_quality_score=65.0,
        new_quality_score=78.5,
        quality_delta=13.5,
        previous_trust_score=70.0,
        new_trust_score=82.0,
        trust_delta=12.0,
        improved_criteria=["narrative_coherence", "character_consistency"],
        regressed_criteria=[],
        unchanged_criteria=["instruction_adherence"],
        is_improvement=True,
        rationale="Demonstrated net gain in craft cohesion.",
    )
    assert rec.is_improvement is True
    assert rec.quality_delta == 13.5
    assert len(rec.improved_criteria) == 2


def test_refinement_metadata_serialization():
    """Verify RefinementMetadata serializes cleanly to dict."""
    meta = RefinementMetadata(
        refinement_triggered=True,
        recovery_attempts=1,
        max_recovery_attempts=2,
        initial_quality_score=62.0,
        final_quality_score=76.0,
        quality_delta=14.0,
        refinement_status=RefinementStatus.IMPROVED.value,
        best_output_selected="attempt_1",
    )
    dumped = meta.model_dump()
    assert dumped["refinement_triggered"] is True
    assert dumped["recovery_attempts"] == 1
    assert dumped["quality_delta"] == 14.0
    assert dumped["best_output_selected"] == "attempt_1"
