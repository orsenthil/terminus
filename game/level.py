"""Tile map loading and level geometry.

Map files are plain text, row 0 = top of the level. Legend:
    #  solid       .  empty        P  player start    S  sulfur crystal (buys time)
    H  archive     G  pedestal water clock            D  gate
    B  ice bridge (solid while its water clock runs)  L  timer lock
    E  exit        ^  burning sulfur pit (deadly)   ?  sign
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
        self.start_time = float(meta.get("start_time", S.START_TIME))
        self.allow_borrow = bool(meta.get("allow_borrow", True))
        self.exit_requires_no_debt = bool(meta.get("exit_requires_no_debt", False))

        width = max(len(r) for r in rows)
        self.rows = [r.ljust(width, ".") for r in rows]
        self.width = width
        self.height = len(rows)

        self.solid = set()
        self.player_start = None
        self.pickups, self.archives, self.glass_tiles = [], [], []
        self.lock_tiles, self.exits, self.pits, self.sign_tiles = [], [], [], []
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
                    self.archives.append(t)
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
                    self.pits.append(t)
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


def find_vents(data):
    """Surface tiles with a steaming sulfur vent (deterministic per level, decoration only)."""
    rng = random.Random(data.id + "vents")
    busy = set(data.pickups + data.archives + data.glass_tiles + data.lock_tiles + data.exits)
    busy |= set(data.sign_tiles) | set(data.pits) | {data.player_start}
    vents = []
    for ix, iz in sorted(data.solid):
        above = (ix, iz + 1)
        if above in data.solid or above in busy or rng.random() > 0.05:
            continue
        if vents and ix - vents[-1][0] < 8:
            continue
        vents.append(above)
    return vents


def build_level_geometry(data, parent):
    """Build one shallow box per solid tile, then flatten them into a single node.

    Exposed ground is ice with a cap of frost; below it is dark basalt flecked with sulfur.
    """
    root = parent.attachNewNode("level_static")
    rng = random.Random(data.id)
    pits = set(data.pits)
    for ix, iz in sorted(data.solid):
        if (ix, iz + 1) in pits:
            # The rock under a burning pit is a trench of hot, dark molten sulfur.
            mb = MeshBuilder("pit_bed")
            k = 0.9 + rng.random() * 0.2
            mb.box(
                ix, -0.5, iz, ix + 1, 0.5, iz + 1, _shade(S.PIT_MOLTEN, k), top_color=S.PIT_SURFACE
            )
            mb.rect(ix, iz + 0.75, ix + 1, iz + 1, _shade(S.PIT_MOLTEN, 1.6), y=-0.51)
            mb.node().reparentTo(root)
            continue
        depth = 0
        while depth < 3 and (ix, iz + depth + 1) in data.solid:
            depth += 1
        surface = depth == 0
        k = 0.9 + rng.random() * 0.14
        mb = MeshBuilder("tile")
        if surface:
            mb.box(ix, -0.5, iz, ix + 1, 0.5, iz + 1, _shade(S.ICE, k), top_color=S.FROST_TOP)
            # A ragged lip of frost hanging over the front face.
            lip = 0.12 + rng.random() * 0.12
            mb.rect(ix, iz + 1 - lip, ix + 1, iz + 1, _shade(S.FROST_TOP, 0.95), y=-0.51)
        else:
            base = S.ROCK if depth < 2 else S.ROCK_DEEP
            mb.box(ix, -0.5, iz, ix + 1, 0.5, iz + 1, _shade(base, k))
            if rng.random() < 0.12:  # sulfur, the one thing this rock is rich in
                for _ in range(rng.randint(1, 3)):
                    fx, fz = ix + rng.uniform(0.15, 0.75), iz + rng.uniform(0.15, 0.75)
                    sz = rng.uniform(0.06, 0.14)
                    mb.rect(fx, fz, fx + sz, fz + sz * 0.7, _shade(S.SULFUR, 0.85), y=-0.51)
        mb.node().reparentTo(root)
    for ix, iz in find_vents(data):
        mb = MeshBuilder("vent")
        mb.rect(ix + 0.3, iz - 0.02, ix + 0.7, iz + 0.05, (0.08, 0.07, 0.07, 1), y=-0.52)
        mb.rect(ix + 0.2, iz - 0.02, ix + 0.3, iz + 0.07, S.SULFUR, y=-0.52)
        mb.rect(ix + 0.7, iz - 0.02, ix + 0.8, iz + 0.07, S.SULFUR, y=-0.52)
        mb.node().reparentTo(root)
    # Burning sulfur pits: a pool of dark molten sulfur with a glowing surface. The blue
    # flames above it are animated separately (objects.PitFlames).
    mb = MeshBuilder("pits")
    for ix, iz in data.pits:
        mb.box(ix, -0.45, iz, ix + 1, 0.45, iz + 0.22, S.PIT_MOLTEN, top_color=S.PIT_SURFACE)
        mb.rect(ix, iz + 0.16, ix + 1, iz + 0.22, S.PIT_SURFACE, y=-0.46)
        for _ in range(2):  # bubbles on the surface
            bx = ix + rng.uniform(0.15, 0.8)
            mb.rect(bx, iz + 0.12, bx + 0.08, iz + 0.18, _shade(S.PIT_SURFACE, 1.1), y=-0.47)
    np = mb.node()
    np.setLightOff()  # the pits glow, day or night
    np.reparentTo(root)
    # Bedrock below the bottom row so the ground doesn't end in a hard edge.
    mb = MeshBuilder("bedrock")
    for ix in range(data.width):
        if (ix, 0) in data.solid:
            mb.box(ix, -0.5, -4, ix + 1, 0.5, 0, _shade(S.ROCK_DEEP, 0.8))
    mb.node().reparentTo(root)
    # A dark backing wall behind the playfield so the level reads as solid rock.
    mb = MeshBuilder("backing")
    for ix, iz in data.solid:
        if (ix, iz + 1) in data.solid or iz == 0:
            mb.rect(ix - 0.1, iz, ix + 1.1, iz + 1.2, (0.11, 0.11, 0.15, 1), y=0.6)
    mb.node().reparentTo(root)
    root.flattenStrong()
    return root
