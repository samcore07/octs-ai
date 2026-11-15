"""
OCTS AI - Memory Governance & Isolation Policy
Enforces strict scope boundaries, access control rules, and conflict resolution hierarchy.
"""

from enum import IntEnum
import logging
from typing import Optional

from backend.memory.schemas import (
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryType,
)

logger = logging.getLogger("octs.memory.policy")


class PrecedenceRank(IntEnum):
    """
    Conflict resolution priority hierarchy.
    Higher integer indicates higher precedence.
    """
    AI_INFERRED = 1
    STABLE_PREFERENCE = 2
    ESTABLISHED_CONSTRAINT = 3
    RECENT_PROJECT_DECISION = 4
    EXPLICIT_CONFIRMED_MEMORY = 5
    CURRENT_USER_INSTRUCTION = 6


class MemoryPolicy:
    """
    Enforces memory governance rules across disciplines, projects, and users.
    """

    @staticmethod
    def get_precedence(record: MemoryRecord) -> PrecedenceRank:
        """Calculates precedence rank for a stored memory record."""
        if record.source == MemorySource.EXPLICIT_USER:
            if record.memory_type == MemoryType.DECISION:
                return PrecedenceRank.RECENT_PROJECT_DECISION
            if record.memory_type == MemoryType.CONSTRAINT:
                return PrecedenceRank.ESTABLISHED_CONSTRAINT
            return PrecedenceRank.EXPLICIT_CONFIRMED_MEMORY

        if record.memory_type == MemoryType.CONSTRAINT:
            return PrecedenceRank.ESTABLISHED_CONSTRAINT
        if record.memory_type == MemoryType.DECISION:
            return PrecedenceRank.RECENT_PROJECT_DECISION
        if record.memory_type == MemoryType.USER_PREFERENCE:
            return PrecedenceRank.STABLE_PREFERENCE

        return PrecedenceRank.AI_INFERRED

    @staticmethod
    def validate_scope_compatibility(
        scope: MemoryScope,
        owner_id: str,
        project_id: Optional[str] = None,
        discipline: Optional[str] = None,
    ) -> bool:
        """
        Verifies whether required identifiers are present for the given scope.
        """
        if not owner_id:
            return False

        if scope == MemoryScope.PROJECT and not project_id:
            logger.warning("Project-scoped memory requires a valid project_id.")
            return False

        if scope == MemoryScope.DISCIPLINE and not discipline:
            logger.warning("Discipline-scoped memory requires a discipline identifier.")
            return False

        return True

    @staticmethod
    def is_eligible_for_retrieval(
        record: MemoryRecord,
        target_owner_id: str,
        target_project_id: Optional[str] = None,
        target_discipline: Optional[str] = None,
    ) -> bool:
        """
        Evaluates whether a candidate memory can be presented to a given execution context.
        """
        # Strict user isolation
        if record.owner_id != target_owner_id:
            return False

        # Status must be active
        if record.status.value != "active":
            return False

        # Project boundary enforcement:
        if record.scope == MemoryScope.PROJECT:
            if not target_project_id or record.project_id != target_project_id:
                return False

        # Discipline boundary enforcement:
        if record.scope == MemoryScope.DISCIPLINE:
            if record.discipline and target_discipline and record.discipline != target_discipline:
                return False

        return True
