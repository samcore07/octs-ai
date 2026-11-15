"""
OCTS AI - End-to-End Refinement Integration Tests
Verifies OrchestrationExecutor, FastAPI POST /ask contract, regression reversion,
and backward compatibility of response payloads.
"""

from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from backend.config import Settings
from backend.orchestration.executor import OrchestrationExecutor
from backend.schemas import PromptRequest
from server import app, executor


def test_executor_e2e_successful_refinement():
    """Verify OrchestrationExecutor executes self-correction and returns improved artifact."""
    mock_model = MagicMock()
    call_counts = {"count": 0}

    def _mock_invoke(messages):
        call_counts["count"] += 1
        count = call_counts["count"]
        mock_resp = MagicMock()
        if count == 1:
            # Low scoring initial output
            mock_resp.content = "Brief story draft."
        elif count == 2:
            # Peer review critique
            mock_resp.content = (
                '{"strengths": ["Premise"], "actionable_critique": ["Too short"], '
                '"suggested_improvements": ["Expand scenes"]}'
            )
        else:
            # High scoring refined version
            mock_resp.content = (
                "### Act I: The Awakening\nElena entered the temple.\n\n"
                "### Act II: The Ordeal\nThe shadow beasts attacked.\n\n"
                "### Act III: The Victory\nShe banished the darkness forever."
            )
        return mock_resp

    mock_model.invoke.side_effect = _mock_invoke

    exec_instance = OrchestrationExecutor(model=mock_model)
    req = PromptRequest(
        prompt="Write a story outline with Elena and the shadow beasts.",
        role="writers",
    )

    resp = exec_instance.execute(req)

    assert resp.reply is not None
    assert "Act I" in resp.reply
    assert resp.recovery_triggered is True
    assert resp.refinement is not None
    assert resp.refinement["refinement_triggered"] is True
    assert resp.refinement["recovery_attempts"] >= 1
    assert resp.refinement["refinement_status"] == "improved"
    assert resp.refinement["quality_delta"] is not None
    assert resp.refinement["quality_delta"] > 0


def test_executor_e2e_reversion_on_regression():
    """Verify that when refinement produces a regressed candidate, executor reverts to baseline."""
    mock_model = MagicMock()
    call_counts = {"count": 0}

    def _mock_invoke(messages):
        call_counts["count"] += 1
        count = call_counts["count"]
        mock_resp = MagicMock()
        if count == 1:
            # Brief draft that scores 65.0 on instruction adherence (< 70 threshold)
            mock_resp.content = "Elena went into the cavern."
        elif count == 2:
            # Peer review
            mock_resp.content = '{"strengths": [], "actionable_critique": ["More details"], "suggested_improvements": []}'
        else:
            # Candidate severely regresses (single meaningless word)
            mock_resp.content = "X"
        return mock_resp

    mock_model.invoke.side_effect = _mock_invoke

    exec_instance = OrchestrationExecutor(model=mock_model)
    req = PromptRequest(
        prompt="Write about Elena exploring the cavern.",
        role="writers",
    )

    resp = exec_instance.execute(req)

    # Output must revert to attempt 1 baseline, NOT the regressed "X"!
    assert "Elena went into the cavern." in resp.reply
    assert resp.recovery_triggered is True
    assert resp.refinement is not None
    assert resp.refinement["refinement_status"] in ("regressed_reverted", "max_attempts_reached")


