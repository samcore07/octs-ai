"""
OCTS AI - Evaluation Scoring Calculator
Calculates normalized Quality Score, Reliability Score, and composite TrustScore.
Transparently tracks evaluation coverage, missing/unavailable criteria, and formula explanations.
"""

import logging
from typing import List, Optional, Set, Tuple
from backend.evaluation.schemas import (
    CheckSeverity,
    CriterionResult,
    CriterionStatus,
    ReliabilityCheckResult,
    TrustBreakdown,
)

logger = logging.getLogger("octs.evaluation.calculator")


class ScoringCalculator:
    """
    Transparent scoring calculator for OCTS AI evaluation dimensions.
    Enforces strict mathematical normalization, deduplication, and non-fabrication invariants.
    """

    def __init__(
        self,
        default_quality_weight: float = 0.70,
        default_reliability_weight: float = 0.30,
    ):
        if default_quality_weight < 0.0 or default_reliability_weight < 0.0:
            raise ValueError("Evaluation weights must be non-negative.")
        total = default_quality_weight + default_reliability_weight
        if total <= 0.0:
            raise ValueError("Weight total must be strictly greater than zero.")

        self.quality_weight = default_quality_weight / total
        self.reliability_weight = default_reliability_weight / total

    def calculate_quality_score(
        self,
        criteria: List[CriterionResult],
    ) -> Tuple[Optional[float], float, List[str]]:
        """
        Calculates normalized Quality Score (0 - 100) as the weighted average of applicable criteria.
        Unavailable and skipped criteria are excluded from the active denominator (weights re-normalized).
        Actual evaluated scores of 0.0 remain active and distinguishable from unavailable criteria.

        Returns:
            Tuple[Optional[float], float, List[str]]:
                - Quality Score (or None if all criteria are unavailable/skipped)
                - Evaluation coverage fraction (0.0 to 1.0)
                - List of skipped/unavailable criterion IDs
        """
        if not criteria:
            return None, 0.0, []

        total_active_weight = 0.0
        weighted_sum = 0.0
        skipped_or_missing: List[str] = []
        applicable_count = len(criteria)
        evaluated_count = 0

        for crit in criteria:
            # Check if criterion was skipped or unavailable
            if (
                crit.status in (CriterionStatus.SKIPPED, CriterionStatus.UNAVAILABLE)
                or crit.score is None
            ):
                skipped_or_missing.append(crit.criterion_id)
                continue

            # Valid evaluated score (including 0.0)
            bounded_score = max(0.0, min(100.0, float(crit.score)))
            w = max(0.0, float(crit.weight))

            weighted_sum += bounded_score * w
            total_active_weight += w
            evaluated_count += 1

        coverage = round(evaluated_count / applicable_count, 4) if applicable_count > 0 else 0.0

        if total_active_weight <= 0.0 or evaluated_count == 0:
            return None, coverage, skipped_or_missing

        # Re-normalize over active subset of weights
        quality_score = round(weighted_sum / total_active_weight, 2)
        return quality_score, coverage, skipped_or_missing

    def calculate_reliability_score(
        self,
        checks: List[ReliabilityCheckResult],
    ) -> Tuple[Optional[float], List[str]]:
        """
        Derives deterministic execution reliability score (0 - 100).
        Evaluates pass/fail on execution health checks with deduplication.
        Deductions:
          - CRITICAL check failure: 40 points
          - WARNING check failure: 10 points
          - INFO check: 0 points (never reduces reliability score)
        Skipped and unavailable checks do not count as passes.

        Returns:
            Tuple[Optional[float], List[str]]:
                - Reliability Score (or None if no checks were evaluated)
                - List of failed check IDs
        """
        if not checks:
            return None, []

        score = 100.0
        failed_checks: List[str] = []
        seen_check_ids: Set[str] = set()
        has_evaluated_checks = False

        for check in checks:
            # Deduplicate by check_id to prevent duplicate deductions
            if check.check_id in seen_check_ids:
                logger.warning(f"Ignoring duplicate check '{check.check_id}' in reliability calculation.")
                continue
            seen_check_ids.add(check.check_id)

            # Validate check severity
            if check.severity not in (CheckSeverity.CRITICAL, CheckSeverity.WARNING, CheckSeverity.INFO):
                raise ValueError(f"Invalid check severity: {check.severity}")

            if check.status in (CriterionStatus.UNAVAILABLE, CriterionStatus.SKIPPED):
                continue

            has_evaluated_checks = True
            if check.status == CriterionStatus.FAILED:
                failed_checks.append(check.check_id)
                if check.severity == CheckSeverity.CRITICAL:
                    score -= 40.0
                elif check.severity == CheckSeverity.WARNING:
                    score -= 10.0
                elif check.severity == CheckSeverity.INFO:
                    pass  # INFO never reduces score

        if not has_evaluated_checks:
            return None, []

        reliability_score = max(0.0, min(100.0, round(score, 2)))
        return reliability_score, failed_checks

    def calculate_trust_score(
        self,
        quality_score: Optional[float],
        reliability_score: Optional[float],
        quality_weight: Optional[float] = None,
        reliability_weight: Optional[float] = None,
    ) -> Tuple[Optional[float], Optional[TrustBreakdown]]:
        """
        Calculates composite TrustScore balancing creative quality and deterministic reliability.
        Does NOT calculate or fabricate a score if either dimension is missing or None.
        Enforces non-negative weights and valid weight totals.
        """
        qw = quality_weight if quality_weight is not None else self.quality_weight
        rw = reliability_weight if reliability_weight is not None else self.reliability_weight

        if qw < 0.0 or rw < 0.0:
            raise ValueError("TrustScore weights must be non-negative.")

        total_w = qw + rw
        if total_w <= 0.0:
            raise ValueError("Weight total must be strictly greater than zero.")

        # Normalize weights to sum to 1.0
        qw = qw / total_w
        rw = rw / total_w

        # If either primary dimension is unavailable, composite TrustScore cannot be computed
        if quality_score is None or reliability_score is None:
            breakdown = TrustBreakdown(
                quality_score=quality_score,
                reliability_score=reliability_score,
                quality_weight=round(qw, 2),
                reliability_weight=round(rw, 2),
                formula_explanation="TrustScore unavailable: requires both Quality Score and Reliability Score.",
            )
            return None, breakdown

        trust_score = round((quality_score * qw) + (reliability_score * rw), 2)
        trust_score = max(0.0, min(100.0, trust_score))

        breakdown = TrustBreakdown(
            quality_score=quality_score,
            reliability_score=reliability_score,
            quality_weight=round(qw, 2),
            reliability_weight=round(rw, 2),
            formula_explanation=(
                f"TrustScore ({trust_score}) = (QualityScore [{quality_score}] * {qw:.2f}) + "
                f"(ReliabilityScore [{reliability_score}] * {rw:.2f})"
            ),
        )

        return trust_score, breakdown
