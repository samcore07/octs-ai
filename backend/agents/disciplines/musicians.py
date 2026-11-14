"""
OCTS AI - Musicians & Singers Discipline Configuration
"""

from backend.agents.base import DisciplineConfig

musicians_discipline = DisciplineConfig(
    id="musicians",
    display_name="Musicians & Singers",
    purpose=(
        "Support songwriters, composers, producers, and vocalists in crafting rhythmically "
        "gripping lyrics, rich harmonic voicings, dynamic arrangement arcs, and nuanced sonic textures."
    ),
    scope=(
        "Lyric writing, meter and prosody analysis, rhyme scheme construction, harmonic progressions, "
        "modal interchange, song structuring (verse-chorus-bridge, intro/outro, drops), dynamic tension "
        "and energy curves, instrumentation choices, synth sound design, and acoustic texture curation."
    ),
    specialist_persona_ids=[
        "lyricist_meter_engine",
        "harmonic_arranger",
        "track_structure_architect",
        "sonic_palette_curator",
    ],
    supported_task_categories=[
        "lyric_writing",
        "prosody_meter_analysis",
        "chord_progression_design",
        "harmonic_modulation",
        "song_arrangement",
        "track_structure_pacing",
        "sound_design_instrumentation",
        "sonic_palette_selection",
    ],
    discipline_terminology=[
        "prosody",
        "iambic/trochaic meter",
        "internal rhyme",
        "consonance/assonance",
        "modal interchange",
        "voice leading",
        "secondary dominants",
        "tritone substitution",
        "verse-chorus form",
        "dynamic contour",
        "frequency mask",
        "transient response",
        "harmonic tension",
    ],
    quality_requirements=[
        "Strict metric alignment between natural speech stress and musical downbeats.",
        "Smooth voice leading with intentional harmonic tension and resolution.",
        "Clear narrative and dynamic progression across song sections.",
        "Coherent sonic palette that preserves vocal clarity and frequency separation.",
    ],
    default_output_conventions=[
        "Stanza-by-stanza lyrics with metric stress markings and rhyme annotations.",
        "Roman numeral analysis and chord voicings with root movement notes.",
        "Arrangement timelines with instrument enter/exit cues and energy ratings (1-10).",
        "Sound design recipes detailing oscillator types, filter cutoffs, and acoustic textures.",
    ],
)
