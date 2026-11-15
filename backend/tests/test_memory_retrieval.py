"""
OCTS AI - Memory Retrieval Test Suite
Verifies multi-factor ranking, project/discipline boosting, confidence thresholds,
context XML generation, token budget truncation, and access telemetry updates.
"""

from datetime import datetime, timezone
import pytest

from backend.memory.context_builder import ContextBuilder
from backend.memory.memory_store import MemoryStore
from backend.memory.memory_ranker import MemoryRanker
from backend.memory.memory_retriever import MemoryRetriever
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import (
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
)


def _create_sample_memory(
    content: str,
    memory_type: MemoryType = MemoryType.USER_PREFERENCE,
    scope: MemoryScope = MemoryScope.USER,
    discipline: str = None,
    project_id: str = None,
    importance: float = 0.5,
    confidence: float = 0.9,
) -> MemoryRecord:
    return MemoryRecord(
        owner_id="user_test",
        memory_type=memory_type,
        scope=scope,
        discipline=discipline,
        project_id=project_id,
        content=content,
        confidence=confidence,
        importance=importance,
        status=MemoryStatus.ACTIVE,
        source=MemorySource.EXPLICIT_USER,
    )


def test_ranking_weights_and_ordering():
    """Verify memory ranker orders candidates by composite score correctly."""
    ranker = MemoryRanker()

    mem_relevant = _create_sample_memory(
        content="Always write fast-paced cyberpunk dialogue with slang.",
        importance=0.9,
    )
    mem_irrelevant = _create_sample_memory(
        content="Prefers soft watercolor color palette.",
        importance=0.3,
    )

    prompt = "Draft a fast-paced cyberpunk dialogue scene."
    ranked = ranker.rank_memories(
        candidates=[mem_irrelevant, mem_relevant],
        prompt=prompt,
        min_threshold=0.30,
    )

    assert len(ranked) >= 1
    # mem_relevant should rank first because of keyword overlap and higher importance
    assert ranked[0][0].content == mem_relevant.content
    assert ranked[0][1] > 0.50


def test_project_match_boosting():
    """Verify target project match provides a strong score boost."""
    ranker = MemoryRanker()

    mem_proj = _create_sample_memory(
        content="Setting is the orbital station Odyssey.",
        scope=MemoryScope.PROJECT,
        project_id="proj_station",
    )
    mem_other_proj = _create_sample_memory(
        content="Setting is medieval castle.",
        scope=MemoryScope.PROJECT,
        project_id="proj_fantasy",
    )

    ranked = ranker.rank_memories(
        candidates=[mem_proj, mem_other_proj],
        prompt="Describe the environment.",
        target_project_id="proj_station",
        min_threshold=0.20,
    )

    # mem_proj should score significantly higher due to project match factor
    assert ranked[0][0].project_id == "proj_station"
    score_station = ranked[0][1]
    score_fantasy = next((s for m, s, _ in ranked if m.project_id == "proj_fantasy"), 0.0)
    assert score_station > score_fantasy


def test_discipline_match_boosting():
    """Verify matching discipline boosts score over unrelated disciplines."""
    ranker = MemoryRanker()

    mem_writers = _create_sample_memory(
        content="Use deep third-person POV.",
        scope=MemoryScope.DISCIPLINE,
        discipline="writers",
    )
    mem_musicians = _create_sample_memory(
        content="Tempo must be 120 BPM.",
        scope=MemoryScope.DISCIPLINE,
        discipline="musicians",
    )

    ranked = ranker.rank_memories(
        candidates=[mem_writers, mem_musicians],
        prompt="Write the opening lines.",
        target_discipline="writers",
        min_threshold=0.20,
    )

    assert ranked[0][0].discipline == "writers"


def test_confidence_threshold_filtering():
    """Verify items below the minimum composite threshold are excluded."""
    ranker = MemoryRanker()

    mem_low = _create_sample_memory(
        content="Irrelevant detail from long ago.",
        importance=0.1,
    )
    ranked = ranker.rank_memories(
        candidates=[mem_low],
        prompt="Generate orchestral composition.",
        min_threshold=0.90,  # Unreasonably high threshold
    )
    assert len(ranked) == 0


def test_context_builder_xml_formatting():
    """Verify context builder outputs isolated XML tags and groups by category."""
    builder = ContextBuilder(max_context_tokens=1000)

    mem_const = _create_sample_memory("Never use purple prose.", MemoryType.CONSTRAINT)
    mem_dec = _create_sample_memory("Selected 3-act structure.", MemoryType.DECISION)
    mem_pref = _create_sample_memory("Prefers concise sentences.", MemoryType.USER_PREFERENCE)

    ranked = [
        (mem_const, 0.95, "Score 0.95"),
        (mem_dec, 0.90, "Score 0.90"),
        (mem_pref, 0.85, "Score 0.85"),
    ]

    context_xml, telemetry = builder.build_context(ranked)

    assert "<retrieved_memory_context>" in context_xml
    assert "</retrieved_memory_context>" in context_xml
    assert "ESTABLISHED CRAFT CONSTRAINTS:" in context_xml
    assert "Never use purple prose." in context_xml
    assert "APPROVED CREATIVE DECISIONS:" in context_xml
    assert "Selected 3-act structure." in context_xml
    assert "USER CREATIVE PREFERENCES:" in context_xml
    assert "Prefers concise sentences." in context_xml
    assert len(telemetry) == 3


def test_context_builder_token_budget_truncation():
    """Verify context builder respects strict character/token ceiling."""
    # max 20 tokens = 80 chars
    builder = ContextBuilder(max_context_tokens=20)

    long_mem1 = _create_sample_memory("A" * 60)
    long_mem2 = _create_sample_memory("B" * 60)

    ranked = [
        (long_mem1, 0.95, "Score 0.95"),
        (long_mem2, 0.90, "Score 0.90"),
    ]

    context_xml, telemetry = builder.build_context(ranked)
    # Total chars inside entries shouldn't exceed 80 chars
    assert len(telemetry) == 1
    assert "A" * 60 in context_xml
    assert "B" * 60 not in context_xml


def test_memory_retriever_access_tracking(tmp_path):
    """Verify memory retrieval records access count and timestamp in repository."""
    db_file = tmp_path / "test_access.db"
    db_url = f"sqlite:///{db_file}"
    store = MemoryStore(database_url=db_url)
    repo = MemoryRepository(store=store)

    mem = _create_sample_memory("Prefers crisp dialogue in scripts.", MemoryType.USER_PREFERENCE)
    created = repo.create_memory(mem)
    assert created.access_count == 0
    assert created.last_accessed_at is None

    retriever = MemoryRetriever(repository=repo)
    context_str, items = retriever.retrieve_context(
        prompt="Write a crisp dialogue script.",
        owner_id="user_test",
        discipline=None,
    )

    assert len(items) >= 1
    fetched = repo.get_memory(created.memory_id)
    assert fetched is not None
    assert fetched.access_count == 1
    assert fetched.last_accessed_at is not None
