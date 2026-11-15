"""
OCTS AI - Evaluation Scoring Tests (Phase 4)
Verifies Quality Score calculation, re-normalization, actual 0.0 vs UNAVAILABLE handling,
Reliability Score deduplication and deductions, coverage formulas, and TrustScore validation table.
"""

import pytest
from backend.evaluation.schemas import (
    CheckSeverity,
    CriterionResult,
    CriterionStatus,
    ReliabilityCheckResult,
)
from backend.evaluation.scoring.calculator import ScoringCalculator


# ---------------------------------------------------------------------------
# Fix 2: Quality Score, UNAVAILABLE Handling & Coverage
# ---------------------------------------------------------------------------

def test_quality_score_example_from_specification():
    """
    Verify exact example from specification:
    A: 0.33, score=80, PASSED
    B: 0.33, score=90, PASSED
    C: 0.34, score=None, UNAVAILABLE
    Expected: Quality Score = 85.0, Coverage = 66.67% (0.6667)
    (Must NOT be calculated as 56.67 by treating C as zero).
    """
    calc = ScoringCalculator()
    criteria = [
        CriterionResult(
            criterion_id="crit_a",
            criterion_name="Criterion A",
            score=80.0,
            weight=0.33,
            weighted_score=26.4,
            evidence="Good",
            status=CriterionStatus.PASSED,
        ),
        CriterionResult(
            criterion_id="crit_b",
            criterion_name="Criterion B",
            score=90.0,
            weight=0.33,
            weighted_score=29.7,
            evidence="Excellent",
            status=CriterionStatus.PASSED,
        ),
        CriterionResult(
            criterion_id="crit_c",
            criterion_name="Criterion C",
            score=None,
            weight=0.34,
            weighted_score=None,
            evidence="Unavailable",
            status=CriterionStatus.UNAVAILABLE,
        ),
    ]

    quality_score, coverage, skipped = calc.calculate_quality_score(criteria)
    # Active weights: 0.33 + 0.33 = 0.66. Sum: (80*0.33 + 90*0.33) = 26.4 + 29.7 = 56.1.
    # 56.1 / 0.66 = 85.0
    assert quality_score == 85.0
    assert coverage == 0.6667
    assert skipped == ["crit_c"]


def test_quality_score_distinguishes_actual_zero_from_unavailable():
    """Verify an actual evaluated score of 0.0 is treated as FAILED and included in the denominator."""
    calc = ScoringCalculator()
    criteria = [
        CriterionResult(
            criterion_id="crit_a",
            criterion_name="Criterion A",
            score=80.0,
            weight=0.50,
            weighted_score=40.0,
            evidence="Good",
            status=CriterionStatus.PASSED,
        ),
        CriterionResult(
            criterion_id="crit_b",
            criterion_name="Criterion B",
            score=0.0,
            weight=0.50,
            weighted_score=0.0,
            evidence="Completely failed",
            status=CriterionStatus.FAILED,
        ),
    ]

    quality_score, coverage, skipped = calc.calculate_quality_score(criteria)
    # Active weights: 1.0. Sum: (80*0.5 + 0*0.5) = 40.0. Quality Score = 40.0, Coverage = 1.0
    assert quality_score == 40.0
    assert coverage == 1.0
    assert len(skipped) == 0


def test_quality_score_all_criteria_unavailable():
    """Verify when all criteria are UNAVAILABLE or SKIPPED, Quality Score is None and coverage is 0.0."""
    calc = ScoringCalculator()
    criteria = [
        CriterionResult(
            criterion_id="crit_a",
            criterion_name="Criterion A",
            score=None,
            weight=0.50,
            weighted_score=None,
            evidence="Unavailable",
            status=CriterionStatus.UNAVAILABLE,
        ),
        CriterionResult(
            criterion_id="crit_b",
            criterion_name="Criterion B",
            score=None,
            weight=0.50,
            weighted_score=None,
            evidence="Skipped",
            status=CriterionStatus.SKIPPED,
        ),
    ]

    quality_score, coverage, skipped = calc.calculate_quality_score(criteria)
    assert quality_score is None
    assert coverage == 0.0
    assert set(skipped) == {"crit_a", "crit_b"}


def test_quality_score_multiple_unavailable_criteria():
    """Verify multiple unavailable criteria are properly excluded from scoring."""
    calc = ScoringCalculator()
    criteria = [
        CriterionResult(
            criterion_id="c1",
            criterion_name="C1",
            score=100.0,
            weight=0.20,
            weighted_score=20.0,
            evidence="Perfect",
            status=CriterionStatus.PASSED,
        ),
        CriterionResult(
            criterion_id="c2",
            criterion_name="C2",
            score=None,
            weight=0.40,
            weighted_score=None,
            evidence="N/A",
            status=CriterionStatus.UNAVAILABLE,
        ),
        CriterionResult(
            criterion_id="c3",
            criterion_name="C3",
            score=None,
            weight=0.40,
            weighted_score=None,
            evidence="N/A",
            status=CriterionStatus.SKIPPED,
        ),
    ]

    quality_score, coverage, skipped = calc.calculate_quality_score(criteria)
    assert quality_score == 100.0
    assert coverage == round(1 / 3, 4)
    assert len(skipped) == 2


