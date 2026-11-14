"""
OCTS AI - Agent Router & Classifier (Refined Phase 3)
Determines the optimal specialist persona or triggers clarification when discipline is ambiguous.
Differentiates between:
  Case A: Clear discipline and specialist
  Case B: Known discipline, uncertain specialist (safe specialist fallback)
  Case C: Ambiguous discipline (structured needs_clarification result)
  Case D: Routing failure / invalid persona protection
"""

from typing import Any, Dict, Optional
from backend.agents.base import RoutingResult
from backend.agents.registry import get_registry
from backend.agents.routing.rules import (
    DEFAULT_PERSONAS,
    TASK_TYPE_MAPPING,
    detect_best_discipline,
    score_prompt_for_discipline,
)


class AgentRouter:
    """Routes creative tasks to specialist personas with intelligent clarification for ambiguous queries."""

    def __init__(self, registry=None):
        self.registry = registry or get_registry()

    def route(
        self,
        prompt: str,
        discipline_id: Optional[str] = None,
        task_type: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None,
        model: Optional[Any] = None,
    ) -> RoutingResult:
        """
        Routes the user's prompt to the most qualified specialist persona or requests clarification.

        Args:
            prompt: User creative inquiry or request text.
            discipline_id: Optional target discipline ('writers', 'musicians', 'creators', 'designers').
            task_type: Optional explicit task category.
            session_context: Optional session context dictionary.
            model: Optional LangChain model for assisted classification.

        Returns:
            RoutingResult with persona, confidence, rationale, and needs_clarification flag.
        """
        prompt_text = (prompt or "").strip()

        # 1. Explicit task_type mapping
        if task_type:
            normalized_task = task_type.lower().strip()
            if normalized_task in TASK_TYPE_MAPPING:
                mapped_persona_id = TASK_TYPE_MAPPING[normalized_task]
                persona = self.registry.get_persona(mapped_persona_id)
                if persona:
                    # If discipline was specified, verify match; otherwise adopt persona's discipline
                    clean_discipline = (discipline_id or "").lower().strip()
                    if not clean_discipline or clean_discipline == persona.discipline_id:
                        return RoutingResult(
                            discipline_id=persona.discipline_id,
                            persona_id=mapped_persona_id,
                            confidence=0.95,
                            rationale=f"Selected {persona.display_name} based on explicit task categorization '{task_type}'.",
                            routing_method="deterministic_rule",
                            needs_clarification=False,
                        )

        # 2. Check if an explicit discipline was provided and is valid
        clean_discipline = (discipline_id or "").lower().strip() if discipline_id else None
        valid_discipline = self.registry.get_discipline(clean_discipline) if clean_discipline else None

        # -------------------------------------------------------------------
        # SCENARIO 1: Discipline is KNOWN (Explicitly selected by user)
        # -------------------------------------------------------------------
        if valid_discipline:
            disc_id = valid_discipline.id
            scores = score_prompt_for_discipline(prompt_text, disc_id)

            # Case A: Specialist is clear from craft patterns within known discipline
            if scores and scores[0][1] > 0.0:
                top_persona_id, top_score = scores[0]
                persona = self.registry.get_persona(top_persona_id)

                alt_persona_id = None
                if len(scores) > 1 and scores[1][1] > 0.0:
                    alt_persona_id = scores[1][0]

                margin = top_score - (scores[1][1] if len(scores) > 1 else 0.0)
                confidence = min(0.92, 0.65 + (top_score * 0.05) + (margin * 0.05))

                return RoutingResult(
                    discipline_id=disc_id,
                    persona_id=top_persona_id,
                    confidence=round(confidence, 2),
                    rationale=f"Selected {persona.display_name} based on domain craft keywords and task pattern matching.",
                    alternative_persona_id=alt_persona_id,
                    routing_method="deterministic_rule",
                    needs_clarification=False,
                )

            # Optional model-assisted classification within the known discipline
            if model is not None:
                model_result = self._classify_with_model(prompt_text, disc_id, model)
                if model_result:
                    return model_result

            # Case B: Discipline is known, but specialist is uncertain -> safe discipline lead fallback
            default_persona_id = DEFAULT_PERSONAS.get(disc_id, valid_discipline.specialist_persona_ids[0])
            persona = self.registry.get_persona(default_persona_id)

            return RoutingResult(
                discipline_id=disc_id,
                persona_id=default_persona_id,
                confidence=0.50,
                rationale=(
                    f"Discipline is confirmed as {valid_discipline.display_name}, but specific craft task was general. "
                    f"Assigned primary lead specialist ({persona.display_name}) for guidance."
                ),
                alternative_persona_id=(
                    valid_discipline.specialist_persona_ids[1]
                    if len(valid_discipline.specialist_persona_ids) > 1
                    else None
                ),
                routing_method="discipline_default_fallback",
                needs_clarification=False,
            )

        # -------------------------------------------------------------------
        # SCENARIO 2: Discipline is NOT SPECIFIED or UNRECOGNIZED
        # -------------------------------------------------------------------
        # Try to infer discipline from prompt keywords across all 4 disciplines
        best_disc, best_persona, top_score, _ = detect_best_discipline(prompt_text)

        if best_disc and best_persona and top_score > 0.0:
            # Case A/B inferred from clear domain craft keywords
            persona = self.registry.get_persona(best_persona)
            disc_config = self.registry.get_discipline(best_disc)
            confidence = min(0.90, 0.65 + (top_score * 0.05))

            return RoutingResult(
                discipline_id=best_disc,
                persona_id=best_persona,
                confidence=round(confidence, 2),
                rationale=f"Detected {disc_config.display_name} discipline based on craft keywords and assigned {persona.display_name}.",
                routing_method="deterministic_rule",
                needs_clarification=False,
            )

        # Case C: Discipline itself is ambiguous (e.g., "I want to create something interesting")
        # Do NOT guess or default arbitrarily to writers. Return structured clarification result.
        return RoutingResult(
            discipline_id=None,
            persona_id=None,
            confidence=0.0,
            rationale="The creative discipline could not be determined from your request.",
            routing_method="clarification_required",
            needs_clarification=True,
            clarification_question=(
                "Which creative discipline are you working in? "
                "(Writers & Storytellers, Musicians & Singers, Content Creators, or Visual Artists & Designers)"
            ),
        )

    def _classify_with_model(
        self, prompt: str, discipline_id: str, model: Any
    ) -> Optional[RoutingResult]:
        """
        Executes model-assisted classification with strict validation against registered personas.
        Never allows unvetted or hallucinated persona IDs.
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

            for p in personas:
                if p.id in raw_content:
                    return RoutingResult(
                        discipline_id=discipline_id,
                        persona_id=p.id,
                        confidence=0.85,
                        rationale=f"Selected {p.display_name} via context-aware task classification.",
                        routing_method="model_classification",
                        needs_clarification=False,
                    )
        except Exception:
            pass

        return None
