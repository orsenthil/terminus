"""In-world objects: sulfur crystal pickups, archives, pedestal water clocks, gates, ice
bridges, timer locks, exits and signs. Each object owns its nodes; logic is kept small and
explicit."""

import math

from panda3d.core import ClockObject, Plane, PlaneNode, Point3, TransparencyAttrib, Vec3

from game import settings as S
from game.hourglass import Hourglass
from game.render_util import MeshBuilder, make_text


def _dist(ax, az, bx, bz):
    return math.hypot(ax - bx, az - bz)


def _glass_shape(mb, w, h, y, color):
    """Outline-ish hourglass silhouette: two triangles meeting at the neck (origin)."""
    mb.flat_tri((-w, h), (w, h), (0, 0), color, y)
    mb.flat_tri((-w, -h), (0, 0), (w, -h), color, y)


class WaterDisplay:
    """The water in a two-chamber water clock.

    Each chamber holds a full triangle of water that is cut off at the water line by a clip
    plane, so the surface stays flat like a real liquid. The top chamber narrows toward the
    neck, the bottom chamber widens toward its floor; heights are chosen so the visible area
    matches the fraction of water in each. A single drop falls through the neck while the
    clock runs.
    """

    def __init__(self, parent, w, h, color=S.WATER_DAY, y=-0.02):
        self.w, self.h = w, h
        self.root = parent.attachNewNode("water_display")
        self.chambers = []
        for name, pts in (
            ("top_water", ((-w, h), (w, h), (0, 0))),
            ("bottom_water", ((-w, -h), (0, 0), (w, -h))),
        ):
            mb = MeshBuilder(name)
            mb.flat_tri(*pts, color, y)
            water = mb.node()
            water.reparentTo(self.root)
            line = self.root.attachNewNode(
                PlaneNode(name + "_line", Plane(Vec3(0, 0, -1), Point3(0, 0, 0)))
            )
            water.setClipPlane(line)
            self.chambers.append((water, line))
        mb = MeshBuilder("drop")
        r = max(0.012, w * 0.07)
        mb.rect(-r, -r * 1.6, r, r * 1.6, color, y - 0.01)
        self.drop = mb.node()
        self.drop.reparentTo(self.root)
        for np in (self.chambers[0][0], self.chambers[1][0], self.drop):
            np.setTwoSided(True)
            np.setLightOff()
        self.bottom_level = -h

    @property
    def top(self):
        return self.chambers[0][0]

    @property
    def bottom(self):
        return self.chambers[1][0]

    def set_color(self, color):
        """Recolour the water (blue by day, purple by night)."""
        for np in (self.top, self.bottom, self.drop):
            np.setColor(*color)

    def set_fill(self, top_frac, bottom_frac, flowing):
        h = self.h
        top_frac = max(0.0, min(1.0, top_frac))
        bottom_frac = max(0.0, min(1.0, bottom_frac))
        # Top chamber: water from the neck (z=0) up to h*sqrt(f) holds a fraction f.
        self.chambers[0][1].setZ(h * math.sqrt(top_frac))
        self.top.show() if top_frac > 0.001 else self.top.hide()
        # Bottom chamber: water from the floor (z=-h) up to h*(1-sqrt(1-f)).
        self.bottom_level = -h + h * (1.0 - math.sqrt(1.0 - bottom_frac))
        self.chambers[1][1].setZ(self.bottom_level)
        self.bottom.show() if bottom_frac > 0.001 else self.bottom.hide()
        if flowing:
            k = (ClockObject.getGlobalClock().getFrameTime() * 2.5) % 1.0
            self.drop.setZ(-k * k * (0 - self.bottom_level) - 0.02)
            self.drop.show()
        else:
            self.drop.hide()


class Pickup:
    """A cluster of glowing sulfur crystals. Collecting it buys time."""

    def __init__(self, parent, tile):
        self.x, self.z = tile[0] + 0.5, tile[1] + 0.3
        self.collected = False
        self.root = parent.attachNewNode("pickup")
        mb = MeshBuilder("sulfur")
        for cx, w, top, color in (
            (-0.2, 0.11, 0.42, S.SULFUR),
            (0.2, 0.1, 0.36, S.SULFUR),
            (0.0, 0.14, 0.62, S.SULFUR_GLOW),
        ):
            mb.quad(
                (cx - w, -0.1, 0.1),
                (cx, -0.1, 0.0),
                (cx + w, -0.1, 0.1),
                (cx, -0.1, top),
                color,
                (0, -1, 0),
            )
        mb.flat_tri((-0.03, 0.2), (0.07, 0.25), (0.0, 0.5), S.SULFUR_GLOW, -0.12)  # facet
        np = mb.node()
        np.setTwoSided(True)
        np.setLightOff()
        np.reparentTo(self.root)
        self.root.setPos(tile[0] + 0.5, -0.2, tile[1])
        self.phase = tile[0] * 0.7

    def update(self, dt, t):
        if not self.collected:
            self.root.setZ(self.z - 0.3 + 0.06 * math.sin(t * 3 + self.phase))
            glow = 0.85 + 0.15 * math.sin(t * 4 + self.phase)
            self.root.setColorScale(glow, glow, glow, 1)

    def set_collected(self, value):
        self.collected = value
        self.root.hide() if value else self.root.show()


