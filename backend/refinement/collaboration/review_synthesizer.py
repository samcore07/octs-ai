"""
OCTS AI - Review Synthesizer
Combines objective rubric evaluation deficiencies and specialist peer review
critiques into unified, non-conflicting, prioritized refinement directives.
Sanitizes peer reviews to prevent prompt injection and brief mutation.
"""

from typing import List, Optional, Set
from backend.evaluation.scoring.weights import DISCIPLINE_DEFAULT_WEIGHTS
from backend.refinement.schemas import CriterionFeedback, PeerReviewResult


class ReviewSynthesizer:
    """
    Synthesizes rubric deficiency feedback and peer review critiques.
    Resolves potential contradictions, prioritizes core craft constraints,
    and defends against prompt injection or user brief modification.
    """

    ALL_VALID_CRITERIA: Set[str] = {
        cid for matrix in DISCIPLINE_DEFAULT_WEIGHTS.values() for cid in matrix.keys()
    }

    def synthesize(
        self,
        weak_criteria: List[CriterionFeedback],
        peer_review: Optional[PeerReviewResult] = None,
    ) -> str:
        """
        Creates a prioritized, consolidated feedback block for the author persona.
        """
        sections: List[str] = []

        # 1. Preservation Mandates
        strengths: List[str] = []
        if peer_review and peer_review.strengths:
            for s in peer_review.strengths:
                clean = self._sanitize_text(s)
                if clean:
                    strengths.append(clean)
        if not strengths:
            strengths.append("Preserve core premise, persona tone, and established creative direction.")

        sections.append("### 1. Strengths to Retain")
        for s in strengths:
            sections.append(f"- {s}")

        # 2. Priority Rubric Remediations (Highest precedence)
        sections.append("\n### 2. Mandatory Rubric Remediations (Priority)")
        valid_weak = [
            item for item in weak_criteria
            if item.criterion_id in self.ALL_VALID_CRITERIA or not self.ALL_VALID_CRITERIA
        ]

        if valid_weak:
            for item in valid_weak:
                rec = self._sanitize_text(item.actionable_recommendation)
                sections.append(
                    f"- **{item.criterion_name}** (Gap: {item.gap:.1f} pts): {rec}"
                )
        else:
            sections.append("- Elevate craft nuance, eliminate generic phrasing, and deepen domain rigor.")

        # 3. Specialist Peer Recommendations (Secondary guidance)
        if peer_review and peer_review.suggested_improvements:
            reviewer_name = self._sanitize_text(peer_review.reviewer_persona_name) or "Peer Reviewer"
            sections.append(f"\n### 3. Peer Specialist Advice (from {reviewer_name})")
            seen_recs = set()
            for imp in peer_review.suggested_improvements:
                clean_imp = self._sanitize_text(imp)
                if clean_imp and clean_imp.lower() not in seen_recs:
                    sections.append(f"- {clean_imp}")
                    seen_recs.add(clean_imp.lower())

        return "\n".join(sections)

    @staticmethod
    def _sanitize_text(text: str) -> str:
        """Strips dangerous injection keywords, script tags, and excessive length."""
        if not text:
            return ""
        s = str(text).strip()
        # Truncate overly long strings
        if len(s) > 1000:
            s = s[:1000]
        # Neutralize common prompt injection patterns
        for pattern in [
            "system override",
            "system prompt override",
            "ignore previous instructions",
            "ignore constraints",
            "disregard instructions",
            "bypass rubric",
            "<script>",
        ]:
            s = re_sub_insensitive(pattern, "[REDACTED_ADVERSARIAL_INSTRUCTION]", s)
        return s


def re_sub_insensitive(pattern: str, repl: str, text: str) -> str:
    """Case-insensitive string replacement."""
    import re
    return re.sub(re.escape(pattern), repl, text, flags=re.IGNORECASE)
