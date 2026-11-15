"""
OCTS AI - Memory Schemas Unit Tests
Verifies Pydantic v2 validation, enum constraints, bounds, defaults, and serialization.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from backend.memory.schemas import (
    MemoryCreate,
    MemoryMetadata,
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
    MemoryUpdate,
    ProjectRecord,
    RetrievedMemoryItem,
)


def test_memory_record_valid_defaults():
    """Verify MemoryRecord generates valid defaults, UUID, and UTC timestamps."""
    record = MemoryRecord(
        memory_type=MemoryType.USER_PREFERENCE,
        content="Prefers concise, punchy sentence rhythm in dialogue.",
        discipline="writers",
    )

    assert record.memory_id is not None
    assert len(record.memory_id) == 36
    assert record.owner_id == "default_user"
    assert record.memory_type == MemoryType.USER_PREFERENCE
    assert record.scope == MemoryScope.USER
    assert record.discipline == "writers"
    assert record.confidence == 0.85
    assert record.importance == 0.70
    assert record.status == MemoryStatus.ACTIVE
    assert record.version == 1
    assert record.created_at.tzinfo is not None
    assert record.access_count == 0


def test_memory_record_invalid_empty_content():
    """Verify empty or whitespace content raises ValidationError."""
    with pytest.raises(ValidationError):
        MemoryRecord(
            memory_type=MemoryType.CONSTRAINT,
            content="   ",
        )


def test_memory_record_confidence_bounds():
    """Verify confidence must be between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        MemoryRecord(
            memory_type=MemoryType.DECISION,
            content="Valid content.",
            confidence=1.5,
        )

    with pytest.raises(ValidationError):
        MemoryRecord(
            memory_type=MemoryType.DECISION,
            content="Valid content.",
            confidence=-0.1,
        )


def test_memory_record_discipline_validation():
    """Verify discipline must be one of allowed disciplines."""
    rec = MemoryRecord(
        memory_type=MemoryType.USER_PREFERENCE,
        content="Valid content.",
        discipline="musicians",
    )
    assert rec.discipline == "musicians"

    with pytest.raises(ValidationError):
        MemoryRecord(
            memory_type=MemoryType.USER_PREFERENCE,
            content="Valid content.",
            discipline="invalid_discipline_name",
        )


def test_project_record_serialization():
    """Verify ProjectRecord model serializes and deserializes accurately."""
    proj = ProjectRecord(
        name="Elena Cyberpunk Saga",
        description="A dark sci-fi interactive fiction series.",
        discipline="writers",
        metadata={"genre": "cyberpunk", "target_words": 50000},
    )

    assert proj.project_id is not None
    assert proj.is_active is True
    assert proj.metadata["genre"] == "cyberpunk"
    dump = proj.model_dump()
    assert dump["name"] == "Elena Cyberpunk Saga"


def test_memory_metadata_serialization():
    """Verify MemoryMetadata serializes cleanly with retrieved items."""
    item = RetrievedMemoryItem(
        memory_id="test-id",
        memory_type="constraint",
        content="No purple prose.",
        relevance_score=0.92,
        retrieval_reason="Exact keyword match",
    )
    meta = MemoryMetadata(
        enabled=True,
        retrieval_performed=True,
        memories_used=1,
        extraction_performed=True,
        persistence_status="success",
        memories_retrieved=[item],
        project_id="proj-123",
    )

    dump = meta.model_dump()
    assert dump["enabled"] is True
    assert dump["memories_used"] == 1
    assert len(dump["memories_retrieved"]) == 1
    assert dump["memories_retrieved"][0]["memory_id"] == "test-id"
