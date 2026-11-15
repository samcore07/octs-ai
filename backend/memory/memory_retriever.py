"""
OCTS AI - Memory Retrieval Pipeline
Retrieves scope-eligible candidate memories, applies multi-factor ranking,
enforces token budgets, and formats passive context blocks.
"""

import logging
from typing import List, Optional, Tuple

from backend.memory.config import MemorySettings
from backend.memory.context_builder import ContextBuilder
from backend.memory.memory_policy import MemoryPolicy
from backend.memory.memory_ranker import MemoryRanker
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import RetrievedMemoryItem

logger = logging.getLogger("octs.memory.retriever")


class MemoryRetriever:
    """
    Coordinates end-to-end memory retrieval for incoming requests.
    """

    def __init__(
        self,
        repository: Optional[MemoryRepository] = None,
        ranker: Optional[MemoryRanker] = None,
        context_builder: Optional[ContextBuilder] = None,
        policy: Optional[MemoryPolicy] = None,
        settings: Optional[MemorySettings] = None,
    ):
        self.settings = settings or MemorySettings()
        self.repository = repository or MemoryRepository()
        self.ranker = ranker or MemoryRanker()
        self.context_builder = context_builder or ContextBuilder(
            max_context_tokens=self.settings.memory_max_context_tokens
        )
        self.policy = policy or MemoryPolicy()

    def retrieve_context(
        self,
        prompt: str,
        owner_id: str,
        project_id: Optional[str] = None,
        discipline: Optional[str] = None,
    ) -> Tuple[str, List[RetrievedMemoryItem]]:
        """
        Retrieves relevant memories and constructs the isolated context string.
        Returns (context_block, retrieved_items_telemetry).
        """
        if not self.settings.memory_retrieval_enabled or not self.settings.memory_enabled:
            return "", []

        try:
            candidates = self.repository.query_retrieval_candidates(
                owner_id=owner_id,
                project_id=project_id,
                discipline=discipline,
                min_confidence=self.settings.memory_relevance_threshold,
            )

            # Filter candidates through policy
            eligible = [
                m for m in candidates
                if self.policy.is_eligible_for_retrieval(
                    record=m,
                    target_owner_id=owner_id,
                    target_project_id=project_id,
                    target_discipline=discipline,
                )
            ]

            if not eligible:
                return "", []

            # Rank candidates
            ranked = self.ranker.rank_memories(
                candidates=eligible,
                prompt=prompt,
                target_project_id=project_id,
                target_discipline=discipline,
                min_threshold=self.settings.memory_relevance_threshold,
            )

            # Build context within token budget
            context_block, telemetry_items = self.context_builder.build_context(
                ranked_items=ranked,
                max_memories=self.settings.memory_max_retrieved,
            )

            # Update access telemetry
            used_ids = [item.memory_id for item in telemetry_items]
            if used_ids:
                self.repository.record_access(used_ids)

            logger.info(
                f"Retrieved {len(telemetry_items)} memories for owner='{owner_id}', "
                f"proj='{project_id}', disc='{discipline}'"
            )
            return context_block, telemetry_items

        except Exception as e:
            logger.error(f"Error during memory retrieval: {e}", exc_info=True)
            return "", []
