"""
OCTS AI - Writers & Storytellers Discipline Configuration
"""

from backend.agents.base import DisciplineConfig

writers_discipline = DisciplineConfig(
    id="writers",
    display_name="Writers & Storytellers",
    purpose=(
        "Empower novelists, screenwriters, dramatists, and narrative designers to build "
        "compelling story architectures, authentic worlds, evocative prose, and rigorous factual context."
    ),
    scope=(
        "Plot outlining, three-act and non-linear narrative structuring, character arc development, "
        "dialogue pacing, sensory prose enhancement, lore consistency tracking, timeline auditing, "
        "historical and technical research integration."
    ),
    specialist_persona_ids=[
        "narrative_architect",
        "lore_continuity_keeper",
        "prose_stylist",
        "research_scout",
    ],
    supported_task_categories=[
        "story_structure",
        "plot_development",
        "worldbuilding_lore",
        "character_continuity",
        "prose_enhancement",
        "dialogue_refinement",
        "factual_research",
        "thematic_analysis",
    ],
    discipline_terminology=[
        "inciting incident",
        "rising action",
        "climax",
        "catharsis",
        "character flaw",
        "dramatic irony",
        "subtext",
        "sensory grounding",
        "prose cadence",
        "worldbuilding bible",
        "exposition",
        "timeline chronology",
    ],
    quality_requirements=[
        "Internal logical consistency without chronological paradoxes.",
        "Clear emotional stakes and protagonist agency in narrative decisions.",
        "Avoidance of purple prose, cliches, and ungrounded exposition dumps.",
        "Accurate historical, cultural, or physical constraints where applicable.",
    ],
    default_output_conventions=[
        "Structured scene-by-scene or act-by-act breakdowns.",
        "Specific line-level prose examples with annotations.",
        "Bullet-pointed lore facts categorized by faction, timeline, or rule set.",
        "Actionable narrative interventions highlighting cause-and-effect mechanics.",
    ],
)
