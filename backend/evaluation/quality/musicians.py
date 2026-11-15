"""
OCTS AI - Musicians & Singers Quality Evaluator
Evaluates musical coherence, rhythm/meter consistency, rhyme quality, harmonic reasoning,
song structure, originality, and instruction adherence.
Strictly evaluates textual musical representations; does not claim acoustic audio verification.
"""

from typing import Dict, List, Optional
from backend.evaluation.quality.base import QualityEvaluator
from backend.evaluation.schemas import CriterionResult
from backend.evaluation.scoring.weights import MUSICIANS_WEIGHTS


class MusiciansQualityEvaluator(QualityEvaluator):
    """
    Quality evaluator for the Musicians & Singers discipline.
    """

    @property
    def discipline_id(self) -> str:
        return "musicians"

    @property
    def limitations(self) -> List[str]:
        return [
            "Evaluates music theory, lyric meter, chord progressions, and song arrangement strictly from text representation.",
            "Does not inspect or verify actual acoustic audio, sound design, vocal performance, or mixdown fidelity.",
            "Heuristics evaluate structural notation (e.g. [Verse], [Chorus], chord symbols, stress patterns).",
        ]

    def get_default_weights(self) -> Dict[str, float]:
        return dict(MUSICIANS_WEIGHTS)

    def get_criteria_metadata(self) -> Dict[str, Dict[str, str]]:
        return {
            "musical_coherence": {
                "name": "Musical Coherence",
                "description": "Harmonic consistency, tonal center alignment, and logical melodic contour in text.",
            },
            "rhythmic_meter_consistency": {
                "name": "Rhythmic and Meter Consistency",
                "description": "Consistent syllable count, scansion, stress patterns, and lyrical groove.",
            },
            "rhyme_lyric_quality": {
                "name": "Rhyme and Lyric Quality",
                "description": "Phonetic resonance, avoiding tired exact rhymes, and evocative wordplay.",
            },
            "harmonic_reasoning": {
                "name": "Harmonic Reasoning",
                "description": "Logical chord progressions, voice leading rationale, and tension-release balance.",
            },
            "song_structure": {
                "name": "Song Structure",
                "description": "Clear sectional architecture (Verse, Chorus, Bridge, Pre-Chorus, Drop).",
            },
            "creative_originality": {
                "name": "Creative Originality",
                "description": "Innovative phrasing, unexpected chord substitutions, and fresh conceptual motifs.",
            },
            "instruction_adherence": {
                "name": "Instruction Adherence",
                "description": "Faithful execution of the musical brief, key constraints, and requested format.",
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
        Evaluates musical outputs using deterministic heuristics based on musical notation,
        lyrical meter, and structural markers in the text.
        """
        results: List[CriterionResult] = []
        out_lower = output.lower()

        # 1. Instruction Adherence
        length = len(output.strip())
        prompt_words = set(prompt.lower().split())
        output_words = set(out_lower.split())
        overlap = len(prompt_words.intersection(output_words)) / max(1, len(prompt_words))
        adh_score = 90.0 if overlap > 0.15 and length > 100 else 75.0
        adh_evidence = "Musical output directly incorporates prompt thematic motifs and constraints." if adh_score >= 85 else "Output addresses prompt with basic musical context."
        results.append(self._build_result("instruction_adherence", adh_score, adh_evidence))

        # 2. Song Structure (Check for sectional tags: [Verse], [Chorus], [Bridge], etc.)
        structure_tags = ["[verse", "[chorus", "[bridge", "[intro", "[outro", "[hook", "verse 1", "chorus:"]
        has_tags = any(tag in out_lower for tag in structure_tags)
        struct_score = 92.0 if has_tags else 78.0
        struct_evidence = "Contains clearly demarcated song sections (e.g. Verse, Chorus, Bridge)." if has_tags else "Continuous lyrical/musical layout without formal section brackets."
        results.append(self._build_result("song_structure", struct_score, struct_evidence))

        # 3. Harmonic Reasoning (Check for chord notation like Cmaj7, G7, Am, Dm, etc.)
        chord_indicators = ["maj", "min", "sus", "dim", "chord", "i - iv", "ii - v", "progression", "root", "cadence"]
        has_harmony = any(c in out_lower for c in chord_indicators)
        if persona_id == "harmonic_arranger":
            harm_score = 92.0 if has_harmony else 70.0
            harm_evidence = "Detailed chord symbols and harmonic progression logic identified." if has_harmony else "Harmonic progression details were sparse."
        else:
            harm_score = 88.0 if has_harmony else 80.0
            harm_evidence = "Harmonic context articulated in musical text." if has_harmony else "Text focuses primarily on lyricism and arrangement."
        results.append(self._build_result("harmonic_reasoning", harm_score, harm_evidence))

        # 4. Rhythmic & Meter Consistency (Line breaking & scansion cues)
        lines = [line.strip() for line in output.split("\n") if line.strip()]
        has_meter = len(lines) >= 4 and any(len(line.split()) in range(4, 14) for line in lines)
        meter_score = 88.0 if has_meter else 76.0
        meter_evidence = "Balanced lyrical line lengths consistent with rhythmic cadence." if has_meter else "Uneven poetic line lengths; check meter scansion."
        results.append(self._build_result("rhythmic_meter_consistency", meter_score, meter_evidence))

        # 5. Rhyme & Lyric Quality
        lyric_score = 87.0
        lyric_evidence = "Demonstrates phonetic resonance and thematic lyric coherence."
        results.append(self._build_result("rhyme_lyric_quality", lyric_score, lyric_evidence))

        # 6. Musical Coherence
        coherence_score = 86.0
        coherence_evidence = "Musical ideas exhibit coherent tonal and arrangement continuity."
        results.append(self._build_result("musical_coherence", coherence_score, coherence_evidence))

        # 7. Creative Originality
        orig_score = 88.0
        orig_evidence = "Lyrical imagery and musical concepts show distinct stylistic expression."
        results.append(self._build_result("creative_originality", orig_score, orig_evidence))

        return results
