"""
OCTS AI - Refinement Feedback Builder
Transforms Phase 4 evaluation results into structured, actionable feedback
and formatted prompts targeting weak rubric criteria.
"""

from typing import Any, Dict, List, Optional
from backend.evaluation.schemas import CriterionResult, EvaluationResult
from backend.refinement.schemas import CriterionFeedback, PeerReviewResult


class FeedbackBuilder:
    """
    Constructs targeted, actionable feedback from evaluation weaknesses
    and synthesizes prompts for specialist self-correction.
    """

    def __init__(self, threshold: float = 70.0):
        self.threshold = threshold

    def extract_weak_criteria(
        self,
        evaluation: Any,
        threshold: Optional[float] = None,
    ) -> List[CriterionFeedback]:
        """
        Scans evaluation criteria and identifies items scoring below threshold.
        Accepts EvaluationResult, dict, or list of CriterionResult.
        """
        active_threshold = threshold if threshold is not None else self.threshold
        criteria_list: List[Any] = []

        if isinstance(evaluation, EvaluationResult):
            criteria_list = evaluation.criteria_breakdown
        elif isinstance(evaluation, dict):
            raw_breakdown = evaluation.get("criteria_breakdown", [])
            for item in raw_breakdown:
                if isinstance(item, dict):
                    criteria_list.append(CriterionResult(**item))
                elif isinstance(item, CriterionResult):
                    criteria_list.append(item)
        elif isinstance(evaluation, list):
            criteria_list = evaluation

        weak: List[CriterionFeedback] = []
        for cr in criteria_list:
            if not isinstance(cr, CriterionResult):
                continue
            if cr.score is not None and cr.score < active_threshold:
                gap = round(max(0.0, 100.0 - cr.score), 2)
                recommendation = self._generate_recommendation(cr.criterion_id, cr.evidence)
                weak.append(
                    CriterionFeedback(
                        criterion_id=cr.criterion_id,
                        criterion_name=cr.criterion_name,
                        current_score=cr.score,
                        max_score=cr.max_score,
                        gap=gap,
                        deficiency_summary=cr.evidence or "Did not meet target quality threshold.",
                        actionable_recommendation=recommendation,
                    )
                )

        # Sort descending by gap so most severe deficiency comes first
        weak.sort(key=lambda x: x.gap, reverse=True)
        return weak

    def _generate_recommendation(self, criterion_id: str, evidence: str) -> str:
        """
        Derives an actionable craft remediation recommendation based on criterion id.
        """
        cid = criterion_id.lower()
        if "narrative" in cid or "coherence" in cid:
            return "Reinforce causal logic between events; ensure every scene beat directly triggers the next."
        if "character" in cid:
            return "Sharpen character voice, internal motivation, and active decision-making agency."
        if "originality" in cid or "creativity" in cid:
            return "Subvert familiar tropes with unexpected twists, deeper nuance, or fresh metaphorical framing."
        if "structure" in cid or "structural" in cid:
            return "Organize content with clear sectional hierarchy, distinct headings, and controlled pacing."
        if "style" in cid or "tone" in cid:
            return "Maintain consistent stylistic rhythm, sensory specificity, and atmospheric vocabulary."
        if "instruction" in cid or "adherence" in cid:
            return "Directly address all constraints, format requirements, and explicit details requested in the prompt."
        if "meter" in cid or "rhythm" in cid or "cadence" in cid:
            return "Tighten syllable counts, align stress accents with the rhythmic pulse, and smooth vocal flow."
        if "harmony" in cid or "chord" in cid:
            return "Enrich harmonic progression with modal interchange, secondary dominants, and smooth voice leading."
        if "hook" in cid or "retention" in cid:
            return "Front-load visceral stakes, curiosity gaps, and dynamic pacing in the opening beats."
        if "friction" in cid or "clarity" in cid:
            return "Eliminate ambiguity, reduce cognitive overhead, and clarify the core takeaway."
        if "token" in cid or "color" in cid or "contrast" in cid:
            return "Verify color contrast ratios, systematize spacing tokens, and adhere to accessible scale steps."
        if "hierarchy" in cid or "grid" in cid or "visual" in cid:
            return "Enforce strict typographic scale, align elements to a 4/8pt baseline grid, and balance whitespace."
        return f"Address deficiency identified: {evidence}"

    def build_refinement_prompt(
        self,
        original_prompt: str,
        previous_output: str,
        weak_criteria: List[CriterionFeedback],
        persona_name: str,
        peer_review: Optional[PeerReviewResult] = None,
    ) -> str:
        """
        Compiles the complete refinement instruction prompt provided to the specialist persona.
        """
        lines = [
            f"# AUTONOMOUS CRAFT REFINEMENT DIRECTIVE",
            f"You are refining your previous generation to eliminate identified craft deficiencies.",
            "",
            "## 1. Original Creative Request",
            f"{original_prompt.strip()}",
            "",
            "## 2. Previous Candidate Draft",
            "```text",
            f"{previous_output.strip()}",
            "```",
            "",
            "## 3. Rubric Deficiencies to Remediate",
        ]

        if not weak_criteria:
            lines.append("- Output fell short of composite quality threshold; elevate depth, polish, and craft nuance.")
        else:
            for item in weak_criteria:
                lines.append(
                    f"- **{item.criterion_name}** (Current Score: {item.current_score:.1f}/100, Gap: {item.gap:.1f}):"
                )
                lines.append(f"  * Deficiency: {item.deficiency_summary}")
                lines.append(f"  * Mandatory Fix: {item.actionable_recommendation}")

        if peer_review and peer_review.status != "skipped":
            lines.append("")
            lines.append(f"## 4. Specialist Peer Critique (from {peer_review.reviewer_persona_name})")
            if peer_review.strengths:
                lines.append("**Preserve These Strengths:**")
                for s in peer_review.strengths:
                    lines.append(f"- {s}")
            if peer_review.actionable_critique:
                lines.append("**Peer Critiques:**")
                for c in peer_review.actionable_critique:
                    lines.append(f"- {c}")
            if peer_review.suggested_improvements:
                lines.append("**Peer Recommendations:**")
                for rec in peer_review.suggested_improvements:
                    lines.append(f"- {rec}")

        lines.extend([
            "",
            "## 5. Execution Instructions",
            "1. Produce a COMPLETE, fully realized new version of the output.",
            "2. DO NOT output partial fragments, diffs, apologies, or conversational meta-commentary.",
            "3. Maintain all successful elements of the previous draft while directly resolving the weaknesses above.",
            "4. Strictly adhere to your persona's domain constraints and structural guidelines.",
            "",
            "Begin the refined generation now:",
        ])

        return "\n".join(lines)
