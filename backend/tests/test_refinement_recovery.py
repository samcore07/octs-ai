"""
OCTS AI - Refinement Recovery Manager Unit Tests
Verifies attempt bounding, loop termination at max attempts, and trigger decisions.
"""

from backend.refinement.recovery.recovery_manager import RecoveryManager


def test_recovery_manager_bounding_limits():
    """Verify RecoveryManager respects max_attempts bound (default 2)."""
    rm = RecoveryManager(max_attempts=2)

    assert rm.can_attempt_recovery(0) is True
    assert rm.next_attempt_number(0) == 1

    assert rm.can_attempt_recovery(1) is True
    assert rm.next_attempt_number(1) == 2

    # At limit, additional recovery attempts are blocked
    assert rm.can_attempt_recovery(2) is False
    assert rm.can_attempt_recovery(3) is False


def test_recovery_manager_trigger_decisions():
    """Verify should_trigger triggers only when quality < threshold and attempts < max."""
    rm = RecoveryManager(max_attempts=2)

    # Low score, 0 attempts -> Trigger
    assert rm.should_trigger(quality_score=65.0, threshold=70.0, current_attempts=0) is True

    # Low score, 1 attempt -> Trigger
    assert rm.should_trigger(quality_score=68.0, threshold=70.0, current_attempts=1) is True

    # Low score, but 2 attempts already executed -> Blocked
    assert rm.should_trigger(quality_score=68.0, threshold=70.0, current_attempts=2) is False

    # Score meets threshold -> Do not trigger
    assert rm.should_trigger(quality_score=75.0, threshold=70.0, current_attempts=0) is False
    assert rm.should_trigger(quality_score=70.0, threshold=70.0, current_attempts=0) is False

    # None score -> Do not trigger
    assert rm.should_trigger(quality_score=None, threshold=70.0, current_attempts=0) is False


def test_recovery_manager_configuration_bounds_and_safety_cap():
    """Verify RecoveryManager validates attempts against 0-5 bounds and raises ValueError on violations."""
    import pytest
    from backend.config import Settings

    # 0 attempts configured (refinement disabled via 0 attempts)
    rm0 = RecoveryManager(max_attempts=0)
    assert rm0.can_attempt_recovery(0) is False

    # 1 attempt configured
    rm1 = RecoveryManager(max_attempts=1)
    assert rm1.can_attempt_recovery(0) is True
    assert rm1.can_attempt_recovery(1) is False

    # Maximum safety cap (5)
    rm5 = RecoveryManager(max_attempts=5)
    assert rm5.can_attempt_recovery(4) is True
    assert rm5.can_attempt_recovery(5) is False

    # Negative attempts rejected
    with pytest.raises(ValueError, match="cannot be negative"):
        RecoveryManager(max_attempts=-1)

    # Exceeding safety cap rejected
    with pytest.raises(ValueError, match="safety cap"):
        RecoveryManager(max_attempts=6)

    # Config Settings pydantic validation
    s = Settings(refinement_max_attempts=3)
    assert s.refinement_max_attempts == 3

    with pytest.raises(Exception):
        Settings(refinement_max_attempts=6)

    with pytest.raises(Exception):
        Settings(refinement_max_attempts=-1)

