"""
OCTS AI - Memory Orchestration Integration Tests
Verifies memory injection into specialist prompts, memory toggle bypass,
clarification bypass, failed generation bypass, and extraction from winning candidate.
"""

from unittest.mock import MagicMock
import tempfile
import pytest

from backend.config import Settings
from backend.memory.config import MemorySettings
from backend.memory.memory_manager import MemoryManager
from backend.memory.memory_store import MemoryStore
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import (
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
)
from backend.orchestration.executor import OrchestrationExecutor


@pytest.fixture
def memory_test_env():
    """Provides isolated MemoryManager backed by a temporary SQLite database."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    db_url = f"sqlite:///{temp_file.name}"

    mem_settings = MemorySettings(
        memory_enabled=True,
        memory_retrieval_enabled=True,
        memory_auto_extraction=True,
        memory_database_url=db_url,
    )
    store = MemoryStore(settings=mem_settings, database_url=db_url)
    repo = MemoryRepository(store=store)
    manager = MemoryManager(settings=mem_settings, repository=repo)

    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Drafted scene adhering to craft guidelines."
    mock_model.invoke.return_value = mock_response

    return manager, repo, mock_model


def test_memory_context_injection_into_persona_prompt(memory_test_env):
    """Verify stored active memory is retrieved and injected into the specialist's prompt."""
    manager, repo, mock_model = memory_test_env

    # Seed an active preference
    mem = MemoryRecord(
        owner_id="user_writer",
        memory_type=MemoryType.USER_PREFERENCE,
        scope=MemoryScope.USER,
        content="Always write fast-paced cyberpunk dialogue with slang.",
        source=MemorySource.EXPLICIT_USER,
        confidence=0.95,
        importance=0.9,
    )
    repo.create_memory(mem)

    executor = OrchestrationExecutor(
        model_override=mock_model,
        memory_manager_override=manager,
    )

    res = executor.execute_prompt(
        prompt="Write a fast-paced dialogue between two street couriers.",
        role="writers",
        owner_id="user_writer",
    )

    assert res.reply is not None
    assert res.memory is not None
    assert res.memory.get("retrieval_performed") is True
    assert res.memory.get("memories_used") >= 1

    # Verify model received the memory context block in the initial specialist invocation
    initial_call_args = mock_model.invoke.call_args_list[0][0][0]
    user_msg_content = initial_call_args[1].content
    assert "<retrieved_memory_context>" in user_msg_content
    assert "Always write fast-paced cyberpunk dialogue with slang." in user_msg_content
    assert "Task:\nWrite a fast-paced dialogue between two street couriers." in user_msg_content


def test_memory_disabled_toggle_bypasses_retrieval_and_extraction(memory_test_env):
    """Verify when memory is disabled, no retrieval occurs and no memories are saved."""
    manager, repo, mock_model = memory_test_env
    manager.settings.memory_enabled = False

    executor = OrchestrationExecutor(
        model_override=mock_model,
        memory_manager_override=manager,
    )

    prompt = "I prefer noir tone when writing crime fiction."
    res = executor.execute_prompt(
        prompt=prompt,
        role="writers",
        owner_id="user_disabled",
    )

    assert res.reply is not None
    assert res.memory is not None
    assert res.memory.get("enabled") is False
    assert res.memory.get("memories_used") == 0

    # Ensure no memory was persisted
    stored = repo.list_memories(owner_id="user_disabled")
    assert len(stored) == 0


def test_clarification_path_skips_extraction(memory_test_env):
    """Verify ambiguous prompt triggering clarification never extracts or persists memories."""
    manager, repo, mock_model = memory_test_env

    executor = OrchestrationExecutor(
        model_override=mock_model,
        memory_manager_override=manager,
    )

    # Completely ambiguous prompt spanning multiple creative disciplines
    ambiguous_prompt = "I prefer noir tone. Can you help me make something artistic?"
    res = executor.execute_prompt(
        prompt=ambiguous_prompt,
        role=None,  # No role specified
        owner_id="user_clarify",
    )

    if res.needs_clarification:
        assert res.memory is not None
        assert res.memory.get("new_memories_extracted") == 0
        stored = repo.list_memories(owner_id="user_clarify")
        assert len(stored) == 0


def test_failed_generation_skips_extraction(memory_test_env):
    """Verify execution failures abort memory extraction."""
    manager, repo, mock_model = memory_test_env

    # Simulate model failure
    mock_model.invoke.side_effect = RuntimeError("Fatal LLM crash")

    executor = OrchestrationExecutor(
        model_override=mock_model,
        memory_manager_override=manager,
    )

    with pytest.raises(RuntimeError):
        executor.execute_prompt(
            prompt="I prefer noir tone. Draft chapter 1.",
            role="writers",
            owner_id="user_fail",
        )

    # Verify no extraction occurred
    stored = repo.list_memories(owner_id="user_fail")
    assert len(stored) == 0


def test_successful_execution_extracts_and_persists_memory(memory_test_env):
    """Verify normal successful execution extracts explicit preference and persists to DB."""
    manager, repo, mock_model = memory_test_env

    executor = OrchestrationExecutor(
        model_override=mock_model,
        memory_manager_override=manager,
    )

    prompt = "I prefer noir tone when writing mysteries."
    res = executor.execute_prompt(
        prompt=prompt,
        role="writers",
        owner_id="user_extract",
    )

    assert res.reply is not None
    assert res.memory is not None
    assert res.memory.get("extraction_performed") is True
    assert res.memory.get("persistence_status") == "success"

    stored = repo.list_memories(owner_id="user_extract")
    assert len(stored) >= 1
    assert any("noir tone" in m.content.lower() for m in stored)


def test_refinement_reversion_extracts_from_winning_baseline(memory_test_env):
    """Verify when refined candidate regresses, extraction operates on winning baseline artifact."""
    manager, repo, mock_model = memory_test_env

    call_counts = {"count": 0}

    def _mock_invoke(messages):
        call_counts["count"] += 1
        count = call_counts["count"]
        mock_resp = MagicMock()
        if count == 1:
            # Baseline output
            mock_resp.content = (
                "### Act I: Baseline Narrative\n"
                "The protagonist is Marcus Vance, an investigator.\n"
                "### Act II: Investigation\n"
                "Marcus tracks the clues across the neon city.\n"
                "### Act III: Resolution\n"
                "Marcus solves the case."
            )
        elif count == 2:
            # Peer review
            mock_resp.content = '{"strengths": ["Plot"], "actionable_critique": ["Expand"], "suggested_improvements": ["Add dialogue"]}'
        else:
            # Regressed refined output (empty or poor)
            mock_resp.content = "Brief fragment."
        return mock_resp

    mock_model.invoke.side_effect = _mock_invoke

    executor = OrchestrationExecutor(
        model_override=mock_model,
        memory_manager_override=manager,
    )

    prompt = "In our sci-fi project, the protagonist is Marcus Vance. Write a three-act mystery outline."
    res = executor.execute_prompt(
        prompt=prompt,
        role="writers",
        project_id="proj_marcus",
        owner_id="user_rev",
    )

    # Regressed draft rejected; baseline selected as best_output
    assert res.reply is not None
    assert "Act I: Baseline Narrative" in res.reply

    # Memory extraction should reflect the winning baseline
    stored = repo.list_memories(owner_id="user_rev", project_id="proj_marcus")
    assert len(stored) >= 1
    assert any("marcus vance" in m.content.lower() for m in stored)

