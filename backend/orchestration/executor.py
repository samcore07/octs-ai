"""
OCTS AI - Orchestration Executor (Refined Phase 3)
High-level execution harness managing invocation of the LangGraph workflow, recursion limits, and schema translation.
Receives explicit model and router dependencies.
"""

import logging
import time
import uuid
from typing import Any, Dict, Optional

from backend.config import Settings, get_settings
from backend.schemas import PromptRequest, PromptResponse
from backend.agents.registry import AgentRegistry, get_registry
from backend.agents.routing.classifier import AgentRouter
from backend.orchestration.graph import get_orchestration_graph
from backend.orchestration.state import OrchestrationState

logger = logging.getLogger("octs.orchestration.executor")


class OrchestrationExecutor:
    """
    Executes creative queries through the single shared LangGraph orchestration pipeline.
    Uses explicit dependency injection for the LLM model and router.
    """

    def __init__(
        self,
        model: Optional[Any] = None,
        router: Optional[AgentRouter] = None,
        registry: Optional[AgentRegistry] = None,
        settings: Optional[Settings] = None,
        model_override: Optional[Any] = None,
        router_override: Optional[Any] = None,
        graph=None,
    ):
        self.settings = settings or get_settings()
        self.model = model if model is not None else model_override
        self.registry = registry or get_registry()
        active_router = router if router is not None else router_override
        self.router = active_router or AgentRouter(registry=self.registry)
        self.graph = graph or get_orchestration_graph(
            model=self.model,
            router=self.router,
            registry=self.registry,
        )

    def run(
        self,
        prompt: str,
        role: Optional[str] = None,
        session_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> OrchestrationState:
        """
        Executes a prompt through the LangGraph StateGraph pipeline.
        """
        request_id = str(uuid.uuid4())
        started_at = time.perf_counter()

        # Clean discipline input: None if omitted or general
        clean_role = None
        if role and isinstance(role, str):
            r = role.strip().lower()
            if r in self.settings.allowed_disciplines:
                clean_role = r

        initial_state: OrchestrationState = {
            "request_id": request_id,
            "original_prompt": prompt,
            "discipline_id": clean_role,
            "task_type": task_type,
            "session_id": session_id,
            "execution_status": "initialized",
            "started_at": started_at,
            "needs_clarification": False,
        }

        config = {
            "recursion_limit": self.settings.max_recursion_limit,
            "tags": ["octs-orchestration", clean_role or "unspecified"],
            "metadata": {
                "request_id": request_id,
                "role": clean_role or "unspecified",
                "session_id": session_id,
            },
        }

        logger.info(
            f"Invoking LangGraph pipeline [req_id={request_id[:8]}, role={clean_role}, "
            f"prompt_len={len(prompt) if prompt else 0}]"
        )

        try:
            final_state = self.graph.invoke(initial_state, config=config)
            return final_state
        except Exception as e:
            logger.error(f"Uncaught graph execution error [req_id={request_id}]: {e}")
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            return {
                **initial_state,
                "execution_status": "failed",
                "execution_error": str(e),
                "generated_output": f"Internal execution failure: {str(e)}",
                "latency_ms": elapsed_ms,
                "completed_at": time.time(),
            }

    def execute_prompt(
        self,
        prompt: str,
        role: Optional[str] = None,
        session_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> PromptResponse:
        """
        Runs the workflow and converts output state into the PromptResponse schema.
        Handles both normal executions and clarification outcomes.
        """
        final_state = self.run(
            prompt=prompt,
            role=role,
            session_id=session_id,
            task_type=task_type,
        )

        # Handle runtime provider exceptions
        if final_state.get("execution_status") == "failed" and final_state.get("execution_error"):
            err = final_state.get("execution_error", "")
            if "Model execution error" in err or "AI model dependency was not provided" in err:
                raise RuntimeError(err)

        reply = final_state.get("generated_output") or "No creative output was produced."

        return PromptResponse(
            reply=reply,
            role=final_state.get("discipline_id"),
            agent_used=final_state.get("selected_persona_id"),
            trust_score=None,
            trust_breakdown=None,
            latency_ms=final_state.get("latency_ms"),
            recovery_triggered=False,
            model_used=final_state.get("model_name", self.settings.model_name),
            needs_clarification=final_state.get("needs_clarification", False),
            clarification_question=final_state.get("clarification_question"),
            routing_confidence=final_state.get("routing_confidence"),
            execution_status=final_state.get("execution_status"),
        )

    def execute(self, request: PromptRequest) -> PromptResponse:
        """
        Convenience execution method accepting a validated PromptRequest schema.
        """
        return self.execute_prompt(
            prompt=request.prompt,
            role=request.role,
            session_id=request.session_id,
            task_type=getattr(request, "task_type", None),
        )
