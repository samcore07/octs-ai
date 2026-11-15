"""
OCTS AI - Base Memory Extractor Interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from backend.memory.schemas import MemoryRecord


class BaseExtractor(ABC):
    """
    Abstract interface for domain-specific memory extractors.
    """

    @abstractmethod
    def extract(
        self,
        prompt: str,
        output: str,
        discipline: Optional[str] = None,
        project_id: Optional[str] = None,
        owner_id: str = "default_user",
        session_id: Optional[str] = None,
    ) -> List[MemoryRecord]:
        """
        Extracts structured memory records from a completed prompt-response pair.
        """
        pass
