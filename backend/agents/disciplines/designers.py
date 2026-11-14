"""
OCTS AI - Visual Artists & Designers Discipline Configuration
"""

from backend.agents.base import DisciplineConfig

designers_discipline = DisciplineConfig(
    id="designers",
    display_name="Visual Artists & Designers",
    purpose=(
        "Equip graphic designers, UI/UX architects, art directors, and visual artists with "
        "high-leverage divergent ideation, rigorous design system audits, aesthetic criticism, and "
        "accessible token architecture."
    ),
    scope=(
        "Concept sketching prompts, visual metaphor exploration, moodboard curation, UI layout "
        "and grid balance auditing, Gestalt hierarchy evaluation, composition and lighting criticism, "
        "color palette generation, and WCAG-compliant design token systems."
    ),
    specialist_persona_ids=[
        "concept_ideation_engine",
        "visual_system_auditor",
        "art_direction_critic",
        "design_token_palette_architect",
    ],
    supported_task_categories=[
        "concept_ideation",
        "visual_metaphor_generation",
        "ui_system_auditing",
        "layout_hierarchy_balance",
        "art_direction_critique",
        "lighting_composition_analysis",
        "design_tokens_architecture",
        "color_palette_accessibility",
    ],
    discipline_terminology=[
        "gestalt principles",
        "visual hierarchy",
        "negative space",
        "grid baseline",
        "optical balance",
        "rule of thirds",
        "chiaroscuro",
        "focal anchor",
        "design tokens",
        "semantic color scale",
        "WCAG 2.2 AAA/AA",
        "typographic scale ratio",
    ],
    quality_requirements=[
        "Visual ideas must break conventional stock tropes through non-obvious thematic juxtapositions.",
        "System audits must pinpoint exact spacing, typography, and contrast violations.",
        "Critiques must balance objective formal principles with emotional and atmospheric resonance.",
        "Design tokens must ensure strict mathematical proportion and accessible color contrast ratios.",
    ],
    default_output_conventions=[
        "Concept briefs with moodboard descriptors, visual motifs, and artistic references.",
        "Component-level audit tables with current flaw, design principle violated, and exact fix.",
        "Art direction reviews detailing lighting direction, palette mood, and compositional focal points.",
        "JSON/CSS token sheets with semantic naming, HEX values, and WCAG contrast calculations.",
    ],
)
