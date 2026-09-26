import pytest

from game.debt import Debt


def make():
    return Debt(rate=0.1, period=10, cap=60)


def test_borrow_adds_principal():
    d = make()
    assert d.borrow(10) == pytest.approx(10)
    assert d.principal == pytest.approx(10)
    assert d.total == pytest.approx(10)
    assert d.in_debt
    assert d.total_borrowed == pytest.approx(10)


def test_no_interest_before_period():
    d = make()
    d.borrow(10)
    assert d.update(9.9) == 0
    assert d.total == pytest.approx(10)


def test_compounds_over_multiple_ticks():
    d = make()
    d.borrow(10)
    assert d.update(10) == 1
    assert d.total == pytest.approx(11)
    assert d.update(10) == 1
    assert d.total == pytest.approx(12.1)
    assert d.update(20) == 2
    assert d.total == pytest.approx(10 * 1.1**4)
    assert d.principal == pytest.approx(10)
    assert d.interest == pytest.approx(10 * 1.1**4 - 10)


def test_no_interest_when_not_in_debt():
    d = make()
    assert d.update(100) == 0
    assert d.total == 0


def test_partial_repayment_pays_interest_first():
    d = make()
    d.borrow(10)
    d.update(10)  # 1.0 interest
    used = d.repay(3)
    assert used == pytest.approx(3)
    assert d.interest == pytest.approx(0)
    assert d.principal == pytest.approx(8)
    assert d.total_interest_paid == pytest.approx(1)
    assert d.in_debt


def test_full_repayment_clears_and_returns_only_what_was_owed():
    d = make()
    d.borrow(10)
    d.update(10)
    used = d.repay(100)
    assert used == pytest.approx(11)
    assert d.total == 0
    assert not d.in_debt
    assert d.timer == 0


def test_cap_limits_borrowing():
    d = make()
    assert d.borrow(50) == pytest.approx(50)
    assert d.borrow(50) == pytest.approx(10)
    assert d.at_cap
    assert d.borrow(1) == 0


def test_interest_cannot_exceed_cap():
    d = make()
    d.borrow(58)
    d.update(10)
    assert d.total == pytest.approx(60)


def test_clear_counts_as_paid():
    d = make()
    d.borrow(10)
    d.update(10)
    assert d.clear() == pytest.approx(11)
    assert d.total_interest_paid == pytest.approx(1)
    assert not d.in_debt
