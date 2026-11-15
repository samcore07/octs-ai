"""
OCTS AI - Constraint Memory Extractor
Extracts mandatory creative constraints, negative bounds, and technical specifications.
"""

import logging
import re
from typing import List, Optional

from backend.memory.extractors.base import BaseExtractor
from backend.memory.schemas import (
    MemoryRecord,
    MemoryScope,
    MemorySource,
    MemoryType,
)

logger = logging.getLogger("octs.memory.extractors.constraint")

CONSTRAINT_PATTERNS = [
    re.compile(r"(?i)\b(?:never\s+use|do\s+not\s+use|avoid\s+using|avoid\s+all)\s+([^.?!;\n]{4,80})"),
    re.compile(r"(?i)\b(?:must\s+(?:always\s+)?(?:contain|include|adhere\s+to|pass|maintain))\s+([^.?!;\n]{4,80})"),
    re.compile(r"(?i)\b(?:strict\s+constraint:\s*|rule:\s*)\s*([^.?!;\n]{4,80})"),
    re.compile(r"(?i)\b(?:maximum\s+(?:length|word\s+count|tempo)\s+is)\s+([^.?!;\n]{3,50})"),
]


class ConstraintExtractor(BaseExtractor):
    """
    Extracts durable negative and positive craft constraints.
    """

    def extract(
        self,
        prompt: str,
        output: str,
        discipline: Optional[str] = None,
        project_id: Optional[str] = None,
        owner_id: str = "default_user",
        session_id: Optional[str] = None,
    ) -> List[MemoryRecord]:
        memories: List[MemoryRecord] = []
        if not prompt or not isinstance(prompt, str):
            return memories

        for pat in CONSTRAINT_PATTERNS:
            match = pat.search(prompt)
            if match:
                raw_constraint = match.group(1).strip()
                if len(raw_constraint) >= 4:
                    scope = MemoryScope.PROJECT if project_id else (
                        MemoryScope.DISCIPLINE if discipline else MemoryScope.USER
                    )
                    content = f"Mandatory creative constraint: {raw_constraint}."

                    mem = MemoryRecord(
                        owner_id=owner_id,
                        memory_type=MemoryType.CONSTRAINT,
                        scope=scope,
                        discipline=discipline,
                        project_id=project_id,
                        session_id=session_id,
                        content=content,
                        structured_data={
                            "constraint": raw_constraint,
                            "discipline": discipline,
                            "project_id": project_id,
                        },
                        source=MemorySource.EXPLICIT_USER,
                        confidence=0.95,
                        importance=0.90,  # Constraints carry high importance
                    )
                    memories.append(mem)
                    logger.info(f"Extracted creative constraint: {content}")
                    break

        return memories
