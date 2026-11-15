"""
OCTS AI - Quality Evaluator Base Interface
Defines the standard contract for discipline-specific creative quality assessment.
Enforces non-negative weights summing to 1.0, normalized 0 - 100 scoring,
and explicit domain limitations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from backend.evaluation.schemas import CriterionResult, CriterionStatus
from backend.evaluation.scoring.weights import validate_weights


class QualityEvaluator(ABC):
    """
    Abstract base class for creative discipline evaluators.
    """

    def __init__(self, weights_override: Optional[Dict[str, float]] = None):
        self.weights = weights_override or self.get_default_weights()
        validate_weights(self.weights)

    @property
    @abstractmethod
    def discipline_id(self) -> str:
        """The identifier of the creative discipline this evaluator handles."""
        pass

    @property
    @abstractmethod
    def limitations(self) -> List[str]:
        """Explicit boundaries and craft constraints of this evaluator."""
        pass

    @abstractmethod
    def get_default_weights(self) -> Dict[str, float]:
        """Returns standard weight distribution across criteria (sums to 1.0)."""
        pass

    @abstractmethod
    def get_criteria_metadata(self) -> Dict[str, Dict[str, str]]:
        """Returns metadata (name, description) for each rubric criterion."""
        pass

    @abstractmethod
    def evaluate(
        self,
        prompt: str,
        output: str,
        persona_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> List[CriterionResult]:
        """
        Executes discipline-specific quality evaluation.
        Produces standardized CriterionResult objects with normalized scores (0 - 100).
        """
        pass

    def _build_result(
        self,
        criterion_id: str,
        score: Optional[float],
        evidence: str,
        status: CriterionStatus = CriterionStatus.PASSED,
    ) -> CriterionResult:
        """Helper to construct a validated CriterionResult."""
        meta = self.get_criteria_metadata().get(criterion_id, {})
        name = meta.get("name", criterion_id.replace("_", " ").title())
        weight = self.weights.get(criterion_id, 0.0)

        if status in (CriterionStatus.SKIPPED, CriterionStatus.UNAVAILABLE) or score is None:
            bounded_score = None
            weighted_score = None
        else:
            bounded_score = max(0.0, min(100.0, float(score)))
            weighted_score = round(bounded_score * weight, 2)

        return CriterionResult(
            criterion_id=criterion_id,
            criterion_name=name,
            score=bounded_score,
            max_score=100.0,
            weight=weight,
            weighted_score=weighted_score,
            evidence=evidence,
            status=status,
        )
