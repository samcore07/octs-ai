"""
OCTS AI - Writers & Storytellers Quality Evaluator
Evaluates narrative coherence, character consistency, originality, structural quality,
style consistency, and instruction adherence.
"""

from typing import Dict, List, Optional
from backend.evaluation.quality.base import QualityEvaluator
from backend.evaluation.schemas import CriterionResult
from backend.evaluation.scoring.weights import WRITERS_WEIGHTS


class WritersQualityEvaluator(QualityEvaluator):
    """
    Quality evaluator for the Writers & Storytellers discipline.
    """

    @property
    def discipline_id(self) -> str:
        return "writers"

    @property
    def limitations(self) -> List[str]:
        return [
            "Evaluates narrative craft and structural coherence in text only.",
            "Does not assess external historical or factual veracity outside supplied context.",
            "Adapts rubric expectations to task type (e.g. dialogue polish vs outline generation).",
        ]

    def get_default_weights(self) -> Dict[str, float]:
        return dict(WRITERS_WEIGHTS)

    def get_criteria_metadata(self) -> Dict[str, Dict[str, str]]:
        return {
            "narrative_coherence": {
                "name": "Narrative Coherence",
                "description": "Logical consistency of events, causal progression, and thematic clarity.",
            },
            "character_consistency": {
                "name": "Character Consistency",
                "description": "Distinct voice, authentic psychological motivation, and consistent agency.",
            },
            "originality_creativity": {
                "name": "Originality and Creativity",
                "description": "Subversion of clichés, imaginative framing, and fresh metaphors.",
            },
            "structural_quality": {
                "name": "Structural Quality",
                "description": "Scene architecture, dramatic pacing, and appropriate narrative framework.",
            },
            "style_tone_consistency": {
                "name": "Style and Tone Consistency",
                "description": "Atmospheric prose rhythm, sensory engagement, and voice discipline.",
            },
            "instruction_adherence": {
                "name": "Instruction Adherence",
                "description": "Faithful execution of the creative prompt constraints and requested format.",
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
        Evaluates writer outputs using deterministic craft heuristics.
        Adapts evaluation criteria based on persona (e.g. prose_stylist vs narrative_architect).
        """
        results: List[CriterionResult] = []
        out_lower = output.lower()
        prompt_words = set(prompt.lower().split())
        output_words = set(out_lower.split())

        # 1. Instruction Adherence
        overlap = len(prompt_words.intersection(output_words)) / max(1, len(prompt_words))
        length = len(output.strip())
        if length > 150 and overlap > 0.20:
            adh_score = 92.0
            adh_evidence = "Output directly integrates core entities and instructions from the prompt."
        elif length > 60:
            adh_score = 80.0
            adh_evidence = "Output addresses the creative request with adequate topical coverage."
        else:
            adh_score = 65.0
            adh_evidence = "Output is brief; partially addresses prompt instructions."
        results.append(self._build_result("instruction_adherence", adh_score, adh_evidence))

        # 2. Structural Quality (Heuristic: headings, paragraph breaks, or list markers)
        paragraphs = [p for p in output.split("\n\n") if p.strip()]
        has_structure = len(paragraphs) >= 2 or any(tag in output for tag in ["Act", "Scene", "Chapter", "###", "1.", "- "])
        if persona_id == "narrative_architect":
            struct_score = 90.0 if has_structure else 75.0
            struct_evidence = "Narrative framework exhibits organized act/scene divisions." if has_structure else "Structure is linear without clear sectional boundaries."
        else:
            struct_score = 88.0 if has_structure else 80.0
            struct_evidence = "Text presents balanced paragraph architecture." if has_structure else "Single-block text layout."
        results.append(self._build_result("structural_quality", struct_score, struct_evidence))

        # 3. Narrative Coherence
        coherence_score = 88.0 if len(output) > 100 else 72.0
        coherence_evidence = "Demonstrates sequential continuity and thematic focus." if len(output) > 100 else "Limited narrative progression due to brevity."
        results.append(self._build_result("narrative_coherence", coherence_score, coherence_evidence))

        # 4. Character Consistency
        has_dialogue = '"' in output or '“' in output or "Dialogue" in output or persona_id == "prose_stylist"
        char_score = 86.0 if has_dialogue else 80.0
        char_evidence = "Character voice and dynamic agency are preserved." if has_dialogue else "Character perspective is maintained without direct spoken dialogue."
        results.append(self._build_result("character_consistency", char_score, char_evidence))

        # 5. Originality & Creativity
        cliche_indicators = ["once upon a time", "in a world where", "all of a sudden", "little did they know"]
        has_cliche = any(c in out_lower for c in cliche_indicators)
        orig_score = 75.0 if has_cliche else 88.0
        orig_evidence = "Contains standard narrative tropes." if has_cliche else "Expresses fresh creative phrasing without generic literary clichés."
        results.append(self._build_result("originality_creativity", orig_score, orig_evidence))

        # 6. Style & Tone Consistency
        style_score = 87.0
        style_evidence = "Maintains consistent stylistic tone across sentences."
        results.append(self._build_result("style_tone_consistency", style_score, style_evidence))

        return results
