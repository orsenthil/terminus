import pytest

from game.hourglass import Hourglass
from game.objects import TimerLockLogic


def test_lock_opens_within_tolerance():
    lock = TimerLockLogic(15, tolerance=0.5)
    assert lock.interact() == "start"
    for _ in range(1520):
        lock.update(0.01)
    assert lock.interact() == "success"
    assert lock.solved
    assert lock.interact() is None


def test_lock_fails_and_resets():
    lock = TimerLockLogic(15, tolerance=0.5)
    lock.interact()
    lock.update(14.0)
    assert lock.interact() == "fail"
    assert not lock.running and not lock.solved
    assert lock.interact() == "start"


def test_seven_and_eleven_measure_fifteen():
    """The intended solution: flip both; start the lock when the 7 empties; flip the 11
    when it empties; stop the lock when it empties again."""
    dt = 1 / 120
    seven = Hourglass(bottom=7, capacity=7)
    eleven = Hourglass(bottom=11, capacity=11)
    lock = TimerLockLogic(15)
    seven.flip()
    eleven.flip()
    flipped_eleven = False
    for _ in range(int(40 / dt)):
        was = (seven.empty, eleven.empty)
        seven.update(dt)
        eleven.update(dt)
        lock.update(dt)
        if seven.empty and not was[0]:
            assert lock.interact() == "start"
        if eleven.empty and not was[1]:
            if not flipped_eleven:
                eleven.flip()
                flipped_eleven = True
            else:
                assert lock.interact() == "success"
                break
    assert lock.solved
    assert lock.elapsed == pytest.approx(15, abs=0.05)
