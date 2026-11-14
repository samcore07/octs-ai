"""
OCTS AI - Deterministic Routing Rules & Pattern Engine
Discipline-specific keyword dictionaries, task type mappings, and scoring heuristics.
"""

import re
from typing import Dict, List, Optional, Tuple


# Primary default persona per discipline when no specific triggers match
DEFAULT_PERSONAS: Dict[str, str] = {
    "writers": "narrative_architect",
    "musicians": "track_structure_architect",
    "creators": "hook_retention_architect",
    "designers": "concept_ideation_engine",
}

# Explicit task type to persona mapping
TASK_TYPE_MAPPING: Dict[str, str] = {
    # Writers
    "story_outline": "narrative_architect",
    "plot_structuring": "narrative_architect",
    "pacing_diagnosis": "narrative_architect",
    "character_arc_design": "narrative_architect",
    "act_breakdown": "narrative_architect",
    "worldbuilding_audit": "lore_continuity_keeper",
    "timeline_validation": "lore_continuity_keeper",
    "canon_consistency_check": "lore_continuity_keeper",
    "magic_tech_rule_definition": "lore_continuity_keeper",
    "prose_polishing": "prose_stylist",
    "voice_calibration": "prose_stylist",
    "dialogue_subtext_refinement": "prose_stylist",
    "sensory_grounding": "prose_stylist",
    "historical_fact_checking": "research_scout",
    "scientific_plausibility_audit": "research_scout",
    "forensic_procedure_mapping": "research_scout",

    # Musicians
    "lyric_generation": "lyricist_meter_engine",
    "prosody_meter_audit": "lyricist_meter_engine",
    "rhyme_scheme_design": "lyricist_meter_engine",
    "chord_progression_design": "harmonic_arranger",
    "reharmonization": "harmonic_arranger",
    "voice_leading_optimization": "harmonic_arranger",
    "modal_interchange": "harmonic_arranger",
    "song_arrangement_design": "track_structure_architect",
    "energy_curve_mapping": "track_structure_architect",
    "section_transition_engineering": "track_structure_architect",
    "sound_design_curation": "sonic_palette_curator",
    "synth_patch_architecture": "sonic_palette_curator",
    "frequency_slotting_plan": "sonic_palette_curator",

    # Creators
    "hook_generation": "hook_retention_architect",
    "retention_curve_optimization": "hook_retention_architect",
    "thumbnail_title_pairing": "hook_retention_architect",
    "content_repurposing": "multi_platform_transmuter",
    "thread_writing": "multi_platform_transmuter",
    "shorts_scripting": "multi_platform_transmuter",
    "content_calendar_design": "editorial_cadence_planner",
    "publishing_cadence_optimization": "editorial_cadence_planner",
    "production_workflow_batching": "editorial_cadence_planner",
    "cognitive_friction_audit": "audience_friction_auditor",
    "cta_conversion_optimization": "audience_friction_auditor",
    "comprehension_clarity_check": "audience_friction_auditor",

    # Designers
    "visual_brainstorming": "concept_ideation_engine",
    "metaphor_generation": "concept_ideation_engine",
    "moodboard_curation": "concept_ideation_engine",
    "layout_hierarchy_audit": "visual_system_auditor",
    "gestalt_evaluation": "visual_system_auditor",
    "grid_spacing_check": "visual_system_auditor",
    "composition_critique": "art_direction_critic",
    "lighting_atmosphere_review": "art_direction_critic",
    "color_temperature_analysis": "art_direction_critic",
    "color_palette_architecture": "design_token_palette_architect",
    "design_token_engineering": "design_token_palette_architect",
    "wcag_contrast_calculation": "design_token_palette_architect",
}


