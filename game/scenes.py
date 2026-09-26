"""Scenes: title, level intro, play (with pause menu and death screen), and win.

Every scene tracks the nodes, GUI and event handlers it creates and removes them in exit().
Scenes never add their own tasks; Game drives fixed_update() and update().
"""

import math

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from panda3d.core import PointLight

from game import settings as S
from game.backdrop import Backdrop
from game.collector import Collector
from game.daynight import DayNight
from game.debt import Debt
from game.effects import Particles, Shake
from game.hourglass import Hourglass
from game.hud import HUD
from game.level import build_level_geometry, load_level_data
from game.objects import Bridge, Exit, Gate, PedestalGlass, Pickup, Shrine, Sign, TimerLock
from game.physics import TileGrid, aabb_overlap
from game.player import PlayerController, PlayerView
from game.render_util import make_card, make_hourglass_3d, make_text


class Scene(DirectObject):
    def __init__(self, game):
        self.game = game
        self.base = game.base
        self.audio = game.audio
        self.nodes = []
        self.gui = []
        self.handlers = {}
        self.t = 0.0

    # lifecycle
    def enter(self):
        pass

    def suspend(self):
        """Called when a transition away from this scene starts: stop reacting to input."""
        self.ignoreAll()
        self.handlers = {}

    def exit(self):
        self.ignoreAll()
        self.handlers = {}
        for g in self.gui:
            g.destroy()
        for n in self.nodes:
            n.removeNode()
        self.gui, self.nodes = [], []

    def fixed_update(self, dt):
        pass

    def update(self, dt):
        self.t += dt

    # helpers
    def bind(self, action, fn, *args):
        """Bind an action from settings.KEYS. Several actions may share a key (Space is
        both jump and confirm), so every key goes through one dispatcher."""
        for key in S.KEYS[action]:
            if key not in self.handlers:
                self.handlers[key] = []
                self.accept(key, self._dispatch, [key])
            self.handlers[key].append((fn, args))

    def _dispatch(self, key):
        for fn, args in list(self.handlers.get(key, ())):
            fn(*args)

    def text(self, text, pos, scale, parent=None, fg=S.TEXT_COLOR, **kw):
        t = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            fg=fg,
            shadow=(0, 0, 0, 0.9),
            parent=parent if parent is not None else self.base.aspect2d,
            mayChange=True,
            **kw,
        )
        self.gui.append(t)
        return t

    def node(self, np):
        self.nodes.append(np)
        return np


class Menu:
    """Keyboard + mouse menu made of DirectButtons."""

    def __init__(self, scene, parent, items, top=0.2, spacing=0.14):
        self.scene = scene
        self.buttons = []
        self.index = 0
        for i, (label, fn) in enumerate(items):
            b = DirectButton(
                parent=parent,
                text=label,
                scale=0.07,
                pos=(0, 0, top - i * spacing),
                frameSize=(-5, 5, -0.6, 1.1),
                relief=DGG.FLAT,
                frameColor=(0.2, 0.15, 0.1, 0.8),
                text_fg=S.TEXT_COLOR,
                command=self._activate,
                extraArgs=[i],
                rolloverSound=None,
                clickSound=None,
            )
            b.bind(DGG.ENTER, self._hover, [i])
            self.buttons.append((b, fn))
        self.highlight()

    def _hover(self, i, _event=None):
        if i != self.index:
            self.index = i
            self.scene.audio.play_sfx("menu_move")
            self.highlight()

    def move(self, delta):
        self.index = (self.index + delta) % len(self.buttons)
        self.scene.audio.play_sfx("menu_move")
        self.highlight()

    def highlight(self):
        for i, (b, _) in enumerate(self.buttons):
            if i == self.index:
                b["frameColor"] = (0.75, 0.55, 0.2, 0.95)
                b["text_fg"] = (0.1, 0.05, 0.0, 1)
            else:
                b["frameColor"] = (0.2, 0.15, 0.1, 0.8)
                b["text_fg"] = S.TEXT_COLOR

    def select(self):
        self._activate(self.index)

    def _activate(self, i):
        self.scene.audio.play_sfx("menu_select")
        self.buttons[i][1]()

    def destroy(self):
        for b, _ in self.buttons:
            b.destroy()
        self.buttons = []


