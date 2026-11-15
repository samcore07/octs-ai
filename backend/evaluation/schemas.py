"""
OCTS AI - Evaluation Engine Pydantic Schemas
Defines strongly typed data structures for quality criteria, reliability checks,
scoring breakdowns, LLM judge status, and unified evaluation results.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvaluationMode(str, Enum):
    """Operational mode for the evaluation engine."""
    DETERMINISTIC = "deterministic"
    LLM_JUDGE = "llm_judge"
    HYBRID = "hybrid"


class JudgeStatus(str, Enum):
    """Operational status of the LLM-as-a-Judge execution."""
    NOT_USED = "not_used"
    SUCCESS = "success"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


class CriterionStatus(str, Enum):
    """Execution status for an individual rubric criterion."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"


class CheckSeverity(str, Enum):
    """Severity classification for deterministic reliability checks."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class CriterionResult(BaseModel):
    """
    Evaluated result for a single domain-specific craft criterion.
    Standardized on a 0.0 - 100.0 normalized scale.
    score and weighted_score are None when status is SKIPPED or UNAVAILABLE.
    """
    model_config = ConfigDict(extra="ignore")

    criterion_id: str = Field(..., description="Unique machine identifier (e.g. narrative_coherence).")
    criterion_name: str = Field(..., description="Human-readable title of the criterion.")
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Normalized score achieved (0 - 100), or None if skipped/unavailable.",
    )
    max_score: float = Field(default=100.0, description="Maximum possible score for normalization.")
    weight: float = Field(..., ge=0.0, le=1.0, description="Relative criterion weight within the discipline rubric.")
    weighted_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Score multiplied by weight, or None if skipped/unavailable.",
    )
    evidence: str = Field(..., description="Concise evidence or rationale supporting the assigned score.")
    status: CriterionStatus = Field(default=CriterionStatus.PASSED, description="Evaluation outcome status.")


class ReliabilityCheckResult(BaseModel):
    """
    Evaluated result for a single deterministic execution health check.
    """
    model_config = ConfigDict(extra="ignore")

    check_id: str = Field(..., description="Unique machine identifier for the check.")
    check_name: str = Field(..., description="Human-readable title of the check.")
    status: CriterionStatus = Field(..., description="Execution status: passed, failed, skipped, unavailable.")
    severity: CheckSeverity = Field(default=CheckSeverity.CRITICAL, description="Severity if this check fails.")
    explanation: str = Field(..., description="Concise explanation of check execution and findings.")


class TrustBreakdown(BaseModel):
    """
    Detailed mathematical breakdown of the composite TrustScore calculation.
    """
    model_config = ConfigDict(extra="ignore")

    quality_score: Optional[float] = Field(default=None, description="Weighted average of creative quality criteria (0 - 100).")
    reliability_score: Optional[float] = Field(default=None, description="Score derived from deterministic execution checks (0 - 100).")
    quality_weight: float = Field(default=0.70, description="Configured weight for creative quality.")
    reliability_weight: float = Field(default=0.30, description="Configured weight for execution reliability.")
    formula_explanation: str = Field(
        default="TrustScore = (QualityScore * quality_weight) + (ReliabilityScore * reliability_weight)",
        description="Explanation of the composite TrustScore calculation.",
    )


class EvaluationResult(BaseModel):
    """
    Unified payload encapsulating the full evaluation outcome.
    Preserves independent Quality and Reliability dimensions alongside composite TrustScore.
    Includes explicit fallback transparency metadata for LLM-as-a-Judge.
    """
    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    evaluation_id: str = Field(..., description="Unique UUID for this evaluation execution.")
    evaluation_status: str = Field(
        ...,
        description="Status: completed | partially_completed | failed | skipped | unavailable",
    )
    discipline: Optional[str] = Field(default=None, description="Evaluated creative discipline.")
    agent_used: Optional[str] = Field(default=None, description="Evaluated specialist persona.")
    evaluation_mode: EvaluationMode = Field(
        default=EvaluationMode.DETERMINISTIC,
        description="Configured evaluation mode.",
    )
    evaluation_method: str = Field(
        default="deterministic",
        description="Actual method that produced final quality score: deterministic | llm_judge | hybrid",
    )
    judge_status: JudgeStatus = Field(
        default=JudgeStatus.NOT_USED,
        description="Operational status of the LLM-as-a-Judge execution.",
    )
    fallback_triggered: bool = Field(
        default=False,
        description="Whether deterministic fallback was triggered due to judge failure.",
    )
    fallback_reason: Optional[str] = Field(
        default=None,
        description="Sanitized reason for triggering fallback.",
    )
    quality_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Subjective/rubric creative quality score (0 - 100).",
    )
    reliability_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Objective deterministic reliability score (0 - 100).",
    )
    trust_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Composite TrustScore balancing quality and reliability (0 - 100).",
    )
    trust_breakdown: Optional[TrustBreakdown] = Field(
        default=None,
        description="Component breakdown of TrustScore calculation.",
    )
    criteria_breakdown: List[CriterionResult] = Field(
        default_factory=list,
        description="Discipline-specific quality rubric criteria results.",
    )
    reliability_checks: List[ReliabilityCheckResult] = Field(
        default_factory=list,
        description="Deterministic reliability and execution health checks.",
    )
    evaluation_coverage: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Fraction of applicable criteria successfully evaluated (0.0 - 1.0).",
    )
    evaluation_summary: str = Field(
        ...,
        description="High-level diagnostic summary of the evaluation.",
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Explicit boundaries of the evaluation (e.g. text-only reasoning, no audio/visual verification).",
    )
    evaluated_at: float = Field(..., description="Unix timestamp when evaluation was completed.")
    evaluation_duration_ms: int = Field(default=0, description="Latency in milliseconds incurred by evaluation.")
