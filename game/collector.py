"""The Collector: a ghost that drifts toward you while you owe time."""

import math
import random

from panda3d.core import TransparencyAttrib

from game import settings as S
from game.render_util import MeshBuilder


def collector_speed(debt_total):
    return S.COLLECTOR_BASE_SPEED + debt_total * S.COLLECTOR_DEBT_FACTOR


class Collector:
    def __init__(self, parent):
        self.x = 0.0
        self.z = 0.0
        self.alpha = 0.0
        self.active = False  # hunting
        self.sting_armed = True
        self.rng = random.Random(7)
        self.root = parent.attachNewNode("collector")
        self.root.setTransparency(TransparencyAttrib.MAlpha)
        self.root.setLightOff()
        self.root.setDepthWrite(False)
        self.root.setBin("transparent", 30)
        # A faint aura so the dark figure reads against the night sky.
        aura = MeshBuilder("aura")
        ac = (0.7, 0.15, 0.35, 0.35)
        ay = -1.45
        aura.flat_tri((-1.3, -0.5), (1.3, -0.5), (0.0, 2.6), ac, ay)
        aura.flat_tri((-1.7, 0.6), (0.0, 1.8), (-0.3, -0.4), ac, ay)
        aura.flat_tri((1.7, 0.6), (0.3, -0.4), (0.0, 1.8), ac, ay)
        aura.rect(-0.65, 1.4, 0.65, 2.6, ac, ay)
        aura.flat_tri((-0.65, 2.6), (0.65, 2.6), (0.0, 3.1), ac, ay)
        self.aura = aura.node()
        self.aura.setTwoSided(True)
        self.aura.reparentTo(self.root)
        body = MeshBuilder("collector")
        c = S.COLLECTOR_COLOR
        y = -1.5  # in front of the level: not of this world
        body.flat_tri((-0.9, -0.2), (0.9, -0.2), (0.0, 2.0), c, y)  # robe
        body.flat_tri((-1.3, 0.6), (0.0, 1.5), (-0.2, -0.1), c, y)  # sleeves
        body.flat_tri((1.3, 0.6), (0.2, -0.1), (0.0, 1.5), c, y)
        body.rect(-0.45, 1.5, 0.45, 2.4, c, y)  # hood
        body.flat_tri((-0.45, 2.4), (0.45, 2.4), (0.0, 2.8), c, y)
        eye = (1.0, 0.25, 0.1, 1)
        body.rect(-0.28, 1.9, -0.1, 2.02, eye, y - 0.01)
        body.rect(0.1, 1.9, 0.28, 2.02, eye, y - 0.01)
        np = body.node()
        np.setTwoSided(True)
        np.reparentTo(self.root)
        # A few tattered strips at the hem that sway.
        self.strips = []
        for i in range(5):
            mb = MeshBuilder("strip")
            xo = -0.7 + i * 0.35
            mb.flat_tri((xo - 0.15, 0.0), (xo + 0.15, 0.0), (xo, -0.7), c, y)
            s = mb.node()
            s.setTwoSided(True)
            s.reparentTo(self.root)
            self.strips.append(s)
        self.root.hide()

    def spawn(self, view_left, player_x, player_z):
        self.x = min(
            view_left - S.COLLECTOR_SPAWN_MARGIN, player_x - S.COLLECTOR_MIN_SPAWN_DISTANCE
        )
        self.z = player_z + 1.0
        self.active = True
        self.sting_armed = True

    def dismiss(self):
        """Stop hunting and fade out."""
        self.active = False

    def vanish(self):
        self.active = False
        self.alpha = 0.0
        self.root.hide()

    def center(self):
        return self.x, self.z + 1.0

    def update(self, dt, t, px, pz, debt_total):
        """Move toward the player centre. Returns 'near' the first time it gets close."""
        event = None
        if self.active:
            self.alpha = min(1.0, self.alpha + S.COLLECTOR_FADE_SPEED * dt)
            cx, cz = self.center()
            tx, tz = px, pz + S.PLAYER_HEIGHT / 2
            dx, dz = tx - cx, tz - cz
            dist = math.hypot(dx, dz)
            if dist > 1e-4:
                step = min(dist, collector_speed(debt_total) * dt)
                self.x += dx / dist * step
                self.z += dz / dist * step
            if dist < S.COLLECTOR_STING_DISTANCE and self.sting_armed:
                self.sting_armed = False
                event = "near"
            elif dist > S.COLLECTOR_STING_REARM:
                self.sting_armed = True
        else:
            self.alpha = max(0.0, self.alpha - S.COLLECTOR_FADE_SPEED * dt)
        if self.alpha <= 0.0:
            self.root.hide()
            return event
        self.root.show()
        flicker = 0.75 + 0.25 * self.rng.random()
        self.root.setAlphaScale(self.alpha * flicker)
        self.root.setPos(self.x, 0, self.z + 0.12 * math.sin(t * 2.5))
        self.aura.setAlphaScale(0.6 + 0.4 * math.sin(t * 4))
        for i, s in enumerate(self.strips):
            s.setR(10 * math.sin(t * 5 + i))
        return event

    def touches(self, px, pz):
        if not self.active or self.alpha < 0.3:
            return False
        cx, cz = self.center()
        return (
            abs(px - cx) < S.COLLECTOR_RADIUS + S.PLAYER_WIDTH / 2
            and abs(pz + S.PLAYER_HEIGHT / 2 - cz) < 1.0 + S.PLAYER_HEIGHT / 2
        )

    def destroy(self):
        self.root.removeNode()
