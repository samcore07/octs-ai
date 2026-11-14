"""
Octs AI - Pydantic Request & Response Schemas
Guarantees backward compatibility with frontend while preparing for structured agent outputs.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class PromptRequest(BaseModel):
    """
    Standard request model for task submission.
    Preserves exact backward compatibility with existing frontend payload: {"prompt": "..."}.
    """

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The creative task, goal, or query to process.",
    )
    role: Optional[str] = Field(
        default=None,
        description="Optional explicit creative discipline: writers | musicians | creators | designers",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional thread or session identifier for conversational continuity.",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Prompt cannot be empty or solely whitespace.")
        return v.strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            normalized = v.strip().lower()
            allowed = {"writers", "musicians", "creators", "designers"}
            if normalized not in allowed:
                raise ValueError(
                    f"Invalid creative role '{v}'. Allowed roles: {', '.join(sorted(allowed))}"
                )
            return normalized
        return v


class PromptResponse(BaseModel):
    """
    Standard response model for task execution.
    The 'reply' key is mandatory to guarantee zero regression with existing UI clients.
    """

    reply: str = Field(..., description="The verified creative output text.")
    role: Optional[str] = Field(default=None, description="The creative discipline utilized.")
    agent_used: Optional[str] = Field(default=None, description="The specialized agent persona invoked.")
    trust_score: Optional[float] = Field(default=None, description="Computed craft adherence and confidence score (0.0 - 100.0).")
    trust_breakdown: Optional[Dict[str, Any]] = Field(default=None, description="Detailed rubric evaluation results.")
    latency_ms: Optional[int] = Field(default=None, description="Server-measured execution latency in milliseconds.")
    recovery_triggered: bool = Field(default=False, description="Whether autonomous recovery loops were triggered.")
    model_used: Optional[str] = Field(default=None, description="The model name that produced the final output.")


class HealthResponse(BaseModel):
    """System health and diagnostic response model."""

    status: str = "ok"
    version: str = "0.2.0"
    model_provider: str
    model_name: str
    langsmith_tracing: bool