def test_api_ask_endpoint_includes_refinement_field():
    """Verify POST /ask endpoint response contains the refinement field in schema."""
    client = TestClient(app)

    mock_model = MagicMock()
    mock_model.invoke.return_value.content = (
        "### Act I: The Calling\nMarcus departed his home planet.\n\n"
        "### Act II: The Asteroid Field\nHe navigated through the cosmic storms.\n\n"
        "### Act III: The New Horizon\nHe arrived at the sanctuary."
    )

    old_model = executor.model
    old_graph = executor.graph
    try:
        executor.model = mock_model
        executor.graph = None  # Force rebuild with mock_model
        executor.__init__(model=mock_model)

        response = client.post(
            "/ask",
            json={"prompt": "Write a three-act space journey outline for Marcus.", "role": "writers"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "recovery_triggered" in data
        assert "refinement" in data
        assert data["refinement"] is not None
        assert "refinement_triggered" in data["refinement"]
        assert "refinement_status" in data["refinement"]
    finally:
        executor.model = old_model
        executor.graph = old_graph


def test_refinement_bypassed_when_config_disabled():
    """Verify refinement does not execute when REFINEMENT_ENABLED is False."""
    custom_settings = Settings(refinement_enabled=False)
    mock_model = MagicMock()
    mock_model.invoke.return_value.content = "Brief text."

    exec_instance = OrchestrationExecutor(model=mock_model, settings=custom_settings)
    req = PromptRequest(prompt="Story", role="writers")
    resp = exec_instance.execute(req)

    assert resp.recovery_triggered is False
    assert resp.refinement is not None
    assert resp.refinement["refinement_triggered"] is False
    assert resp.refinement["refinement_status"] in ("not_needed", "skipped")


def test_final_response_artifact_consistency_and_telemetry():
    """Verify that reply, evaluation, trust_score, and telemetry consistently reflect the winning candidate."""
    mock_model = MagicMock()
    call_counts = {"count": 0}

    def _mock_invoke(messages):
        call_counts["count"] += 1
        count = call_counts["count"]
        mock_resp = MagicMock()
        if count == 1:
            mock_resp.content = "Short draft."
        elif count == 2:
            mock_resp.content = (
                '{"strengths": ["Premise"], "actionable_critique": ["Too brief"], '
                '"suggested_improvements": ["Expand three acts"]}'
            )
        else:
            mock_resp.content = (
                "### Act I: The Gathering\nHeroes assembled.\n\n"
                "### Act II: The Conflict\nBattle raged across the valley.\n\n"
                "### Act III: The Epilogue\nPeace was restored."
            )
        return mock_resp

    mock_model.invoke.side_effect = _mock_invoke

    exec_instance = OrchestrationExecutor(model=mock_model)
    req = PromptRequest(
        prompt="Write a three-act battle outline.",
        role="writers",
    )
    resp = exec_instance.execute(req)

    # 1. Output must match winning candidate
    assert "### Act I: The Gathering" in resp.reply
    # 2. Evaluation and trust score must match winning candidate's evaluation
    assert resp.evaluation is not None
    assert resp.trust_score == resp.evaluation["trust_score"]
    assert resp.trust_breakdown == resp.evaluation["trust_breakdown"]
    assert resp.trust_breakdown["quality_score"] == resp.evaluation["quality_score"]
    assert resp.trust_breakdown["reliability_score"] == resp.evaluation["reliability_score"]
    # 3. Refinement metadata tracks final scores matching winning candidate
    assert resp.refinement["final_quality_score"] == resp.evaluation["quality_score"]
    assert resp.refinement["final_trust_score"] == resp.evaluation["trust_score"]
    # 4. Telemetry tracking
    assert resp.refinement["model_call_count"] >= 2
    assert resp.refinement["reviewer_call_count"] >= 1
    assert "total_refinement_latency_ms" in resp.refinement


def test_clarification_path_bypasses_refinement_strictly():
    """Verify clarification request sets refinement_status='skipped' and recovery_triggered=False."""
    # An ambiguous prompt without discipline should trigger clarification
    exec_instance = OrchestrationExecutor()
    req = PromptRequest(
        prompt="Can you give me something creative?",
        role=None,
    )
    resp = exec_instance.execute(req)

    assert resp.needs_clarification is True
    assert resp.recovery_triggered is False
    assert resp.refinement is not None
    assert resp.refinement["refinement_triggered"] is False
    assert resp.refinement["refinement_status"] == "skipped"

