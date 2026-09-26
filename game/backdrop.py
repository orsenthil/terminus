"""The sky and horizon of Terminus, following the day / night cycle.

Terminus sits at the very edge of the galaxy and circles a dim red dwarf. Its sky holds few
stars, a faint band of the galaxy seen from outside, and four moons (two large, two small)
that never line up. Below the sky lies a dark, cold sea dotted with ice-capped islands, some
carrying the domes of the colony. Everything is procedural and unlit.
"""

import math
import random

from panda3d.core import TransparencyAttrib

from game.daynight import lerp
from game.render_util import MeshBuilder


def flat_disc(mb, cx, cz, r, color, y=0.0, segments=32):
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        mb.flat_tri(
            (cx, cz),
            (cx + r * math.cos(a0), cz + r * math.sin(a0)),
            (cx + r * math.cos(a1), cz + r * math.sin(a1)),
            color,
            y,
        )


def _dome(mb, cx, base, r, color, y=0.0, segments=16):
    """A half disc sitting on `base`."""
    for i in range(segments):
        a0 = math.pi * i / segments
        a1 = math.pi * (i + 1) / segments
        mb.flat_tri(
            (cx, base),
            (cx + r * math.cos(a0), base + r * math.sin(a0)),
            (cx + r * math.cos(a1), base + r * math.sin(a1)),
            color,
            y,
        )


