"""
OCTS AI - Project Memory Extractor
Extracts project-specific facts, character dossiers, worldbuilding rules,
and brand identity definitions.
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

logger = logging.getLogger("octs.memory.extractors.project")

PROJECT_FACT_PATTERNS = [
    (re.compile(r"(?i)\b(?:the\s+project\s+(?:title|name)\s+is|project:\s*)\s*['\"]?([^.?!,;\n]{3,80})['\"]?"), "project_title"),
    (re.compile(r"(?i)\b(?:the\s+(?:protagonist|main\s+character)\s+is)\s+([A-Z][a-zA-Z\s]{1,40})"), "character_protagonist"),
    (re.compile(r"(?i)\b(?:our\s+target\s+audience\s+is)\s+([^.?!;\n]{5,100})"), "target_audience"),
    (re.compile(r"(?i)\b(?:the\s+(?:setting|world|magic\s+system)\s+is\s+called|set\s+in)\s+([A-Z][a-zA-Z\s]{2,50})"), "world_setting"),
    (re.compile(r"(?i)\b(?:brand\s+(?:name|identity)\s+is)\s+([^.?!;\n]{3,60})"), "brand_identity"),
]


class ProjectExtractor(BaseExtractor):
    """
    Extracts durable project entities and lore.
    Requires an active project_id or creates one for the project scope.
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
        if not prompt or not isinstance(prompt, str) or not project_id:
            # Project memories strictly require an active project context
            return memories

        for pat, key in PROJECT_FACT_PATTERNS:
            match = pat.search(prompt)
            if match:
                fact_val = match.group(1).strip()
                if len(fact_val) >= 3:
                    content = f"Project entity ({key.replace('_', ' ')}): {fact_val}."
                    mem = MemoryRecord(
                        owner_id=owner_id,
                        memory_type=MemoryType.PROJECT,
                        scope=MemoryScope.PROJECT,
                        discipline=discipline,
                        project_id=project_id,
                        session_id=session_id,
                        content=content,
                        structured_data={
                            "entity_type": key,
                            "entity_value": fact_val,
                            "project_id": project_id,
                        },
                        source=MemorySource.EXPLICIT_USER,
                        confidence=0.90,
                        importance=0.85,
                    )
                    memories.append(mem)
                    logger.info(f"Extracted project entity: {content}")
                    break

        return memories
