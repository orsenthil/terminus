"""Deterministic AABB-vs-tile-grid collision. Pure logic, no Panda3D.

World coordinates: X right, Z up, 1 tile = 1 unit. Tile (ix, iz) covers
[ix, ix + 1] x [iz, iz + 1]. Bodies are described by their bottom-centre point.
"""

import math

EPS = 1e-6
MAX_SUBSTEP = 0.4  # never move more than this per sub-step (prevents tunneling)


class TileGrid:
    """Solid tiles in world coordinates. The level sides are walls; above and below are open."""

    def __init__(self, width, height, solid=()):
        self.width = width
        self.height = height
        self.solid = set(solid)

    def is_solid(self, ix, iz):
        if ix < 0 or ix >= self.width:
            return True
        return (ix, iz) in self.solid

    def set_solid(self, ix, iz, value):
        if value:
            self.solid.add((ix, iz))
        else:
            self.solid.discard((ix, iz))

    def overlaps(self, left, bottom, right, top):
        """True if the box overlaps any solid tile."""
        for ix in range(math.floor(left + EPS), math.floor(right - EPS) + 1):
            for iz in range(math.floor(bottom + EPS), math.floor(top - EPS) + 1):
                if self.is_solid(ix, iz):
                    return True
        return False


class Body:
    """An axis-aligned box that moves through a TileGrid."""

    def __init__(self, x, z, w, h):
        self.x = x  # centre
        self.z = z  # bottom
        self.w = w
        self.h = h
        self.vx = 0.0
        self.vz = 0.0
        self.on_ground = False
        self.hit_wall = False
        self.hit_ceiling = False

    @property
    def left(self):
        return self.x - self.w / 2

    @property
    def right(self):
        return self.x + self.w / 2

    @property
    def top(self):
        return self.z + self.h

    def rows(self):
        return range(math.floor(self.z + EPS), math.floor(self.top - EPS) + 1)

    def cols(self):
        return range(math.floor(self.left + EPS), math.floor(self.right - EPS) + 1)


def _move_x(body, grid, dx):
    body.x += dx
    if dx > 0:
        col = math.floor(body.right - EPS)
        if any(grid.is_solid(col, iz) for iz in body.rows()):
            body.x = col - body.w / 2
            body.vx = 0.0
            body.hit_wall = True
    elif dx < 0:
        col = math.floor(body.left + EPS)
        if any(grid.is_solid(col, iz) for iz in body.rows()):
            body.x = col + 1 + body.w / 2
            body.vx = 0.0
            body.hit_wall = True


def _move_z(body, grid, dz):
    body.z += dz
    if dz < 0:
        row = math.floor(body.z + EPS)
        if any(grid.is_solid(ix, row) for ix in body.cols()):
            body.z = row + 1
            body.vz = 0.0
            body.on_ground = True
    elif dz > 0:
        row = math.floor(body.top - EPS)
        if any(grid.is_solid(ix, row) for ix in body.cols()):
            body.z = row - body.h
            body.vz = 0.0
            body.hit_ceiling = True


def move_and_collide(body, grid, dt):
    """Move `body` by its velocity for dt seconds, resolving X then Z against the grid."""
    body.on_ground = False
    body.hit_wall = False
    body.hit_ceiling = False
    dx = body.vx * dt
    dz = body.vz * dt
    steps = max(1, math.ceil(max(abs(dx), abs(dz)) / MAX_SUBSTEP))
    sx, sz = dx / steps, dz / steps
    for _ in range(steps):
        if body.vx != 0.0:
            _move_x(body, grid, sx)
        if body.vz != 0.0:
            _move_z(body, grid, sz)
    return body


def aabb_overlap(a, b):
    """Overlap test for (left, bottom, right, top) tuples."""
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
