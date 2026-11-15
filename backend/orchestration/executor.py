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
        evaluation_engine: Optional[Any] = None,
        refinement_engine: Optional[Any] = None,
        memory_manager: Optional[Any] = None,
        settings: Optional[Settings] = None,
        model_override: Optional[Any] = None,
        router_override: Optional[Any] = None,
        evaluation_engine_override: Optional[Any] = None,
        refinement_engine_override: Optional[Any] = None,
        memory_manager_override: Optional[Any] = None,
        graph=None,
    ):
        self.settings = settings or get_settings()
        self.model = model if model is not None else model_override
        self.registry = registry or get_registry()
        active_router = router if router is not None else router_override
        self.router = active_router or AgentRouter(registry=self.registry)

        active_engine = evaluation_engine if evaluation_engine is not None else evaluation_engine_override
        if active_engine is None:
            from backend.evaluation.engine import EvaluationEngine
            self.evaluation_engine = EvaluationEngine(
                model=self.model,
                settings=self.settings,
            )
        else:
            self.evaluation_engine = active_engine

        active_refinement = refinement_engine if refinement_engine is not None else refinement_engine_override
        if active_refinement is None:
            from backend.refinement.engine import RefinementEngine
            self.refinement_engine = RefinementEngine(
                model=self.model,
                settings=self.settings,
            )
        else:
            self.refinement_engine = active_refinement

        active_memory = memory_manager if memory_manager is not None else memory_manager_override
        if active_memory is None:
            from backend.memory.memory_manager import MemoryManager
            self.memory_manager = MemoryManager()
        else:
            self.memory_manager = active_memory

        self.graph = graph or get_orchestration_graph(
            model=self.model,
            router=self.router,
            registry=self.registry,
            evaluator_engine=self.evaluation_engine,
            refinement_engine=self.refinement_engine,
            memory_manager=self.memory_manager,
        )

    def run(
        self,
        prompt: str,
        role: Optional[str] = None,
        session_id: Optional[str] = None,
        task_type: Optional[str] = None,
        project_id: Optional[str] = None,
        owner_id: Optional[str] = None,
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

        resolved_owner = (owner_id or "").strip() or getattr(self.settings, "memory_default_owner_id", "default_user")

        initial_state: OrchestrationState = {
            "request_id": request_id,
            "original_prompt": prompt,
            "discipline_id": clean_role,
            "task_type": task_type,
            "session_id": session_id,
            "owner_id": resolved_owner,
            "project_id": project_id,
            "execution_status": "initialized",
            "started_at": started_at,
            "needs_clarification": False,
        }

        # Calculate safe dynamic recursion limit from configured refinement attempts
        max_attempts = getattr(self.settings, "refinement_max_attempts", 2)
        safe_recursion_limit = max(self.settings.max_recursion_limit, 15 + 8 * max_attempts)

        config = {
            "recursion_limit": safe_recursion_limit,
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
        project_id: Optional[str] = None,
        owner_id: Optional[str] = None,
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
            project_id=project_id,
            owner_id=owner_id,
        )

        # Handle runtime provider exceptions
        if final_state.get("execution_status") == "failed" and final_state.get("execution_error"):
            err = final_state.get("execution_error", "")
            if "Model execution error" in err or "AI model dependency was not provided" in err:
                raise RuntimeError(err)

        reply = final_state.get("best_output") or final_state.get("generated_output") or "No creative output was produced."
        recovery_triggered = final_state.get("recovery_attempts", 0) > 0
        refinement_metadata = final_state.get("refinement_metadata")
        memory_metadata = final_state.get("memory_metadata")

        return PromptResponse(
            reply=reply,
            role=final_state.get("discipline_id"),
            agent_used=final_state.get("selected_persona_id"),
            trust_score=final_state.get("trust_score"),
            trust_breakdown=final_state.get("trust_breakdown"),
            evaluation=final_state.get("evaluation_result"),
            latency_ms=final_state.get("latency_ms"),
            recovery_triggered=recovery_triggered,
            model_used=final_state.get("model_name", self.settings.model_name),
            needs_clarification=final_state.get("needs_clarification", False),
            clarification_question=final_state.get("clarification_question"),
            routing_confidence=final_state.get("routing_confidence"),
            execution_status=final_state.get("execution_status"),
            refinement=refinement_metadata,
            memory=memory_metadata,
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
            project_id=getattr(request, "project_id", None),
            owner_id=getattr(request, "owner_id", None),
        )
