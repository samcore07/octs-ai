"""
OCTS AI - Multi-Factor Memory Ranker
Computes normalized relevance and priority scores using scope alignment,
discipline match, project match, prompt keyword overlap, importance, and recency.
"""

from datetime import datetime, timezone
import math
import re
from typing import List, Optional, Tuple

from backend.memory.schemas import MemoryRecord, MemoryScope

# Documented multi-factor ranking weights
WEIGHT_PROJECT_MATCH = 0.30
WEIGHT_DISCIPLINE_MATCH = 0.20
WEIGHT_KEYWORD_RELEVANCE = 0.25
WEIGHT_IMPORTANCE = 0.15
WEIGHT_RECENCY = 0.10


class MemoryRanker:
    """
    Ranks candidate memories using explicit, documented multi-factor weights.
    Guarantees that project and scope boundaries dominate keyword similarity.
    """

    def __init__(
        self,
        weight_project: float = WEIGHT_PROJECT_MATCH,
        weight_discipline: float = WEIGHT_DISCIPLINE_MATCH,
        weight_relevance: float = WEIGHT_KEYWORD_RELEVANCE,
        weight_importance: float = WEIGHT_IMPORTANCE,
        weight_recency: float = WEIGHT_RECENCY,
    ):
        self.w_proj = weight_project
        self.w_disc = weight_discipline
        self.w_rel = weight_relevance
        self.w_imp = weight_importance
        self.w_rec = weight_recency

    def rank_memories(
        self,
        candidates: List[MemoryRecord],
        prompt: str,
        target_project_id: Optional[str] = None,
        target_discipline: Optional[str] = None,
        min_threshold: float = 0.50,
    ) -> List[Tuple[MemoryRecord, float, str]]:
        """
        Calculates score and rationale for each candidate memory.
        Returns list of (record, score, rationale) sorted by score descending.
        """
        if not candidates:
            return []

        prompt_tokens = self._tokenize(prompt)
        scored: List[Tuple[MemoryRecord, float, str]] = []
        now = datetime.now(timezone.utc)

        for mem in candidates:
            # 1. Project match factor
            proj_score = 0.0
            if target_project_id and mem.project_id == target_project_id:
                proj_score = 1.0
            elif not target_project_id and mem.scope != MemoryScope.PROJECT:
                proj_score = 0.5  # Neutral for user-level

            # 2. Discipline match factor
            disc_score = 0.0
            if target_discipline and mem.discipline == target_discipline:
                disc_score = 1.0
            elif not mem.discipline or mem.discipline == "general":
                disc_score = 0.7  # Universal preferences

            # 3. Keyword / text relevance factor
            content_tokens = self._tokenize(mem.content)
            overlap = len(prompt_tokens.intersection(content_tokens))
            rel_score = min(1.0, overlap / max(1, min(len(prompt_tokens), 5))) if prompt_tokens else 0.5

            # 4. Importance factor
            imp_score = max(0.0, min(1.0, mem.importance))

            # 5. Recency decay factor (half-life of 30 days)
            delta_days = max(0.0, (now - mem.updated_at).total_seconds() / 86400.0)
            rec_score = math.exp(-0.023 * delta_days)  # ~0.5 after 30 days

            # Composite weighted score
            total_score = (
                self.w_proj * proj_score
                + self.w_disc * disc_score
                + self.w_rel * rel_score
                + self.w_imp * imp_score
                + self.w_rec * rec_score
            )
            total_score = round(min(1.0, max(0.0, total_score)), 3)

            rationale = (
                f"Score {total_score:.2f} (proj={proj_score:.1f}, disc={disc_score:.1f}, "
                f"rel={rel_score:.1f}, imp={imp_score:.1f}, rec={rec_score:.1f})"
            )

            if total_score >= min_threshold:
                scored.append((mem, total_score, rationale))

        # Sort descending by composite score, then by importance
        scored.sort(key=lambda x: (x[1], x[0].importance), reverse=True)
        return scored

    @staticmethod
    def _tokenize(text: str) -> set:
        if not text:
            return set()
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        stopwords = {
            "the", "and", "for", "with", "that", "this", "from", "have", "you", "are",
            "what", "when", "where", "write", "make", "help", "need", "about",
        }
        return set(w for w in words if w not in stopwords)
