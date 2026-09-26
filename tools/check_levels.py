"""Development tool: verify each level's exit is reachable using the real player physics.

Searches over standing positions with a small set of moves (walk, hop, jumps of several
heights, with and without a running start) and reports the fastest route time. Gates are
treated as open and sand bridges as solid, i.e. "reachable once the puzzles are solved".

    uv run python tools/check_levels.py [level_id ...]
"""

import heapq
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import settings as S  # noqa: E402
from game.level import load_level_data  # noqa: E402
from game.physics import TileGrid, aabb_overlap  # noqa: E402
from game.player import PlayerController  # noqa: E402

DT = 1 / 60
HOLDS = (0.0, 0.08, 0.16, 1.0)


def make_grid(data):
    solid = set(data.solid)
    for group in data.bridges:
        solid.update(group)
    return TileGrid(data.width, data.height, solid)


def dead(body, data):
    if body.z < -3:
        return True
    box = (body.left, body.z, body.right, body.top)
    return any(aabb_overlap(box, (ix, iz, ix + 1, iz + S.SPIKE_HEIGHT)) for ix, iz in data.spikes)


def at_exit(body, data):
    box = (body.left, body.z, body.right, body.top)
    return any(aabb_overlap(box, (ix, iz, ix + 1, iz + 2)) for ix, iz in data.exits)


def simulate(data, grid, x, z, vx, move, hold):
    pc = PlayerController(x, z)
    pc.body.vx = vx
    pc.was_on_ground = True
    jumped = hold > 0
    if jumped:
        pc.press_jump()
    t, airborne = 0.0, False
    while t < 3.0:
        pc.step(DT, grid, move, t < hold)
        t += DT
        b = pc.body
        if dead(b, data):
            return None
        if at_exit(b, data):
            return (b.x, b.z, b.vx, t, True)
        if not b.on_ground:
            airborne = True
        elif airborne or (not jumped and abs(b.x - x) >= 1.0) or (jumped and t > 0.1):
            return (b.x, b.z, b.vx, t, False)
        if not jumped and move == 0 and t > 0.3:
            return None
    return None


def check(level_id, verbose=True):
    data = load_level_data(level_id)
    grid = make_grid(data)
    sx, sz = data.player_start
    start = (sx + 0.5, float(sz), 0.0)
    best = {}
    heap = [(0.0, start)]
    while heap:
        cost, (x, z, vx) = heapq.heappop(heap)
        key = (round(x * 2), round(z), round(vx / 4))
        if key in best:
            continue
        best[key] = cost
        for move in (-1, 0, 1):
            for hold in HOLDS:
                if move == 0 and hold == 0:
                    continue
                res = simulate(data, grid, x, z, vx if move * vx >= 0 else 0.0, move, hold)
                if res is None:
                    continue
                nx, nz, nvx, t, won = res
                if won:
                    if verbose:
                        print(f"{level_id}: exit reachable, fastest route ~{cost + t:.1f}s")
                    return cost + t
                heapq.heappush(heap, (cost + t, (nx, nz, nvx)))
    if verbose:
        print(f"{level_id}: EXIT NOT REACHABLE ({len(best)} positions explored)")
    return None


def main():
    ids = sys.argv[1:] or S.LEVEL_ORDER
    ok = all(check(i) is not None for i in ids)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
