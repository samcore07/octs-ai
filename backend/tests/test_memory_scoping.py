"""
OCTS AI - Memory Scoping & Isolation Unit Tests
Verifies strict user isolation, project boundaries, cross-project leakage prevention,
discipline matching, and identity resolution constraints.
"""

import os
import tempfile
import pytest

from backend.memory.identity import AnonymousIdentityProvider, HeaderIdentityProvider
from backend.memory.memory_store import MemoryStore
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import (
    MemoryRecord,
    MemoryScope,
    MemoryType,
    ProjectRecord,
)


@pytest.fixture
def temp_repo():
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    store = MemoryStore(database_url=f"sqlite:///{temp_file.name}")
    repo = MemoryRepository(store=store)
    yield repo, temp_file.name
    if os.path.exists(temp_file.name):
        try:
            os.remove(temp_file.name)
        except OSError:
            pass


def test_user_isolation_strictly_enforced(temp_repo):
    """Verify memories belonging to User A are completely invisible to User B."""
    repo, _ = temp_repo

    # User A memory
    mem_a = MemoryRecord(
        owner_id="user_alice",
        memory_type=MemoryType.USER_PREFERENCE,
        content="Alice prefers dark atmospheric prose.",
    )
    repo.create_memory(mem_a)

    # User B memory
    mem_b = MemoryRecord(
        owner_id="user_bob",
        memory_type=MemoryType.USER_PREFERENCE,
        content="Bob prefers comedic slapstick scripts.",
    )
    repo.create_memory(mem_b)

    # Query for Alice -> only Alice's memories returned
    cands_alice = repo.query_retrieval_candidates(owner_id="user_alice")
    assert len(cands_alice) == 1
    assert cands_alice[0].content == "Alice prefers dark atmospheric prose."

    # Query for Bob -> only Bob's memories returned
    cands_bob = repo.query_retrieval_candidates(owner_id="user_bob")
    assert len(cands_bob) == 1
    assert cands_bob[0].content == "Bob prefers comedic slapstick scripts."

    # Attempt to directly fetch Alice's memory using Bob's owner_id
    assert repo.get_memory(mem_a.memory_id, owner_id="user_bob") is None


def test_project_isolation_and_leakage_prevention(temp_repo):
    """Verify Project A memories never leak into Project B or project-agnostic queries."""
    repo, _ = temp_repo

    owner = "creator_1"

    # 1. User-level preference (should apply across projects)
    user_pref = MemoryRecord(
        owner_id=owner,
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.USER,
        content="Prefers 16:9 aspect ratio thumbnails.",
    )
    repo.create_memory(user_pref)

    # 2. Project A memory (Secret Sci-Fi Movie)
    mem_proj_a = MemoryRecord(
        owner_id=owner,
        memory_type=MemoryType.PROJECT,
        scope=MemoryScope.PROJECT,
        project_id="proj_sci_fi_alpha",
        content="The main alien antagonist is named Zorak.",
    )
    repo.create_memory(mem_proj_a)

    # 3. Project B memory (Children Book)
    mem_proj_b = MemoryRecord(
        owner_id=owner,
        memory_type=MemoryType.PROJECT,
        scope=MemoryScope.PROJECT,
        project_id="proj_kids_book_beta",
        content="The cute friendly puppy is named Barnaby.",
    )
    repo.create_memory(mem_proj_b)

    # A. Query in Project A context:
    # Must retrieve user_pref and Project A, but NEVER Project B!
    cands_a = repo.query_retrieval_candidates(owner_id=owner, project_id="proj_sci_fi_alpha")
    contents_a = [m.content for m in cands_a]
    assert "Prefers 16:9 aspect ratio thumbnails." in contents_a
    assert "The main alien antagonist is named Zorak." in contents_a
    assert "The cute friendly puppy is named Barnaby." not in contents_a

    # B. Query in Project B context:
    # Must retrieve user_pref and Project B, but NEVER Project A!
    cands_b = repo.query_retrieval_candidates(owner_id=owner, project_id="proj_kids_book_beta")
    contents_b = [m.content for m in cands_b]
    assert "Prefers 16:9 aspect ratio thumbnails." in contents_b
    assert "The cute friendly puppy is named Barnaby." in contents_b
    assert "The main alien antagonist is named Zorak." not in contents_b

    # C. Query without any project context (project_id=None):
    # Must retrieve user_pref, but NEVER leak Project A or Project B memories!
    cands_none = repo.query_retrieval_candidates(owner_id=owner, project_id=None)
    contents_none = [m.content for m in cands_none]
    assert "Prefers 16:9 aspect ratio thumbnails." in contents_none
    assert "The main alien antagonist is named Zorak." not in contents_none
    assert "The cute friendly puppy is named Barnaby." not in contents_none


def test_discipline_isolation(temp_repo):
    """Verify discipline-specific preferences do not contaminate other disciplines."""
    repo, _ = temp_repo
    owner = "multidisciplinary_artist"

    # Writers preference
    writers_mem = MemoryRecord(
        owner_id=owner,
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.DISCIPLINE,
        discipline="writers",
        content="Avoid second-person narrative voice.",
    )
    repo.create_memory(writers_mem)

    # Musicians preference
    musicians_mem = MemoryRecord(
        owner_id=owner,
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.DISCIPLINE,
        discipline="musicians",
        content="Always use natural minor scale for verse chords.",
    )
    repo.create_memory(musicians_mem)

    # Query for Writers task
    writers_cands = repo.query_retrieval_candidates(owner_id=owner, discipline="writers")
    w_contents = [m.content for m in writers_cands]
    assert "Avoid second-person narrative voice." in w_contents
    assert "Always use natural minor scale for verse chords." not in w_contents

    # Query for Musicians task
    musicians_cands = repo.query_retrieval_candidates(owner_id=owner, discipline="musicians")
    m_contents = [m.content for m in musicians_cands]
    assert "Always use natural minor scale for verse chords." in m_contents
    assert "Avoid second-person narrative voice." not in m_contents


def test_identity_provider_resolution():
    """Verify IdentityProvider resolves headers correctly and flags unauthenticated limitations."""
    header_provider = HeaderIdentityProvider(user_header="x-user-id")

    # Authenticated via proxy header
    ctx_auth = header_provider.resolve_identity(headers={"X-User-Id": "corp_designer_99", "X-Tenant-Id": "studio_a"})
    assert ctx_auth.owner_id == "corp_designer_99"
    assert ctx_auth.is_authenticated is True
    assert ctx_auth.tenant_id == "studio_a"

    # Fallback when header is missing
    ctx_anon = header_provider.resolve_identity(headers={})
    assert ctx_anon.owner_id == "default_user"
    assert ctx_anon.is_authenticated is False

    # Anonymous development provider
    anon_provider = AnonymousIdentityProvider(default_owner_id="local_user")
    ctx_dev = anon_provider.resolve_identity()
    assert ctx_dev.owner_id == "local_user"
    assert ctx_dev.is_authenticated is False