class MenuBackdrop:
    """The clockwork sky for menu scenes, with a quick day / night cycle of its own."""

    CAM_Z = 5.0

    def __init__(self, scene, daynight=None):
        self.scene = scene
        self.backdrop = Backdrop(scene.base.render, 60, seed=9)
        scene.node(self.backdrop.root)
        self.daynight = daynight or DayNight(day=9, night=9, fade=2.5, time=4.0)
        scene.base.camera.setPos(0, S.CAMERA_Y, self.CAM_Z)

    def update(self, dt, t, advance=True):
        if advance:
            self.daynight.update(dt)
        _, h = self.scene.game.view_size()
        self.backdrop.update(t, 0.0, self.CAM_Z, h, self.daynight)
        self.scene.game.apply_daylight(self.daynight)


# ---------------------------------------------------------------------------------------
class TitleScene(Scene):
    def enter(self):
        self.sky = MenuBackdrop(self)
        self.glass = self.node(make_hourglass_3d(2.0, 0.7))
        self.glass.reparentTo(self.base.render)
        # Its own light so the hourglass stays bright through the night.
        lamp = self.node(self.base.render.attachNewNode(PointLight("title_lamp")))
        lamp.node().setColor((0.9, 0.85, 0.8, 1))
        lamp.setPos(-4, -20, 9)
        self.glass.setLight(lamp)
        self.glass.setPos(0, 0, 5.4)
        self.glass.setScale(2.4)
        self.text(S.WINDOW_TITLE, (0, 0.62), 0.17)
        self.text(
            "Borrow time to accomplish your task. Repay the debt, and set yourself free.",
            (0, 0.5),
            0.05,
        )
        self.prompt = self.text("Press Space", (0, -0.62), 0.08)
        self.text(
            "Move: Arrows / A D    Jump: Space    Borrow: hold Shift    Interact: E"
            "    Restart: R    Mute: M    Pause: Esc",
            (0, -0.9),
            0.038,
        )
        self.bind("confirm", self.start_game)
        self.bind("pause", self.game.quit)
        self.audio.play_music("title")

    def start_game(self):
        self.audio.play_sfx("menu_select")
        self.game.stats = {"borrowed": 0.0, "interest_paid": 0.0, "deaths": 0}
        self.game.change_scene(lambda: LevelIntroScene(self.game, 0))

    def update(self, dt):
        super().update(dt)
        self.sky.update(dt, self.t)
        self.glass.find("**/hourglass_sand").setColor(*self.sky.daynight.sand())
        self.glass.setH(self.t * 25)
        self.glass.setR(8 * math.sin(self.t * 0.7))
        self.prompt.setAlphaScale(0.55 + 0.45 * math.sin(self.t * 3))


# ---------------------------------------------------------------------------------------
class LevelIntroScene(Scene):
    def __init__(self, game, index):
        super().__init__(game)
        self.index = index

    def enter(self):
        data = load_level_data(S.LEVEL_ORDER[self.index])
        self.sky = MenuBackdrop(self, self.game.daynight)
        self.node(make_card(-1, -1, 1, 1, (0, 0, 0.03, 0.6), "dim")).reparentTo(self.base.render2d)
        self.text(f"Level {self.index + 1} of {len(S.LEVEL_ORDER)}", (0, 0.2), 0.06)
        self.text(data.name, (0, 0.02), 0.16, fg=S.GOLD)
        self.text(data.subtitle, (0, -0.14), 0.06)
        self.bind("confirm", self.go)
        self.done = False

    def go(self):
        if not self.done:
            self.done = True
            self.game.change_scene(lambda: PlayScene(self.game, self.index))

    def update(self, dt):
        super().update(dt)
        self.sky.update(dt, self.t, advance=False)
        if self.t >= S.LEVEL_INTRO_TIME:
            self.go()


