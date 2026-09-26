"""Player: a movement controller (pure logic on top of physics) and its rendering node."""

from game import settings as S
from game.physics import Body, move_and_collide
from game.render_util import MeshBuilder

PLAYER_Y = -1.0


def _approach(value, target, delta):
    if value < target:
        return min(value + delta, target)
    return max(value - delta, target)


class PlayerController:
    """Snappy platformer movement: acceleration, friction, coyote time, jump buffer."""

    def __init__(self, x, z):
        self.body = Body(x, z, S.PLAYER_WIDTH, S.PLAYER_HEIGHT)
        self.facing = 1
        self.coyote = 0.0
        self.buffer = 0.0
        self.jumping = False  # rising from a jump that can still be cut short
        self.was_on_ground = False
        self.body.on_ground = False

    def press_jump(self):
        self.buffer = S.JUMP_BUFFER_TIME

    def teleport(self, x, z):
        self.body.x, self.body.z = x, z
        self.body.vx = self.body.vz = 0.0
        self.coyote = self.buffer = 0.0
        self.jumping = False

    def step(self, dt, grid, move_dir, jump_held):
        """Advance one physics step. Returns a set of event names ('jump', 'land')."""
        events = set()
        b = self.body
        grounded = self.was_on_ground

        target = move_dir * S.RUN_SPEED
        if move_dir:
            self.facing = 1 if move_dir > 0 else -1
            accel = S.GROUND_ACCEL if grounded else S.AIR_ACCEL
        else:
            accel = S.GROUND_FRICTION if grounded else S.AIR_FRICTION
        b.vx = _approach(b.vx, target, accel * dt)

        self.coyote = S.COYOTE_TIME if grounded else max(0.0, self.coyote - dt)
        self.buffer = max(0.0, self.buffer - dt)
        if self.buffer > 0 and self.coyote > 0:
            b.vz = S.JUMP_VELOCITY
            self.buffer = self.coyote = 0.0
            self.jumping = True
            events.add("jump")

        if self.jumping and not jump_held and b.vz > 0:
            b.vz *= S.JUMP_CUT_MULTIPLIER
            self.jumping = False
        if b.vz <= 0:
            self.jumping = False

        b.vz = max(-S.MAX_FALL_SPEED, b.vz - S.GRAVITY * dt)
        move_and_collide(b, grid, dt)
        if b.hit_ceiling:
            self.jumping = False
        if b.on_ground and not self.was_on_ground:
            events.add("land")
        self.was_on_ground = b.on_ground
        return events


class PlayerView:
    """A little cloaked traveller built from boxes; squashes and stretches.

    Facing left uses a mirrored copy of the mesh rather than a 180-degree turn: a turn would
    show the camera the boxes' back sides and the figure would vanish.
    """

    def __init__(self, parent):
        self.root = parent.attachNewNode("player")
        self.pivot = self.root.attachNewNode("pivot")
        self.mesh_right = self._build(1).node()
        self.mesh_left = self._build(-1).node()
        for mesh in (self.mesh_right, self.mesh_left):
            mesh.reparentTo(self.pivot)
        self.mesh_left.hide()
        self.squash = 0.0  # >0 squashed (landing), <0 stretched (jumping)

    @staticmethod
    def _build(facing):
        mb = MeshBuilder("player_mesh")
        w = S.PLAYER_WIDTH / 2
        cloak = S.PLAYER_CLOAK
        dark = tuple(c * 0.7 for c in cloak[:3]) + (1,)
        mb.box(-w, -0.3, 0.0, w, 0.3, 0.62, cloak, top_color=dark, back=True)
        mb.box(-w * 0.8, -0.28, 0.0, w * 0.8, 0.28, 0.1, (0.25, 0.18, 0.12, 1), back=True)
        mb.box(-0.24, -0.25, 0.58, 0.24, 0.25, 0.92, S.PLAYER_SKIN, back=True)
        mb.box(-0.28, -0.29, 0.8, 0.28, 0.29, 0.98, dark, back=True)
        ex0, ex1 = sorted((0.08 * facing, 0.16 * facing))
        mb.box(ex0, -0.27, 0.7, ex1, -0.24, 0.78, (0.1, 0.1, 0.15, 1))  # eye
        mb.box(-w - 0.02, -0.2, 0.25, w + 0.02, 0.2, 0.32, S.GOLD, back=True)  # belt
        return mb

    def kick(self, amount):
        self.squash = amount

    def update(self, dt, controller):
        b = controller.body
        # In front of every level object (tiles, pedestals, locks, gates, bridges); only the
        # ghostly Collector (y = -1.5) passes in front of the player.
        self.root.setPos(b.x, PLAYER_Y, b.z)
        self.squash = _approach(
            self.squash, 0.0, S.SQUASH_RECOVER * dt * max(0.05, abs(self.squash))
        )
        sx = 1.0 + self.squash
        sz = 1.0 - self.squash
        self.pivot.setScale(sx, 1.0, sz)
        if controller.facing > 0:
            self.mesh_right.show()
            self.mesh_left.hide()
        else:
            self.mesh_left.show()
            self.mesh_right.hide()

    def hide(self):
        self.root.hide()

    def show(self):
        self.root.show()

    def destroy(self):
        self.root.removeNode()
