"""
OCTS AI - Decision Memory Extractor
Extracts established project choices, selected directions, and approved creative concepts.
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

logger = logging.getLogger("octs.memory.extractors.decision")

DECISION_PATTERNS = [
    re.compile(r"(?i)\b(?:we\s+(?:have\s+)?decided\s+to|let's\s+go\s+with|i've\s+decided\s+on)\s+([^.?!;\n]{5,100})"),
    re.compile(r"(?i)\b(?:we\s+(?:have\s+)?chosen|we\s+are\s+selecting)\s+([^.?!;\n]{5,100})"),
    re.compile(r"(?i)\b(?:approved\s+(?:concept|direction|palette|structure)\s+is)\s+([^.?!;\n]{5,100})"),
]


class DecisionExtractor(BaseExtractor):
    """
    Extracts explicit creative decisions made during collaboration.
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

        for pat in DECISION_PATTERNS:
            match = pat.search(prompt)
            if match:
                decision_text = match.group(1).strip()
                if len(decision_text) >= 5:
                    scope = MemoryScope.PROJECT if project_id else MemoryScope.USER
                    content = f"Creative decision: Selected '{decision_text}'."

                    mem = MemoryRecord(
                        owner_id=owner_id,
                        memory_type=MemoryType.DECISION,
                        scope=scope,
                        discipline=discipline,
                        project_id=project_id,
                        session_id=session_id,
                        content=content,
                        structured_data={
                            "decision": decision_text,
                            "discipline": discipline,
                            "project_id": project_id,
                        },
                        source=MemorySource.EXPLICIT_USER,
                        confidence=0.90,
                        importance=0.80,
                    )
                    memories.append(mem)
                    logger.info(f"Extracted creative decision: {content}")
                    break

        return memories
