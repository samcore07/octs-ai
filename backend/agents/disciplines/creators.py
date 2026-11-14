"""
OCTS AI - Content Creators Discipline Configuration
"""

from backend.agents.base import DisciplineConfig

creators_discipline = DisciplineConfig(
    id="creators",
    display_name="Content Creators",
    purpose=(
        "Accelerate video creators, podcasters, newsletter writers, and social strategists "
        "in capturing viewer attention, repurposing core concepts across platforms, planning sustainable "
        "editorial cadences, and diagnosing audience cognitive friction."
    ),
    scope=(
        "First-3-second hook crafting, curiosity gap construction, YouTube/Shorts retention pacing, "
        "cross-platform content transmutation (longform to short-form, thread, newsletter), editorial "
        "calendar strategy, pillar content clustering, and audience comprehension/CTA friction auditing."
    ),
    specialist_persona_ids=[
        "hook_retention_architect",
        "multi_platform_transmuter",
        "editorial_cadence_planner",
        "audience_friction_auditor",
    ],
    supported_task_categories=[
        "hook_engineering",
        "retention_curve_optimization",
        "cross_platform_repurposing",
        "scriptwriting_shortform",
        "editorial_calendar_planning",
        "content_batching_workflows",
        "cognitive_friction_auditing",
        "call_to_action_optimization",
    ],
    discipline_terminology=[
        "retention drop-off",
        "pattern interrupt",
        "curiosity gap",
        "thumbnail-title synergy",
        "open loop",
        "platform native formatting",
        "pillar asset",
        "micro-content",
        "editorial cadence",
        "friction audit",
        "cognitive load",
        "above-the-fold payoff",
    ],
    quality_requirements=[
        "Hooks must deliver immediate stakes or intrigue within the initial sentence or 3 seconds.",
        "Zero generic summaries when transmuting across platforms; maintain native platform idioms.",
        "Sustainable batching workflows that prevent creator burnout.",
        "Friction audits must provide line-by-line elimination of viewer confusion and drop-off risks.",
    ],
    default_output_conventions=[
        "Timed script breakdowns (0:00-0:03, 0:03-0:15, body, climax, CTA).",
        "Platform-by-platform asset matrices with character limits, aspect ratios, and visual cues.",
        "Weekly/monthly calendar grids with production lead times and pillar linkages.",
        "Friction heatmaps identifying cognitive overload zones and precise wording cuts.",
    ],
)
