"""
OCTS AI - Memory Extraction Coordinator
Runs specialized extractors, enforces validation, privacy limits,
and bounds extraction count per interaction.
"""

import logging
from typing import List, Optional

from backend.memory.extractors import (
    BaseExtractor,
    ConstraintExtractor,
    DecisionExtractor,
    PreferenceExtractor,
    ProjectExtractor,
)
from backend.memory.memory_policy import MemoryPolicy
from backend.memory.memory_validator import MemoryValidator
from backend.memory.schemas import MemoryRecord

logger = logging.getLogger("octs.memory.extractor")


class MemoryExtractor:
    """
    Coordinates extraction of structured memories from completed creative interactions.
    Guarantees privacy safety, non-blocking execution, and zero persistence of ephemeral commands.
    """

    def __init__(
        self,
        extractors: Optional[List[BaseExtractor]] = None,
        validator: Optional[MemoryValidator] = None,
        policy: Optional[MemoryPolicy] = None,
        max_extract_per_turn: int = 3,
    ):
        self.extractors = extractors or [
            ConstraintExtractor(),
            DecisionExtractor(),
            ProjectExtractor(),
            PreferenceExtractor(),
        ]
        self.validator = validator or MemoryValidator()
        self.policy = policy or MemoryPolicy()
        self.max_extract_per_turn = max_extract_per_turn

    def extract_memories(
        self,
        prompt: str,
        output: str,
        discipline: Optional[str] = None,
        project_id: Optional[str] = None,
        owner_id: str = "default_user",
        session_id: Optional[str] = None,
    ) -> List[MemoryRecord]:
        """
        Extracts validated, policy-compliant memory records.
        """
        if not prompt or not prompt.strip():
            return []

        candidates: List[MemoryRecord] = []

        try:
            for ext in self.extractors:
                extracted = ext.extract(
                    prompt=prompt,
                    output=output,
                    discipline=discipline,
                    project_id=project_id,
                    owner_id=owner_id,
                    session_id=session_id,
                )
                candidates.extend(extracted)
                if len(candidates) >= self.max_extract_per_turn:
                    break
        except Exception as e:
            logger.warning(f"Error during memory extraction: {e}", exc_info=True)
            return []

        # Validate candidates
        validated: List[MemoryRecord] = []
        seen_contents = set()

        for mem in candidates:
            is_valid, reason = self.validator.validate_content(mem.content)
            if not is_valid:
                logger.debug(f"Memory candidate rejected by validator: {reason}")
                continue

            # Scope compatibility verification
            if not self.policy.validate_scope_compatibility(
                scope=mem.scope,
                owner_id=mem.owner_id,
                project_id=mem.project_id,
                discipline=mem.discipline,
            ):
                continue

            # Deduplication
            content_key = mem.content.lower().strip()
            if content_key in seen_contents:
                continue

            # Sanitize delimiters
            mem.content = self.validator.sanitize_content(mem.content)
            seen_contents.add(content_key)
            validated.append(mem)

            if len(validated) >= self.max_extract_per_turn:
                break

        return validated