class Archive:
    """A stone archive terminal: a checkpoint, and where you repay your time debt."""

    def __init__(self, parent, tile):
        self.x, self.z = tile[0] + 0.5, tile[1]
        self.active = False
        self.root = parent.attachNewNode("archive")
        self.root.setPos(self.x, 0.1, self.z)
        mb = MeshBuilder("archive")
        stone, dark = S.STONE, (0.36, 0.37, 0.43, 1)
        mb.box(-0.75, -0.45, 0, 0.75, 0.45, 0.3, dark)
        mb.box(-0.6, -0.4, 0.3, 0.6, 0.4, 2.2, stone, top_color=S.FROST_TOP)
        mb.box(-0.68, -0.43, 2.2, 0.68, 0.43, 2.35, dark, top_color=S.FROST_TOP)
        mb.node().reparentTo(self.root)
        # The terminal's screen: rows of glowing record lines, and a small water clock.
        mb = MeshBuilder("screen")
        mb.rect(-0.45, 1.25, 0.45, 2.05, (0.05, 0.12, 0.2, 1), -0.41)
        for k in range(5):
            z = 1.35 + k * 0.14
            mb.rect(-0.38, z, -0.38 + 0.2 + 0.08 * ((k * 3) % 4), z + 0.05, (0.4, 0.8, 1, 1), -0.42)
        self.screen = mb.node()
        self.screen.setLightOff()
        self.screen.reparentTo(self.root)
        mb = MeshBuilder("archive_clock")
        _glass_shape(mb, 0.28, 0.42, -0.43, (0.45, 0.6, 0.8, 0.55))
        clock = mb.node()
        clock.setTransparency(TransparencyAttrib.MAlpha)
        clock.setLightOff()
        clock.setTwoSided(True)
        clock.reparentTo(self.root)
        clock.setZ(0.72)
        self.water = WaterDisplay(clock, 0.25, 0.38, y=-0.44)
        self.water.set_fill(0.3, 0.5, False)
        self.glow = self.root.attachNewNode("glow")
        mb = MeshBuilder("glow")
        mb.rect(-1.0, 0, 1.0, 2.7, (0.4, 0.75, 1.0, 0.25), 0.5)
        g = mb.node()
        g.setTransparency(TransparencyAttrib.MAlpha)
        g.setLightOff()
        g.reparentTo(self.glow)
        self.glow.hide()
        self.pouring = False

    def near(self, px, pz):
        return abs(px - self.x) < S.ARCHIVE_RADIUS and abs(pz - self.z) < 1.5

    def set_active(self, value):
        self.active = value
        self.glow.show() if value else self.glow.hide()

    def update(self, dt, t):
        level = 0.5 if not self.pouring else 0.5 + 0.1 * math.sin(t * 8)
        self.water.set_fill(0.3 + 0.05 * math.sin(t * 0.5), level, True)
        self.screen.setColorScale(*([0.8 + 0.2 * math.sin(t * 3)] * 3), 1)
        if self.active:
            self.glow.setAlphaScale(0.7 + 0.3 * math.sin(t * 2))


