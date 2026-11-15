"""
OCTS AI - Memory Consolidation Test Suite
Verifies conflict resolution hierarchy, non-destructive superseding, version incrementing,
duplicate skipping, and discipline-scoped isolation.
"""

import tempfile
import pytest

from backend.memory.memory_consolidator import MemoryConsolidator
from backend.memory.memory_policy import MemoryPolicy, PrecedenceRank
from backend.memory.memory_store import MemoryStore
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import (
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
)


@pytest.fixture
def consolidator_setup():
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    db_url = f"sqlite:///{temp_file.name}"
    store = MemoryStore(database_url=db_url)
    repo = MemoryRepository(store=store)
    policy = MemoryPolicy()
    consolidator = MemoryConsolidator(repository=repo, policy=policy)
    return consolidator, repo


def test_explicit_user_supersedes_inferred_preference(consolidator_setup):
    """Verify an explicit user directive supersedes an older AI-inferred preference."""
    consolidator, repo = consolidator_setup

    # 1. Existing inferred preference
    inferred_mem = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.USER,
        content="User seems to enjoy lighthearted comedy.",
        structured_data={"preference_topic": "creative_style"},
        source=MemorySource.INFERRED_AGENT,
        confidence=0.6,
        importance=0.4,
        status=MemoryStatus.ACTIVE,
    )
    repo.create_memory(inferred_mem)

    # 2. New explicit user preference on the same topic
    explicit_mem = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.USER,
        content="User explicitly prefers grimdark realism.",
        structured_data={"preference_topic": "creative_style"},
        source=MemorySource.EXPLICIT_USER,
        confidence=0.95,
        importance=0.9,
    )

    saved_list = consolidator.consolidate_and_save([explicit_mem])
    assert len(saved_list) == 1
    new_saved = saved_list[0]

    # Verify version and superseding
    assert new_saved.version == 2

    old_fetched = repo.get_memory(inferred_mem.memory_id)
    assert old_fetched.status == MemoryStatus.SUPERSEDED
    assert old_fetched.superseded_by == new_saved.memory_id


def test_version_increment_and_superseded_linkage(consolidator_setup):
    """Verify version increments consecutively across multiple superseding cycles."""
    consolidator, repo = consolidator_setup

    v1 = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.DISCIPLINE,
        discipline="writers",
        content="Prefer first person POV.",
        structured_data={"preference_topic": "creative_style"},
        source=MemorySource.EXPLICIT_USER,
    )
    saved_v1 = repo.create_memory(v1)
    assert saved_v1.version == 1

    v2 = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.DISCIPLINE,
        discipline="writers",
        content="Prefer third person limited POV.",
        structured_data={"preference_topic": "creative_style"},
        source=MemorySource.EXPLICIT_USER,
    )
    saved_v2 = consolidator.consolidate_and_save([v2])[0]
    assert saved_v2.version == 2

    # Check v1 is superseded by v2
    v1_recheck = repo.get_memory(v1.memory_id)
    assert v1_recheck.status == MemoryStatus.SUPERSEDED
    assert v1_recheck.superseded_by == saved_v2.memory_id


def test_duplicate_content_skipping(consolidator_setup):
    """Verify duplicate memory content is cleanly skipped without raising errors."""
    consolidator, repo = consolidator_setup

    mem = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.CONSTRAINT,
        scope=MemoryScope.USER,
        content="Never use passive voice in action sequences.",
        source=MemorySource.EXPLICIT_USER,
    )
    repo.create_memory(mem)

    # Attempt to persist identical memory
    duplicate = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.CONSTRAINT,
        scope=MemoryScope.USER,
        content="Never use passive voice in action sequences. ",
        source=MemorySource.EXPLICIT_USER,
    )
    result = consolidator.consolidate_and_save([duplicate])
    assert len(result) == 0

    # Verify only 1 record exists in repository
    all_memories = repo.list_memories(owner_id="user_1")
    assert len(all_memories) == 1


def test_lower_precedence_cannot_override_higher_precedence(consolidator_setup):
    """Verify AI inference cannot supersede an explicit user memory."""
    consolidator, repo = consolidator_setup

    explicit_mem = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.USER,
        content="User requires dark fantasy aesthetic.",
        structured_data={"preference_topic": "creative_style"},
        source=MemorySource.EXPLICIT_USER,
    )
    repo.create_memory(explicit_mem)

    # Inferred attempt on same topic
    inferred_candidate = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.USER,
        content="User might like high fantasy.",
        structured_data={"preference_topic": "creative_style"},
        source=MemorySource.INFERRED_AGENT,
    )

    result = consolidator.consolidate_and_save([inferred_candidate])
    # The candidate should not supersede the explicit memory
    assert len(result) == 0

    recheck_explicit = repo.get_memory(explicit_mem.memory_id)
    assert recheck_explicit.status == MemoryStatus.ACTIVE
    assert recheck_explicit.superseded_by is None


def test_different_discipline_no_conflict(consolidator_setup):
    """Verify preferences for different disciplines do not conflict or supersede."""
    consolidator, repo = consolidator_setup

    writers_pref = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.DISCIPLINE,
        discipline="writers",
        content="User prefers minimalist prose.",
        structured_data={"preference_topic": "creative_style"},
        source=MemorySource.EXPLICIT_USER,
    )
    repo.create_memory(writers_pref)

    musicians_pref = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.DISCIPLINE,
        discipline="musicians",
        content="User prefers maximalist wall of sound.",
        structured_data={"preference_topic": "creative_style"},
        source=MemorySource.EXPLICIT_USER,
    )

    result = consolidator.consolidate_and_save([musicians_pref])
    assert len(result) == 1

    # Both should remain active
    w = repo.get_memory(writers_pref.memory_id)
    m = repo.get_memory(musicians_pref.memory_id)
    assert w.status == MemoryStatus.ACTIVE
    assert m.status == MemoryStatus.ACTIVE
