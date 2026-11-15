"""
OCTS AI - Memory Extraction Test Suite
Verifies extraction across preference, project facts, decisions, constraints,
ephemeral command rejection, and PII/secret scrubbing.
"""

import pytest

from backend.memory.extractors import (
    ConstraintExtractor,
    DecisionExtractor,
    PreferenceExtractor,
    ProjectExtractor,
)
from backend.memory.memory_extractor import MemoryExtractor
from backend.memory.schemas import MemoryScope, MemoryType


def test_preference_extraction():
    """Verify explicit user creative preference extraction."""
    extractor = MemoryExtractor(extractors=[PreferenceExtractor()])
    prompt = "I prefer noir tone when crafting mystery dialogue."
    output = "Here is the dialogue..."

    memories = extractor.extract_memories(
        prompt=prompt,
        output=output,
        discipline="writers",
        owner_id="user_123",
    )

    assert len(memories) >= 1
    mem = memories[0]
    assert mem.memory_type == MemoryType.USER_PREFERENCE
    assert "noir tone" in mem.content.lower()
    assert mem.owner_id == "user_123"
    assert mem.discipline == "writers"


def test_project_fact_extraction():
    """Verify project entity and character lore extraction."""
    extractor = MemoryExtractor(extractors=[ProjectExtractor()])
    prompt = "In our sci-fi novel, the protagonist is Marcus Vance, an orbital engineer."
    output = "Understood, Marcus Vance is established."

    memories = extractor.extract_memories(
        prompt=prompt,
        output=output,
        discipline="writers",
        project_id="proj_mars",
        owner_id="user_123",
    )

    assert len(memories) >= 1
    mem = memories[0]
    assert mem.memory_type == MemoryType.PROJECT
    assert "marcus vance" in mem.content.lower()
    assert mem.project_id == "proj_mars"


def test_decision_extraction():
    """Verify creative decision extraction."""
    extractor = MemoryExtractor(extractors=[DecisionExtractor()])
    prompt = "After reviewing the pitches, we decided to use a 3-act structure with multiple points of view."
    output = "Outlining the 3-act structure..."

    memories = extractor.extract_memories(
        prompt=prompt,
        output=output,
        discipline="writers",
        project_id="proj_epic",
        owner_id="user_123",
    )

    assert len(memories) >= 1
    mem = memories[0]
    assert mem.memory_type == MemoryType.DECISION
    assert "3-act structure" in mem.content.lower()


def test_constraint_extraction():
    """Verify mandatory craft constraint extraction."""
    extractor = MemoryExtractor(extractors=[ConstraintExtractor()])
    prompt = "Please ensure you never use purple prose or melodramatic cliffhangers."
    output = "Drafting with sharp, grounded prose."

    memories = extractor.extract_memories(
        prompt=prompt,
        output=output,
        discipline="writers",
        owner_id="user_123",
    )

    assert len(memories) >= 1
    mem = memories[0]
    assert mem.memory_type == MemoryType.CONSTRAINT
    assert "purple prose" in mem.content.lower()


def test_ephemeral_command_rejection():
    """Verify standard conversational and ephemeral instructions do not trigger extraction."""
    extractor = MemoryExtractor()
    ephemeral_prompts = [
        "Please help me write a story about a dragon.",
        "Hello, can you give me some ideas for a song?",
        "Fix the typo in paragraph 2.",
        "Summarize this text in 5 bullet points.",
        "Can you act as a music producer?",
    ]

    for p in ephemeral_prompts:
        memories = extractor.extract_memories(
            prompt=p,
            output="Done.",
            discipline="writers",
            owner_id="user_123",
        )
        assert len(memories) == 0, f"Expected 0 extractions for ephemeral prompt: '{p}', got {memories}"


def test_pii_and_secret_rejection():
    """Verify candidates containing credit cards, SSNs, or API keys are rejected."""
    extractor = MemoryExtractor()

    # Credit card attempt
    cc_prompt = "I prefer using account 4532-1488-1234-5678 for billing references."
    memories_cc = extractor.extract_memories(
        prompt=cc_prompt,
        output="Understood.",
        owner_id="user_123",
    )
    assert len(memories_cc) == 0

    # API Key attempt (dynamically constructed mock token to avoid triggering repository secret scanners)
    mock_test_key = "AI" + "za" + "Sy" + ("DUMMY_MOCK_TEST_KEY_FOR_SANITIZER_"[:33])
    key_prompt = f"Strict constraint: rule: use key {mock_test_key} in headers."
    memories_key = extractor.extract_memories(
        prompt=key_prompt,
        output="Understood.",
        owner_id="user_123",
    )
    assert len(memories_key) == 0


def test_extractor_error_handling_malformed_inputs():
    """Verify graceful recovery on malformed or None inputs."""
    extractor = MemoryExtractor()

    assert extractor.extract_memories(prompt="", output="something") == []
    assert extractor.extract_memories(prompt=None, output=None) == []  # type: ignore


def test_extraction_bounded_per_turn():
    """Verify maximum extractions per turn is strictly enforced."""
    extractor = MemoryExtractor(max_extract_per_turn=2)
    multi_prompt = (
        "I prefer noir tone. "
        "Strict constraint: rule: never use flashback sequences. "
        "We decided to use 3-act structure. "
        "The protagonist is Marcus Vance."
    )

    memories = extractor.extract_memories(
        prompt=multi_prompt,
        output="Plan created.",
        project_id="proj_1",
        discipline="writers",
        owner_id="user_123",
    )
    assert len(memories) <= 2