# High-signal keywords and multi-word patterns mapped to personas
PERSONA_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "writers": {
        "narrative_architect": [
            r"\bplot\b", r"\boutline\b", r"\bact\b", r"\bstructure\b", r"\barc\b",
            r"\bpacing\b", r"\binciting incident\b", r"\bclimax\b", r"\bturning point\b",
            r"\bbeat sheet\b", r"\bstory circle\b", r"\bhero'?s journey\b", r"\bthree[- ]act\b",
            r"\bprotagonist\b", r"\bantagonist\b", r"\bstakes\b", r"\bconflict\b",
        ],
        "lore_continuity_keeper": [
            r"\blore\b", r"\bworldbuilding\b", r"\bmagic system\b", r"\btimeline\b",
            r"\bcanon\b", r"\bcontinuity\b", r"\bchronology\b", r"\bparadox\b",
            r"\bcontradiction\b", r"\bworld bible\b", r"\bkingdom\b", r"\bfaction\b",
            r"\bmythology\b", r"\brules of magic\b", r"\bgeography\b",
        ],
        "prose_stylist": [
            r"\bprose\b", r"\bvoice\b", r"\bsensory\b", r"\bcadence\b", r"\bdialogue\b",
            r"\bsubtext\b", r"\bmetaphor\b", r"\bsentence rhythm\b", r"\bpolish\b",
            r"\bpurple prose\b", r"\bfilter words\b", r"\bshow don'?t tell\b", r"\bstyle\b",
            r"\bline[- ]edit\b", r"\btone\b", r"\bpoetic\b",
        ],
        "research_scout": [
            r"\bresearch\b", r"\bhistorical\b", r"\bfact\b", r"\bforensic\b", r"\bweapon\b",
            r"\bmedical\b", r"\bauthenticity\b", r"\bballistics\b", r"\bplausibility\b",
            r"\banachronism\b", r"\bperiod detail\b", r"\brealism\b", r"\bprocedure\b",
            r"\b19th century\b", r"\bmedieval\b", r"\bscientific\b",
        ],
    },
    "musicians": {
        "lyricist_meter_engine": [
            r"\blyric\b", r"\brhyme\b", r"\bmeter\b", r"\bsyllable\b", r"\bprosody\b",
            r"\bvocal hook\b", r"\bverse\b", r"\bstress\b", r"\bcouplet\b", r"\bflow\b",
            r"\bslant rhyme\b", r"\bassonance\b", r"\bconsonance\b", r"\bsongwriting\b",
        ],
        "harmonic_arranger": [
            r"\bchord\b", r"\bprogression\b", r"\bharmony\b", r"\bvoicing\b", r"\bmodulation\b",
            r"\bmodal interchange\b", r"\bvoice leading\b", r"\breharmoniz\w*", r"\bkey change\b",
            r"\broman numeral\b", r"\bsecondary dominant\b", r"\btritone\b", r"\bminor\b",
            r"\bmajor 7th\b", r"\bii-v-i\b",
        ],
        "track_structure_architect": [
            r"\bstructure\b", r"\barrangement\b", r"\bchorus\b", r"\bbridge\b", r"\bintro\b",
            r"\boutro\b", r"\bdrop\b", r"\bbuild[- ]up\b", r"\benergy curve\b", r"\bdynamics\b",
            r"\btransition\b", r"\bform\b", r"\bpre[- ]chorus\b", r"\bpost[- ]chorus\b",
            r"\bear candy\b",
        ],
        "sonic_palette_curator": [
            r"\bsound design\b", r"\btimbre\b", r"\bsynth\b", r"\bfrequency\b", r"\bsample\b",
            r"\breverb\b", r"\bspatial\b", r"\btexture\b", r"\b808\b", r"\banalog\b",
            r"\bpatch\b", r"\bfilter\b", r"\boscillator\b", r"\bmix\b", r"\binstrumentation\b",
            r"\bspectrum\b", r"\bwavetable\b",
        ],
    },
    "creators": {
        "hook_retention_architect": [
            r"\bhook\b", r"\bretention\b", r"\bfirst 3 seconds\b", r"\bcuriosity gap\b",
            r"\bdrop[- ]off\b", r"\bthumbnail\b", r"\btitle\b", r"\bpattern interrupt\b",
            r"\bwatch time\b", r"\bopening frame\b", r"\bopen loop\b", r"\byoutube hook\b",
            r"\bscroll[- ]stopper\b",
        ],
        "multi_platform_transmuter": [
            r"\brepurpose\b", r"\bthread\b", r"\btwitter\b", r"\bx post\b", r"\blinkedin\b",
            r"\bshort\b", r"\breel\b", r"\btiktok\b", r"\bnewsletter\b", r"\bsubstack\b",
            r"\batomiz\w*", r"\bcross[- ]platform\b", r"\btranscript\b", r"\bcarousels\b",
        ],
        "editorial_cadence_planner": [
            r"\bcalendar\b", r"\bschedule\b", r"\bcadence\b", r"\bbatch\b", r"\bworkflow\b",
            r"\bproduction\b", r"\bbuffer\b", r"\bburnout\b", r"\bcontent plan\b",
            r"\bweekly\b", r"\bmonthly\b", r"\bpillar\b", r"\bseries\b", r"\bconsistency\b",
        ],
        "audience_friction_auditor": [
            r"\bfriction\b", r"\bclarity\b", r"\bcta\b", r"\bcall to action\b", r"\bcognitive\b",
            r"\bcurse of knowledge\b", r"\bsimplif\w*", r"\bconfusing\b", r"\bjargon\b",
            r"\breadability\b", r"\baudience drag\b", r"\bdrop[- ]off rate\b",
        ],
    },
    "designers": {
        "concept_ideation_engine": [
            r"\bconcept\b", r"\bideation\b", r"\bbrainstorm\b", r"\bvisual metaphor\b",
            r"\bmoodboard\b", r"\baesthetic\b", r"\bcreative direction\b", r"\bprompt\b",
            r"\bsketch\b", r"\btheme\b", r"\bjuxtaposition\b", r"\banti[- ]trope\b",
            r"\bbrutalis\w*", r"\bmateriality\b",
        ],
        "visual_system_auditor": [
            r"\blayout\b", r"\bgrid\b", r"\bhierarchy\b", r"\bwhitespace\b", r"\bgestalt\b",
            r"\bpadding\b", r"\bmargin\b", r"\balignment\b", r"\bui audit\b", r"\bclutter\b",
            r"\bspacing\b", r"\boptical balance\b", r"\btypography hierarchy\b", r"\bline length\b",
        ],
        "art_direction_critic": [
            r"\bcritique\b", r"\bcomposition\b", r"\blighting\b", r"\bshadows\b", r"\bfocal point\b",
            r"\batmosphere\b", r"\bcolor temperature\b", r"\brule of thirds\b", r"\bfeedback\b",
            r"\brender review\b", r"\bdepth\b", r"\bchiaroscuro\b", r"\bcolor grading\b",
        ],
        "design_token_palette_architect": [
            r"\bpalette\b", r"\btokens\b", r"\bwcag\b", r"\bcontrast\b", r"\baccessibility\b",
            r"\bdark mode\b", r"\bhex\b", r"\bsemantic color\b", r"\btypographic scale\b",
            r"\bratio\b", r"\bdtcg\b", r"\bcss custom properties\b", r"\bluminance\b",
        ],
    },
}


