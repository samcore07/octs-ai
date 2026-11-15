"""
OCTS AI - Improvement Analyzer & Best-Output Selection (Refined Phase 5)
Compares successive evaluations across Quality, Reliability, Coverage, and TrustScore.
Enforces multi-dimensional non-regression policies and deterministic best-artifact selection.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.evaluation.schemas import CheckSeverity, CriterionResult, CriterionStatus, EvaluationResult
from backend.refinement.schemas import ImprovementRecord, RefinementStatus


class ImprovementAnalyzer:
    """
    Analyzes whether a refined output achieved genuine multi-dimensional improvement.
    Guarantees deterministic selection: candidates with critical reliability regressions,
    instruction adherence degradation, or lower TrustScores are systematically rejected.
    """

    @staticmethod
    def _extract_eval_metrics(eval_obj: Any) -> Dict[str, Any]:
        """
        Safely extracts evaluation status, quality_score, reliability_score, trust_score,
        coverage, critical failure flags, and individual criteria scores.
        Handles EvaluationResult, dict, or None defensively without fabricating data.
        """
        if eval_obj is None:
            return {
                "status": "unavailable",
                "quality": None,
                "reliability": None,
                "trust": None,
                "coverage": 1.0,
                "has_critical_failure": False,
                "criteria_map": {},
            }

        if isinstance(eval_obj, EvaluationResult):
            quality = eval_obj.quality_score
            reliability = eval_obj.reliability_score
            trust = eval_obj.trust_score
            coverage = getattr(eval_obj, "evaluation_coverage", 1.0)
            status = getattr(eval_obj, "evaluation_status", "completed")

            has_crit_fail = any(
                check.status == CriterionStatus.FAILED and check.severity == CheckSeverity.CRITICAL
                for check in eval_obj.reliability_checks
            )

            criteria_map = {
                cr.criterion_id: cr.score
                for cr in eval_obj.criteria_breakdown
                if cr.score is not None
            }

            return {
                "status": status,
                "quality": quality,
                "reliability": reliability,
                "trust": trust,
                "coverage": coverage if coverage is not None else 1.0,
                "has_critical_failure": has_crit_fail,
                "criteria_map": criteria_map,
            }

        if isinstance(eval_obj, dict):
            quality = eval_obj.get("quality_score")
            reliability = eval_obj.get("reliability_score")
            trust = eval_obj.get("trust_score")
            coverage = eval_obj.get("evaluation_coverage", 1.0)
            status = eval_obj.get("evaluation_status", "completed")

            has_crit_fail = False
            for check in eval_obj.get("reliability_checks", []):
                if isinstance(check, dict):
                    c_status = check.get("status")
                    c_sev = check.get("severity")
                    if c_status in ("failed", CriterionStatus.FAILED) and c_sev in ("critical", CheckSeverity.CRITICAL):
                        has_crit_fail = True
                        break

            criteria_map = {}
            for item in eval_obj.get("criteria_breakdown", []):
                if isinstance(item, dict):
                    cid = item.get("criterion_id")
                    sc = item.get("score")
                    if cid and sc is not None:
                        criteria_map[cid] = float(sc)
                elif isinstance(item, CriterionResult):
                    if item.score is not None:
                        criteria_map[item.criterion_id] = item.score

            return {
                "status": status,
                "quality": quality,
                "reliability": reliability,
                "trust": trust,
                "coverage": float(coverage) if coverage is not None else 1.0,
                "has_critical_failure": has_crit_fail,
                "criteria_map": criteria_map,
            }

        return {
            "status": "unavailable",
            "quality": None,
            "reliability": None,
            "trust": None,
            "coverage": 1.0,
            "has_critical_failure": False,
            "criteria_map": {},
        }

    def analyze_improvement(
        self,
        previous_eval: Any,
        candidate_eval: Any,
        attempt_number: int = 1,
    ) -> ImprovementRecord:
        """
        Compares candidate evaluation against previous baseline/best evaluation using
        multi-dimensional criteria: Quality, Reliability, TrustScore, Coverage, and
        Critical Rubric Constraints.
        """
        prev_m = self._extract_eval_metrics(previous_eval)
        cand_m = self._extract_eval_metrics(candidate_eval)

        prev_q, cand_q = prev_m["quality"], cand_m["quality"]
        prev_r, cand_r = prev_m["reliability"], cand_m["reliability"]
        prev_t, cand_t = prev_m["trust"], cand_m["trust"]
        prev_cov, cand_cov = prev_m["coverage"], cand_m["coverage"]
        prev_crit, cand_crit = prev_m["criteria_map"], cand_m["criteria_map"]

        # Calculate deltas (None if missing on either side)
        q_delta = round(cand_q - prev_q, 2) if (prev_q is not None and cand_q is not None) else None
        r_delta = round(cand_r - prev_r, 2) if (prev_r is not None and cand_r is not None) else None
        t_delta = round(cand_t - prev_t, 2) if (prev_t is not None and cand_t is not None) else None
        cov_delta = round(cand_cov - prev_cov, 2) if (prev_cov is not None and cand_cov is not None) else None

        # Track rubric criteria movements
        improved: List[str] = []
        regressed: List[str] = []
        unchanged: List[str] = []

        all_keys = set(prev_crit.keys()).union(set(cand_crit.keys()))
        for k in sorted(all_keys):
            p_val = prev_crit.get(k)
            c_val = cand_crit.get(k)
            if p_val is None or c_val is None:
                continue
            diff = round(c_val - p_val, 2)
            if diff > 0.05:
                improved.append(k)
            elif diff < -0.05:
                regressed.append(k)
            else:
                unchanged.append(k)

        # Baseline score representation
        prev_score = prev_t if prev_t is not None else prev_q
        cand_score = cand_t if cand_t is not None else cand_q

        # =====================================================================
        # Policy Evaluation Decision Rules
        # =====================================================================
        is_accepted = False
        crit_regression = False
        rationale = ""

        # 1. Candidate validity check
        if cand_m["status"] in ("failed", "unavailable") or cand_q is None:
            is_accepted = False
            rationale = "Candidate evaluation failed or produced no valid quality score; preserved previous best."

        # 2. Previous validity check
        elif prev_m["status"] in ("failed", "unavailable") or prev_q is None:
            is_accepted = True
            rationale = "No prior valid evaluation existed; accepted candidate as baseline."

        # 3. Critical Reliability Failure Guard
        # Never accept candidate with a critical reliability failure merely because Quality Score increased
        elif cand_m["has_critical_failure"] and not prev_m["has_critical_failure"]:
            is_accepted = False
            crit_regression = True
            rationale = (
                f"Candidate suffered a critical execution reliability check failure "
                f"(reliability {cand_r} vs previous {prev_r}); preserved previous best despite quality score."
            )

        # 4. Severe Reliability Drop Guard (e.g. reliability dropped below 70.0)
        elif prev_r is not None and cand_r is not None and cand_r < prev_r and cand_r < 70.0:
            is_accepted = False
            crit_regression = True
            rationale = (
                f"Candidate suffered severe reliability degradation ({prev_r:.1f} -> {cand_r:.1f}); "
                f"preserved previous best."
            )

        # 5. Severe Instruction Adherence Regression Guard
        elif (
            prev_crit.get("instruction_adherence") is not None
            and cand_crit.get("instruction_adherence") is not None
            and (prev_crit["instruction_adherence"] - cand_crit["instruction_adherence"]) > 15.0
        ):
            is_accepted = False
            crit_regression = True
            prev_adh = prev_crit["instruction_adherence"]
            cand_adh = cand_crit["instruction_adherence"]
            rationale = (
                f"Candidate instruction adherence regressed significantly ({prev_adh:.1f} -> {cand_adh:.1f}); "
                f"preserved previous best."
            )

        # 6. Evaluation Coverage Drop Guard
        # If candidate coverage dropped heavily, average cannot be trusted
        elif cov_delta is not None and cov_delta < -0.25:
            is_accepted = False
            rationale = (
                f"Candidate evaluation coverage dropped substantially ({prev_cov:.0%} -> {cand_cov:.0%}); "
                f"evidence insufficient to prove superiority."
            )

        # 7. Low Previous Coverage Compensation
        # If previous evaluation was partial (< 60%) and candidate is complete (>= 85%) with comparable quality:
        elif prev_cov < 0.60 and cand_cov >= 0.85 and (q_delta is None or q_delta >= -5.0):
            is_accepted = True
            rationale = (
                f"Candidate achieved substantially higher evaluation coverage ({prev_cov:.0%} -> {cand_cov:.0%}) "
                f"with comparable quality; accepted candidate."
            )

        # 8. TrustScore Comparison (when both are valid and comparable)
        elif prev_t is not None and cand_t is not None:
            if t_delta is not None and t_delta > 0.0:
                # Candidate improved composite TrustScore
                # Ensure reliability didn't silently degrade heavily (> 15 pts) while quality surged
                if r_delta is not None and r_delta < -15.0:
                    is_accepted = False
                    crit_regression = True
                    rationale = (
                        f"Candidate TrustScore was higher, but reliability dropped by {abs(r_delta):.1f} pts; "
                        f"preserved previous best."
                    )
                else:
                    is_accepted = True
                    rationale = (
                        f"Candidate demonstrated composite TrustScore improvement (+{t_delta:.1f} pts: "
                        f"{prev_t:.1f} -> {cand_t:.1f})."
                    )
            elif t_delta is not None and t_delta == 0.0:
                if len(improved) > len(regressed):
                    is_accepted = True
                    rationale = f"TrustScore tied at {cand_t:.1f}, but more criteria improved ({len(improved)}) than regressed ({len(regressed)})."
                else:
                    is_accepted = False
                    rationale = f"TrustScore tied at {cand_t:.1f} without net criteria gain; preserved previous best."
            else:
                is_accepted = False
                rationale = (
                    f"Candidate TrustScore regressed ({t_delta:.1f} pts: {prev_t:.1f} -> {cand_t:.1f}); "
                    f"deterministically reverting to previous best output."
                )

        # 9. Quality Score Comparison (when TrustScore is missing or one-sided)
        elif q_delta is not None and q_delta > 0.0:
            # Verify reliability did not suffer substantial degradation
            if r_delta is not None and r_delta < -15.0:
                is_accepted = False
                crit_regression = True
                rationale = (
                    f"Candidate quality improved (+{q_delta:.1f} pts), but reliability degraded heavily "
                    f"({r_delta:.1f} pts); preserved previous best."
                )
            else:
                is_accepted = True
                rationale = (
                    f"Candidate demonstrated quality improvement (+{q_delta:.1f} pts: "
                    f"{prev_q:.1f} -> {cand_q:.1f}). Criteria improved: {len(improved)}, regressed: {len(regressed)}."
                )

        elif q_delta is not None and q_delta == 0.0:
            if len(improved) > len(regressed):
                is_accepted = True
                rationale = (
                    f"Quality tied at {cand_q:.1f}, but more criteria improved ({len(improved)}) "
                    f"than regressed ({len(regressed)})."
                )
            else:
                is_accepted = False
                rationale = f"Quality tied at {cand_q:.1f} without net criteria gain; preserved previous best."

        else:
            is_accepted = False
            q_str = f"{q_delta:.1f} pts" if q_delta is not None else "N/A"
            rationale = (
                f"Candidate regressed in quality ({q_str}: {prev_q} -> {cand_q}); "
                f"deterministically reverting to previous best output."
            )

        return ImprovementRecord(
            attempt_number=attempt_number,
            selection_reason=rationale,
            candidate_accepted=is_accepted,
            is_improvement=is_accepted,
            previous_best_score=prev_score,
            candidate_score=cand_score,
            previous_quality_score=prev_q,
            new_quality_score=cand_q,
            quality_delta=q_delta,
            previous_reliability_score=prev_r,
            new_reliability_score=cand_r,
            reliability_delta=r_delta,
            previous_coverage=prev_cov,
            new_coverage=cand_cov,
            coverage_delta=cov_delta,
            previous_trust_score=prev_t,
            new_trust_score=cand_t,
            trust_delta=t_delta,
            improved_criteria=improved,
            regressed_criteria=regressed,
            unchanged_criteria=unchanged,
            critical_regression_detected=crit_regression,
            rationale=rationale,
        )

    def select_best_artifact(
        self,
        previous_output: str,
        previous_eval: Any,
        candidate_output: str,
        candidate_eval: Any,
        improvement_record: ImprovementRecord,
        previous_label: str = "initial",
    ) -> Tuple[str, Any, str, RefinementStatus]:
        """
        Deterministically selects between the candidate and previous best artifact
        based on the validated ImprovementRecord.
        Returns: (selected_output, selected_eval, selected_label, status)
        """
        if improvement_record.candidate_accepted:
            selected_label = f"attempt_{improvement_record.attempt_number}"
            return candidate_output, candidate_eval, selected_label, RefinementStatus.IMPROVED
        else:
            return previous_output, previous_eval, previous_label, RefinementStatus.REGRESSED_REVERTED
