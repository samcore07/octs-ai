"""
OCTS AI - Evaluation Criteria Weights & Standards
Defines default rubric weight matrices for each discipline and provides weight validation utilities.
"""

from typing import Dict

# Writers & Storytellers Criteria Weights (Sum: 1.0)
WRITERS_WEIGHTS: Dict[str, float] = {
    "narrative_coherence": 0.20,
    "character_consistency": 0.15,
    "originality_creativity": 0.15,
    "structural_quality": 0.15,
    "style_tone_consistency": 0.15,
    "instruction_adherence": 0.20,
}

# Musicians & Singers Criteria Weights (Sum: 1.0)
MUSICIANS_WEIGHTS: Dict[str, float] = {
    "musical_coherence": 0.15,
    "rhythmic_meter_consistency": 0.15,
    "rhyme_lyric_quality": 0.15,
    "harmonic_reasoning": 0.15,
    "song_structure": 0.15,
    "creative_originality": 0.10,
    "instruction_adherence": 0.15,
}

# Content Creators Criteria Weights (Sum: 1.0)
CREATORS_WEIGHTS: Dict[str, float] = {
    "hook_effectiveness": 0.20,
    "audience_relevance": 0.15,
    "clarity_communication": 0.15,
    "retention_potential": 0.15,
    "platform_suitability": 0.15,
    "content_structure": 0.10,
    "instruction_adherence": 0.10,
}

# Visual Artists & Designers Criteria Weights (Sum: 1.0)
DESIGNERS_WEIGHTS: Dict[str, float] = {
    "visual_hierarchy": 0.15,
    "design_consistency": 0.15,
    "usability_reasoning": 0.15,
    "composition_layout": 0.15,
    "design_system_coherence": 0.15,
    "creative_originality": 0.10,
    "instruction_adherence": 0.15,
}

DISCIPLINE_DEFAULT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "writers": WRITERS_WEIGHTS,
    "musicians": MUSICIANS_WEIGHTS,
    "creators": CREATORS_WEIGHTS,
    "designers": DESIGNERS_WEIGHTS,
}


def validate_weights(weights: Dict[str, float], tolerance: float = 1e-4) -> bool:
    """
    Validates that weights are strictly non-negative and sum to 1.0 within tolerance.
    Raises ValueError on invalid weights.
    """
    if not weights:
        raise ValueError("Weights dictionary cannot be empty.")

    total = 0.0
    for key, weight in weights.items():
        if weight < 0.0:
            raise ValueError(f"Weight for '{key}' cannot be negative ({weight}).")
        total += weight

    if abs(total - 1.0) > tolerance:
        raise ValueError(f"Weights must sum to 1.0 (found {total:.4f}).")

    return True