# ---------------------------------------------------------------------------
# Fix 5: Reliability Scoring Audit & Invariants
# ---------------------------------------------------------------------------

def test_reliability_score_deductions_by_severity():
    """Verify CRITICAL deducts 40, WARNING deducts 10, INFO deducts 0."""
    calc = ScoringCalculator()
    checks = [
        ReliabilityCheckResult(
            check_id="chk_crit",
            check_name="Critical Check",
            status=CriterionStatus.FAILED,
            severity=CheckSeverity.CRITICAL,
            explanation="Critical failure",
        ),
        ReliabilityCheckResult(
            check_id="chk_warn",
            check_name="Warning Check",
            status=CriterionStatus.FAILED,
            severity=CheckSeverity.WARNING,
            explanation="Warning failure",
        ),
        ReliabilityCheckResult(
            check_id="chk_info",
            check_name="Info Check",
            status=CriterionStatus.FAILED,
            severity=CheckSeverity.INFO,
            explanation="Info notification",
        ),
    ]

    # 100 - 40 - 10 - 0 = 50.0
    score, failed = calc.calculate_reliability_score(checks)
    assert score == 50.0
    assert set(failed) == {"chk_crit", "chk_warn", "chk_info"}


def test_reliability_score_deduplication():
    """Verify duplicate check results do not cause duplicate score deductions."""
    calc = ScoringCalculator()
    checks = [
        ReliabilityCheckResult(
            check_id="chk_crit",
            check_name="Critical Check",
            status=CriterionStatus.FAILED,
            severity=CheckSeverity.CRITICAL,
            explanation="Critical failure",
        ),
        ReliabilityCheckResult(
            check_id="chk_crit",  # Duplicate check ID
            check_name="Critical Check",
            status=CriterionStatus.FAILED,
            severity=CheckSeverity.CRITICAL,
            explanation="Duplicate check",
        ),
    ]

    # Should deduct 40 only once -> 100 - 40 = 60.0
    score, failed = calc.calculate_reliability_score(checks)
    assert score == 60.0
    assert failed == ["chk_crit"]


def test_reliability_score_skipped_checks_do_not_count_as_passes():
    """Verify skipped or unavailable checks do not award points."""
    calc = ScoringCalculator()
    checks = [
        ReliabilityCheckResult(
            check_id="chk_unavail",
            check_name="Unavailable Check",
            status=CriterionStatus.UNAVAILABLE,
            severity=CheckSeverity.CRITICAL,
            explanation="Check could not run",
        ),
    ]

    score, failed = calc.calculate_reliability_score(checks)
    assert score is None
    assert len(failed) == 0


def test_reliability_score_invalid_severity():
    """Verify invalid severity value is rejected."""
    calc = ScoringCalculator()
    check = ReliabilityCheckResult(
        check_id="chk_invalid",
        check_name="Invalid Severity",
        status=CriterionStatus.PASSED,
        severity=CheckSeverity.CRITICAL,
        explanation="Valid",
    )
    # Manually tamper severity to test validation
    check.severity = "extreme"  # type: ignore

    with pytest.raises(ValueError, match="Invalid check severity"):
        calc.calculate_reliability_score([check])


# ---------------------------------------------------------------------------
# Fix 6: TrustScore Validation & Specification Table
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "quality,reliability,expected_trust",
    [
        (90.0, 100.0, 93.0),
        (80.0, 90.0, 83.0),
        (None, 100.0, None),
        (90.0, None, None),
        (None, None, None),
    ],
)
def test_trust_score_specification_table(quality, reliability, expected_trust):
    """
    Verify exact TrustScore behavior from the specification table:
    | Quality | Reliability | TrustScore |
    | 90      | 100         | 93         |
    | 80      | 90          | 83         |
    | None    | 100         | None       |
    | 90      | None        | None       |
    | None    | None        | None       |
    """
    calc = ScoringCalculator(default_quality_weight=0.70, default_reliability_weight=0.30)
    trust_score, breakdown = calc.calculate_trust_score(
        quality_score=quality,
        reliability_score=reliability,
    )

    assert trust_score == expected_trust
    if expected_trust is not None:
        assert breakdown is not None
        assert breakdown.quality_score == quality
        assert breakdown.reliability_score == reliability
        assert f"TrustScore ({expected_trust})" in breakdown.formula_explanation
    else:
        assert "unavailable" in breakdown.formula_explanation.lower()


def test_trust_score_invalid_weights_rejected():
    """Verify negative weights or zero total weights are rejected."""
    with pytest.raises(ValueError, match="must be non-negative"):
        ScoringCalculator(default_quality_weight=-0.5, default_reliability_weight=0.5)

    with pytest.raises(ValueError, match="must be non-negative"):
        ScoringCalculator(default_quality_weight=0.5, default_reliability_weight=-0.5)

    with pytest.raises(ValueError, match="strictly greater than zero"):
        ScoringCalculator(default_quality_weight=0.0, default_reliability_weight=0.0)

    calc = ScoringCalculator()
    with pytest.raises(ValueError, match="must be non-negative"):
        calc.calculate_trust_score(90.0, 90.0, quality_weight=-0.2)

    with pytest.raises(ValueError, match="strictly greater than zero"):
        calc.calculate_trust_score(90.0, 90.0, quality_weight=0.0, reliability_weight=0.0)
