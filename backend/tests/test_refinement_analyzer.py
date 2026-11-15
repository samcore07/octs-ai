"""
OCTS AI - Improvement Analyzer & Best-Output Selection Unit Tests
Verifies evaluation comparison, delta calculation, criteria movement, and regression reversion.
"""

from backend.evaluation.schemas import CriterionResult, EvaluationResult
from backend.refinement.recovery.improvement_analyzer import ImprovementAnalyzer
from backend.refinement.schemas import RefinementStatus


def test_analyzer_accepts_improvement():
    """Verify ImprovementAnalyzer accepts candidate when quality score increases."""
    analyzer = ImprovementAnalyzer()

    prev_eval = {
        "quality_score": 62.0,
        "trust_score": 68.0,
        "criteria_breakdown": [
            {"criterion_id": "c1", "score": 60.0},
            {"criterion_id": "c2", "score": 64.0},
        ],
    }

    cand_eval = {
        "quality_score": 75.0,
        "trust_score": 80.0,
        "criteria_breakdown": [
            {"criterion_id": "c1", "score": 78.0},
            {"criterion_id": "c2", "score": 72.0},
        ],
    }

    rec = analyzer.analyze_improvement(prev_eval, cand_eval, attempt_number=1)

    assert rec.is_improvement is True
    assert rec.quality_delta == 13.0
    assert rec.trust_delta == 12.0
    assert set(rec.improved_criteria) == {"c1", "c2"}
    assert len(rec.regressed_criteria) == 0

    best_out, best_ev, label, status = analyzer.select_best_artifact(
        previous_output="Draft 1",
        previous_eval=prev_eval,
        candidate_output="Draft 2 (improved)",
        candidate_eval=cand_eval,
        improvement_record=rec,
        previous_label="initial",
    )

    assert best_out == "Draft 2 (improved)"
    assert best_ev == cand_eval
    assert label == "attempt_1"
    assert status == RefinementStatus.IMPROVED


def test_analyzer_reverts_on_regression():
    """Verify ImprovementAnalyzer rejects candidate and reverts to previous output when quality drops."""
    analyzer = ImprovementAnalyzer()

    prev_eval = {
        "quality_score": 68.0,
        "trust_score": 72.0,
        "criteria_breakdown": [
            {"criterion_id": "c1", "score": 70.0},
            {"criterion_id": "c2", "score": 66.0},
        ],
    }

    # Candidate quality drops to 55.0
    cand_eval = {
        "quality_score": 55.0,
        "trust_score": 60.0,
        "criteria_breakdown": [
            {"criterion_id": "c1", "score": 50.0},
            {"criterion_id": "c2", "score": 60.0},
        ],
    }

    rec = analyzer.analyze_improvement(prev_eval, cand_eval, attempt_number=2)

    assert rec.is_improvement is False
    assert rec.quality_delta == -13.0
    assert set(rec.regressed_criteria) == {"c1", "c2"}
    assert "reverting to previous best output" in rec.rationale.lower()

    best_out, best_ev, label, status = analyzer.select_best_artifact(
        previous_output="Draft 1 (superior)",
        previous_eval=prev_eval,
        candidate_output="Draft 2 (regressed)",
        candidate_eval=cand_eval,
        improvement_record=rec,
        previous_label="initial",
    )

    # Must preserve Draft 1!
    assert best_out == "Draft 1 (superior)"
    assert best_ev == prev_eval
    assert label == "initial"
    assert status == RefinementStatus.REGRESSED_REVERTED


def test_analyzer_handles_none_evaluation_gracefully():
    """Verify analyzer safely rejects candidate when candidate evaluation is None."""
    analyzer = ImprovementAnalyzer()

    prev_eval = {"quality_score": 65.0, "trust_score": 70.0}
    rec = analyzer.analyze_improvement(prev_eval, None, attempt_number=1)

    assert rec.is_improvement is False
    assert "quality score" in rec.rationale.lower()


def test_analyzer_rejects_candidate_on_critical_reliability_failure():
    """Verify candidate with higher quality is rejected if critical reliability check fails."""
    analyzer = ImprovementAnalyzer()

    prev_eval = {
        "quality_score": 70.0,
        "reliability_score": 100.0,
        "trust_score": 79.0,
        "evaluation_coverage": 1.0,
        "reliability_breakdown": [{"check_id": "c1", "status": "passed", "severity": "critical"}],
    }
    cand_eval = {
        "quality_score": 85.0,  # Higher quality!
        "reliability_score": 50.0,  # Critical failure!
        "trust_score": 74.5,
        "evaluation_coverage": 1.0,
        "reliability_breakdown": [{"check_id": "c1", "status": "failed", "severity": "critical"}],
    }

    rec = analyzer.analyze_improvement(prev_eval, cand_eval, attempt_number=1)
    assert rec.candidate_accepted is False
    assert rec.critical_regression_detected is True
    assert "reliability" in rec.selection_reason.lower()


