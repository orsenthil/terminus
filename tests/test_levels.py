import os

import pytest

from game import settings as S
from game.level import LevelData, LevelError, load_level_data

LEVEL_IDS = sorted(f[:-4] for f in os.listdir(S.LEVELS_DIR) if f.endswith(".txt"))


def test_level_order_matches_files():
    assert sorted(S.LEVEL_ORDER) == LEVEL_IDS
    assert len(LEVEL_IDS) == 6


@pytest.mark.parametrize("level_id", LEVEL_IDS)
def test_level_parses_with_one_start_and_an_exit(level_id):
    data = load_level_data(level_id)
    text = "".join(data.rows)
    assert text.count("P") == 1
    assert text.count("E") >= 1
    assert data.name
    assert data.start_sand > 0


@pytest.mark.parametrize("level_id", LEVEL_IDS)
def test_level_links_are_valid(level_id):
    data = load_level_data(level_id)
    assert len(data.glasses) == len(data.glass_tiles)
    assert len(data.locks) == len(data.lock_tiles)
    for g in data.glasses:
        assert g["capacity"] > 0


def test_row_zero_is_top():
    data = LevelData("t", ["P..", "..E", "###"], {})
    assert data.player_start == (0, 2)
    assert data.exits == [(2, 1)]
    assert (0, 0) in data.solid


def test_gate_groups_are_connected_tiles():
    data = LevelData("t", ["D..D", "D..D", "P..E", "####"], {})
    assert len(data.gates) == 2
    assert all(len(g) == 2 for g in data.gates)


def test_missing_start_or_exit_is_an_error():
    with pytest.raises(LevelError):
        LevelData("t", ["...E", "####"], {})
    with pytest.raises(LevelError):
        LevelData("t", ["P...", "####"], {})


def test_json_count_mismatch_is_an_error():
    with pytest.raises(LevelError):
        LevelData("t", ["PG.E", "####"], {"glasses": []})