# ---------------------------------------------------------------------------------------
class WinScene(Scene):
    def enter(self):
        self.sky = MenuBackdrop(self)
        self.glass = self.node(make_hourglass_3d(2.0, 0.7))
        self.glass.reparentTo(self.base.render)
        self.glass.setPos(0, 0, 5.8)
        self.glass.setScale(1.6)
        st = self.game.stats
        self.text("Free.", (0, 0.62), 0.15, fg=S.GOLD)
        self.text("You repaid every borrowed second. Terminus lets you go.", (0, 0.5), 0.06)
        self.text(
            f"Time borrowed:  {st['borrowed']:.1f} s\n"
            f"Interest paid:  {st['interest_paid']:.1f} s\n"
            f"Deaths:  {st['deaths']}",
            (0, -0.38),
            0.07,
        )
        self.prompt = self.text("Press Space", (0, -0.8), 0.06)
        self.bind("confirm", self.back)
        self.audio.play_music("win")

    def back(self):
        self.game.change_scene(lambda: TitleScene(self.game))

    def update(self, dt):
        super().update(dt)
        self.sky.update(dt, self.t)
        self.glass.find("**/hourglass_sand").setColor(*self.sky.daynight.sand())
        self.glass.setH(self.t * 15)
        self.prompt.setAlphaScale(0.55 + 0.45 * math.sin(self.t * 3))


