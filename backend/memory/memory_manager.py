"""
OCTS AI - Central Memory Subsystem Manager
Facade coordinating identity, retrieval, extraction, consolidation, and persistence.
"""

import logging
from typing import List, Optional, Tuple

from backend.memory.config import MemorySettings
from backend.memory.identity import AnonymousIdentityProvider, HeaderIdentityProvider, IdentityProvider
from backend.memory.memory_consolidator import MemoryConsolidator
from backend.memory.memory_extractor import MemoryExtractor
from backend.memory.memory_retriever import MemoryRetriever
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import (
    MemoryCreate,
    MemoryMetadata,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    MemoryUpdate,
    ProjectCreate,
    ProjectRecord,
    ProjectUpdate,
    RetrievedMemoryItem,
)

logger = logging.getLogger("octs.memory.manager")


class MemoryManager:
    """
    Central orchestrator for Phase 6 persistent memory operations.
    Exposes clean interfaces for LangGraph orchestration nodes and FastAPI endpoints.
    """

    def __init__(
        self,
        repository: Optional[MemoryRepository] = None,
        retriever: Optional[MemoryRetriever] = None,
        extractor: Optional[MemoryExtractor] = None,
        consolidator: Optional[MemoryConsolidator] = None,
        identity_provider: Optional[IdentityProvider] = None,
        settings: Optional[MemorySettings] = None,
    ):
        self.settings = settings or MemorySettings()
        self.repository = repository or MemoryRepository()
        self.identity_provider = identity_provider or HeaderIdentityProvider(
            default_owner_id=self.settings.memory_default_owner_id
        )
        self.retriever = retriever or MemoryRetriever(
            repository=self.repository,
            settings=self.settings,
        )
        self.extractor = extractor or MemoryExtractor()
        self.consolidator = consolidator or MemoryConsolidator(
            repository=self.repository,
        )

    # --------------------------------------------------------------------------
    # Orchestration Lifecycle Methods
    # --------------------------------------------------------------------------

    def retrieve_context(
        self,
        prompt: str,
        owner_id: str,
        project_id: Optional[str] = None,
        discipline: Optional[str] = None,
    ) -> Tuple[str, List[RetrievedMemoryItem]]:
        """
        Retrieves relevant memory context for prompt execution.
        """
        if not self.settings.memory_enabled or not self.settings.memory_retrieval_enabled:
            return "", []

        return self.retriever.retrieve_context(
            prompt=prompt,
            owner_id=owner_id,
            project_id=project_id,
            discipline=discipline,
        )

    def extract_and_persist(
        self,
        prompt: str,
        output: str,
        discipline: Optional[str] = None,
        project_id: Optional[str] = None,
        owner_id: str = "default_user",
        session_id: Optional[str] = None,
    ) -> List[MemoryRecord]:
        """
        Extracts new memories from a completed interaction and consolidates them into the store.
        """
        if not self.settings.memory_enabled or not self.settings.memory_auto_extraction:
            return []

        try:
            candidates = self.extractor.extract_memories(
                prompt=prompt,
                output=output,
                discipline=discipline,
                project_id=project_id,
                owner_id=owner_id,
                session_id=session_id,
            )

            if not candidates:
                return []

            persisted = self.consolidator.consolidate_and_save(candidates)
            logger.info(f"Consolidated and saved {len(persisted)} new memory records.")
            return persisted
        except Exception as e:
            logger.error(f"Error extracting/persisting memories: {e}", exc_info=True)
            return []

    # --------------------------------------------------------------------------
    # API Direct Operations
    # --------------------------------------------------------------------------

    def list_memories(
        self,
        owner_id: str,
        project_id: Optional[str] = None,
        discipline: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        status: Optional[MemoryStatus] = MemoryStatus.ACTIVE,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MemoryRecord]:
        return self.repository.list_memories(
            owner_id=owner_id,
            project_id=project_id,
            discipline=discipline,
            memory_type=memory_type,
            status=status,
            limit=limit,
            offset=offset,
        )

    def get_memory(self, memory_id: str, owner_id: Optional[str] = None) -> Optional[MemoryRecord]:
        return self.repository.get_memory(memory_id=memory_id, owner_id=owner_id)

    def create_memory(self, create_data: MemoryCreate, owner_id: str) -> MemoryRecord:
        record = MemoryRecord(
            owner_id=owner_id,
            memory_type=create_data.memory_type,
            scope=create_data.scope,
            discipline=create_data.discipline,
            project_id=create_data.project_id,
            content=create_data.content,
            structured_data=create_data.structured_data,
            source=create_data.source,
            confidence=create_data.confidence,
            importance=create_data.importance,
        )
        return self.repository.create_memory(record)

    def update_memory(
        self,
        memory_id: str,
        update_data: MemoryUpdate,
        owner_id: Optional[str] = None,
    ) -> Optional[MemoryRecord]:
        return self.repository.update_memory(
            memory_id=memory_id,
            update=update_data,
            owner_id=owner_id,
        )

    def delete_memory(self, memory_id: str, owner_id: Optional[str] = None) -> bool:
        return self.repository.delete_memory(memory_id=memory_id, owner_id=owner_id)

    def archive_memory(self, memory_id: str, owner_id: Optional[str] = None) -> bool:
        return self.repository.archive_memory(memory_id=memory_id, owner_id=owner_id)

    def list_projects(self, owner_id: str) -> List[ProjectRecord]:
        return self.repository.list_projects(owner_id=owner_id)

    def get_project(self, project_id: str, owner_id: Optional[str] = None) -> Optional[ProjectRecord]:
        return self.repository.get_project(project_id=project_id, owner_id=owner_id)

    def create_project(self, create_data: ProjectCreate, owner_id: str) -> ProjectRecord:
        record = ProjectRecord(
            owner_id=owner_id,
            name=create_data.name,
            description=create_data.description,
            discipline=create_data.discipline,
            metadata=create_data.metadata,
        )
        return self.repository.create_project(record)

    def update_project(
        self,
        project_id: str,
        update_data: ProjectUpdate,
        owner_id: Optional[str] = None,
    ) -> Optional[ProjectRecord]:
        return self.repository.update_project(
            project_id=project_id,
            update=update_data,
            owner_id=owner_id,
        )

    def delete_project(self, project_id: str, owner_id: Optional[str] = None) -> bool:
        return self.repository.delete_project(project_id=project_id, owner_id=owner_id)
