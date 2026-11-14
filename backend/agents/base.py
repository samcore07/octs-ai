"""
OCTS AI - Agent Persona & Discipline Base Schemas
Unified Pydantic v2 definitions for creative disciplines, personas, and routing results.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)


class ModelConfig(BaseModel):
    """Recommended model execution parameters for a specialist persona."""
    model_config = ConfigDict(extra="ignore")

    model_name: Optional[str] = Field(
        default=None,
        description="Optional model override (e.g., larger context or reasoning model)."
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for creativity vs precision."
    )
    top_p: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold."
    )
    max_output_tokens: int = Field(
        default=4096,
        ge=256,
        le=32768,
        description="Maximum tokens allowed for persona response."
    )


class PersonaDefinition(BaseModel):
    """
    Unified definition for a specialized creative agent persona.
    Encapsulates domain instructions, craft constraints, expected outputs, and LangChain prompt templates.
    """
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique snake_case identifier (e.g., narrative_architect).")
    display_name: str = Field(..., description="Human-readable persona title.")
    discipline_id: str = Field(..., description="Associated discipline identifier.")
    description: str = Field(..., description="Concise summary of persona purpose and specialization.")
    primary_responsibilities: List[str] = Field(
        ...,
        description="Key responsibilities and technical craft functions owned by this persona."
    )
    supported_task_types: List[str] = Field(
        ...,
        description="List of task categorizations routed to this persona."
    )
    system_instructions: str = Field(
        ...,
        description="Detailed, domain-specific instruction prompt for the model."
    )
    domain_constraints: List[str] = Field(
        ...,
        description="Rigorous domain constraints and rules the persona must adhere to."
    )
    expected_output_structure: List[str] = Field(
        ...,
        description="Standardized sections or architectural breakdown expected in outputs."
    )
    evaluation_criteria: List[str] = Field(
        ...,
        description="Heuristic criteria for judging the craft quality of this persona's output."
    )
    model_config_recommendation: ModelConfig = Field(
        default_factory=ModelConfig,
        description="Recommended LLM hyperparameter configuration."
    )
    available_tool_permissions: List[str] = Field(
        default_factory=list,
        description="Permission identifiers for tools accessible to this persona."
    )

    def format_system_prompt(self) -> str:
        """
        Compiles the persona's instructions, responsibilities, constraints,
        and output structure into a comprehensive markdown system prompt.
        """
        responsibilities_block = "\n".join(f"- {r}" for r in self.primary_responsibilities)
        constraints_block = "\n".join(f"- {c}" for c in self.domain_constraints)
        structure_block = "\n".join(f"- {s}" for s in self.expected_output_structure)
        criteria_block = "\n".join(f"- {crit}" for crit in self.evaluation_criteria)

        return (
            f"# ROLE: {self.display_name} (Discipline: {self.discipline_id})\n\n"
            f"## Specialization & Mission\n"
            f"{self.description}\n\n"
            f"## Core Directives & Instructions\n"
            f"{self.system_instructions}\n\n"
            f"## Primary Responsibilities\n"
            f"{responsibilities_block}\n\n"
            f"## Rigorous Craft & Domain Constraints\n"
            f"{constraints_block}\n\n"
            f"## Expected Output Architecture\n"
            f"{structure_block}\n\n"
            f"## Craft Evaluation Criteria\n"
            f"{criteria_block}\n\n"
            f"Always approach the creative challenge with technical depth, actionable craftsmanship, "
            f"and zero generic platitudes."
        )

    def build_prompt_template(self) -> ChatPromptTemplate:
        """
        Builds a reusable LangChain ChatPromptTemplate configured with this persona's system prompt.
        Accepts `{input}` (and optional `{context}`) when formatted.
        """
        system_text = self.format_system_prompt()
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_text),
            HumanMessagePromptTemplate.from_template("{input}")
        ])


class DisciplineConfig(BaseModel):
    """
    Configuration and domain parameters for one of the four creative disciplines.
    """
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique discipline identifier ('writers', 'musicians', 'creators', 'designers').")
    display_name: str = Field(..., description="Human-readable discipline title.")
    purpose: str = Field(..., description="Primary creative purpose and scope of the discipline.")
    scope: str = Field(..., description="Detailed description of supported creative operations.")
    specialist_persona_ids: List[str] = Field(
        ...,
        description="List of the 4 specialist persona IDs registered under this discipline."
    )
    supported_task_categories: List[str] = Field(
        ...,
        description="High-level task categories handled by this discipline."
    )
    discipline_terminology: List[str] = Field(
        ...,
        description="Standard technical terminology and craft vocabulary of the discipline."
    )
    quality_requirements: List[str] = Field(
        ...,
        description="Discipline-wide craft benchmarks and quality criteria."
    )
    default_output_conventions: List[str] = Field(
        ...,
        description="Structural and formatting conventions expected by users in this discipline."
    )

    def get_personas(self) -> List[PersonaDefinition]:
        """Retrieves instantiated persona objects for this discipline from the central registry."""
        from backend.agents.registry import get_registry
        registry = get_registry()
        return [
            registry.get_persona(pid)
            for pid in self.specialist_persona_ids
            if registry.get_persona(pid) is not None
        ]


class RoutingResult(BaseModel):
    """Result of agent task routing."""
    model_config = ConfigDict(extra="ignore")

    discipline_id: str = Field(..., description="Resolved discipline ID.")
    persona_id: str = Field(..., description="Target specialist persona ID.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Routing certainty score between 0.0 and 1.0.")
    rationale: str = Field(..., description="User-safe explanation of why this specialist was assigned.")
    alternative_persona_id: Optional[str] = Field(
        default=None,
        description="Secondary recommendation if the user's task spans multiple specialties."
    )
    routing_method: str = Field(
        default="deterministic_rule",
        description="Mechanism used: 'deterministic_rule', 'model_classification', or 'discipline_default_fallback'."
    )
