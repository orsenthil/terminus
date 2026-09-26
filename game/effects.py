"""Cheap visual effects: pooled sand particles and camera shake."""

import math
import random

from panda3d.core import TransparencyAttrib

from game import settings as S
from game.render_util import MeshBuilder


class Particles:
    """A fixed pool of small cards with velocity and lifetime (no Panda3D particle system)."""

    def __init__(self, parent, size=S.PARTICLE_POOL):
        self.root = parent.attachNewNode("particles")
        self.root.setLightOff()
        self.root.setTransparency(TransparencyAttrib.MAlpha)
        self.root.setDepthWrite(False)
        self.root.setBin("transparent", 40)
        mb = MeshBuilder("grain")
        mb.rect(-0.06, -0.06, 0.06, 0.06, (1, 1, 1, 1))
        template = mb.node()
        template.setTwoSided(True)
        self.pool = []
        for _ in range(size):
            np = template.copyTo(self.root)
            np.hide()
            # [node, x, z, vx, vz, life, max_life, gravity, alive]
            self.pool.append([np, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, False])
        self.next = 0
        self.rng = random.Random(3)

    def emit(
        self,
        x,
        z,
        count=8,
        color=S.GOLD,
        speed=3.0,
        spread=math.pi,
        angle=math.pi / 2,
        life=0.6,
        gravity=S.PARTICLE_GRAVITY,
        y=-0.8,
        jitter=0.1,
    ):
        for _ in range(count):
            p = self.pool[self.next]
            self.next = (self.next + 1) % len(self.pool)
            a = angle + self.rng.uniform(-spread, spread)
            v = speed * self.rng.uniform(0.4, 1.0)
            p[1] = x + self.rng.uniform(-jitter, jitter)
            p[2] = z + self.rng.uniform(-jitter, jitter)
            p[3], p[4] = math.cos(a) * v, math.sin(a) * v
            p[5] = p[6] = life * self.rng.uniform(0.6, 1.0)
            p[7] = gravity
            p[8] = True
            p[0].setColor(*color)
            p[0].setY(y)
            p[0].show()

    def emit_toward(self, x, z, tx, tz, count=2, color=S.GOLD, life=0.4):
        """Grains that fly from (x, z) to (tx, tz) over their lifetime."""
        for _ in range(count):
            p = self.pool[self.next]
            self.next = (self.next + 1) % len(self.pool)
            lt = life * self.rng.uniform(0.7, 1.0)
            sx = x + self.rng.uniform(-0.3, 0.3)
            sz = z + self.rng.uniform(-0.3, 0.3)
            p[1], p[2] = sx, sz
            p[3], p[4] = (tx - sx) / lt, (tz - sz) / lt
            p[5] = p[6] = lt
            p[7] = 0.0
            p[8] = True
            p[0].setColor(*color)
            p[0].setY(-0.8)
            p[0].show()

    def update(self, dt):
        for p in self.pool:
            if not p[8]:
                continue
            p[5] -= dt
            if p[5] <= 0:
                p[8] = False
                p[0].hide()
                continue
            p[4] -= p[7] * dt
            p[1] += p[3] * dt
            p[2] += p[4] * dt
            k = p[5] / p[6]
            p[0].setPos(p[1], p[0].getY(), p[2])
            p[0].setScale(0.5 + k)
            p[0].setAlphaScale(min(1.0, k * 2))

    def destroy(self):
        self.root.removeNode()


class Shake:
    def __init__(self):
        self.amount = 0.0
        self.rng = random.Random(11)

    def add(self, amount):
        self.amount = min(S.SHAKE_MAX, self.amount + amount)

    def offset(self, dt):
        self.amount = max(0.0, self.amount - S.SHAKE_DECAY * dt * max(0.3, self.amount))
        if self.amount <= 0:
            return 0.0, 0.0
        a = self.amount
        return self.rng.uniform(-a, a), self.rng.uniform(-a, a)
