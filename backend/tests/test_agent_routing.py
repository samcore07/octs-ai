"""
OCTS AI - Agent Routing Unit Tests
Verifies deterministic rules, task type matching, edge cases, fallbacks, and mocked model classification.
"""

from unittest.mock import MagicMock
import pytest
from backend.agents.routing.classifier import AgentRouter


@pytest.fixture
def router():
    return AgentRouter()


# Representative queries for all 16 personas
REPRESENTATIVE_TEST_CASES = [
    # Writers
    ("I need help designing a three-act plot outline and pacing the climax.", "writers", "narrative_architect"),
    ("Check my story bible and magic system rules for continuity contradictions.", "writers", "lore_continuity_keeper"),
    ("Polish this dialogue scene to add subtext and remove purple prose and filter words.", "writers", "prose_stylist"),
    ("What were the authentic forensic and ballistics procedures in the late 19th century?", "writers", "research_scout"),

    # Musicians
    ("Help me write lyrics with a tight rhyme scheme, good meter, and strong vocal hooks.", "musicians", "lyricist_meter_engine"),
    ("Design a chord progression using modal interchange and smooth voice leading.", "musicians", "harmonic_arranger"),
    ("How do I arrange the song structure with dynamic energy curves from verse into the chorus drop?", "musicians", "track_structure_architect"),
    ("What synth patch and sound design textures should I use to slot the frequencies between the 808 and vocal?", "musicians", "sonic_palette_curator"),

    # Creators
    ("Create a high-retention video hook for the first 3 seconds to prevent audience drop-off.", "creators", "hook_retention_architect"),
    ("Repurpose this longform video transcript into an X thread and a LinkedIn post.", "creators", "multi_platform_transmuter"),
    ("Build a 30-day editorial content calendar and batching production schedule to prevent burnout.", "creators", "editorial_cadence_planner"),
    ("Audit this landing page script for cognitive friction, jargon, and improve the call to action.", "creators", "audience_friction_auditor"),

    # Designers
    ("Brainstorm divergent visual concepts and moodboard metaphors for a brutalist fintech brand.", "designers", "concept_ideation_engine"),
    ("Audit this UI layout for grid alignment, Gestalt hierarchy, and whitespace padding consistency.", "designers", "visual_system_auditor"),
    ("Provide a critique on the lighting, atmospheric depth, and composition of this rendering.", "designers", "art_direction_critic"),
    ("Generate a semantic design tokens color palette that passes WCAG 2.2 AAA contrast standards.", "designers", "design_token_palette_architect"),
]


@pytest.mark.parametrize("prompt,discipline_id,expected_persona", REPRESENTATIVE_TEST_CASES)
def test_representative_prompt_routing(router, prompt, discipline_id, expected_persona):
    """Verify high-accuracy deterministic routing across representative domain queries."""
    result = router.route(prompt=prompt, discipline_id=discipline_id)
    assert result.discipline_id == discipline_id
    assert result.persona_id == expected_persona
    assert result.confidence >= 0.65
    assert result.routing_method == "deterministic_rule"
    assert len(result.rationale) > 10


def test_explicit_task_type_routing(router):
    """Verify explicit task_type overrides keyword heuristics and yields high confidence."""
    result = router.route(
        prompt="A very generic creative question",
        discipline_id="writers",
        task_type="worldbuilding_audit",
    )
    assert result.persona_id == "lore_continuity_keeper"
    assert result.confidence >= 0.95
    assert result.routing_method == "deterministic_rule"
    assert "explicit task categorization" in result.rationale


def test_invalid_discipline_handling(router):
    """Verify unknown discipline safely falls back to default without throwing exceptions."""
    result = router.route(
        prompt="Tell me about quantum gravity",
        discipline_id="astrophysics",
    )
    assert result.discipline_id == "writers"
    assert result.persona_id == "narrative_architect"
    assert result.routing_method == "discipline_default_fallback"
    assert "unrecognized" in result.rationale


def test_ambiguous_prompt_fallback_routing(router):
    """Verify completely generic prompts fall back gracefully to the discipline's default persona."""
    result = router.route(
        prompt="Hello, I want to create something nice today.",
        discipline_id="designers",
    )
    assert result.discipline_id == "designers"
    assert result.persona_id == "concept_ideation_engine"
    assert result.confidence == 0.50
    assert result.routing_method == "discipline_default_fallback"


def test_alternative_persona_recommendation(router):
    """Verify multi-domain prompts suggest a plausible alternative persona."""
    prompt = "Help me design the plot outline and also polish the prose cadence."
    result = router.route(prompt=prompt, discipline_id="writers")
    assert result.persona_id in ["narrative_architect", "prose_stylist"]
    assert result.alternative_persona_id is not None
    assert result.alternative_persona_id in ["narrative_architect", "prose_stylist"]


def test_model_assisted_classification_success(router):
    """Verify model-assisted classification is invoked and trusted when output matches valid persona."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "lore_continuity_keeper"
    mock_model.invoke.return_value = mock_response

    # Ambiguous prompt with zero keyword matches so model is consulted
    result = router.route(
        prompt="Generic ambiguous prompt with zero keywords xyz123",
        discipline_id="writers",
        model=mock_model,
    )
    assert result.persona_id == "lore_continuity_keeper"
    assert result.routing_method == "model_classification"
    assert result.confidence == 0.85


def test_model_assisted_classification_malformed_fallback(router):
    """Verify that when the model returns hallucinations or garbage, router falls back safely."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "some_hallucinated_invalid_persona_xyz"
    mock_model.invoke.return_value = mock_response

    result = router.route(
        prompt="Ambiguous prompt xyz123",
        discipline_id="writers",
        model=mock_model,
    )
    # Must fallback safely to default persona, never adopting hallucinated ID
    assert result.persona_id == "narrative_architect"
    assert result.routing_method == "discipline_default_fallback"


def test_model_assisted_classification_exception_fallback(router):
    """Verify that when model throws an exception (timeout, quota), router catches and falls back safely."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = RuntimeError("API quota exhausted")

    result = router.route(
        prompt="Ambiguous prompt xyz123",
        discipline_id="writers",
        model=mock_model,
    )
    assert result.persona_id == "narrative_architect"
    assert result.routing_method == "discipline_default_fallback"
