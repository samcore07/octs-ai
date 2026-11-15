"""
OCTS AI - Evaluation Package
Provides independent Creative Quality and Execution Reliability evaluation,
scoring calculation, deterministic checks, and LLM-as-a-Judge assessment.
"""

from backend.evaluation.engine import EvaluationEngine
from backend.evaluation.evaluator_registry import EvaluatorRegistry, get_evaluator_registry
from backend.evaluation.schemas import (
    CheckSeverity,
    CriterionResult,
    CriterionStatus,
    EvaluationMode,
    EvaluationResult,
    JudgeStatus,
    ReliabilityCheckResult,
    TrustBreakdown,
)
from backend.evaluation.scoring.calculator import ScoringCalculator
from backend.evaluation.scoring.weights import validate_weights

__all__ = [
    "EvaluationEngine",
    "EvaluatorRegistry",
    "get_evaluator_registry",
    "EvaluationResult",
    "CriterionResult",
    "ReliabilityCheckResult",
    "TrustBreakdown",
    "EvaluationMode",
    "JudgeStatus",
    "CriterionStatus",
    "CheckSeverity",
    "ScoringCalculator",
    "validate_weights",
]
