"""
Octs AI - Observability & LangSmith Tracing Setup
Provides graceful, optional tracing integration that never breaks local execution.
"""

import logging
import os
from backend.config import Settings

logger = logging.getLogger("octs.tracing")


def setup_tracing(settings: Settings) -> bool:
    """
    Configures LangSmith tracing based on settings.
    Guarantees zero crashes if LangSmith is disabled, offline, or missing keys.

    Returns:
        bool: True if LangSmith tracing is active, False otherwise.
    """
    if not settings.langsmith_tracing:
        logger.info("LangSmith tracing is disabled by configuration (LANGSMITH_TRACING=false).")
        # Ensure tracing is explicitly off in environment
        os.environ["LANGSMITH_TRACING"] = "false"
        return False

    if not settings.langsmith_api_key or not settings.langsmith_api_key.strip():
        logger.warning(
            "LANGSMITH_TRACING is set to true, but LANGSMITH_API_KEY is not configured. "
            "Continuing execution without LangSmith tracing."
        )
        os.environ["LANGSMITH_TRACING"] = "false"
        return False

    # Apply configuration safely to process environment for LangChain/LangGraph auto-instrumentation
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.strip()
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project.strip()
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint.strip()

    # Redacted log to never print credentials
    masked_key = settings.langsmith_api_key[:4] + "..." + settings.langsmith_api_key[-4:] if len(settings.langsmith_api_key) > 8 else "****"
    logger.info(
        f"LangSmith tracing enabled successfully for project '{settings.langsmith_project}' (Key: {masked_key})."
    )
    return True
