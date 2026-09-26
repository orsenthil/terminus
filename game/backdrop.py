"""The sky behind every level: a clockwork world that follows the day / night cycle.

Layers, far to near: stars, distant towers, huge slowly turning gears, and floating islands.
Everything is procedural and unlit; colours follow the DayNight blend.
"""

import math
import random

from panda3d.core import TransparencyAttrib

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


def _ring(mb, cx, cz, r0, r1, color, y=0.0, segments=32):
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        mb.quad(
            (cx + r0 * math.cos(a0), y, cz + r0 * math.sin(a0)),
            (cx + r1 * math.cos(a0), y, cz + r1 * math.sin(a0)),
            (cx + r1 * math.cos(a1), y, cz + r1 * math.sin(a1)),
            (cx + r0 * math.cos(a1), y, cz + r0 * math.sin(a1)),
            color,
            (0, -1, 0),
        )


def _gear(mb, cx, cz, r, teeth, color, y=0.0):
    tooth = r * 0.16
    steps = teeth * 4
    pts = []
    for i in range(steps):
        a = 2 * math.pi * i / steps
        rr = r + tooth if (i % 4) in (1, 2) else r
        pts.append((cx + rr * math.cos(a), cz + rr * math.sin(a)))
    for i in range(steps):
        mb.flat_tri((cx, cz), pts[i], pts[(i + 1) % steps], color, y)
    hub = tuple(c * 0.75 for c in color[:3]) + (1,)
    _ring(mb, cx, cz, r * 0.25, r * 0.4, hub, y - 0.01, 16)
    for k in range(5):  # spokes
        a = 2 * math.pi * k / 5
        c, s = math.cos(a), math.sin(a)
        w = r * 0.06
        mb.quad(
            (cx + c * r * 0.4 - s * w, y - 0.01, cz + s * r * 0.4 + c * w),
            (cx + c * r * 0.85 - s * w, y - 0.01, cz + s * r * 0.85 + c * w),
            (cx + c * r * 0.85 + s * w, y - 0.01, cz + s * r * 0.85 - c * w),
            (cx + c * r * 0.4 + s * w, y - 0.01, cz + s * r * 0.4 - c * w),
            hub,
            (0, -1, 0),
        )
    _ring(mb, cx, cz, r * 0.85, r * 0.95, hub, y - 0.01)


class Backdrop:
    def __init__(self, parent, width, seed=42):
        self.root = parent.attachNewNode("backdrop")
        self.root.setLightOff()
        self.root.setDepthWrite(False)
        rng = random.Random(seed)
        span = width + 80
        self.layers = []  # (node, parallax factor)

        # Stars (night only)
        mb = MeshBuilder("stars")
        for _ in range(280):
            x, z = rng.uniform(-40, span), rng.uniform(2, 40)
            s = rng.uniform(0.04, 0.12)
            b = rng.uniform(0.6, 1.0)
            mb.rect(x - s, z - s, x + s, z + s, (b, b, min(1, b * 1.1), 1))
        self.stars = self._layer(mb.node(), 0.95, 190)
        self.stars.setTransparency(TransparencyAttrib.MAlpha)

        # Clock towers and floating hourglasses in the distance.
        towers = MeshBuilder("towers")
        stone = (0.42, 0.36, 0.5, 1)
        dark = (0.34, 0.29, 0.42, 1)
        x = -30.0
        while x < span:
            w = rng.uniform(2.5, 4.5)
            h = rng.uniform(9, 17)
            towers.rect(x, -20, x + w, h, stone)
            towers.rect(x + w * 0.7, -20, x + w, h, dark)
            towers.flat_tri((x - 0.4, h), (x + w + 0.4, h), (x + w / 2, h + w * 1.1), dark)
            x += w + rng.uniform(10, 26)
            if rng.random() < 0.6:  # a floating hourglass between towers
                hx, hz = x - rng.uniform(4, 8), rng.uniform(9, 15)
                towers.flat_tri((hx - 0.9, hz + 1.4), (hx + 0.9, hz + 1.4), (hx, hz), stone)
                towers.flat_tri((hx - 0.9, hz - 1.4), (hx, hz), (hx + 0.9, hz - 1.4), stone)
        self.towers = self._layer(towers.node(), 0.8, 160)

        # Giant turning gears.
        self.gear_layer = self.root.attachNewNode("gears")
        self.gear_layer.setY(130)
        self.layers.append((self.gear_layer, 0.6))
        self.gears = []
        x = -20.0
        while x < span:
            r = rng.uniform(2.5, 6.5)
            gm = MeshBuilder("gear")
            shade = rng.uniform(0.85, 1.0)
            _gear(gm, 0, 0, r, int(r * 2.2) + 6, (0.5 * shade, 0.4 * shade, 0.45 * shade, 1))
            g = gm.node()
            g.reparentTo(self.gear_layer)
            g.setPos(x, 0, rng.uniform(3, 12))
            speed = rng.choice((-1, 1)) * rng.uniform(4, 12) * 3 / r
            self.gears.append((g, speed))
            x += r * 2 + rng.uniform(6, 18)

        # Floating islands, and a sea of sand below.
        near = MeshBuilder("islands")
        rock = (0.55, 0.4, 0.33, 1)
        x = -20.0
        while x < span:
            w = rng.uniform(4, 8)
            z = rng.uniform(6, 11)
            near.rect(x, z, x + w, z + 0.5, (0.8, 0.66, 0.45, 1))
            near.flat_tri((x, z), (x + w, z), (x + w * rng.uniform(0.35, 0.65), z - w * 0.8), rock)
            x += w + rng.uniform(12, 28)
        step = 1.0
        x = -40.0
        while x < span:
            z0 = -0.5 + 0.5 * math.sin(x * 0.2) + 0.3 * math.sin(x * 0.53)
            z1 = -0.5 + 0.5 * math.sin((x + step) * 0.2) + 0.3 * math.sin((x + step) * 0.53)
            near.quad((x, 0, -20), (x + step, 0, -20), (x + step, 0, z1), (x, 0, z0), rock)
            x += step
        self.islands = self._layer(near.node(), 0.35, 100)

    def _layer(self, np, factor, y):
        np.reparentTo(self.root)
        np.setY(y)
        self.layers.append((np, factor))
        return np

    def update(self, t, cam_x, cam_z, view_h, daynight):
        n = daynight.night
        for np, factor in self.layers:
            np.setX(cam_x * factor)
            np.setZ(2.0 + (cam_z - view_h / 2) * factor)
        scale = daynight.layer_scale()
        for np in (self.towers, self.gear_layer, self.islands):
            np.setColorScale(*scale)
        self.stars.setAlphaScale(n)

        for g, speed in self.gears:
            g.setR(t * speed)

    def destroy(self):
        self.root.removeNode()
