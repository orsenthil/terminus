"""Tile map loading and level geometry.

Map files are plain text, row 0 = top of the level. Legend:
    #  solid       .  empty        P  player start    S  sand pickup
    H  shrine      G  pedestal glass                  D  gate
    B  sand bridge (solid while its glass runs)       L  timer lock
    E  exit        ^  spikes       ?  sign
Objects that need extra data (glasses, locks, signs) are matched to entries in the level's
.json file in reading order (top to bottom, left to right). Gates and bridges are groups of
connected D / B tiles, also numbered in reading order.
"""

import json
import os
import random

from game import settings as S
from game.render_util import MeshBuilder

LEGEND = set("#.PSHGDBLE^?")


class LevelError(ValueError):
    pass


class LevelData:
    def __init__(self, level_id, rows, meta):
        self.id = level_id
        self.meta = meta
        self.name = meta.get("name", level_id)
        self.subtitle = meta.get("subtitle", "")
        self.start_sand = float(meta.get("start_sand", S.START_SAND))
        self.allow_borrow = bool(meta.get("allow_borrow", True))
        self.exit_requires_no_debt = bool(meta.get("exit_requires_no_debt", False))

        width = max(len(r) for r in rows)
        self.rows = [r.ljust(width, ".") for r in rows]
        self.width = width
        self.height = len(rows)

        self.solid = set()
        self.player_start = None
        self.pickups, self.shrines, self.glass_tiles = [], [], []
        self.lock_tiles, self.exits, self.spikes, self.sign_tiles = [], [], [], []
        gate_tiles, bridge_tiles = [], []
        for row, line in enumerate(self.rows):
            for col, ch in enumerate(line):
                if ch not in LEGEND:
                    raise LevelError(f"{level_id}: unknown tile {ch!r} at row {row}, col {col}")
                t = self.to_world(col, row)
                if ch == "#":
                    self.solid.add(t)
                elif ch == "P":
                    if self.player_start is not None:
                        raise LevelError(f"{level_id}: more than one P")
                    self.player_start = t
                elif ch == "S":
                    self.pickups.append(t)
                elif ch == "H":
                    self.shrines.append(t)
                elif ch == "G":
                    self.glass_tiles.append(t)
                elif ch == "D":
                    gate_tiles.append(t)
                elif ch == "B":
                    bridge_tiles.append(t)
                elif ch == "L":
                    self.lock_tiles.append(t)
                elif ch == "E":
                    self.exits.append(t)
                elif ch == "^":
                    self.spikes.append(t)
                elif ch == "?":
                    self.sign_tiles.append(t)
        if self.player_start is None:
            raise LevelError(f"{level_id}: no player start (P)")
        if not self.exits:
            raise LevelError(f"{level_id}: no exit (E)")
        self.gates = _groups(gate_tiles)
        self.bridges = _groups(bridge_tiles)

        self.glasses = meta.get("glasses", [])
        self.locks = meta.get("locks", [])
        self.signs = meta.get("signs", [])
        self._check_counts()

    def _check_counts(self):
        pairs = (
            ("glasses", self.glass_tiles, self.glasses),
            ("locks", self.lock_tiles, self.locks),
            ("signs", self.sign_tiles, self.signs),
        )
        for label, tiles, entries in pairs:
            if len(tiles) != len(entries):
                raise LevelError(
                    f"{self.id}: {len(tiles)} {label} tiles but {len(entries)} json entries"
                )
        for entry in self.glasses + self.locks:
            for g in entry.get("gates", []):
                if not 0 <= g < len(self.gates):
                    raise LevelError(f"{self.id}: link to missing gate {g}")
            for b in entry.get("bridges", []):
                if not 0 <= b < len(self.bridges):
                    raise LevelError(f"{self.id}: link to missing bridge {b}")

    def to_world(self, col, row):
        """Map (col, row) with row 0 at the top -> world tile (ix, iz) with Z up."""
        return (col, self.height - 1 - row)


def _groups(tiles):
    """Connected groups (4-neighbour) of tiles, ordered by reading order of their first tile."""
    remaining = set(tiles)
    groups = []
    for start in tiles:  # tiles arrive in reading order
        if start not in remaining:
            continue
        stack, group = [start], []
        remaining.discard(start)
        while stack:
            x, z = stack.pop()
            group.append((x, z))
            for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if n in remaining:
                    remaining.discard(n)
                    stack.append(n)
        groups.append(sorted(group))
    return groups


def level_paths(level_id):
    return (
        os.path.join(S.LEVELS_DIR, level_id + ".txt"),
        os.path.join(S.LEVELS_DIR, level_id + ".json"),
    )


def load_level_data(level_id):
    txt, meta_path = level_paths(level_id)
    with open(txt, encoding="utf-8") as f:
        rows = [line.rstrip("\n") for line in f if line.strip()]
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    return LevelData(level_id, rows, meta)


# --- Geometry ----------------------------------------------------------------------------


def _shade(color, k):
    return (min(1, color[0] * k), min(1, color[1] * k), min(1, color[2] * k), color[3])


def build_level_geometry(data, parent):
    """Build one shallow box per solid tile, then flatten them into a single node."""
    root = parent.attachNewNode("level_static")
    rng = random.Random(data.id)
    for ix, iz in sorted(data.solid):
        depth = 0
        while depth < 3 and (ix, iz + depth + 1) in data.solid:
            depth += 1
        surface = depth == 0
        base = (S.SAND_BODY, S.SAND_BODY, S.SAND_DEEP, S.SAND_DEEP)[depth]
        k = 0.92 + rng.random() * 0.12
        front = _shade(S.SAND_TOP if surface else base, k * (0.95 if surface else 1.0))
        top = _shade(S.SAND_TOP, k)
        mb = MeshBuilder("tile")
        mb.box(ix, -0.5, iz, ix + 1, 0.5, iz + 1, front, top_color=top)
        mb.node().reparentTo(root)
    for ix, iz in data.spikes:
        mb = MeshBuilder("spike")
        for i in range(3):
            x0 = ix + i / 3
            mb.tri(
                (x0, -0.25, iz),
                (x0 + 1 / 3, -0.25, iz),
                (x0 + 1 / 6, 0.0, iz + S.SPIKE_HEIGHT + 0.1),
                S.SPIKE_COLOR,
            )
            mb.tri(
                (x0, 0.25, iz),
                (x0 + 1 / 6, 0.0, iz + S.SPIKE_HEIGHT + 0.1),
                (x0 + 1 / 3, 0.25, iz),
                _shade(S.SPIKE_COLOR, 0.7),
            )
        np = mb.node()
        np.setTwoSided(True)
        np.setLightOff()  # spikes stay visible at night
        np.reparentTo(root)
    # Bedrock below the bottom row so the ground doesn't end in a hard edge.
    mb = MeshBuilder("bedrock")
    for ix in range(data.width):
        if (ix, 0) in data.solid:
            mb.box(ix, -0.5, -4, ix + 1, 0.5, 0, _shade(S.SAND_DEEP, 0.8))
    mb.node().reparentTo(root)
    # A dark backing wall behind the playfield so the level reads as a solid ruin.
    mb = MeshBuilder("backing")
    for ix, iz in data.solid:
        if (ix, iz + 1) in data.solid or iz == 0:
            mb.rect(ix - 0.1, iz, ix + 1.1, iz + 1.2, (0.25, 0.17, 0.12, 1), y=0.6)
    mb.node().reparentTo(root)
    root.flattenStrong()
    return root