def score_prompt_for_discipline(prompt: str, discipline_id: str) -> List[Tuple[str, float]]:
    """
    Evaluates a user prompt against all personas in a discipline using regex patterns.
    Returns a sorted list of (persona_id, score) in descending order of relevance.
    """
    discipline = discipline_id.lower().strip()
    patterns = PERSONA_PATTERNS.get(discipline, {})
    if not patterns:
        return []

    scores: Dict[str, float] = {pid: 0.0 for pid in patterns}
    prompt_lower = prompt.lower()

    for pid, regex_list in patterns.items():
        match_count = 0
        for pattern in regex_list:
            matches = len(re.findall(pattern, prompt_lower))
            if matches > 0:
                match_count += matches

        # Base scoring calculation
        scores[pid] = float(match_count)

    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_scores


def detect_best_discipline(prompt: str) -> Tuple[Optional[str], Optional[str], float, Dict[str, float]]:
    """
    Evaluates a prompt across all 4 disciplines to detect the most relevant discipline.
    Returns (best_discipline_id, best_persona_id, best_score, discipline_max_scores).
    If no discipline has positive matches, best_discipline_id will be None.
    """
    disc_scores: Dict[str, float] = {}
    best_personas: Dict[str, str] = {}

    for disc in ["writers", "musicians", "creators", "designers"]:
        scores = score_prompt_for_discipline(prompt, disc)
        if scores and scores[0][1] > 0.0:
            disc_scores[disc] = scores[0][1]
            best_personas[disc] = scores[0][0]
        else:
            disc_scores[disc] = 0.0
            best_personas[disc] = DEFAULT_PERSONAS[disc]

    sorted_disc = sorted(disc_scores.items(), key=lambda item: item[1], reverse=True)
    top_disc, top_score = sorted_disc[0]

    if top_score == 0.0:
        return (None, None, 0.0, disc_scores)

    # If top score is tied between multiple disciplines, check for ambiguity
    second_score = sorted_disc[1][1] if len(sorted_disc) > 1 else 0.0
    if top_score == second_score and top_score > 0.0:
        # Tie between two disciplines without explicit user preference
        return (None, None, top_score, disc_scores)

    return (top_disc, best_personas.get(top_disc), top_score, disc_scores)