class PedestalGlass:
    """A small water clock on a pedestal. Linked gates/bridges are active while it runs."""

    def __init__(self, parent, tile, capacity, gates=(), bridges=()):
        self.x, self.z = tile[0] + 0.5, tile[1]
        self.capacity = float(capacity)
        self.glass = Hourglass(top=0.0, bottom=self.capacity, capacity=self.capacity)
        self.gates = list(gates)
        self.bridges = list(bridges)
        self.spin = 0.0
        self.root = parent.attachNewNode("pedestal_glass")
        self.root.setPos(self.x, -0.1, self.z)
        self.root.setScale(1.3)
        mb = MeshBuilder("pedestal")
        mb.box(-0.35, -0.3, 0, 0.35, 0.3, 0.55, S.STONE, top_color=(0.7, 0.62, 0.55, 1))
        mb.node().reparentTo(self.root)
        self.flipper = self.root.attachNewNode("flipper")
        self.flipper.setZ(1.35)
        mb = MeshBuilder("glass")
        wood = (0.34, 0.36, 0.44, 1)  # dark metal caps
        mb.box(-0.42, -0.2, 0.72, 0.42, 0.2, 0.8, wood)
        mb.box(-0.42, -0.2, -0.8, 0.42, 0.2, -0.72, wood)
        frame = mb.node()
        frame.reparentTo(self.flipper)
        mb = MeshBuilder("bulbs")
        _glass_shape(mb, 0.36, 0.72, -0.22, (0.55, 0.7, 0.9, 0.45))
        bulbs = mb.node()
        bulbs.setTransparency(TransparencyAttrib.MAlpha)
        bulbs.setTwoSided(True)
        bulbs.setLightOff()
        bulbs.reparentTo(self.flipper)
        self.water = WaterDisplay(self.flipper, 0.32, 0.66, y=-0.25)
        # Capacity label on the pedestal so glasses can be told apart at a glance.
        self.label = make_text(
            parent, f"{self.capacity:g}s", (self.x, -2, self.z + 0.2), 0.38, S.TEXT_COLOR
        )
        # "EMPTY!" flashes above the glass the moment its water runs out.
        self.empty_text = make_text(parent, "EMPTY!", (self.x, -2, self.z + 4.0), 0.45, S.GOLD)
        self.empty_text.hide()
        self.empty_flash = 0.0
        self.refresh()

    @property
    def running(self):
        return not self.glass.empty

    def flip(self):
        self.glass.flip()
        self.spin = 180.0
        self.refresh()

    def reset(self):
        self.glass = Hourglass(top=0.0, bottom=self.capacity, capacity=self.capacity)
        self.spin = 0.0
        self.empty_flash = 0.0
        self.empty_text.hide()
        self.refresh()

    def update(self, dt, t):
        """Advance the glass. Returns True on the step its water runs out."""
        was_running = self.running
        self.glass.update(dt)
        if self.spin > 0:
            self.spin = max(0.0, self.spin - 900 * dt)
        emptied = was_running and not self.running
        if emptied:
            self.empty_flash = 1.5
        if self.empty_flash > 0:
            self.empty_flash = max(0.0, self.empty_flash - dt)
            self.empty_text.show()
            self.empty_text.setAlphaScale(min(1.0, self.empty_flash * 2))
            self.empty_text.setScale(0.45 + 0.1 * self.empty_flash)
        else:
            self.empty_text.hide()
        self.refresh()
        return emptied

    def refresh(self):
        c = self.capacity
        self.water.set_fill(
            self.glass.top / c, self.glass.bottom / c, self.running and not self.spin
        )
        self.flipper.setR(self.spin)


class Gate:
    """A stone door made of D tiles; solid while closed."""

    def __init__(self, parent, tiles, grid):
        self.tiles = tiles
        self.grid = grid
        self.open = False
        self.openness = 0.0
        xs = [t[0] for t in tiles]
        zs = [t[1] for t in tiles]
        self.x0, self.x1 = min(xs), max(xs) + 1
        self.z0, self.z1 = min(zs), max(zs) + 1
        self.height = self.z1 - self.z0
        self.root = parent.attachNewNode("gate")
        mb = MeshBuilder("gate")
        for ix, iz in tiles:
            shade = 1.0 if (ix + iz) % 2 else 0.88
            color = tuple(ch * shade for ch in S.GATE_COLOR[:3]) + (1,)
            mb.box(ix + 0.08, -0.4, iz, ix + 0.92, 0.4, iz + 1, color)
            mb.rect(ix + 0.35, iz + 0.3, ix + 0.65, iz + 0.7, S.GOLD, -0.41)
        mb.node().reparentTo(self.root)
        self.set_solid(True)

    def set_solid(self, value):
        for ix, iz in self.tiles:
            self.grid.set_solid(ix, iz, value)

    def want(self, open_, player_box):
        """Request a state. Closing is deferred while the player stands in the doorway.
        Returns 'open' / 'close' when the state actually changes."""
        if open_ == self.open:
            return None
        if not open_:
            left, bottom, right, top = player_box
            if left < self.x1 and right > self.x0 and bottom < self.z1 and top > self.z0:
                return None
        self.open = open_
        self.set_solid(not open_)
        return "open" if open_ else "close"

    def update(self, dt):
        target = 1.0 if self.open else 0.0
        speed = 6.0 if self.open else 10.0
        if self.openness < target:
            self.openness = min(target, self.openness + speed * dt)
        else:
            self.openness = max(target, self.openness - speed * dt)
        self.root.setZ(-self.openness * self.height)


