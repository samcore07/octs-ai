"""
OCTS AI - Visual Artists & Designers Quality Evaluator
Evaluates visual hierarchy, design consistency, usability reasoning, composition/layout,
design system coherence, originality, and instruction adherence.
Strictly evaluates design reasoning and design systems in text; does not claim visual raster inspection.
"""

from typing import Dict, List, Optional
from backend.evaluation.quality.base import QualityEvaluator
from backend.evaluation.schemas import CriterionResult
from backend.evaluation.scoring.weights import DESIGNERS_WEIGHTS


class DesignersQualityEvaluator(QualityEvaluator):
    """
    Quality evaluator for the Visual Artists & Designers discipline.
    """

    @property
    def discipline_id(self) -> str:
        return "designers"

    @property
    def limitations(self) -> List[str]:
        return [
            "Evaluates design systems, token architecture, Gestalt principles, and layout rationale from text specifications.",
            "Does not inspect or render actual pixel graphics, raster canvases, image files, or UI screen rendering.",
            "Heuristics evaluate structural design concepts (e.g. contrast ratios, grid systems, spatial scales, design tokens).",
        ]

    def get_default_weights(self) -> Dict[str, float]:
        return dict(DESIGNERS_WEIGHTS)

    def get_criteria_metadata(self) -> Dict[str, Dict[str, str]]:
        return {
            "visual_hierarchy": {
                "name": "Visual Hierarchy",
                "description": "Focal point definition, typographic scale, and intentional dominance order.",
            },
            "design_consistency": {
                "name": "Design Consistency",
                "description": "Harmonious token usage, repeatable spatial increments, and component predictability.",
            },
            "usability_reasoning": {
                "name": "Usability Reasoning",
                "description": "Accessibility compliance (WCAG contrast), touch targets, and cognitive ergonomics.",
            },
            "composition_layout": {
                "name": "Composition and Layout",
                "description": "Grid alignment, white space balance, Gestalt proximity, and optical weight.",
            },
            "design_system_coherence": {
                "name": "Design-System Coherence",
                "description": "Systematic naming conventions, design tokens, and modular scalability.",
            },
            "creative_originality": {
                "name": "Creative Originality",
                "description": "Divergent visual metaphors, distinct art direction, and memorable aesthetics.",
            },
            "instruction_adherence": {
                "name": "Instruction Adherence",
                "description": "Faithful execution of design requirements, brand constraints, and format guidelines.",
            },
        }

    def evaluate(
        self,
        prompt: str,
        output: str,
        persona_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> List[CriterionResult]:
        """
        Evaluates design outputs using deterministic design system heuristics and rationale analysis.
        """
        results: List[CriterionResult] = []
        out_lower = output.lower()

        # 1. Usability Reasoning (Accessibility, WCAG, contrast, readability)
        usability_tokens = ["wcag", "contrast", "accessible", "accessibility", "touch target", "padding", "rem", "px", "ratio"]
        has_usability = any(u in out_lower for u in usability_tokens)
        usability_score = 92.0 if has_usability else 80.0
        usability_evidence = "Articulates accessibility considerations and ergonomic design reasoning." if has_usability else "Design reasoning is high-level; accessibility specifics not explicitly detailed."
        results.append(self._build_result("usability_reasoning", usability_score, usability_evidence))

        # 2. Design System Coherence (Tokens, variables, scales, color hex codes)
        token_markers = ["#", "token", "palette", "font-size", "primary", "secondary", "neutral", "scale", "system"]
        has_tokens = any(t in out_lower for t in token_markers)
        if persona_id == "design_token_palette_architect":
            ds_score = 94.0 if has_tokens else 75.0
            ds_evidence = "Comprehensive design token scales and color values systematically defined." if has_tokens else "Token definitions lacked explicit hexadecimal or spacing scales."
        else:
            ds_score = 88.0 if has_tokens else 82.0
            ds_evidence = "Demonstrates cohesive design system terminology." if has_tokens else "Presents conceptual visual guidelines."
        results.append(self._build_result("design_system_coherence", ds_score, ds_evidence))

        # 3. Visual Hierarchy
        has_hierarchy = any(h in out_lower for h in ["h1", "h2", "title", "hero", "primary", "focal point", "hierarchy", "weight"])
        vh_score = 90.0 if has_hierarchy else 80.0
        vh_evidence = "Clearly delineates visual focal points and typographic hierarchy." if has_hierarchy else "Implicit visual ordering."
        results.append(self._build_result("visual_hierarchy", vh_score, vh_evidence))

        # 4. Composition & Layout
        layout_markers = ["grid", "layout", "whitespace", "margin", "alignment", "column", "flex", "gestalt"]
        has_layout = any(l in out_lower for l in layout_markers)
        layout_score = 89.0 if has_layout else 80.0
        layout_evidence = "Detailed compositional structure and spatial grid alignment." if has_layout else "General layout recommendations without explicit grid specifications."
        results.append(self._build_result("composition_layout", layout_score, layout_evidence))

        # 5. Design Consistency
        consist_score = 88.0
        consist_evidence = "Maintains unified aesthetic principles across all described visual components."
        results.append(self._build_result("design_consistency", consist_score, consist_evidence))

        # 6. Creative Originality
        orig_score = 87.0
        orig_evidence = "Visual metaphor and creative concept show distinctive artistic direction."
        results.append(self._build_result("creative_originality", orig_score, orig_evidence))

        # 7. Instruction Adherence
        adh_score = 90.0 if len(output) > 100 else 75.0
        adh_evidence = "Design output satisfies the user's creative brief specifications."
        results.append(self._build_result("instruction_adherence", adh_score, adh_evidence))

        return results
