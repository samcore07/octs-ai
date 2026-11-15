"""
OCTS AI - Memory Consolidator & Conflict Resolver
Manages memory superseding, deduplication, and preference updates.
Enforces the conflict resolution hierarchy without silent data deletion.
"""

import logging
from typing import List, Optional

from backend.memory.memory_policy import MemoryPolicy
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import MemoryRecord, MemoryStatus

logger = logging.getLogger("octs.memory.consolidator")


class MemoryConsolidator:
    """
    Consolidates incoming memory candidates against existing stored records.
    Detects contradictions, handles version increments, and supersedes outdated entries.
    """

    def __init__(self, repository: Optional[MemoryRepository] = None, policy: Optional[MemoryPolicy] = None):
        self.repository = repository or MemoryRepository()
        self.policy = policy or MemoryPolicy()

    def consolidate_and_save(self, new_records: List[MemoryRecord]) -> List[MemoryRecord]:
        """
        Processes new candidate memory records, resolving conflicts against existing records.
        """
        if not new_records:
            return []

        persisted: List[MemoryRecord] = []

        for new_rec in new_records:
            try:
                # Query existing active memories for this owner and type
                existing_active = self.repository.list_memories(
                    owner_id=new_rec.owner_id,
                    project_id=new_rec.project_id,
                    discipline=new_rec.discipline,
                    memory_type=new_rec.memory_type,
                    status=MemoryStatus.ACTIVE,
                    limit=50,
                )

                superseded_target: Optional[MemoryRecord] = None
                rejected_by_precedence = False

                for old_rec in existing_active:
                    # Check for direct contradiction or update in structured data
                    if self._is_conflict_or_update(old_rec, new_rec):
                        old_prec = self.policy.get_precedence(old_rec)
                        new_prec = self.policy.get_precedence(new_rec)

                        # New record wins if it has equal or higher precedence
                        if new_prec >= old_prec:
                            superseded_target = old_rec
                            break
                        else:
                            # Old record has higher precedence (e.g. established explicit constraint vs weak inferred preference)
                            logger.info(
                                f"Preserving higher precedence memory {old_rec.memory_id} over candidate {new_rec.memory_id}"
                            )
                            rejected_by_precedence = True
                            break

                if rejected_by_precedence:
                    continue

                if superseded_target:
                    logger.info(
                        f"Superseding memory {superseded_target.memory_id} (v{superseded_target.version}) "
                        f"with new memory {new_rec.memory_id}"
                    )
                    saved = self.repository.supersede_memory(
                        old_memory_id=superseded_target.memory_id,
                        new_record=new_rec,
                        owner_id=new_rec.owner_id,
                    )
                    persisted.append(saved)
                else:
                    # Check exact duplicate content
                    is_duplicate = any(
                        old.content.strip().lower() == new_rec.content.strip().lower()
                        for old in existing_active
                    )
                    if not is_duplicate:
                        saved = self.repository.create_memory(new_rec)
                        persisted.append(saved)
                    else:
                        logger.debug(f"Skipping exact duplicate memory: '{new_rec.content[:50]}'")

            except Exception as e:
                logger.error(f"Error consolidating memory {new_rec.memory_id}: {e}", exc_info=True)

        return persisted

    def _is_conflict_or_update(self, old: MemoryRecord, new: MemoryRecord) -> bool:
        """Determines if two records target the same entity or preference topic."""
        # 1. Matching preference topic or entity key
        old_data = old.structured_data or {}
        new_data = new.structured_data or {}

        if "preference_topic" in old_data and "preference_topic" in new_data:
            if old_data["preference_topic"] == new_data["preference_topic"]:
                if old.discipline == new.discipline:
                    return True

        if "entity_type" in old_data and "entity_type" in new_data:
            if old_data["entity_type"] == new_data["entity_type"]:
                if old.project_id == new.project_id:
                    return True

        return False
