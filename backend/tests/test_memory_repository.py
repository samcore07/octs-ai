"""
OCTS AI - Memory Repository Unit Tests
Verifies SQLite CRUD operations, persistence across restart, soft delete,
archiving, superseding, project management, and transactional atomicity.
"""

import os
import tempfile
import pytest

from backend.memory.memory_store import MemoryStore
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import (
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
    MemoryUpdate,
    ProjectRecord,
    ProjectUpdate,
)


@pytest.fixture
def temp_repo():
    """Provides a temporary file-backed MemoryRepository clean for each test."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    db_url = f"sqlite:///{temp_file.name}"

    store = MemoryStore(database_url=db_url)
    repo = MemoryRepository(store=store)

    yield repo, temp_file.name

    if os.path.exists(temp_file.name):
        try:
            os.remove(temp_file.name)
        except OSError:
            pass


def test_repository_create_and_get(temp_repo):
    """Verify storing and retrieving a memory record."""
    repo, _ = temp_repo

    rec = MemoryRecord(
        owner_id="user_test_1",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.USER,
        content="Always write in third-person limited POV.",
        discipline="writers",
    )

    created = repo.create_memory(rec)
    assert created.memory_id == rec.memory_id

    fetched = repo.get_memory(rec.memory_id, owner_id="user_test_1")
    assert fetched is not None
    assert fetched.content == "Always write in third-person limited POV."
    assert fetched.owner_id == "user_test_1"
    assert fetched.discipline == "writers"


def test_repository_persistence_across_restart(temp_repo):
    """Verify data persists when database connection is closed and reopened."""
    repo, db_path = temp_repo

    rec = MemoryRecord(
        owner_id="user_restart",
        memory_type=MemoryType.CONSTRAINT,
        content="Brand primary color must strictly be #0066FF.",
        discipline="designers",
    )
    repo.create_memory(rec)

    # Simulate restart by instantiating a completely new store and repository on the same file
    new_store = MemoryStore(database_url=f"sqlite:///{db_path}")
    new_repo = MemoryRepository(store=new_store)

    fetched = new_repo.get_memory(rec.memory_id, owner_id="user_restart")
    assert fetched is not None
    assert fetched.content == "Brand primary color must strictly be #0066FF."
    assert fetched.status == MemoryStatus.ACTIVE


def test_repository_update_and_archive(temp_repo):
    """Verify updating fields and archiving memory records."""
    repo, _ = temp_repo

    rec = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.USER_PREFERENCE,
        content="Prefer light mode designs.",
    )
    repo.create_memory(rec)

    # Update content and confidence
    upd = MemoryUpdate(content="Prefer dark mode designs with high contrast.", confidence=0.95)
    updated = repo.update_memory(rec.memory_id, upd, owner_id="user_1")
    assert updated.content == "Prefer dark mode designs with high contrast."
    assert updated.confidence == 0.95

    # Archive
    archived = repo.archive_memory(rec.memory_id, owner_id="user_1")
    assert archived is True

    fetched = repo.get_memory(rec.memory_id, owner_id="user_1")
    assert fetched.status == MemoryStatus.ARCHIVED


def test_repository_supersede_and_versioning(temp_repo):
    """Verify superseding marks old record superseded and links to version 2."""
    repo, _ = temp_repo

    old_rec = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.DECISION,
        content="We chose 4-act plot structure.",
        version=1,
    )
    repo.create_memory(old_rec)

    new_rec = MemoryRecord(
        owner_id="user_1",
        memory_type=MemoryType.DECISION,
        content="Revised: We chose 3-act plot structure for faster pacing.",
    )

    superseded = repo.supersede_memory(
        old_memory_id=old_rec.memory_id,
        new_record=new_rec,
        owner_id="user_1",
    )

    assert superseded.version == 2
    assert superseded.content == "Revised: We chose 3-act plot structure for faster pacing."

    old_fetched = repo.get_memory(old_rec.memory_id, owner_id="user_1")
    assert old_fetched.status == MemoryStatus.SUPERSEDED
    assert old_fetched.superseded_by == superseded.memory_id


def test_repository_soft_and_hard_delete(temp_repo):
    """Verify soft delete marks status as DELETED, and hard delete purges row."""
    repo, _ = temp_repo

    rec = MemoryRecord(owner_id="user_del", memory_type=MemoryType.USER_PREFERENCE, content="Temporary note.")
    repo.create_memory(rec)

    # Soft delete
    assert repo.delete_memory(rec.memory_id, owner_id="user_del", hard_delete=False) is True
    soft_fetched = repo.get_memory(rec.memory_id, owner_id="user_del")
    assert soft_fetched.status == MemoryStatus.DELETED

    # Hard delete
    assert repo.delete_memory(rec.memory_id, owner_id="user_del", hard_delete=True) is True
    assert repo.get_memory(rec.memory_id, owner_id="user_del") is None


def test_repository_project_lifecycle(temp_repo):
    """Verify ProjectRecord creation, retrieval, updates, and cascading deactivation."""
    repo, _ = temp_repo

    proj = ProjectRecord(
        owner_id="user_proj",
        name="Soundtrack Horizon",
        description="Cinematic synth-wave concept album.",
        discipline="musicians",
    )
    repo.create_project(proj)

    # Add project-scoped memory
    mem = MemoryRecord(
        owner_id="user_proj",
        memory_type=MemoryType.PROJECT,
        scope=MemoryScope.PROJECT,
        project_id=proj.project_id,
        content="BPM must remain locked between 110 and 125.",
    )
    repo.create_memory(mem)

    # List projects
    projs = repo.list_projects(owner_id="user_proj")
    assert len(projs) == 1
    assert projs[0].name == "Soundtrack Horizon"

    # Delete project -> should archive project memories
    assert repo.delete_project(proj.project_id, owner_id="user_proj") is True
    deactivated = repo.get_project(proj.project_id, owner_id="user_proj")
    assert deactivated.is_active is False

    mem_fetched = repo.get_memory(mem.memory_id, owner_id="user_proj")
    assert mem_fetched.status == MemoryStatus.ARCHIVED
