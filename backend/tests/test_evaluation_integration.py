"""
OCTS AI - Evaluation Integration Tests (Phase 4)
Verifies full end-to-end pipeline execution with evaluation enabled across all 4 disciplines,
clarification short-circuits, failure handling, LLM Judge success/fallback, and FastAPI /ask backward compatibility.
"""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.evaluation.engine import EvaluationEngine
from backend.evaluation.judges.llm_judge import LLMJudge
from backend.evaluation.schemas import EvaluationMode, JudgeStatus
from backend.orchestration.executor import OrchestrationExecutor
from server import app


@pytest.fixture
def test_client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Discipline Pipeline Executions
# ---------------------------------------------------------------------------

def test_integration_full_pipeline_writers_evaluation():
    """Verify writers task generates output, evaluates quality & reliability, and returns TrustScore."""
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = (
        "### Act I: The Awakening\n"
        "Princess Lyra uncovers a hidden vault beneath the citadel.\n\n"
        "### Act II: The Conflict\n"
        "She faces the traitorous council in open defiance.\n\n"
        "### Act III: The Resolution\n"
        "The citadel is preserved through enduring unity."
    )
    mock_model.invoke.return_value = mock_resp

    executor = OrchestrationExecutor(model_override=mock_model)
    response = executor.execute_prompt(
        prompt="Design a 3-act story outline with high narrative stakes.",
        role="writers",
    )

    assert response.reply == mock_resp.content
    assert response.role == "writers"
    assert response.agent_used == "narrative_architect"
    assert response.trust_score is not None
    assert 0.0 <= response.trust_score <= 100.0
    assert response.trust_breakdown is not None
    assert response.trust_breakdown["quality_score"] is not None
    assert response.trust_breakdown["reliability_score"] is not None
    assert response.evaluation is not None
    assert response.evaluation["evaluation_status"] == "completed"
    assert len(response.evaluation["criteria_breakdown"]) == 6
    assert len(response.evaluation["reliability_checks"]) == 7


def test_integration_full_pipeline_musicians_evaluation():
    """Verify musicians task evaluates lyrics, chords, and song structure."""
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = (
        "[Verse 1]\n"
        "Shadows stretching down the empty street\n"
        "Cmaj7 - Am7 - Dm7 - G7\n\n"
        "[Chorus]\n"
        "We chase the golden sunrise until morning comes\n"
        "F - G - Em - Am"
    )
    mock_model.invoke.return_value = mock_resp

    executor = OrchestrationExecutor(model_override=mock_model)
    response = executor.execute_prompt(
        prompt="Design a chord progression using modal interchange and harmonic voice leading.",
        role="musicians",
    )

    assert response.role == "musicians"
    assert response.agent_used == "harmonic_arranger"
    assert response.trust_score is not None
    assert response.evaluation["evaluation_status"] == "completed"


def test_integration_full_pipeline_creators_evaluation():
    """Verify creators task evaluates hook effectiveness and retention architecture."""
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = (
        "Stop scrolling if you want to double your video watch time!\n"
        "Hook: Show the surprising result first.\n"
        "Body: Break down the exact framework in 3 steps.\n"
        "CTA: Save this for your next video shoot!"
    )
    mock_model.invoke.return_value = mock_resp

    executor = OrchestrationExecutor(model_override=mock_model)
    response = executor.execute_prompt(
        prompt="Write a high-retention hook for YouTube Shorts.",
        role="creators",
    )

    assert response.role == "creators"
    assert response.agent_used == "hook_retention_architect"
    assert response.trust_score is not None
    assert response.evaluation["evaluation_status"] == "completed"


def test_integration_full_pipeline_designers_evaluation():
    """Verify designers task evaluates design system tokens and visual hierarchy."""
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = (
        "### Semantic Color Tokens (WCAG AAA)\n"
        "- --color-primary: #1E40AF (Contrast 7.1:1)\n"
        "- --color-background: #FFFFFF\n"
        "Typography scale: h1=32px/40px, body=16px/24px."
    )
    mock_model.invoke.return_value = mock_resp

    executor = OrchestrationExecutor(model_override=mock_model)
    response = executor.execute_prompt(
        prompt="Create a color token palette with WCAG AAA contrast.",
        role="designers",
    )

    assert response.role == "designers"
    assert response.agent_used == "design_token_palette_architect"
    assert response.trust_score is not None
    assert response.evaluation["evaluation_status"] == "completed"