def _island(mb, x, w, h, rock, snow, rng, y=0.0):
    """A rocky island rising from the sea (z=0), its upper part capped with snow and ice.
    Returns the height of its top at the centre (where domes can sit)."""
    n = 8
    pts = []
    for i in range(n + 1):
        k = i / n
        bump = 0.85 + 0.3 * rng.random() if 0 < i < n else 1.0
        pts.append((x + w * k, h * math.sin(math.pi * k) ** 0.6 * bump))
    for (x0, z0), (x1, z1) in zip(pts, pts[1:], strict=False):
        mb.quad((x0, y, -0.5), (x1, y, -0.5), (x1, y, z1), (x0, y, z0), rock, (0, -1, 0))
        mb.quad(
            (x0, y - 0.01, z0 * 0.72),
            (x1, y - 0.01, z1 * 0.72),
            (x1, y - 0.01, z1),
            (x0, y - 0.01, z0),
            snow,
            (0, -1, 0),
        )
    return pts[n // 2][1]


class Backdrop:
    def __init__(self, parent, width, seed=42):
        self.root = parent.attachNewNode("backdrop")
        self.root.setLightOff()
        self.root.setDepthWrite(False)
        rng = random.Random(seed)
        span = width + 80
        self.layers = []  # (node, parallax factor, lift) for the horizon layers

        # --- sky (moves with the camera, with only a hint of parallax) ---
        self.sky = self.root.attachNewNode("sky")
        self.sky.setY(190)
        self.sky.setTransparency(TransparencyAttrib.MAlpha)

        # Few stars: this is the edge of the galaxy.
        mb = MeshBuilder("stars")
        for _ in range(55):
            x, z = rng.uniform(-22, 22), rng.uniform(-1, 10)
            s = rng.uniform(0.04, 0.1)
            b = rng.uniform(0.55, 1.0)
            mb.rect(x - s, z - s, x + s, z + s, (b, b, min(1, b * 1.1), 1))
        self.stars = mb.node()
        self.stars.reparentTo(self.sky)

        # The galaxy seen from outside: a faint, tilted smudge of light.
        mb = MeshBuilder("galaxy")
        for k, (dx, dz, r, a) in enumerate(
            ((0, 0, 3.2, 0.07), (0.8, 0.2, 2.2, 0.08), (-0.6, -0.1, 1.6, 0.1), (0.2, 0, 0.7, 0.2))
        ):
            flat_disc(mb, dx, dz, r, (0.75, 0.7, 0.95, a), 0.01 * k, 28)
        self.galaxy = mb.node()
        self.galaxy.reparentTo(self.sky)
        self.galaxy.setPos(-13, 0, 7.5)
        self.galaxy.setScale(2.2, 1, 0.45)
        self.galaxy.setR(-18)

        # The red dwarf sun, low and dim.
        mb = MeshBuilder("sun")
        flat_disc(mb, 0, 0, 3.2, (0.9, 0.3, 0.2, 0.12), 0.02, 40)
        flat_disc(mb, 0, 0, 2.3, (0.95, 0.35, 0.22, 0.25), 0.01, 40)
        flat_disc(mb, 0, 0, 1.55, (0.98, 0.42, 0.25, 1.0), 0.0, 40)
        self.sun = mb.node()
        self.sun.reparentTo(self.sky)
        self.sun.setPos(9, 0, -2.2)

        # Four moons: two large, two small. They sit apart and never line up.
        mb = MeshBuilder("moons")
        pale, shade = (0.82, 0.84, 0.92, 1), (0.66, 0.68, 0.78, 1)
        # Kept clear of the HUD (top-left), the puzzle panel (top-centre) and level name.
        for cx, cz, r in (
            (-3.0, 3.0, 1.2),
            (11.5, 4.2, 0.9),
            (4.0, 1.2, 0.38),
            (-12.0, 1.8, 0.28),
        ):
            flat_disc(mb, cx, cz, r, pale, 0.0, 28)
            flat_disc(mb, cx + r * 0.3, cz + r * 0.2, r * 0.22, shade, -0.01, 12)
            flat_disc(mb, cx - r * 0.35, cz - r * 0.25, r * 0.15, shade, -0.01, 12)
        self.moons = mb.node()
        self.moons.reparentTo(self.sky)

        # --- the far sea, islands and the colony's domes ---
        far = MeshBuilder("far_islands")
        windows = MeshBuilder("dome_windows")
        far.rect(-40, -20, span + 40, 0.15, (0.12, 0.15, 0.23, 1))  # the sea
        far.rect(-40, 0.1, span + 40, 0.2, (0.3, 0.36, 0.48, 1))  # its horizon line
        rock, snow = (0.25, 0.26, 0.33, 1), (0.78, 0.84, 0.94, 1)
        dome = (0.66, 0.7, 0.8, 1)
        x = -30.0
        k = 0
        while x < span:
            w = rng.uniform(8, 16)
            h = rng.uniform(1.8, 4.0)
            top = _island(far, x, w, h, rock, snow, rng)
            if k % 2 == 0:  # every other island carries part of the colony
                cx = x + w / 2
                for dx, r in ((-1.8, 1.0), (0.0, 1.6), (1.7, 0.8)):
                    _dome(far, cx + dx, top * 0.9, r, dome, -0.02)
                    wz = top * 0.9 + r * 0.35
                    for wx in (-0.35 * r, 0.0, 0.35 * r):
                        x0 = cx + dx + wx
                        windows.rect(
                            x0 - 0.07, wz, x0 + 0.07, wz + 0.12, (1.0, 0.85, 0.5, 1), -0.03
                        )
            x += w + rng.uniform(10, 24)
            k += 1
        self.far = self._layer(far.node(), 0.7, 150, lift=1.6)
        self.windows = self._layer(windows.node(), 0.7, 149, lift=1.6)

        # --- nearer islands and cold water ---
        near = MeshBuilder("near_islands")
        near.rect(-40, -20, span + 40, -0.6, (0.08, 0.1, 0.16, 1))
        for _ in range(int(span / 6)):  # glints on the water
            gx, gz = rng.uniform(-40, span), rng.uniform(-3, -0.9)
            near.rect(gx, gz, gx + rng.uniform(0.6, 1.8), gz + 0.06, (0.3, 0.38, 0.52, 1), -0.01)
        rock, snow = (0.2, 0.2, 0.26, 1), (0.86, 0.9, 0.98, 1)
        x = -20.0
        while x < span:
            w = rng.uniform(10, 20)
            _island(near, x, w, rng.uniform(1.6, 3.2), rock, snow, rng, -0.02)
            x += w + rng.uniform(16, 34)
        self.near = self._layer(near.node(), 0.4, 100)

    def _layer(self, np, factor, y, lift=0.0):
        """Add a horizon layer. `lift` raises it so farther layers peek over nearer ones."""
        np.reparentTo(self.root)
        np.setY(y)
        self.layers.append((np, factor, lift))
        return np

    def update(self, t, cam_x, cam_z, view_h, daynight):
        n = daynight.night
        for np, factor, lift in self.layers:
            np.setX(cam_x * factor)
            np.setZ(2.0 + lift + (cam_z - view_h / 2) * factor)
        self.sky.setPos(cam_x * 0.98, 190, cam_z)
        scale = daynight.layer_scale()
        self.far.setColorScale(*scale)
        self.near.setColorScale(*scale)
        # Colony windows glow at night.
        self.windows.setColorScale(*lerp((0.45, 0.45, 0.5, 1), (1.0, 1.0, 1.0, 1), n))
        self.sun.setAlphaScale(1 - n)
        self.sun.show() if n < 0.99 else self.sun.hide()
        self.moons.setAlphaScale(0.12 + 0.88 * n)
        self.stars.setAlphaScale(n)
        self.galaxy.setAlphaScale(n)

    def destroy(self):
        self.root.removeNode()
