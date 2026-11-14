"""
OCTS AI - Agent Router & Classifier
Determines the optimal specialist persona for a given user prompt and creative discipline.
Combines explicit task mapping, deterministic heuristic pattern scoring, and safe model classification with deterministic fallback.
"""

from typing import Any, Dict, Optional
from backend.agents.base import RoutingResult
from backend.agents.registry import get_registry
from backend.agents.routing.rules import (
    DEFAULT_PERSONAS,
    TASK_TYPE_MAPPING,
    score_prompt_for_discipline,
)


class AgentRouter:
    """Routes creative tasks to specialist personas within a specified discipline."""

    def __init__(self, registry=None):
        self.registry = registry or get_registry()

    def route(
        self,
        prompt: str,
        discipline_id: str,
        task_type: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None,
        model: Optional[Any] = None,
    ) -> RoutingResult:
        """
        Routes the user's prompt to the most qualified specialist persona.

        Args:
            prompt: User creative inquiry or request text.
            discipline_id: Target discipline identifier ('writers', 'musicians', 'creators', 'designers').
            task_type: Optional explicit task category.
            session_context: Optional session context dictionary.
            model: Optional LangChain model for assisted classification on ambiguous tasks.

        Returns:
            RoutingResult containing resolved discipline, persona, confidence, rationale, and alternatives.
        """
        # Validate discipline
        clean_discipline = (discipline_id or "").lower().strip()
        discipline_config = self.registry.get_discipline(clean_discipline)

        if not discipline_config:
            # Fallback to writers if an unknown discipline is passed, or reject safely
            clean_discipline = "writers"
            discipline_config = self.registry.get_discipline("writers")
            default_persona_id = DEFAULT_PERSONAS["writers"]
            persona = self.registry.get_persona(default_persona_id)

            return RoutingResult(
                discipline_id=clean_discipline,
                persona_id=default_persona_id,
                confidence=0.30,
                rationale=(
                    f"Discipline '{discipline_id}' is unrecognized. Defaulted to "
                    f"Writers & Storytellers with {persona.display_name}."
                ),
                routing_method="discipline_default_fallback",
            )

        # 1. Check explicit task_type mapping if provided
        if task_type:
            normalized_task = task_type.lower().strip()
            if normalized_task in TASK_TYPE_MAPPING:
                mapped_persona_id = TASK_TYPE_MAPPING[normalized_task]
                persona = self.registry.get_persona(mapped_persona_id)
                # Verify that the mapped persona belongs to the selected discipline
                if persona and persona.discipline_id == clean_discipline:
                    return RoutingResult(
                        discipline_id=clean_discipline,
                        persona_id=mapped_persona_id,
                        confidence=0.95,
                        rationale=f"Selected {persona.display_name} based on explicit task categorization '{task_type}'.",
                        routing_method="deterministic_rule",
                    )

        # 2. Deterministic heuristic pattern scoring
        scores = score_prompt_for_discipline(prompt, clean_discipline)
        if scores and scores[0][1] > 0.0:
            top_persona_id, top_score = scores[0]
            persona = self.registry.get_persona(top_persona_id)

            alt_persona_id = None
            if len(scores) > 1 and scores[1][1] > 0.0:
                alt_persona_id = scores[1][0]

            # Confidence scaled by match intensity and separation margin
            margin = top_score - (scores[1][1] if len(scores) > 1 else 0.0)
            confidence = min(0.92, 0.65 + (top_score * 0.05) + (margin * 0.05))

            return RoutingResult(
                discipline_id=clean_discipline,
                persona_id=top_persona_id,
                confidence=round(confidence, 2),
                rationale=(
                    f"Selected {persona.display_name} based on domain craft keywords and "
                    f"task pattern matching."
                ),
                alternative_persona_id=alt_persona_id,
                routing_method="deterministic_rule",
            )

        # 3. Model-assisted classification for ambiguous prompts (if model provided)
        if model is not None:
            model_result = self._classify_with_model(prompt, clean_discipline, model)
            if model_result:
                return model_result

        # 4. Fallback to discipline default persona
        default_persona_id = DEFAULT_PERSONAS.get(clean_discipline, discipline_config.specialist_persona_ids[0])
        persona = self.registry.get_persona(default_persona_id)

        return RoutingResult(
            discipline_id=clean_discipline,
            persona_id=default_persona_id,
            confidence=0.50,
            rationale=(
                f"Assigned primary discipline specialist ({persona.display_name}) "
                f"for general creative guidance."
            ),
            alternative_persona_id=(
                discipline_config.specialist_persona_ids[1]
                if len(discipline_config.specialist_persona_ids) > 1
                else None
            ),
            routing_method="discipline_default_fallback",
        )

    def _classify_with_model(
        self, prompt: str, discipline_id: str, model: Any
    ) -> Optional[RoutingResult]:
        """
        Executes safe model-assisted classification with structured output and error trapping.
        Never throws exceptions and never returns unvetted persona IDs.
        """
        discipline = self.registry.get_discipline(discipline_id)
        if not discipline:
            return None

        personas = discipline.get_personas()
        persona_options = "\n".join(
            f"- {p.id}: {p.display_name} — {p.description}"
            for p in personas
        )

        classification_prompt = (
            f"You are a routing classifier for the {discipline.display_name} creative harness.\n"
            f"Given the user's prompt below, identify which specialist persona is best suited to help.\n\n"
            f"Available Personas:\n{persona_options}\n\n"
            f"User Prompt: \"{prompt}\"\n\n"
            f"Respond with ONLY the exact persona id (e.g., '{personas[0].id}') and nothing else."
        )

        try:
            response = model.invoke(classification_prompt)
            raw_content = getattr(response, "content", str(response)).strip().lower()

            # Find matching persona ID from valid options
            for p in personas:
                if p.id in raw_content:
                    return RoutingResult(
                        discipline_id=discipline_id,
                        persona_id=p.id,
                        confidence=0.85,
                        rationale=f"Selected {p.display_name} via context-aware task classification.",
                        routing_method="model_classification",
                    )
        except Exception:
            # Model failure or timeout: silently fail over to deterministic rules
            pass

        return None
