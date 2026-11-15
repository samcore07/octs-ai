"""
OCTS AI - User Preference Memory Extractor
Extracts stable creative preferences across tone, genre, structure, and aesthetics.
Distinguishes explicit user directives from temporary one-off requests.
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

logger = logging.getLogger("octs.memory.extractors.preference")

EXPLICIT_PREF_PATTERNS = [
    re.compile(r"(?i)\b(?:i\s+prefer|my\s+preference\s+is)\s+([^.?!,;\n]{4,80})"),
    re.compile(r"(?i)\b(?:i\s+always\s+(?:want|use|like|prefer))\s+([^.?!,;\n]{4,80})"),
    re.compile(r"(?i)\b(?:from\s+now\s+on[,\s]+(?:always\s+)?(?:use|write|make|create))\s+([^.?!,;\n]{4,80})"),
    re.compile(r"(?i)\b(?:my\s+(?:favorite|preferred)\s+(?:tone|style|genre|aesthetic|palette)\s+is)\s+([^.?!,;\n]{4,80})"),
]


class PreferenceExtractor(BaseExtractor):
    """
    Extracts durable creative preferences from interaction text.
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

        # 1. Search for explicit user preference declarations
        for pat in EXPLICIT_PREF_PATTERNS:
            match = pat.search(prompt)
            if match:
                pref_value = match.group(1).strip()
                # Clean filler endings
                pref_value = re.sub(r"\s+(?:please|thanks|thank you)$", "", pref_value, flags=re.I)
                if len(pref_value) >= 4:
                    scope = MemoryScope.DISCIPLINE if discipline else MemoryScope.USER
                    disc_label = f" in {discipline}" if discipline else ""
                    content = f"User prefers {pref_value}{disc_label}."

                    mem = MemoryRecord(
                        owner_id=owner_id,
                        memory_type=MemoryType.USER_PREFERENCE,
                        scope=scope,
                        discipline=discipline,
                        project_id=project_id,
                        session_id=session_id,
                        content=content,
                        structured_data={
                            "preference_topic": "creative_style",
                            "preference_value": pref_value,
                            "discipline": discipline,
                        },
                        source=MemorySource.EXPLICIT_USER,
                        confidence=0.95,
                        importance=0.85,
                    )
                    memories.append(mem)
                    logger.info(f"Extracted explicit user preference: {content}")
                    # Extract at most 1 primary preference per turn
                    break

        return memories
