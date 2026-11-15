"""
OCTS AI - Reliability Evaluator
Executes deterministic execution integrity checks against orchestration state.
Does not make subjective judgments or invoke LLMs.
"""

from typing import Any, Dict, List, Optional
from backend.agents.registry import AgentRegistry, get_registry
from backend.evaluation.schemas import ReliabilityCheckResult
from backend.evaluation.reliability.checks import (
    check_execution_successful,
    check_latency_recorded,
    check_output_exists,
    check_output_not_empty,
    check_persona_discipline_match,
    check_persona_resolved,
    check_substantive_length,
)


class ReliabilityEvaluator:
    """
    Evaluates system execution reliability using strictly deterministic invariants.
    """

    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or get_registry()

    def evaluate(self, state: Dict[str, Any]) -> List[ReliabilityCheckResult]:
        """
        Executes all registered deterministic checks against the orchestration state.
        """
        checks: List[ReliabilityCheckResult] = [
            check_output_exists(state),
            check_output_not_empty(state),
            check_persona_resolved(state, registry=self.registry),
            check_persona_discipline_match(state, registry=self.registry),
            check_execution_successful(state),
            check_latency_recorded(state),
            check_substantive_length(state),
        ]
        return checks
