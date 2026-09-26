import pytest

from game.hourglass import Hourglass


def test_drains_one_second_per_second():
    g = Hourglass(top=60)
    g.update(1.5)
    assert g.top == pytest.approx(58.5)
    assert g.bottom == pytest.approx(1.5)
    assert not g.empty


def test_drain_never_goes_negative():
    g = Hourglass(top=2)
    moved = g.update(5)
    assert moved == pytest.approx(2)
    assert g.top == 0
    assert g.bottom == pytest.approx(2)
    assert g.empty


def test_flip_at_half_empty_gives_back_what_drained():
    g = Hourglass(top=11)
    g.update(4)
    g.flip()
    assert g.top == pytest.approx(4)
    assert g.bottom == pytest.approx(7)


def test_flip_when_empty_restores_full_glass():
    g = Hourglass(top=7)
    g.update(10)
    assert g.empty
    g.flip()
    assert g.top == pytest.approx(7)
    assert g.bottom == 0


def test_add_clamps_to_capacity():
    g = Hourglass(top=5, capacity=10)
    assert g.add(20) == pytest.approx(5)
    assert g.top == pytest.approx(10)
    assert g.add(-3) == 0


def test_add_without_capacity_is_unbounded():
    g = Hourglass(top=5)
    g.add(100)
    assert g.top == pytest.approx(105)


def test_remove_clamps_at_zero():
    g = Hourglass(top=3)
    assert g.remove(5) == pytest.approx(3)
    assert g.top == 0
    assert g.empty
    assert g.remove(1) == 0


def test_fraction():
    g = Hourglass(top=3, bottom=1)
    assert g.fraction == pytest.approx(0.75)
    assert Hourglass().fraction == 0