# ---------------------------------------------------------------------------------------
class PlayScene(Scene):
    def __init__(self, game, index):
        super().__init__(game)
        self.index = index
        self.data = load_level_data(S.LEVEL_ORDER[index])

    # --- setup -----------------------------------------------------------------------
    def enter(self):
        data = self.data
        base = self.base
        self.world = self.node(base.render.attachNewNode("world"))
        build_level_geometry(data, self.world)
        self.backdrop = Backdrop(self.world, data.width)
        self.grid = TileGrid(data.width, data.height, data.solid)

        self.pickups = [Pickup(self.world, t) for t in data.pickups]
        self.shrines = [Shrine(self.world, t) for t in data.shrines]
        self.gates = [Gate(self.world, tiles, self.grid) for tiles in data.gates]
        self.bridges = [Bridge(self.world, tiles, self.grid) for tiles in data.bridges]
        self.glasses = [
            PedestalGlass(self.world, t, g["capacity"], g.get("gates", []), g.get("bridges", []))
            for t, g in zip(data.glass_tiles, data.glasses, strict=True)
        ]
        self.locks = [
            TimerLock(
                self.world,
                t,
                lk["target"],
                lk.get("gates", []),
                lk.get("glasses", []),
                lk.get("guide", []),
                lk.get("title", ""),
            )
            for t, lk in zip(data.lock_tiles, data.locks, strict=True)
        ]
        # Guide progress per lock: [current step, events seen during that step].
        self.guide_progress = [[0, set()] for _ in self.locks]
        self.exits = [Exit(self.world, t, data.exit_requires_no_debt) for t in data.exits]
        self.signs = [
            Sign(self.world, t, text) for t, text in zip(data.sign_tiles, data.signs, strict=True)
        ]

        sx, sz = data.player_start
        self.player = PlayerController(sx + 0.5, sz)
        self.view = PlayerView(self.world)
        self.collector = Collector(self.world)
        self.particles = Particles(self.world)
        self.shake = Shake()
        self.life = Hourglass(top=data.start_sand, capacity=S.LIFE_MAX)
        self.debt = Debt()
        self.checkpoint = self._snapshot(sx + 0.5, sz)
        self.collected_since_checkpoint = []

        self.hud = HUD(base, show_debt=data.allow_borrow)
        self.hud.set_level_name(f"{self.index + 1}. {data.name}")
        self.tint = self.node(make_card(-1, -1, 1, 1, S.DEBT_TINT_COLOR, "debt_tint"))
        self.tint.reparentTo(base.render2d)
        self.tint.setBin("background", 0)
        self.tint.setTransparency(True)
        self.tint.setAlphaScale(0)
        # Running out of time: the whole screen pulses red.
        self.low_tint = self.node(make_card(-1, -1, 1, 1, S.LOW_TIME_TINT, "low_time_tint"))
        self.low_tint.reparentTo(base.render2d)
        self.low_tint.setBin("background", 1)
        self.low_tint.setTransparency(True)
        self.low_tint.setAlphaScale(0)
        self.low_time_warned = False

        # At night the traveller carries a lantern that lights the platforms nearby.
        lantern = PointLight("lantern")
        lantern.setAttenuation(S.LANTERN_ATTENUATION)
        self.lantern = self.view.root.attachNewNode(lantern)
        self.lantern.setPos(0, -2.0, 0.8)
        base.render.setLight(self.lantern)
        self.prompt = make_text(self.world, "", (0, -3, 0), 0.4, S.GOLD_GLOW)

        self.state = "play"
        self.borrowing = False
        self.pouring = False
        self.pause_frame = None
        self.menu = None
        self.dead_frame = None
        self.complete_timer = 0.0
        self.borrow_denied_shown = False

        w, h = self.game.view_size()
        self.cam_x = self.player.body.x
        self.cam_z = self.player.body.z + S.CAMERA_Z_OFFSET
        self.cam_x, self.cam_z = self._clamp_cam(self.cam_x, self.cam_z)

        self.bind("jump", self.on_jump)
        self.bind("interact", self.on_interact)
        self.bind("restart", self.restart)
        self.bind("pause", self.on_pause)
        self.bind("menu_up", self.on_menu, -1)
        self.bind("menu_down", self.on_menu, 1)
        self.bind("confirm", self.on_confirm)
        self.audio.play_music("level_calm")
        self.update(0.0)

    def exit(self):
        self.game.stats["borrowed"] += self.debt.total_borrowed
        self.game.stats["interest_paid"] += self.debt.total_interest_paid
        self.audio.stop_loop("borrow_loop")
        self.audio.stop_loop("shrine_pour_loop")
        self.base.render.clearLight(self.lantern)
        self._close_pause()
        if self.dead_frame is not None:
            self.dead_frame.destroy()
            self.dead_frame = None
        self.hud.destroy()
        super().exit()

    # --- checkpoints -----------------------------------------------------------------
    def _snapshot(self, x, z):
        return {
            "x": x,
            "z": z,
            "life": self.life.top,
            "debt": self.debt.snapshot(),
        }

    def respawn(self):
        cp = self.checkpoint
        self.player.teleport(cp["x"], cp["z"])
        floor = min(15.0, self.data.start_sand)
        self.life = Hourglass(top=max(cp["life"], floor), capacity=S.LIFE_MAX)
        self.debt.restore(cp["debt"])
        self.collector.vanish()
        for p in self.collected_since_checkpoint:
            p.set_collected(False)
        self.collected_since_checkpoint = []
        for g in self.glasses:
            g.reset()
        for lock in self.locks:
            if not lock.logic.solved:
                lock.logic.reset()
        self.guide_progress = [[0, set()] for _ in self.locks]
        self.view.show()
        self.state = "play"
        self.audio.play_music("level_calm")

    # --- input -----------------------------------------------------------------------
    def on_jump(self):
        if self.state == "play":
            self.player.press_jump()

    def on_interact(self):
        if self.state != "play":
            return
        target = self._interact_target()
        if isinstance(target, PedestalGlass):
            target.flip()
            self.audio.play_sfx("flip_glass")
            self.particles.emit(target.x, target.z + 1.4, 10, S.GOLD, speed=2.5)
            self._guide_event(f"flip:{self.glasses.index(target)}")
        elif isinstance(target, TimerLock):
            result = target.logic.interact()
            index = self.locks.index(target)
            if result == "start":
                self.audio.play_sfx("lock_start")
                self._guide_start(index)
            elif result == "success":
                self.audio.play_sfx("lock_success")
                self.particles.emit(target.x, target.z + 1.2, 30, S.GOLD_GLOW, speed=4)
                self.hud.show_message("Measured! The lock opens.")
            elif result == "fail":
                self.audio.play_sfx("lock_fail")
                target.fail_flash = 0.6
                self.shake.add(0.15)
                when = "Too early!" if target.logic.last_error < 0 else "Too late!"
                for i in target.glasses:
                    self.glasses[i].reset()
                self.guide_progress[index] = [0, set()]
                self.hud.show_message(
                    f"{when} The lock and its glasses reset. Try again from step 1.", 4.0
                )

    # --- puzzle guide ----------------------------------------------------------------
    def _guide_event(self, event):
        """Advance every unsolved lock guide whose current step waits for `event`."""
        for lock, progress in zip(self.locks, self.guide_progress, strict=True):
            if lock.logic.solved or progress[0] >= len(lock.guide):
                continue
            step = lock.guide[progress[0]]
            if event in step["on"]:
                progress[1].add(event)
                if set(step["on"]) <= progress[1]:
                    progress[0] += 1
                    progress[1] = set()

    def _guide_start(self, index):
        """Starting a lock always moves its guide to the step after 'start'."""
        lock, progress = self.locks[index], self.guide_progress[index]
        for i, step in enumerate(lock.guide):
            if "start" in step["on"]:
                progress[0], progress[1] = max(progress[0], i + 1), set()

    def _active_guide(self):
        b = self.player.body
        best = None
        for lock, progress in zip(self.locks, self.guide_progress, strict=True):
            if lock.guide and not lock.logic.solved and abs(lock.x - b.x) < 11:
                if best is None or abs(lock.x - b.x) < abs(best[0].x - b.x):
                    best = (lock, progress)
        return best

    def on_pause(self):
        if self.state == "play":
            self.state = "paused"
            self.audio.stop_loop("borrow_loop")
            self.audio.stop_loop("shrine_pour_loop")
            self._open_pause()
        elif self.state == "paused":
            self.resume()

    def on_menu(self, delta):
        if self.state == "paused" and self.menu is not None:
            self.menu.move(delta)

    def on_confirm(self):
        if self.state == "paused" and self.menu is not None:
            self.menu.select()
        elif self.state == "dead" and self.dead_frame is not None:
            self.dead_frame.destroy()
            self.dead_frame = None
            self.respawn()

    def restart(self):
        if self.state in ("play", "paused", "dead"):
            self.game.change_scene(lambda: PlayScene(self.game, self.index))

    def resume(self):
        self._close_pause()
        self.state = "play"

    def toggle_mute(self):
        self.audio.toggle_mute()

    def quit_to_title(self):
        self.game.change_scene(lambda: TitleScene(self.game))

    def _open_pause(self):
        self.pause_frame = DirectFrame(
            frameColor=(0.02, 0.02, 0.06, 0.75), frameSize=(-0.6, 0.6, -0.55, 0.62)
        )
        OnscreenText(text="Paused", parent=self.pause_frame, pos=(0, 0.42), scale=0.1, fg=S.GOLD)
        self.menu = Menu(
            self,
            self.pause_frame,
            [
                ("Resume", self.resume),
                ("Restart level", self.restart),
                ("Toggle mute", self.toggle_mute),
                ("Quit to title", self.quit_to_title),
            ],
            top=0.2,
        )

    def _close_pause(self):
        if self.menu is not None:
            self.menu.destroy()
            self.menu = None
        if self.pause_frame is not None:
            self.pause_frame.destroy()
            self.pause_frame = None

    # --- gameplay --------------------------------------------------------------------
    def _player_box(self):
        b = self.player.body
        return (b.left, b.z, b.right, b.top)

    def _interact_target(self):
        b = self.player.body
        best, best_d = None, S.INTERACT_RADIUS
        for obj in self.glasses + self.locks:
            dx = abs(obj.x - b.x)
            if dx < best_d and abs(obj.z - b.z) < 1.5:
                if isinstance(obj, TimerLock) and obj.logic.solved:
                    continue
                best, best_d = obj, dx
        return best

    def die(self, reason):
        if self.state != "play":
            return
        self.state = "dead"
        self.game.stats["deaths"] += 1
        b = self.player.body
        self.view.hide()
        self.particles.emit(b.x, b.z + 0.5, 40, S.GOLD, speed=6, life=1.0)
        self.shake.add(0.5)
        self.audio.stop_loop("borrow_loop")
        self.audio.stop_loop("shrine_pour_loop")
        self.audio.play_sfx("death")
        self.audio.stop_music(0.5)
        self.audio.play_music("game_over")
        self.dead_frame = DirectFrame(
            frameColor=(0.05, 0.0, 0.02, 0.7), frameSize=(-3, 3, -0.3, 0.35)
        )
        OnscreenText(text=reason, parent=self.dead_frame, pos=(0, 0.12), scale=0.11, fg=S.GOLD)
        where = "the last shrine" if self.checkpoint.get("shrine") else "the start"
        OnscreenText(
            text=f"Space: try again from {where}      R: restart level",
            parent=self.dead_frame,
            pos=(0, -0.1),
            scale=0.055,
            fg=S.TEXT_COLOR,
        )

    def complete(self):
        self.state = "complete"
        self.complete_timer = 1.4
        self.audio.stop_loop("borrow_loop")
        self.audio.stop_loop("shrine_pour_loop")
        self.audio.stop_music(0.8)
        self.audio.play_music("level_complete")
        b = self.player.body
        self.particles.emit(b.x, b.z + 1, 40, S.GOLD_GLOW, speed=5, life=1.2)
        self.hud.show_message("The way opens.")

    def fixed_update(self, dt):
        if self.state == "complete":
            self.complete_timer -= dt
            if self.complete_timer <= 0:
                self.state = "leaving"
                nxt = self.index + 1
                if nxt < len(S.LEVEL_ORDER):
                    self.game.change_scene(lambda: LevelIntroScene(self.game, nxt))
                else:
                    self.game.change_scene(lambda: WinScene(self.game))
            return
        if self.state != "play":
            return
        g = self.game
        b = self.player.body

        # Borrow
        want_borrow = g.held("borrow")
        self.borrowing = False
        if want_borrow and not self.data.allow_borrow:
            if not self.borrow_denied_shown:
                self.hud.show_message("No one will lend you time here.")
                self.borrow_denied_shown = True
        elif want_borrow:
            room = max(0.0, S.LIFE_MAX - self.life.top)
            amount = self.debt.borrow(min(S.BORROW_RATE * dt, room))
            if amount > 0:
                self.life.add(amount)
                self.borrowing = True
        if not want_borrow:
            self.borrow_denied_shown = False

        # Life drains; debt compounds
        self.life.update(dt)
        for _ in range(self.debt.update(dt)):
            self.hud.interest_pop()
            self.audio.play_sfx("interest_tick")
            self.shake.add(0.08)
        if self.life.empty:
            self.die("Out of time")
            return

        # Movement
        move = (1 if g.held("right") else 0) - (1 if g.held("left") else 0)
        events = self.player.step(dt, self.grid, move, g.held("jump"))
        if "jump" in events:
            self.audio.play_sfx("jump")
            self.view.kick(-S.SQUASH_AMOUNT)
        if "land" in events:
            self.audio.play_sfx("land")
            self.view.kick(S.SQUASH_AMOUNT)
            self.particles.emit(b.x, b.z + 0.05, 6, S.SAND_TOP, speed=2.0, spread=1.2, life=0.35)

        # Hazards
        box = self._player_box()
        if b.z < -2.0:
            self.die("Lost to the dunes")
            return
        for ix, iz in self.data.spikes:
            if aabb_overlap(box, (ix + 0.15, iz, ix + 0.85, iz + S.SPIKE_HEIGHT)):
                self.die("Impaled on the spikes")
                return

        # Pickups
        for p in self.pickups:
            if not p.collected and abs(p.x - b.x) < S.PICKUP_RADIUS and abs(p.z - b.z) < 0.9:
                p.set_collected(True)
                self.collected_since_checkpoint.append(p)
                self.life.add(S.PICKUP_SAND)
                self.audio.play_sfx("pickup")
                self.particles.emit(p.x, p.z + 0.3, 14, S.GOLD_GLOW, speed=3.5)

        # Shrines: checkpoint + pour sand into debt while E is held
        self.pouring = False
        for s in self.shrines:
            s.pouring = False
            if not s.near(b.x, b.z):
                continue
            if not s.active:
                for other in self.shrines:
                    other.set_active(False)
                s.set_active(True)
                self.checkpoint = self._snapshot(s.x, s.z)
                self.checkpoint["shrine"] = True
                self.collected_since_checkpoint = []
                self.hud.show_message("The shrine will remember you.")
            if g.held("interact") and self.debt.in_debt:
                spare = self.life.top - S.SHRINE_MIN_LIFE
                amount = min(S.SHRINE_POUR_RATE * dt, spare, self.debt.total)
                if amount > 0:
                    self.life.remove(amount)
                    self.debt.repay(amount)
                    self.pouring = s.pouring = True
                    if not self.debt.in_debt:
                        self.hud.show_message("Debt settled.")
                    # Keep the checkpoint's debt in step with what was just paid.
                    self.checkpoint = self._snapshot(s.x, s.z)
                    self.checkpoint["shrine"] = True

        # Glasses drive gates and bridges; solved locks hold their gates open.
        for i, gl in enumerate(self.glasses):
            if gl.update(dt, self.t):
                self._guide_event(f"empty:{i}")
        for lock in self.locks:
            lock.update(dt, self.t)
        gate_open = [False] * len(self.gates)
        bridge_on = [False] * len(self.bridges)
        for gl in self.glasses:
            if gl.running:
                for i in gl.gates:
                    gate_open[i] = True
                for i in gl.bridges:
                    bridge_on[i] = True
        for lock in self.locks:
            if lock.logic.solved:
                for i in lock.gates:
                    gate_open[i] = True
        for gate, want in zip(self.gates, gate_open, strict=True):
            change = gate.want(want, box)
            if change == "open":
                self.audio.play_sfx("gate_open")
            elif change == "close":
                self.audio.play_sfx("gate_close")
                self.shake.add(0.1)
        for bridge, want in zip(self.bridges, bridge_on, strict=True):
            bridge.set_active(want)

        # The Collector
        col = self.collector
        if self.debt.in_debt and not col.active:
            w, _ = self.game.view_size()
            col.spawn(self.cam_x - w / 2, b.x, b.z)
        elif not self.debt.in_debt and col.active:
            col.dismiss()
        if col.update(dt, self.t, b.x, b.z, self.debt.total) == "near":
            self.audio.play_music("collector_near")
        if col.touches(b.x, b.z):
            taken = self.debt.clear()
            self.life.remove(taken)
            col.vanish()
            self.audio.play_sfx("collector_hit")
            self.shake.add(0.6)
            self.particles.emit(b.x, b.z + 0.5, 30, S.DEBT_RED, speed=5)
            self.hud.show_message(f"The Collector took {taken:.0f} seconds.")
            if self.life.empty:
                self.die("The Collector took everything")
                return

        # Exit
        for ex in self.exits:
            if aabb_overlap(box, ex.box()):
                if ex.requires_no_debt and self.debt.in_debt:
                    if self.hud.message_time <= 0:
                        self.hud.show_message(
                            "The last door stays shut until your time debt is repaid."
                        )
                else:
                    self.complete()
                    return

    # --- per frame -------------------------------------------------------------------
    def _clamp_cam(self, x, z):
        w, h = self.game.view_size()
        x = max(w / 2, min(self.data.width - w / 2, x))
        z = max(h / 2 - 1.0, min(self.data.height - h / 2 + 1.0, z))
        return x, z

    def update(self, dt):
        super().update(dt)
        b = self.player.body
        g = self.game

        # Camera: lookahead + damping, clamped to the level; shake as an offset.
        tx = b.x + self.player.facing * S.CAMERA_LOOKAHEAD
        tz = b.z + S.CAMERA_Z_OFFSET
        k = 1.0 - math.exp(-S.CAMERA_DAMPING * dt) if dt > 0 else 0.0
        self.cam_x += (tx - self.cam_x) * k
        self.cam_z += (tz - self.cam_z) * k
        self.cam_x, self.cam_z = self._clamp_cam(self.cam_x, self.cam_z)
        sx, sz = self.shake.offset(dt)
        self.base.camera.setPos(self.cam_x + sx, S.CAMERA_Y, self.cam_z + sz)
        # Day and night: the clock runs while you play (not while paused or dead).
        dn = g.daynight
        if self.state == "play":
            dn.update(dt)
        g.apply_daylight(dn)
        _, h = g.view_size()
        self.backdrop.update(self.t, self.cam_x, self.cam_z, h, dn)
        n = dn.night
        self.lantern.node().setColor(tuple(c * (0.1 + 1.1 * n) for c in S.LANTERN_COLOR[:3]) + (1,))
        sand = dn.sand()
        for gl in self.glasses:
            gl.sand.set_color(sand)
        for s in self.shrines:
            s.sand.set_color(sand)
        self.hud.sand.set_color(sand)

        # Visuals
        self.view.update(dt, self.player)
        for p in self.pickups:
            p.update(dt, self.t)
        for s in self.shrines:
            s.update(dt, self.t)
        for gate in self.gates:
            gate.update(dt)
        for ex in self.exits:
            ex.update(dt, self.t, ex.requires_no_debt and self.debt.in_debt)
        near_sign = min(
            (s for s in self.signs if abs(s.x - b.x) < 4.5 and abs(s.z - b.z) < 6),
            key=lambda s: abs(s.x - b.x),
            default=None,
        )
        for sign in self.signs:
            sign.update(dt, sign is near_sign)
        if self.state == "play":
            if self.borrowing:
                self.particles.emit_toward(
                    self.cam_x - 12, self.cam_z + 6, b.x, b.z + 0.5, 2, S.DEBT_RED
                )
                self.particles.emit_toward(b.x, b.z + 1.8, b.x, b.z + 0.5, 1, sand)
            if self.pouring:
                shrine = next(s for s in self.shrines if s.pouring)
                self.particles.emit_toward(b.x, b.z + 0.6, shrine.x, shrine.z + 1.6, 2)
        self.particles.update(dt)

        # Audio loops follow held actions; the debt layer follows the debt.
        playing = self.state == "play"
        loop = self.audio.start_loop if (self.borrowing and playing) else self.audio.stop_loop
        loop("borrow_loop")
        loop = self.audio.start_loop if (self.pouring and playing) else self.audio.stop_loop
        loop("shrine_pour_loop")
        debt_frac = self.debt.total / self.debt.cap
        self.audio.set_layer_volume("level_debt", debt_frac)
        self.tint.setAlphaScale(debt_frac * S.DEBT_TINT_MAX_ALPHA)

        # Low on time: everything turns red, pulsing faster as the sand runs out.
        low = 0.0
        if self.state == "play":
            low = max(0.0, min(1.0, (S.LOW_TIME - self.life.top) / (S.LOW_TIME - 3.0)))
        pulse = 0.7 + 0.3 * math.sin(self.t * (4 + 6 * low))
        self.low_tint.setAlphaScale(low * S.LOW_TIME_MAX_ALPHA * pulse)
        self.world.setColorScale(1, 1 - 0.35 * low, 1 - 0.35 * low, 1)
        if self.state == "play" and self.life.top < S.LOW_TIME and not self.low_time_warned:
            self.low_time_warned = True
            if self.data.allow_borrow:
                self.hud.show_message("Time is running out! Hold SHIFT to borrow time.", 4.0)
            else:
                self.hud.show_message("Time is running out! Grab golden sand.", 4.0)
        elif self.life.top > S.LOW_TIME + 3:
            self.low_time_warned = False

        # Contextual prompt
        label, anchor = "", None
        if self.state == "play":
            target = self._interact_target()
            if isinstance(target, PedestalGlass):
                label, anchor = "[E] Flip", target
            elif isinstance(target, TimerLock):
                label = "[E] Stop" if target.logic.running else "[E] Start"
                anchor = target
            else:
                for s in self.shrines:
                    if s.near(b.x, b.z) and self.debt.in_debt:
                        label, anchor = "Hold [E] to repay", s
        if anchor is not None:
            self.prompt.node().setText(label)
            self.prompt.setPos(anchor.x, -3, anchor.z + 3.3)
            self.prompt.show()
        else:
            self.prompt.hide()

        guide = self._active_guide() if self.state == "play" else None
        if guide is None:
            self.hud.set_guide(None, [], 0)
        else:
            lock, progress = guide
            self.hud.set_guide(lock.title, [st["text"] for st in lock.guide], progress[0])

        self.hud.set_muted(self.audio.muted)
        self.hud.update(dt, self.t, self.life, self.debt, self.borrowing)
