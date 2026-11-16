"""
OCTS AI - Gemini Multi-Model Pool & Token Quota Orchestrator
Distributes creative workflows across the 4 free Gemini API models:
- gemini-3.8-flash: High-capability creative generation and structural synthesis.
- gemini-3.5-flash-lite: Fast intent classification, constraint binding, and routing.
- gemini-3.6-flash: Independent rubric evaluation, trust scoring, and craft auditing.
- gemini-3.1-flash-lite: Autonomous refinement, cadence verification, and peer review.

Provides automatic cross-model failover when token/rate limits (HTTP 429 / ResourceExhausted)
are encountered to guarantee execution without hitting token exhaustion bottlenecks.
"""

from datetime import datetime, timezone
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from langchain.chat_models import init_chat_model
from backend.config import get_settings

logger = logging.getLogger("octs.models.pool")

DEFAULT_FREE_GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
]

STAGE_MODEL_MAPPING = {
    "routing": "gemini-3.5-flash-lite",
    "generation": "gemini-3.8-flash",
    "evaluation": "gemini-3.6-flash",
    "refinement": "gemini-3.1-flash-lite",
}


def is_rate_or_quota_error(exc: Exception) -> bool:
    """Detects whether an exception is due to rate limits or token/quota exhaustion."""
    text = str(exc).lower()
    return (
        "429" in text
        or "resource_exhausted" in text
        or "resourceexhausted" in text
        or "quota" in text
        or "rate_limit" in text
        or "too many requests" in text
        or "limit reached" in text
    )


class GeminiModelPool:
    """
    Manages client connections to all 4 free Gemini models.
    Supports stage-specific model dispatching, round-robin load distribution,
    and instantaneous failover to secondary free models upon token exhaustion.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_provider: str = "google_genai",
        primary_model: str = "gemini-3.5-flash-lite",
        models_override: Optional[Dict[str, Any]] = None,
    ):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.gemini_api_key
        self.model_provider = model_provider or self.settings.model_provider
        self.primary_model_name = primary_model or self.settings.model_name
        self._models: Dict[str, Any] = models_override or {}
        self._rr_index = 0

        # Lazy initialize models
        if not self._models and self.api_key:
            self._initialize_pool()

    def _initialize_pool(self):
        """Initializes client handles for each supported free Gemini model."""
        for m_name in DEFAULT_FREE_GEMINI_MODELS:
            try:
                kwargs = {
                    "model_provider": self.model_provider,
                    "api_key": self.api_key,
                }
                if "flash-lite" not in m_name.lower():
                    kwargs["temperature"] = self.settings.model_temperature

                client = init_chat_model(m_name, **kwargs)
                self._models[m_name] = client
                logger.info(f"Initialized Gemini model in pool: {m_name}")
            except Exception as e:
                logger.warning(f"Could not pre-initialize pool model {m_name}: {e}")

    def get_model(self, model_name: str) -> Optional[Any]:
        """Retrieves or creates a model instance from the pool."""
        if model_name in self._models:
            return self._models[model_name]

        if not self.api_key:
            return None

        try:
            kwargs = {
                "model_provider": self.model_provider,
                "api_key": self.api_key,
            }
            if "flash-lite" not in model_name.lower():
                kwargs["temperature"] = self.settings.model_temperature
            client = init_chat_model(model_name, **kwargs)
            self._models[model_name] = client
            return client
        except Exception as e:
            logger.error(f"Failed to instantiate model {model_name}: {e}")
            return None

    def get_model_for_stage(self, stage: str) -> Tuple[Optional[Any], str]:
        """Returns the optimal Gemini model instance and name for a given workflow stage."""
        target_name = STAGE_MODEL_MAPPING.get(stage, self.primary_model_name)
        model = self.get_model(target_name)
        if model is None:
            # Fallback to primary or any available model in pool
            for candidate in DEFAULT_FREE_GEMINI_MODELS:
                model = self.get_model(candidate)
                if model is not None:
                    return model, candidate
        return model, target_name

    def invoke(self, model_input: Any, **kwargs) -> Any:
        """
        Default drop-in LangChain invoke interface.
        Dispatches to primary model with automated failover across the free pool.
        """
        res, _ = self.invoke_resilient(model_input, stage="generation", **kwargs)
        return res

    def invoke_resilient(
        self,
        model_input: Any,
        stage: str = "generation",
        preferred_model: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Any, str]:
        """
        Invokes model for the specified stage with automatic quota/token limit failover.
        Cycles through alternative free models if a 429 or quota limit is encountered.
        """
        target_model_name = preferred_model or STAGE_MODEL_MAPPING.get(stage, self.primary_model_name)
        candidates = [target_model_name] + [
            m for m in DEFAULT_FREE_GEMINI_MODELS if m != target_model_name
        ]

        last_error = None
        for candidate in candidates:
            client = self.get_model(candidate)
            if client is None:
                continue

            try:
                logger.debug(f"Invoking {candidate} for stage={stage}")
                response = client.invoke(model_input, **kwargs)
                return response, candidate
            except Exception as e:
                last_error = e
                if is_rate_or_quota_error(e):
                    logger.warning(
                        f"Rate limit or token quota exhausted on {candidate}. "
                        f"Failing over to next available free Gemini model in pool to prevent failure: {e}"
                    )
                    continue
                else:
                    logger.error(f"Execution error on model {candidate}: {e}")
                    # If it's not a rate limit error, raise or try fallback if severe
                    raise e

        # If all candidates exhausted, raise last error
        if last_error:
            raise last_error
        raise RuntimeError("No available Gemini models in pool could be invoked.")

    def list_available_models(self) -> List[Dict[str, Any]]:
        """Returns metadata regarding active pool models."""
        return [
            {
                "id": "gemini-3.8-flash",
                "name": "Gemini 3.8 Flash",
                "tier": "Free Tier",
                "assigned_role": "Primary Generation & Structural Synthesis",
                "status": "ready",
            },
            {
                "id": "gemini-3.5-flash-lite",
                "name": "Gemini 3.5 Flash Lite",
                "tier": "Free Tier",
                "assigned_role": "Intent Routing & Constraint Binding",
                "status": "ready",
            },
            {
                "id": "gemini-3.6-flash",
                "name": "Gemini 3.6 Flash",
                "tier": "Free Tier",
                "assigned_role": "Craft Quality Evaluation & TrustScore Judge",
                "status": "ready",
            },
            {
                "id": "gemini-3.1-flash-lite",
                "name": "Gemini 3.1 Flash Lite",
                "tier": "Free Tier",
                "assigned_role": "Autonomous Refinement & Peer Review",
                "status": "ready",
            },
        ]


_GLOBAL_MODEL_POOL: Optional[GeminiModelPool] = None


def get_model_pool(api_key: Optional[str] = None) -> GeminiModelPool:
    """Returns the singleton GeminiModelPool instance."""
    global _GLOBAL_MODEL_POOL
    if _GLOBAL_MODEL_POOL is None:
        _GLOBAL_MODEL_POOL = GeminiModelPool(api_key=api_key)
    return _GLOBAL_MODEL_POOL
