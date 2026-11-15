"""
OCTS AI - Refinement & Collaboration Schemas
Defines strongly typed Pydantic models for autonomous self-correction,
specialist peer review, and evaluation improvement tracking.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RefinementStatus(str, Enum):
    """Operational status of the refinement process."""
    NOT_NEEDED = "not_needed"
    IMPROVED = "improved"
    REGRESSED_REVERTED = "regressed_reverted"
    MAX_ATTEMPTS_REACHED = "max_attempts_reached"
    FAILED = "failed"
    SKIPPED = "skipped"


class PeerReviewStatus(str, Enum):
    """Operational status of the peer review step."""
    COMPLETED = "completed"
    FALLBACK = "fallback"
    SKIPPED = "skipped"
    FAILED = "failed"


class CriterionFeedback(BaseModel):
    """
    Structured feedback for an individual rubric criterion scoring below target threshold.
    """
    model_config = ConfigDict(extra="ignore")

    criterion_id: str = Field(..., description="Machine identifier of the criterion.")
    criterion_name: str = Field(..., description="Human-readable title of the criterion.")
    current_score: float = Field(..., ge=0.0, le=100.0, description="Assigned score from evaluation.")
    max_score: float = Field(default=100.0, description="Maximum scale score.")
    gap: float = Field(..., ge=0.0, le=100.0, description="Score gap relative to maximum or threshold.")
    deficiency_summary: str = Field(..., description="Summary of why the criterion scored low.")
    actionable_recommendation: str = Field(..., description="Concrete instruction for how to remediate the deficiency.")


class PeerReviewResult(BaseModel):
    """
    Structured critique and review output from a peer specialist persona.
    Includes explicit fallback transparency metadata.
    """
    model_config = ConfigDict(extra="ignore")

    reviewer_persona_id: str = Field(..., description="Identifier of the reviewer persona.")
    reviewer_persona_name: str = Field(..., description="Display name of the reviewer persona.")
    reviewer_discipline: str = Field(..., description="Creative discipline of the reviewer.")
    strengths: List[str] = Field(default_factory=list, description="Preserved positive attributes of the candidate.")
    actionable_critique: List[str] = Field(default_factory=list, description="Specific deficiencies identified.")
    suggested_improvements: List[str] = Field(default_factory=list, description="Targeted remediation proposals.")
    rubric_alignment_notes: Optional[str] = Field(default=None, description="Observations aligning with rubric criteria.")
    status: PeerReviewStatus = Field(default=PeerReviewStatus.COMPLETED, description="Status of the peer review.")
    review_method: str = Field(default="llm", description="Method that produced critique: llm | heuristic")
    fallback_triggered: bool = Field(default=False, description="Whether fallback logic was triggered due to reviewer error/timeout.")
    fallback_reason: Optional[str] = Field(default=None, description="Sanitized reason for triggering reviewer fallback.")


class RefinementDecision(BaseModel):
    """
    Deterministic decision indicating whether refinement is warranted and how it should proceed.
    """
    model_config = ConfigDict(extra="ignore")

    should_refine: bool = Field(..., description="Whether to trigger refinement iteration.")
    trigger_reason: str = Field(..., description="Rationale for triggering or bypassing refinement.")
    weak_criteria: List[CriterionFeedback] = Field(default_factory=list, description="Identified weak criteria.")
    target_persona_id: Optional[str] = Field(default=None, description="Author persona responsible for refinement.")
    peer_reviewer_id: Optional[str] = Field(default=None, description="Selected peer reviewer persona, if any.")
    attempt_number: int = Field(default=0, ge=0, description="Current recovery attempt counter.")
    max_attempts: int = Field(default=2, ge=0, le=5, description="Maximum allowed recovery attempts (0 to 5).")


class ImprovementRecord(BaseModel):
    """
    Telemetry record comparing candidate refinement against previous best evaluation.
    Evaluates multi-dimensional criteria including Quality, Reliability, Coverage, and TrustScore.
    """
    model_config = ConfigDict(extra="ignore")

    attempt_number: int = Field(..., ge=1, description="Recovery attempt number.")
    selection_reason: str = Field(default="", description="Policy rationale explaining why candidate was accepted or rejected.")
    candidate_accepted: bool = Field(default=False, description="Whether this candidate was accepted as new best output.")
    is_improvement: bool = Field(default=False, description="Synonym for candidate_accepted for backward compatibility.")
    previous_best_score: Optional[float] = Field(default=None, description="Composite or primary quality score of previous best.")
    candidate_score: Optional[float] = Field(default=None, description="Composite or primary quality score of candidate.")
    previous_quality_score: Optional[float] = Field(default=None, description="Quality score before this refinement.")
    new_quality_score: Optional[float] = Field(default=None, description="Quality score achieved by candidate output.")
    quality_delta: Optional[float] = Field(default=None, description="Change in quality score (+/-).")
    previous_reliability_score: Optional[float] = Field(default=None, description="Reliability score before this refinement.")
    new_reliability_score: Optional[float] = Field(default=None, description="Reliability score achieved by candidate output.")
    reliability_delta: Optional[float] = Field(default=None, description="Change in reliability score (+/-).")
    previous_coverage: Optional[float] = Field(default=None, description="Evaluation coverage before this refinement (0.0 - 1.0).")
    new_coverage: Optional[float] = Field(default=None, description="Evaluation coverage of candidate output (0.0 - 1.0).")
    coverage_delta: Optional[float] = Field(default=None, description="Change in evaluation coverage (+/-).")
    previous_trust_score: Optional[float] = Field(default=None, description="TrustScore before this refinement.")
    new_trust_score: Optional[float] = Field(default=None, description="TrustScore achieved by candidate output.")
    trust_delta: Optional[float] = Field(default=None, description="Change in composite TrustScore (+/-).")
    improved_criteria: List[str] = Field(default_factory=list, description="Criteria IDs that improved.")
    regressed_criteria: List[str] = Field(default_factory=list, description="Criteria IDs that regressed.")
    unchanged_criteria: List[str] = Field(default_factory=list, description="Criteria IDs unchanged.")
    critical_regression_detected: bool = Field(default=False, description="Whether a critical check or severe criterion regression was flagged.")
    rationale: str = Field(default="", description="Summary explanation of acceptance or regression reversion decision.")

    @model_validator(mode="after")
    def populate_defaults(self) -> "ImprovementRecord":
        if not self.selection_reason and self.rationale:
            self.selection_reason = self.rationale
        elif not self.rationale and self.selection_reason:
            self.rationale = self.selection_reason
        return self


class RefinementMetadata(BaseModel):
    """
    Public metadata payload returned in PromptResponse describing refinement lifecycle and telemetry.
    """
    model_config = ConfigDict(extra="ignore")

    refinement_triggered: bool = Field(default=False, description="Whether autonomous refinement loops executed.")
    recovery_attempts: int = Field(default=0, ge=0, description="Total refinement attempts executed.")
    max_recovery_attempts: int = Field(default=2, ge=0, description="Configured maximum recovery attempts limit.")
    initial_quality_score: Optional[float] = Field(default=None, description="Quality score of original initial generation.")
    final_quality_score: Optional[float] = Field(default=None, description="Quality score of final selected generation.")
    quality_delta: Optional[float] = Field(default=None, description="Overall net quality improvement.")
    initial_trust_score: Optional[float] = Field(default=None, description="Composite TrustScore of original initial generation.")
    final_trust_score: Optional[float] = Field(default=None, description="Composite TrustScore of final selected generation.")
    trust_delta: Optional[float] = Field(default=None, description="Overall net TrustScore change.")
    peer_review_conducted: bool = Field(default=False, description="Whether specialist peer review was performed.")
    reviewer_persona_id: Optional[str] = Field(default=None, description="Identifier of the peer reviewer persona.")
    refinement_status: str = Field(
        default=RefinementStatus.NOT_NEEDED.value,
        description="Lifecycle status: not_needed | improved | regressed_reverted | max_attempts_reached | failed | skipped",
    )
    improvement_history: List[ImprovementRecord] = Field(
        default_factory=list,
        description="Detailed chronological log of each refinement attempt.",
    )
    best_output_selected: str = Field(
        default="initial",
        description="Which output candidate was selected for final return (e.g. 'initial', 'attempt_1').",
    )

    # Lightweight performance telemetry
    initial_generation_latency_ms: Optional[int] = Field(default=None, description="Latency in ms of initial generation.")
    peer_review_latency_ms: Optional[int] = Field(default=None, description="Cumulative latency in ms of peer review calls.")
    refinement_generation_latency_ms: Optional[int] = Field(default=None, description="Cumulative latency in ms of refinement calls.")
    evaluation_latency_ms: Optional[int] = Field(default=None, description="Cumulative latency in ms incurred by evaluation.")
    total_refinement_latency_ms: Optional[int] = Field(default=None, description="Total wall-clock duration of refinement loop.")
    model_call_count: int = Field(default=0, description="Total LLM invocations executed across pipeline.")
    reviewer_call_count: int = Field(default=0, description="Total peer reviewer invocations executed.")
