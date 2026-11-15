"""
OCTS AI - Recovery Attempt Manager
Guarantees bounded refinement loops, enforcing strict maximum retry limits.
Configurable with a hard ceiling safety cap of 5 attempts.
"""

from typing import Optional


class RecoveryManager:
    """
    Manages refinement attempt counters and enforces strict bounding limits.
    Prevents runaway recursion or unbounded recovery loops.
    """

    MAX_SAFETY_CAP = 5

    def __init__(self, max_attempts: int = 2):
        if max_attempts < 0:
            raise ValueError("max_attempts cannot be negative.")
        if max_attempts > self.MAX_SAFETY_CAP:
            raise ValueError(f"max_attempts cannot exceed safety cap of {self.MAX_SAFETY_CAP}.")
        self.max_attempts = max_attempts

    def can_attempt_recovery(self, current_attempts: int) -> bool:
        """Determines if additional recovery attempts are permitted."""
        return current_attempts < self.max_attempts

    def next_attempt_number(self, current_attempts: int) -> int:
        """Calculates the upcoming attempt sequence number."""
        return current_attempts + 1

    def should_trigger(
        self,
        quality_score: Optional[float],
        threshold: float = 70.0,
        current_attempts: int = 0,
    ) -> bool:
        """
        Determines whether recovery should be initiated based on score and attempts.
        """
        if quality_score is None:
            return False
        if not self.can_attempt_recovery(current_attempts):
            return False
        return quality_score < threshold
