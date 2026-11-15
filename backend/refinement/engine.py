"""
OCTS AI - Refinement Engine Facade
Unifies controller decision-making, peer review collaboration, feedback synthesis,
and evaluation improvement analysis into a coherent interface.
"""

from typing import Any, Dict, List, Optional, Tuple

from backend.config import Settings, get_settings
from backend.refinement.collaboration.peer_review import PeerReviewer
from backend.refinement.collaboration.review_synthesizer import ReviewSynthesizer
from backend.refinement.collaboration.reviewer_registry import ReviewerRegistry
from backend.refinement.collaboration.reviewer_selector import ReviewerSelector
from backend.refinement.controller import RefinementController
from backend.refinement.feedback_builder import FeedbackBuilder
from backend.refinement.recovery.improvement_analyzer import ImprovementAnalyzer
from backend.refinement.recovery.recovery_manager import RecoveryManager
from backend.refinement.schemas import (
    CriterionFeedback,
    ImprovementRecord,
    PeerReviewResult,
    RefinementDecision,
    RefinementStatus,
)


class RefinementEngine:
    """
    High-level engine orchestrating autonomous recovery, specialist collaboration,
    and evaluation improvement tracking.
    """

    def __init__(
        self,
        model: Optional[Any] = None,
        settings: Optional[Settings] = None,
        reviewer_registry: Optional[ReviewerRegistry] = None,
        reviewer_selector: Optional[ReviewerSelector] = None,
        feedback_builder: Optional[FeedbackBuilder] = None,
        recovery_manager: Optional[RecoveryManager] = None,
        peer_reviewer: Optional[PeerReviewer] = None,
        review_synthesizer: Optional[ReviewSynthesizer] = None,
        improvement_analyzer: Optional[ImprovementAnalyzer] = None,
    ):
        self.settings = settings or get_settings()
        self.model = model
        self.threshold = getattr(self.settings, "refinement_threshold", 70.0)
        self.max_attempts = getattr(self.settings, "refinement_max_attempts", 2)
        self.peer_review_timeout = getattr(self.settings, "peer_review_timeout", 10.0)

        self.registry = reviewer_registry or ReviewerRegistry()
        self.selector = reviewer_selector or ReviewerSelector(registry=self.registry)
        self.feedback_builder = feedback_builder or FeedbackBuilder(threshold=self.threshold)
        self.recovery_manager = recovery_manager or RecoveryManager(max_attempts=self.max_attempts)
        self.peer_reviewer = peer_reviewer or PeerReviewer(model=self.model, timeout=self.peer_review_timeout)
        self.review_synthesizer = review_synthesizer or ReviewSynthesizer()
        self.improvement_analyzer = improvement_analyzer or ImprovementAnalyzer()

        self.controller = RefinementController(
            settings=self.settings,
            feedback_builder=self.feedback_builder,
            recovery_manager=self.recovery_manager,
            reviewer_selector=self.selector,
        )

    def decide_refinement(self, state: Dict[str, Any]) -> RefinementDecision:
        """Determines if refinement should be triggered."""
        return self.controller.evaluate_state(state)

    def conduct_peer_review(
        self,
        reviewer_persona_id: str,
        original_prompt: str,
        candidate_output: str,
        weak_criteria: Optional[List[CriterionFeedback]] = None,
    ) -> PeerReviewResult:
        """Conducts structured specialist peer review."""
        return self.peer_reviewer.review_candidate(
            reviewer_persona_id=reviewer_persona_id,
            original_prompt=original_prompt,
            candidate_output=candidate_output,
            weak_criteria=weak_criteria,
        )

    def synthesize_feedback(
        self,
        weak_criteria: List[CriterionFeedback],
        peer_review: Optional[PeerReviewResult] = None,
    ) -> str:
        """Consolidates rubric gaps and peer recommendations into unified prompt directives."""
        return self.review_synthesizer.synthesize(
            weak_criteria=weak_criteria,
            peer_review=peer_review,
        )

    def analyze_improvement(
        self,
        previous_eval: Any,
        candidate_eval: Any,
        attempt_number: int = 1,
    ) -> ImprovementRecord:
        """Compares evaluations and calculates criteria deltas."""
        return self.improvement_analyzer.analyze_improvement(
            previous_eval=previous_eval,
            candidate_eval=candidate_eval,
            attempt_number=attempt_number,
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
        """Deterministically selects candidate or reverts to previous best."""
        return self.improvement_analyzer.select_best_artifact(
            previous_output=previous_output,
            previous_eval=previous_eval,
            candidate_output=candidate_output,
            candidate_eval=candidate_eval,
            improvement_record=improvement_record,
            previous_label=previous_label,
        )
