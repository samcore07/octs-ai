"""
OCTS AI - Persona Prompts & LangChain Template Unit Tests
Verifies prompt generation, craft depth, constraints, and template formatting for all 16 personas.
"""

import pytest
from langchain_core.prompts import ChatPromptTemplate
from backend.agents.registry import get_registry


@pytest.fixture
def registry():
    return get_registry()


def test_all_16_personas_have_complete_prompt_fields(registry):
    """Verify that all 16 personas define rich craft instructions and constraints."""
    for persona in registry.list_personas():
        assert len(persona.description) > 20
        assert len(persona.primary_responsibilities) >= 4
        assert len(persona.supported_task_types) >= 4
        assert len(persona.system_instructions) > 100
        assert len(persona.domain_constraints) >= 3
        assert len(persona.expected_output_structure) >= 4
        assert len(persona.evaluation_criteria) >= 3
        assert 0.0 <= persona.model_config_recommendation.temperature <= 2.0


def test_format_system_prompt_contains_crucial_sections(registry):
    """Verify that formatted system prompts compile all required sections into markdown."""
    for persona in registry.list_personas():
        prompt_text = persona.format_system_prompt()
        assert f"# ROLE: {persona.display_name}" in prompt_text
        assert f"(Discipline: {persona.discipline_id})" in prompt_text
        assert "## Specialization & Mission" in prompt_text
        assert "## Core Directives & Instructions" in prompt_text
        assert "## Primary Responsibilities" in prompt_text
        assert "## Rigorous Craft & Domain Constraints" in prompt_text
        assert "## Expected Output Architecture" in prompt_text
        assert "## Craft Evaluation Criteria" in prompt_text

        # Verify domain constraints appear in text
        for constraint in persona.domain_constraints:
            assert constraint in prompt_text


def test_build_prompt_template_and_format_messages(registry):
    """Verify that every persona builds a working LangChain ChatPromptTemplate."""
    test_input = "Please audit this creative concept for my upcoming project."
    for persona in registry.list_personas():
        prompt_template = persona.build_prompt_template()
        assert isinstance(prompt_template, ChatPromptTemplate)

        messages = prompt_template.format_messages(input=test_input)
        assert len(messages) == 2
        # Message 0 is system message
        assert messages[0].content == persona.format_system_prompt()
        # Message 1 is human message
        assert messages[1].content == test_input


def test_persona_domain_depth_no_generic_platitudes(registry):
    """Verify that persona instructions are domain-specific and avoid empty generic phrases."""
    generic_phrases = ["you are a helpful assistant", "you are an expert writer and will do anything"]
    for persona in registry.list_personas():
        prompt_lower = persona.system_instructions.lower()
        for generic in generic_phrases:
            assert generic not in prompt_lower
