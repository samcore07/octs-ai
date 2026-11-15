"""
OCTS AI - Evaluation Engine
Central coordinator executing independent Quality Assessment, Reliability Evaluation,
and composite TrustScore derivation across deterministic, LLM-judge, and hybrid modes.
Features explicit fallback transparency, zero-fabrication on clarification, and defensive error containment.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from backend.config import Settings, get_settings
from backend.evaluation.evaluator_registry import EvaluatorRegistry, get_evaluator_registry
from backend.evaluation.judges.llm_judge import LLMJudge
from backend.evaluation.reliability.evaluator import ReliabilityEvaluator
from backend.evaluation.schemas import (
    CriterionResult,
    EvaluationMode,
    EvaluationResult,
    JudgeStatus,
    ReliabilityCheckResult,
)
from backend.evaluation.scoring.calculator import ScoringCalculator

logger = logging.getLogger("octs.evaluation.engine")


class EvaluationEngine:
    """
    Unified evaluation engine for OCTS AI creative workflows.
    Evaluates creative output quality and execution reliability as independent dimensions.
    """

    def __init__(
        self,
        evaluator_registry: Optional[EvaluatorRegistry] = None,
        scoring_calculator: Optional[ScoringCalculator] = None,
        reliability_evaluator: Optional[ReliabilityEvaluator] = None,
        judge: Optional[LLMJudge] = None,
        settings: Optional[Settings] = None,
        model: Optional[Any] = None,
    ):
        self.settings = settings or get_settings()
        self.registry = evaluator_registry or get_evaluator_registry()
        self.calculator = scoring_calculator or ScoringCalculator(
            default_quality_weight=getattr(self.settings, "evaluation_quality_weight", 0.70),
            default_reliability_weight=getattr(self.settings, "evaluation_reliability_weight", 0.30),
        )
        self.reliability = reliability_evaluator or ReliabilityEvaluator()

        # Initialize LLM judge if model provided or judge explicitly passed
        if judge is not None:
            self.judge = judge
        elif model is not None and getattr(self.settings, "evaluation_judge_enabled", False):
            self.judge = LLMJudge(
                model=model,
                timeout_seconds=getattr(self.settings, "evaluation_timeout", 10.0),
                max_retries=getattr(self.settings, "evaluation_max_retries", 1),
            )
        else:
            self.judge = None

    def evaluate_execution(
        self,
        state: Dict[str, Any],
        mode_override: Optional[EvaluationMode] = None,
    ) -> EvaluationResult:
        """
        Coordinates full evaluation of an orchestration execution state.
        Preserves original creative output and never mutates user text.
        """
        eval_id = str(uuid.uuid4())
        started_perf = time.perf_counter()

        # 1. Check if evaluation is disabled via configuration
        if not getattr(self.settings, "evaluation_enabled", True):
            logger.info("Evaluation is disabled in configuration. Skipping evaluation.")
            return EvaluationResult(
                evaluation_id=eval_id,
                evaluation_status="skipped",
                evaluation_mode=EvaluationMode.DETERMINISTIC,
                evaluation_method="disabled",
                judge_status=JudgeStatus.NOT_USED,
                fallback_triggered=False,
                fallback_reason=None,
                quality_score=None,
                reliability_score=None,
                trust_score=None,
                trust_breakdown=None,
                criteria_breakdown=[],
                reliability_checks=[],
                evaluation_coverage=0.0,
                evaluation_summary="Evaluation disabled by configuration.",
                limitations=["Evaluation disabled via EVALUATION_ENABLED=False."],
                evaluated_at=time.time(),
                evaluation_duration_ms=0,
            )

        # 2. Handle early clarification short-circuit (Case C) - Fix 1: Strictly skipped, all scores None
        if state.get("needs_clarification", False) is True:
            logger.info("Request required clarification. Skipping evaluation without fabricating checks or scores.")
            return EvaluationResult(
                evaluation_id=eval_id,
                evaluation_status="skipped",
                discipline=None,
                agent_used=None,
                evaluation_mode=EvaluationMode.DETERMINISTIC,
                evaluation_method="skipped",
                judge_status=JudgeStatus.NOT_USED,
                fallback_triggered=False,
                fallback_reason=None,
                quality_score=None,
                reliability_score=None,
                trust_score=None,
                trust_breakdown=None,
                criteria_breakdown=[],
                reliability_checks=[],
                evaluation_coverage=0.0,
                evaluation_summary="Evaluation skipped: Request required clarification across disciplines; no generation occurred.",
                limitations=["Clarification flow does not generate creative output; evaluation skipped."],
                evaluated_at=time.time(),
                evaluation_duration_ms=int((time.perf_counter() - started_perf) * 1000),
            )

        # 3. Handle upstream execution or validation failures
        exec_status = state.get("execution_status")
        if exec_status in ("validation_failed", "preparation_failed", "execution_failed"):
            logger.warning(f"Execution failed early with status '{exec_status}'. Running reliability checks only.")
            reliability_checks = self.reliability.evaluate(state)
            rel_score, _ = self.calculator.calculate_reliability_score(reliability_checks)

            return EvaluationResult(
                evaluation_id=eval_id,
                evaluation_status="failed",
                discipline=state.get("discipline_id"),
                agent_used=state.get("selected_persona_id"),
                evaluation_mode=EvaluationMode.DETERMINISTIC,
                evaluation_method="deterministic",
                judge_status=JudgeStatus.NOT_USED,
                fallback_triggered=False,
                fallback_reason=None,
                quality_score=None,  # Zero fabrication of quality on failed execution
                reliability_score=rel_score,
                trust_score=None,
                trust_breakdown=None,
                criteria_breakdown=[],
                reliability_checks=reliability_checks,
                evaluation_coverage=0.0,
                evaluation_summary=f"Execution failed with status '{exec_status}'. Creative quality evaluation was skipped.",
                limitations=["Execution was unsuccessful; quality cannot be assessed."],
                evaluated_at=time.time(),
                evaluation_duration_ms=int((time.perf_counter() - started_perf) * 1000),
            )

        try:
            # 4. Deterministic Reliability Checks
            reliability_checks: List[ReliabilityCheckResult] = self.reliability.evaluate(state)
            reliability_score, failed_checks = self.calculator.calculate_reliability_score(reliability_checks)

            # 5. Determine Evaluation Mode
            configured_mode_str = getattr(self.settings, "evaluation_mode", "deterministic").lower()
            eval_mode = mode_override or EvaluationMode(configured_mode_str)

            # 6. Resolve Creative Quality Evaluator
            discipline_id = state.get("discipline_id")
            quality_evaluator = self.registry.get_evaluator(discipline_id)

            criteria_results: List[CriterionResult] = []
            limitations: List[str] = []
            evaluation_summary = "Evaluation completed successfully."
            actual_method = "deterministic"
            actual_judge_status = JudgeStatus.NOT_USED
            fallback_triggered = False
            fallback_reason = None

            prompt = state.get("original_prompt", "")
            output = state.get("generated_output", "")
            persona_id = state.get("selected_persona_id")
            task_type = state.get("task_type")

            if quality_evaluator:
                limitations.extend(quality_evaluator.limitations)

                # Attempt LLM Judge if requested and configured
                judge_success = False
                if eval_mode in (EvaluationMode.LLM_JUDGE, EvaluationMode.HYBRID) and self.judge is not None:
                    judge_results, judge_status, reason = self.judge.evaluate(
                        prompt=prompt,
                        output=output,
                        discipline=quality_evaluator.discipline_id,
                        criteria_metadata=quality_evaluator.get_criteria_metadata(),
                        criteria_weights=quality_evaluator.weights,
                    )
                    actual_judge_status = judge_status
                    if judge_results:
                        criteria_results = judge_results
                        judge_success = True
                        actual_method = "llm_judge" if eval_mode == EvaluationMode.LLM_JUDGE else "hybrid"
                        evaluation_summary = "Evaluated via LLM-as-a-Judge with rubric verification."
                    else:
                        logger.warning(f"LLM Judge evaluation failed ({judge_status}): {reason}. Falling back to deterministic heuristics.")
                        fallback_triggered = True
                        fallback_reason = reason
                        limitations.append(f"LLM Judge fallback triggered ({judge_status.value}): {reason}")
                elif eval_mode in (EvaluationMode.LLM_JUDGE, EvaluationMode.HYBRID) and self.judge is None:
                    actual_judge_status = JudgeStatus.UNAVAILABLE
                    fallback_triggered = True
                    fallback_reason = "No model configured or injected for LLM Judge"
                    limitations.append("LLM Judge unavailable; fell back to deterministic heuristics.")

                # Fallback or Pure Deterministic Mode
                if not judge_success:
                    criteria_results = quality_evaluator.evaluate(
                        prompt=prompt,
                        output=output,
                        persona_id=persona_id,
                        task_type=task_type,
                    )
                    actual_method = "deterministic"
                    if not fallback_triggered:
                        evaluation_summary = "Evaluated via deterministic craft heuristics."
                    else:
                        evaluation_summary = f"Evaluated via deterministic fallback (Judge status: {actual_judge_status.value})."
            else:
                logger.warning(f"No quality evaluator registered for discipline '{discipline_id}'.")
                evaluation_summary = f"No evaluator registered for discipline '{discipline_id}'."
                limitations.append(f"Discipline '{discipline_id}' has no registered rubric evaluator.")

            # 7. Calculate Scores
            quality_score, coverage, skipped_crit = self.calculator.calculate_quality_score(criteria_results)
            trust_score, trust_breakdown = self.calculator.calculate_trust_score(
                quality_score=quality_score,
                reliability_score=reliability_score,
            )

            duration_ms = int((time.perf_counter() - started_perf) * 1000)

            return EvaluationResult(
                evaluation_id=eval_id,
                evaluation_status="completed",
                discipline=discipline_id,
                agent_used=persona_id,
                evaluation_mode=eval_mode,
                evaluation_method=actual_method,
                judge_status=actual_judge_status,
                fallback_triggered=fallback_triggered,
                fallback_reason=fallback_reason,
                quality_score=quality_score,
                reliability_score=reliability_score,
                trust_score=trust_score,
                trust_breakdown=trust_breakdown,
                criteria_breakdown=criteria_results,
                reliability_checks=reliability_checks,
                evaluation_coverage=coverage,
                evaluation_summary=evaluation_summary,
                limitations=limitations,
                evaluated_at=time.time(),
                evaluation_duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Unexpected error in evaluation engine: {e}", exc_info=True)
            duration_ms = int((time.perf_counter() - started_perf) * 1000)
            return EvaluationResult(
                evaluation_id=eval_id,
                evaluation_status="failed",
                discipline=state.get("discipline_id"),
                agent_used=state.get("selected_persona_id"),
                evaluation_mode=EvaluationMode.DETERMINISTIC,
                evaluation_method="deterministic",
                judge_status=JudgeStatus.ERROR,
                fallback_triggered=False,
                fallback_reason=f"Internal evaluation exception: {str(e)}",
                quality_score=None,
                reliability_score=None,
                trust_score=None,
                trust_breakdown=None,
                criteria_breakdown=[],
                reliability_checks=[],
                evaluation_coverage=0.0,
                evaluation_summary=f"Evaluation encountered internal error: {str(e)}",
                limitations=[f"Internal evaluation failure: {str(e)}"],
                evaluated_at=time.time(),
                evaluation_duration_ms=duration_ms,
            )