def test_analyzer_rejects_severe_instruction_adherence_regression():
    """Verify candidate is rejected if instruction adherence drops > 15 points despite higher overall quality."""
    analyzer = ImprovementAnalyzer()

    prev_eval = {
        "quality_score": 70.0,
        "reliability_score": 100.0,
        "trust_score": 79.0,
        "evaluation_coverage": 1.0,
        "criteria_breakdown": [
            {"criterion_id": "instruction_adherence", "score": 90.0},
            {"criterion_id": "originality_creativity", "score": 50.0},
        ],
    }
    cand_eval = {
        "quality_score": 75.0,  # Net +5 overall quality
        "reliability_score": 100.0,
        "trust_score": 82.5,
        "evaluation_coverage": 1.0,
        "criteria_breakdown": [
            {"criterion_id": "instruction_adherence", "score": 68.0},  # Dropped 22 points (> 15 threshold!)
            {"criterion_id": "originality_creativity", "score": 82.0},
        ],
    }

    rec = analyzer.analyze_improvement(prev_eval, cand_eval, attempt_number=1)
    assert rec.candidate_accepted is False
    assert rec.critical_regression_detected is True
    assert "instruction adherence regressed" in rec.selection_reason.lower()


def test_analyzer_coverage_delta_handling():
    """Verify candidate with comprehensive coverage is accepted over partial baseline with comparable quality."""
    analyzer = ImprovementAnalyzer()

    prev_eval = {
        "quality_score": 75.0,
        "reliability_score": 90.0,
        "trust_score": 79.5,
        "evaluation_coverage": 0.50,  # Partial coverage
    }
    cand_eval = {
        "quality_score": 73.0,  # Slightly lower but within tolerance
        "reliability_score": 90.0,
        "trust_score": 78.1,
        "evaluation_coverage": 0.95,  # Comprehensive coverage
    }

    rec = analyzer.analyze_improvement(prev_eval, cand_eval, attempt_number=1)
    assert rec.candidate_accepted is True
    assert "higher evaluation coverage" in rec.selection_reason.lower()

    # Drop in coverage > 25% should be rejected
    prev_full = {
        "quality_score": 75.0,
        "reliability_score": 90.0,
        "trust_score": 79.5,
        "evaluation_coverage": 1.0,
    }
    cand_partial = {
        "quality_score": 80.0,
        "reliability_score": 90.0,
        "trust_score": 83.0,
        "evaluation_coverage": 0.60,  # 40% drop
    }
    rec2 = analyzer.analyze_improvement(prev_full, cand_partial, attempt_number=2)
    assert rec2.candidate_accepted is False
    assert "evaluation coverage dropped" in rec2.selection_reason.lower()


def test_analyzer_trust_score_comparison_and_tie_breaking():
    """Verify TrustScore comparison and criteria count tie-breaking."""
    analyzer = ImprovementAnalyzer()

    # Candidate has higher TrustScore
    prev_eval = {
        "quality_score": 70.0,
        "reliability_score": 70.0,
        "trust_score": 70.0,
        "evaluation_coverage": 1.0,
    }
    cand_eval = {
        "quality_score": 68.0,
        "reliability_score": 90.0,
        "trust_score": 74.6,  # Higher TrustScore!
        "evaluation_coverage": 1.0,
    }
    rec = analyzer.analyze_improvement(prev_eval, cand_eval, attempt_number=1)
    assert rec.candidate_accepted is True
    assert "trustscore improvement" in rec.selection_reason.lower()

    # Identical score tie-break by improved criteria count
    prev_tie = {
        "quality_score": 75.0,
        "reliability_score": 90.0,
        "trust_score": 79.5,
        "evaluation_coverage": 1.0,
        "criteria_breakdown": [
            {"criterion_id": "c1", "score": 70.0},
            {"criterion_id": "c2", "score": 80.0},
        ],
    }
    cand_tie = {
        "quality_score": 75.0,
        "reliability_score": 90.0,
        "trust_score": 79.5,
        "evaluation_coverage": 1.0,
        "criteria_breakdown": [
            {"criterion_id": "c1", "score": 85.0},  # +1 improved
            {"criterion_id": "c2", "score": 65.0},  # -1 regressed
        ],
    }
    rec_tie = analyzer.analyze_improvement(prev_tie, cand_tie, attempt_number=1)
    # Net criteria balance is 1 - 1 = 0 <= 0 -> rejected
    assert rec_tie.candidate_accepted is False