class Bridge:
    """Glowing ice tiles that are solid only while their water clock runs."""

    def __init__(self, parent, tiles, grid):
        self.tiles = tiles
        self.grid = grid
        self.active = False
        self.root = parent.attachNewNode("bridge")
        mb = MeshBuilder("bridge")
        for ix, iz in tiles:
            mb.box(ix + 0.02, -0.45, iz + 0.45, ix + 0.98, 0.45, iz + 1, S.BRIDGE_COLOR)
        np = mb.node()
        np.setTransparency(TransparencyAttrib.MAlpha)
        np.reparentTo(self.root)
        self.set_active(False)

    def set_active(self, value):
        changed = value != self.active
        self.active = value
        for ix, iz in self.tiles:
            self.grid.set_solid(ix, iz, value)
        self.root.setAlphaScale(1.0 if value else 0.12)
        return changed


class TimerLockLogic:
    """Start / stop measurement. Opens if the elapsed time is within tolerance of target."""

    def __init__(self, target, tolerance=S.LOCK_TOLERANCE):
        self.target = float(target)
        self.tolerance = tolerance
        self.running = False
        self.solved = False
        self.elapsed = 0.0
        self.last_error = 0.0  # elapsed - target of the last failed attempt

    def update(self, dt):
        if self.running:
            self.elapsed += dt

    def interact(self):
        """Returns 'start', 'success', 'fail' or None (already solved)."""
        if self.solved:
            return None
        if not self.running:
            self.running = True
            self.elapsed = 0.0
            return "start"
        self.running = False
        if abs(self.elapsed - self.target) <= self.tolerance:
            self.solved = True
            return "success"
        self.last_error = self.elapsed - self.target
        self.elapsed = 0.0
        return "fail"

    def reset(self):
        self.running = False
        self.solved = False
        self.elapsed = 0.0


