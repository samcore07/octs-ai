"""
OCTS AI - LLM-as-a-Judge Evaluation Engine
Executes structured model-based creative quality assessments using isolated prompt framing.
Defensively parses output with Pydantic validation, rejects prompt injections,
strictly validates criterion identifiers, and provides structured transparency for fallbacks.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from langchain_core.messages import HumanMessage, SystemMessage

from backend.evaluation.judges.prompts import (
    JUDGE_SYSTEM_PROMPT,
    format_judge_human_message,
)
from backend.evaluation.schemas import CriterionResult, CriterionStatus, JudgeStatus

logger = logging.getLogger("octs.evaluation.judge")


class JudgeCriterionItem(BaseModel):
    """Pydantic schema for an individual criterion evaluated by the judge."""
    model_config = ConfigDict(extra="ignore")

    score: float = Field(..., ge=0.0, le=100.0)
    evidence: str = Field(..., min_length=1)


class JudgeRawResponse(BaseModel):
    """Pydantic schema for the complete structured JSON response expected from the LLM judge."""
    model_config = ConfigDict(extra="ignore")

    scores: Dict[str, JudgeCriterionItem]
    summary: str = Field(default="LLM-as-a-Judge evaluation completed.")


class LLMJudge:
    """
    Model-based evaluator executing structured quality assessments.
    Uses explicit dependency injection for the LLM.
    Returns (results, judge_status, failure_reason) for fallback transparency.
    """

    def __init__(
        self,
        model: Optional[Any] = None,
        timeout_seconds: float = 10.0,
        max_retries: int = 1,
    ):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def evaluate(
        self,
        prompt: str,
        output: str,
        discipline: str,
        criteria_metadata: Dict[str, Dict[str, str]],
        criteria_weights: Dict[str, float],
    ) -> Tuple[Optional[List[CriterionResult]], JudgeStatus, Optional[str]]:
        """
        Invokes the LLM judge to score the candidate output against rubric criteria.
        Returns:
            Tuple[Optional[List[CriterionResult]], JudgeStatus, Optional[str]]:
                - Evaluated criteria (or None on failure)
                - Operational JudgeStatus enum
                - Sanitized failure reason (if failed)
        """
        if self.model is None:
            logger.warning("LLMJudge invoked without an injected model instance.")
            return None, JudgeStatus.UNAVAILABLE, "No LLM model dependency provided for judge"

        human_msg_content = format_judge_human_message(
            prompt=prompt,
            output=output,
            discipline=discipline,
            criteria=criteria_metadata,
        )

        messages = [
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=human_msg_content),
        ]

        raw_text = None
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.model.invoke(messages)
                raw_text = getattr(response, "content", response)
                if isinstance(raw_text, list):
                    raw_text = "".join(
                        b.get("text", "") if isinstance(b, dict) else str(b)
                        for b in raw_text
                    )
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLMJudge model invocation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    sanitized_reason = self._sanitize_error(last_error)
                    is_timeout = (
                        isinstance(e, TimeoutError)
                        or "timeout" in sanitized_reason.lower()
                        or "timed out" in sanitized_reason.lower()
                        or "deadline" in sanitized_reason.lower()
                    )
                    status = JudgeStatus.TIMEOUT if is_timeout else JudgeStatus.ERROR
                    return None, status, sanitized_reason

        if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
            logger.warning("LLMJudge received empty or non-string response.")
            return None, JudgeStatus.INVALID_RESPONSE, "Judge produced empty response string"

        # Clean potential markdown wrapping (e.g. ```json ... ```)
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            parsed = JudgeRawResponse.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to parse or validate LLMJudge structured output: {e} | Raw text: {raw_text[:200]}")
            return None, JudgeStatus.INVALID_RESPONSE, "Malformed structured JSON output from judge"

        results: List[CriterionResult] = []
        valid_criterion_ids = set(criteria_metadata.keys())

        # Defense-in-depth: Reject any injected or hallucinated criteria not in the rubric
        for returned_cid in list(parsed.scores.keys()):
            if returned_cid not in valid_criterion_ids:
                logger.warning(f"Rejecting extraneous/injected criterion ID '{returned_cid}' from judge output.")

        for cid, meta in criteria_metadata.items():
            name = meta.get("name", cid.replace("_", " ").title())
            weight = criteria_weights.get(cid, 0.0)

            if cid in parsed.scores:
                item = parsed.scores[cid]
                score = round(max(0.0, min(100.0, float(item.score))), 2)
                weighted_score = round(score * weight, 2)
                evidence = item.evidence.strip()
                status = CriterionStatus.PASSED if score >= 70.0 else CriterionStatus.FAILED
            else:
                # Criterion omitted by judge: record as UNAVAILABLE with None score (do not fabricate score or treat as 0.0)
                logger.warning(f"LLMJudge omitted criterion '{cid}' in response. Recording as UNAVAILABLE.")
                score = None
                weighted_score = None
                evidence = "Criterion omitted by LLM Judge in structured response."
                status = CriterionStatus.UNAVAILABLE

            results.append(
                CriterionResult(
                    criterion_id=cid,
                    criterion_name=name,
                    score=score,
                    max_score=100.0,
                    weight=weight,
                    weighted_score=weighted_score,
                    evidence=evidence,
                    status=status,
                )
            )

        return results, JudgeStatus.SUCCESS, None

    @staticmethod
    def _sanitize_error(error_msg: str) -> str:
        """Sanitizes error messages to prevent leaking API keys, file paths, or private traces."""
        if not error_msg:
            return "Internal model error"
        # Redact Google/Gemini API key patterns
        sanitized = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[REDACTED_API_KEY]', error_msg)
        # Redact generic bearer tokens or key parameters
        sanitized = re.sub(r'(key|token|api_key|secret)=["\']?[^"\'\s]+["\']?', r'\1=[REDACTED]', sanitized, flags=re.IGNORECASE)
        # Bounded length
        if len(sanitized) > 120:
            sanitized = sanitized[:117] + "..."
        return sanitized
