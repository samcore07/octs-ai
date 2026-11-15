"""
OCTS AI - Autonomous Refinement Controller
Evaluates execution state, determines whether self-correction or peer review is triggered,
and enforces bounded termination invariants.
"""

import logging
from typing import Any, Dict, Optional

from backend.config import Settings, get_settings
from backend.refinement.collaboration.reviewer_selector import ReviewerSelector
from backend.refinement.feedback_builder import FeedbackBuilder
from backend.refinement.recovery.recovery_manager import RecoveryManager
from backend.refinement.schemas import RefinementDecision

logger = logging.getLogger("octs.refinement.controller")


class RefinementController:
    """
    Orchestrates the decision engine for autonomous refinement and specialist collaboration.
    Enforces strict threshold evaluation, attempt bounding, and reviewer selection.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        feedback_builder: Optional[FeedbackBuilder] = None,
        recovery_manager: Optional[RecoveryManager] = None,
        reviewer_selector: Optional[ReviewerSelector] = None,
    ):
        self.settings = settings or get_settings()
        self.threshold = getattr(self.settings, "refinement_threshold", 70.0)
        self.max_attempts = getattr(self.settings, "refinement_max_attempts", 2)
        self.refinement_enabled = getattr(self.settings, "refinement_enabled", True)
        self.peer_review_enabled = getattr(self.settings, "peer_review_enabled", True)

        self.feedback_builder = feedback_builder or FeedbackBuilder(threshold=self.threshold)
        self.recovery_manager = recovery_manager or RecoveryManager(max_attempts=self.max_attempts)
        self.reviewer_selector = reviewer_selector or ReviewerSelector()

    def evaluate_state(self, state: Dict[str, Any]) -> RefinementDecision:
        """
        Assesses orchestration state and determines whether to trigger refinement.
        """
        # 1. Check global toggle
        if not self.refinement_enabled:
            return RefinementDecision(
                should_refine=False,
                trigger_reason="Autonomous refinement is globally disabled in configuration.",
                attempt_number=state.get("recovery_attempts", 0),
                max_attempts=self.max_attempts,
            )

        # 2. Check clarification & early failure states
        if state.get("needs_clarification"):
            return RefinementDecision(
                should_refine=False,
                trigger_reason="Clarification required; refinement bypassed.",
                attempt_number=state.get("recovery_attempts", 0),
                max_attempts=self.max_attempts,
            )

        status = state.get("execution_status")
        if status in ("validation_failed", "preparation_failed", "execution_failed"):
            return RefinementDecision(
                should_refine=False,
                trigger_reason=f"Pipeline error status '{status}'; refinement bypassed.",
                attempt_number=state.get("recovery_attempts", 0),
                max_attempts=self.max_attempts,
            )

        # 3. Check attempt limits
        current_attempts = state.get("recovery_attempts", 0)
        if not self.recovery_manager.can_attempt_recovery(current_attempts):
            return RefinementDecision(
                should_refine=False,
                trigger_reason=f"Maximum recovery attempts ({self.max_attempts}) reached.",
                attempt_number=current_attempts,
                max_attempts=self.max_attempts,
            )

        # 4. Check quality score & weak criteria
        best_eval = state.get("best_evaluation") or state.get("evaluation_result")
        quality_score = state.get("quality_score")
        if quality_score is None and isinstance(best_eval, dict):
            quality_score = best_eval.get("quality_score")

        if quality_score is None:
            return RefinementDecision(
                should_refine=False,
                trigger_reason="Evaluation quality score is unavailable; bypassing refinement.",
                attempt_number=current_attempts,
                max_attempts=self.max_attempts,
            )

        weak = self.feedback_builder.extract_weak_criteria(best_eval, threshold=self.threshold)

        if quality_score >= self.threshold and not weak:
            return RefinementDecision(
                should_refine=False,
                trigger_reason=(
                    f"Quality score ({quality_score:.1f}) meets or exceeds threshold ({self.threshold:.1f}) with zero weak criteria."
                ),
                attempt_number=current_attempts,
                max_attempts=self.max_attempts,
            )

        # 5. Score is below threshold or weak criteria present -> Refinement triggered
        next_attempt = self.recovery_manager.next_attempt_number(current_attempts)
        author_id = state.get("selected_persona_id")

        peer_reviewer_id = None
        if self.peer_review_enabled and author_id:
            peer_reviewer_id = self.reviewer_selector.select_reviewer(
                author_persona_id=author_id,
                weak_criteria=weak,
                attempt_number=next_attempt,
            )

        logger.info(
            f"Triggering refinement attempt {next_attempt}/{self.max_attempts} for persona '{author_id}'. "
            f"Quality: {quality_score:.1f} < {self.threshold:.1f}. Peer Reviewer: '{peer_reviewer_id}'."
        )

        return RefinementDecision(
            should_refine=True,
            trigger_reason=(
                f"Quality score ({quality_score:.1f}) below threshold ({self.threshold:.1f}). "
                f"Deficiencies detected: {len(weak)}."
            ),
            weak_criteria=weak,
            target_persona_id=author_id,
            peer_reviewer_id=peer_reviewer_id,
            attempt_number=next_attempt,
            max_attempts=self.max_attempts,
        )
