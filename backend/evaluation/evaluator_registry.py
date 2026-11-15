"""
OCTS AI - Evaluator Registry
Central registry managing discipline-specific quality evaluators.
Enables O(1) lookup and dynamic extensibility.
"""

from typing import Dict, List, Optional
from backend.evaluation.quality.base import QualityEvaluator
from backend.evaluation.quality.writers import WritersQualityEvaluator
from backend.evaluation.quality.musicians import MusiciansQualityEvaluator
from backend.evaluation.quality.creators import CreatorsQualityEvaluator
from backend.evaluation.quality.designers import DesignersQualityEvaluator


class EvaluatorRegistry:
    """
    Registry for quality evaluators mapped by discipline identifier.
    """

    def __init__(self):
        self._evaluators: Dict[str, QualityEvaluator] = {}
        self._register_default_evaluators()

    def _register_default_evaluators(self):
        """Initializes standard evaluators for the 4 core creative disciplines."""
        self.register(WritersQualityEvaluator())
        self.register(MusiciansQualityEvaluator())
        self.register(CreatorsQualityEvaluator())
        self.register(DesignersQualityEvaluator())

    def register(self, evaluator: QualityEvaluator):
        """Registers a quality evaluator instance."""
        self._evaluators[evaluator.discipline_id] = evaluator

    def get_evaluator(self, discipline_id: Optional[str]) -> Optional[QualityEvaluator]:
        """Resolves evaluator for a given discipline identifier."""
        if not discipline_id:
            return None
        return self._evaluators.get(discipline_id.strip().lower())

    def list_disciplines(self) -> List[str]:
        """Returns all registered discipline identifiers."""
        return sorted(list(self._evaluators.keys()))


_GLOBAL_EVALUATOR_REGISTRY: Optional[EvaluatorRegistry] = None


def get_evaluator_registry() -> EvaluatorRegistry:
    """Returns singleton instance of the EvaluatorRegistry."""
    global _GLOBAL_EVALUATOR_REGISTRY
    if _GLOBAL_EVALUATOR_REGISTRY is None:
        _GLOBAL_EVALUATOR_REGISTRY = EvaluatorRegistry()
    return _GLOBAL_EVALUATOR_REGISTRY
