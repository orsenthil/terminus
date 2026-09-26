import pytest

from game import settings as S
from game.daynight import DayNight


def make(time=0.0):
    return DayNight(day=30, night=20, fade=4, time=time)


def test_starts_in_full_day():
    dn = make()
    assert dn.night == 0
    assert not dn.is_night
    assert dn.sand() == pytest.approx(S.SAND_DAY)


def test_dusk_blends_into_night():
    dn = make(28)  # halfway through the 4s dusk
    assert 0 < dn.night < 1
    dn.update(2)
    assert dn.night == pytest.approx(1)
    assert dn.is_night


def test_full_night_is_dark_and_purple():
    dn = make(40)
    assert dn.night == pytest.approx(1)
    assert dn.sand() == pytest.approx(S.SAND_NIGHT)
    assert sum(dn.sky()[:3]) < sum(S.DAY_SKY[:3])


def test_dawn_returns_to_day_and_cycle_repeats():
    dn = make(48)  # halfway through dawn
    assert 0 < dn.night < 1
    dn.update(2)
    assert dn.night == pytest.approx(0)
    dn.update(dn.cycle)
    assert dn.night == pytest.approx(0)


def test_progress_runs_across_each_half():
    assert make(15).progress == pytest.approx(0.5)
    assert make(40).progress == pytest.approx(0.5)
    assert make(15).is_day_half and not make(40).is_day_half
