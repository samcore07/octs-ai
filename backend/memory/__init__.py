"""
OCTS AI - Memory & Persistent Intelligence Package
Exports schemas, repository, manager, and settings.
"""

from backend.memory.config import MemorySettings
from backend.memory.identity import AnonymousIdentityProvider, HeaderIdentityProvider, IdentityContext, IdentityProvider
from backend.memory.memory_manager import MemoryManager
from backend.memory.memory_store import MemoryStore
from backend.memory.repositories.memory_repository import MemoryRepository
from backend.memory.schemas import (
    MemoryCreate,
    MemoryMetadata,
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryStatus,
    MemoryType,
    MemoryUpdate,
    ProjectCreate,
    ProjectRecord,
    ProjectUpdate,
    RetrievedMemoryItem,
)

__all__ = [
    "MemorySettings",
    "MemoryManager",
    "MemoryStore",
    "MemoryRepository",
    "IdentityProvider",
    "HeaderIdentityProvider",
    "AnonymousIdentityProvider",
    "IdentityContext",
    "MemoryRecord",
    "MemoryType",
    "MemoryScope",
    "MemoryStatus",
    "MemorySource",
    "MemoryCreate",
    "MemoryUpdate",
    "ProjectRecord",
    "ProjectCreate",
    "ProjectUpdate",
    "RetrievedMemoryItem",
    "MemoryMetadata",
]