class TimerLock:
    """A lock that opens when stopped `target` seconds after it was started.

    `glasses` are the pedestal glasses meant for measuring it (reset when an attempt
    fails); `guide` is an optional list of on-screen steps (see PlayScene)."""

    def __init__(self, parent, tile, target, gates=(), glasses=(), guide=(), title=""):
        self.x, self.z = tile[0] + 0.5, tile[1]
        self.logic = TimerLockLogic(target)
        self.gates = list(gates)
        self.glasses = list(glasses)
        self.guide = list(guide)
        self.title = title
        self.fail_flash = 0.0
        self.label = make_text(
            parent, f"{float(target):g}s", (self.x, -2, self.z + 2.7), 0.45, S.GOLD
        )
        self.root = parent.attachNewNode("lock")
        self.root.setPos(self.x, -0.1, self.z)
        self.root.setScale(1.3)
        mb = MeshBuilder("lock_body")
        mb.box(-0.45, -0.3, 0, 0.45, 0.3, 1.7, (0.35, 0.3, 0.32, 1))
        mb.box(-0.5, -0.32, 1.7, 0.5, 0.32, 1.85, S.STONE)
        mb.node().reparentTo(self.root)
        # Tally marks: groups of five (four strokes and a slash), never a live number.
        mb = MeshBuilder("marks")
        n = int(round(target))
        for i in range(n):
            group, k = divmod(i, 5)
            gx = -0.33 + (group % 3) * 0.24
            gz = 1.25 - (group // 3) * 0.45
            if k < 4:
                x = gx + k * 0.045
                mb.rect(x, gz, x + 0.025, gz + 0.3, (1, 1, 1, 1), -0.31)
            else:
                mb.quad(
                    (gx - 0.03, -0.32, gz + 0.04),
                    (gx + 0.2, -0.32, gz + 0.24),
                    (gx + 0.2, -0.32, gz + 0.28),
                    (gx - 0.03, -0.32, gz + 0.08),
                    (1, 1, 1, 1),
                    (0, -1, 0),
                )
        self.marks = mb.node()
        self.marks.setLightOff()
        self.marks.setTwoSided(True)
        self.marks.reparentTo(self.root)
        mb = MeshBuilder("keyhole")
        mb.rect(-0.08, 0.2, 0.08, 0.5, (0.05, 0.05, 0.05, 1), -0.31)
        mb.node().reparentTo(self.root)
        self.refresh(0.0)

    def refresh(self, t):
        if self.logic.solved:
            self.marks.setColorScale(*S.GOLD)
        elif self.fail_flash > 0:
            self.marks.setColorScale(*S.DEBT_RED)
        elif self.logic.running:
            p = 0.6 + 0.4 * math.sin(t * 6)
            self.marks.setColorScale(1.0, 0.85 * p + 0.15, 0.4 * p, 1)
        else:
            self.marks.setColorScale(0.8, 0.75, 0.7, 1)

    def update(self, dt, t):
        self.logic.update(dt)
        self.fail_flash = max(0.0, self.fail_flash - dt)
        self.refresh(t)


class Exit:
    def __init__(self, parent, tile, requires_no_debt):
        self.x, self.z = tile[0] + 0.5, tile[1]
        self.requires_no_debt = requires_no_debt
        self.root = parent.attachNewNode("exit")
        self.root.setPos(self.x, 0.2, self.z)
        mb = MeshBuilder("arch")
        stone = (0.7, 0.6, 0.5, 1)
        mb.box(-1.0, -0.4, 0, -0.7, 0.4, 2.3, stone)
        mb.box(0.7, -0.4, 0, 1.0, 0.4, 2.3, stone)
        mb.box(-1.2, -0.45, 2.3, 1.2, 0.45, 2.7, stone, top_color=S.FROST_TOP)
        mb.node().reparentTo(self.root)
        mb = MeshBuilder("door")
        mb.rect(-0.7, 0, 0.7, 2.3, (1, 1, 1, 1), 0.1)
        self.door = mb.node()
        self.door.setLightOff()
        self.door.reparentTo(self.root)

    def box(self):
        return (self.x - 0.6, self.z, self.x + 0.6, self.z + 2.0)

    def update(self, dt, t, locked):
        if locked:
            self.door.setColor(0.25, 0.05, 0.08, 1)
        else:
            p = 0.9 + 0.1 * math.sin(t * 3)
            self.door.setColor(1.0 * p, 0.93 * p, 0.62 * p, 1)


class Sign:
    """A hint that appears in the air when the player walks near its spot (no signpost)."""

    def __init__(self, parent, tile, text):
        self.x, self.z = tile[0] + 0.5, tile[1]
        self.text = make_text(
            parent,
            _wrap(text, 30),
            (self.x, -3, self.z + 3.4),
            0.42,
            S.TEXT_COLOR,
            card=(0.08, 0.05, 0.1, 0.75),
        )
        self.alpha = 0.0
        self.text.setAlphaScale(0)

    def update(self, dt, visible):
        target = 1.0 if visible else 0.0
        self.alpha += (target - self.alpha) * min(1.0, dt * 12)
        self.text.setAlphaScale(self.alpha)
        self.text.show() if self.alpha > 0.01 else self.text.hide()


def _wrap(text, width):
    words, lines, line = text.split(), [], ""
    for w in words:
        if line and len(line) + 1 + len(w) > width:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(line)
    return "\n".join(lines)


class PitFlames:
    """Blue flames dancing over the burning sulfur pits (sulfur burns with a blue flame).

    Purely visual; the deadly zone is fixed at PIT_HEIGHT. Only flames near the camera are
    animated each frame."""

    def __init__(self, parent, pits):
        self.root = parent.attachNewNode("pit_flames")
        self.root.setLightOff()
        self.root.setTransparency(TransparencyAttrib.MAlpha)
        self.root.setDepthWrite(False)
        self.root.setBin("transparent", 20)
        self.flames = []  # (node, x, phase)
        for ix, iz in pits:
            for k, off in enumerate((0.28, 0.72)):
                mb = MeshBuilder("flame")
                mb.flat_tri((-0.2, 0), (0.2, 0), (0.0, 0.7), S.PIT_FLAME, 0.0)
                mb.flat_tri((-0.09, 0), (0.09, 0), (0.0, 0.38), S.PIT_FLAME_CORE, -0.01)
                np = mb.node()
                np.setTwoSided(True)
                np.reparentTo(self.root)
                np.setPos(ix + off, -0.55, iz + 0.18)
                self.flames.append((np, ix + off, ix * 1.7 + k * 2.3))

    def update(self, t, cam_x, half_w):
        for np, x, phase in self.flames:
            if abs(x - cam_x) > half_w + 1:
                continue
            h = 0.75 + 0.25 * math.sin(t * 9 + phase) + 0.15 * math.sin(t * 23 + phase * 3)
            np.setScale(0.9 + 0.15 * math.sin(t * 13 + phase), 1, h)
            np.setAlphaScale(0.7 + 0.3 * math.sin(t * 17 + phase * 2))