# ---------------------------------------------------------------------------
# Core Specification Integration Scenarios
# ---------------------------------------------------------------------------

def test_integration_clarification_no_evaluation(test_client):
    """Verify ambiguous prompt (Case C) returns clarification with all scores None and skipped status."""
    payload = {"prompt": "I need creative ideas and advice on my project."}
    response = test_client.post("/ask", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["needs_clarification"] is True
    assert data["trust_score"] is None
    assert data["trust_breakdown"] is None
    # Evaluation should be skipped or None
    if data.get("evaluation"):
        assert data["evaluation"]["evaluation_status"] == "skipped"
        assert data["evaluation"]["quality_score"] is None
        assert data["evaluation"]["reliability_score"] is None
        assert data["evaluation"]["trust_score"] is None
        assert len(data["evaluation"]["reliability_checks"]) == 0


def test_integration_evaluation_disabled():
    """Verify system functions normally with trust_score None when evaluation is disabled."""
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = "Story text generated."
    mock_model.invoke.return_value = mock_resp

    settings = Settings(evaluation_enabled=False)
    executor = OrchestrationExecutor(model_override=mock_model, settings=settings)

    response = executor.execute_prompt(
        prompt="Write a short story about the sea.",
        role="writers",
    )

    assert response.reply == "Story text generated."
    assert response.trust_score is None
    assert response.trust_breakdown is None
    assert response.evaluation["evaluation_status"] == "skipped"
    assert response.evaluation["quality_score"] is None
    assert response.evaluation["reliability_score"] is None


def test_integration_successful_llm_judge_execution():
    """Verify successful LLM Judge execution sets evaluation_method='llm_judge' and judge_status='success'."""
    # Creative model
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = "Opening hook for video: Stop making this mistake!"
    mock_model.invoke.return_value = mock_resp

    # Judge model
    mock_judge_model = MagicMock()
    mock_judge_resp = MagicMock()
    mock_judge_resp.content = """{
      "scores": {
        "hook_effectiveness": {"score": 95.0, "evidence": "Immediate 3-second tension."},
        "audience_relevance": {"score": 90.0, "evidence": "Clear target audience."},
        "clarity_communication": {"score": 92.0, "evidence": "Concise delivery."},
        "retention_potential": {"score": 88.0, "evidence": "High pacing momentum."},
        "platform_suitability": {"score": 94.0, "evidence": "Calibrated for Shorts."},
        "content_structure": {"score": 90.0, "evidence": "Clean 3-step body."},
        "instruction_adherence": {"score": 95.0, "evidence": "Followed all constraints."}
      },
      "summary": "Outstanding creator output."
    }"""
    mock_judge_model.invoke.return_value = mock_judge_resp

    judge = LLMJudge(model=mock_judge_model)
    settings = Settings(evaluation_enabled=True, evaluation_mode="llm_judge", evaluation_judge_enabled=True)
    engine = EvaluationEngine(judge=judge, settings=settings)

    executor = OrchestrationExecutor(
        model_override=mock_model,
        evaluation_engine_override=engine,
        settings=settings,
    )

    response = executor.execute_prompt(
        prompt="Write a high-retention video hook.",
        role="creators",
    )

    assert response.reply == mock_resp.content
    assert response.trust_score is not None
    assert response.evaluation["evaluation_status"] == "completed"
    assert response.evaluation["evaluation_method"] == "llm_judge"
    assert response.evaluation["judge_status"] == "success"
    assert response.evaluation["fallback_triggered"] is False
    assert response.evaluation["fallback_reason"] is None


def test_integration_llm_judge_fallback_to_deterministic():
    """Verify when LLM Judge times out, system falls back to deterministic heuristics and exposes metadata."""
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = (
        "Stop making this 1 morning mistake if you want deep focus!\n"
        "Step 1: Put your phone away.\n"
        "Step 2: Do 30 minutes of deep work."
    )
    mock_model.invoke.return_value = mock_resp

    # Judge model that times out
    mock_judge_model = MagicMock()
    mock_judge_model.invoke.side_effect = TimeoutError("Judge connection timed out after 10000ms")

    judge = LLMJudge(model=mock_judge_model, max_retries=0)
    settings = Settings(evaluation_enabled=True, evaluation_mode="llm_judge", evaluation_judge_enabled=True)
    engine = EvaluationEngine(judge=judge, settings=settings)

    executor = OrchestrationExecutor(
        model_override=mock_model,
        evaluation_engine_override=engine,
        settings=settings,
    )

    response = executor.execute_prompt(
        prompt="Write a hook script for TikTok.",
        role="creators",
    )

    # Creative output MUST be preserved!
    assert response.reply == mock_resp.content
    # Fallback to deterministic occurred
    assert response.evaluation["evaluation_status"] == "completed"
    assert response.evaluation["evaluation_method"] == "deterministic"
    assert response.evaluation["judge_status"] == "timeout"
    assert response.evaluation["fallback_triggered"] is True
    assert ("timeout" in response.evaluation["fallback_reason"].lower() or "timed out" in response.evaluation["fallback_reason"].lower())
    assert response.trust_score is not None


def test_integration_evaluation_failure_preserves_creative_output():
    """Verify unexpected evaluator crash does not drop the generated creative response."""
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = "Critical screenplay scene description."
    mock_model.invoke.return_value = mock_resp

    mock_engine = MagicMock()
    mock_engine.evaluate_execution.side_effect = RuntimeError("Fatal memory corruption in evaluator")

    executor = OrchestrationExecutor(
        model_override=mock_model,
        evaluation_engine_override=mock_engine,
    )

    response = executor.execute_prompt(
        prompt="Write a screenplay scene.",
        role="writers",
    )

    # Creative output preserved!
    assert response.reply == "Critical screenplay scene description."
    assert response.trust_score is None
    assert response.evaluation["evaluation_status"] == "unavailable"


def test_integration_upstream_model_failure_returns_500(test_client, monkeypatch):
    """Verify upstream model exception properly raises 500 without crashing server state."""
    import server
    mock_model = MagicMock()
    mock_model.invoke.side_effect = RuntimeError("Upstream LLM Provider 503 Service Unavailable")

    mock_exec = OrchestrationExecutor(model=mock_model, router=server.router)
    monkeypatch.setattr(server, "executor", mock_exec)
    monkeypatch.setattr(server, "model", mock_model)

    payload = {
        "prompt": "Design a complex narrative arc with multiple POV shifts.",
        "role": "writers",
    }
    response = test_client.post("/ask", json=payload)
    assert response.status_code == 500
    assert "503" in response.json()["detail"]


def test_integration_api_ask_endpoint_schema_contract(test_client, monkeypatch):
    """Verify POST /ask returns backward-compatible schema with populated evaluation fields."""
    import server
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = (
        "Stop scrolling! Here is the documentary retention framework:\n"
        "1. Hook: Start at the climax.\n"
        "2. Body: Unfold the mystery.\n"
        "3. CTA: Subscribe for part two."
    )
    mock_model.invoke.return_value = mock_resp

    mock_exec = OrchestrationExecutor(model=mock_model, router=server.router)
    monkeypatch.setattr(server, "executor", mock_exec)
    monkeypatch.setattr(server, "model", mock_model)

    payload = {
        "prompt": "Create an opening hook and retention strategy for a documentary video.",
        "role": "creators",
    }
    response = test_client.post("/ask", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Core backward compatibility keys
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert "role" in data
    assert data["role"] == "creators"
    assert "agent_used" in data
    assert data["agent_used"] == "hook_retention_architect"

    # Phase 4 Evaluation keys
    assert "trust_score" in data
    assert "trust_breakdown" in data
    assert "evaluation" in data
    assert data["evaluation"]["evaluation_status"] == "completed"
    assert data["evaluation"]["evaluation_method"] == "deterministic"
    assert data["evaluation"]["judge_status"] == "not_used"
    assert data["evaluation"]["fallback_triggered"] is False
    assert len(data["evaluation"]["criteria_breakdown"]) == 7
    assert len(data["evaluation"]["reliability_checks"]) == 7
