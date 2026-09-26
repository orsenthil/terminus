"""ShowBase app: window setup, the single update task, and scene switching with fades."""

import os
import sys

from direct.gui import DirectGuiGlobals as DGG
from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    AmbientLight,
    ButtonRegistry,
    ClockObject,
    DirectionalLight,
    Filename,
    ModifierButtons,
    OrthographicLens,
    SamplerState,
    TextNode,
    loadPrcFileData,
)

from game import settings as S
from game.audio import AudioManager
from game.daynight import DayNight
from game.icon import icon_path
from game.render_util import make_card
from game.scenes import TitleScene


def configure(extra=""):
    icon = icon_path()
    if icon is not None:
        # Our own hourglass instead of the generic (white) Python / Panda3D icon.
        loadPrcFileData("", f"icon-filename {Filename.fromOsSpecific(icon).getFullpath()}")
    loadPrcFileData(
        "",
        f"""
        window-title {S.WINDOW_TITLE}
        win-size {S.WINDOW_SIZE[0]} {S.WINDOW_SIZE[1]}
        sync-video true
        show-frame-rate-meter {"true" if S.DEBUG else "false"}
        framebuffer-multisample 1
        multisamples 4
        notify-level-audio error
        {extra}
        """,
    )


def load_game_font(base):
    """Make Julius Sans One the default font for every TextNode, OnscreenText and DirectGUI
    widget. Falls back to Panda3D's built-in font if the file is missing."""
    if not os.path.isfile(S.FONT_PATH):
        print(f"[font] missing {S.FONT_PATH}, using the default font")
        return None
    font = base.loader.loadFont(Filename.fromOsSpecific(S.FONT_PATH).getFullpath())
    if font is None or not font.isValid():
        return None
    # Render glyphs large, then let mipmaps shrink them smoothly: thin strokes no longer
    # break up into gaps at small sizes.
    font.setPixelsPerUnit(120)
    font.setPageSize(1024, 1024)
    font.setMinfilter(SamplerState.FT_linear_mipmap_linear)
    font.setMagfilter(SamplerState.FT_linear)
    font.setAnisotropicDegree(4)
    # Bold: an outline in the glyph's own colour (white, tinted per text) thickens every
    # stroke. Contrast on a bright sky comes from each text's drop shadow instead.
    font.setOutline((1, 1, 1, 1), S.FONT_BOLDNESS, 0.15)
    TextNode.setDefaultFont(font)
    DGG.setDefaultFont(font)
    return font


class Game:
    """Owns the ShowBase instance, the camera lens, audio, run stats and the active scene."""

    def __init__(self, base):
        self.base = base
        base.disableMouse()
        # Without this, holding Shift turns "space" into "shift-space" and jumps get lost.
        if base.mouseWatcherNode is not None:  # None when running headless
            base.mouseWatcherNode.setModifierButtons(ModifierButtons())
            base.buttonThrowers[0].node().setModifierButtons(ModifierButtons())

        self.lens = OrthographicLens()
        self.lens.setNearFar(1, 400)
        self.aspect = None
        self._update_lens()
        if base.cam is not None:  # None when running windowless (tests)
            base.cam.node().setLens(self.lens)

        amb = AmbientLight("ambient")
        amb.setColor((0.5, 0.47, 0.55, 1))
        dl = DirectionalLight("sun")
        dl.setColor((0.75, 0.68, 0.55, 1))
        self.lights = [base.render.attachNewNode(amb), base.render.attachNewNode(dl)]
        self.lights[1].setHpr(25, -40, 0)
        for light in self.lights:
            base.render.setLight(light)
        self.daynight = DayNight()  # one clock for the whole run, so it carries across levels
        self.apply_daylight(self.daynight)

        self.fade_card = make_card(-1, -1, 1, 1, (0, 0, 0, 1), "fade")
        self.fade_card.reparentTo(base.render2d)
        self.fade_card.setBin("gui-popup", 100)
        self.fade = 1.0
        self.fade_dir = -1  # fading in
        self.pending = None

        self.font = load_game_font(base)
        self.audio = AudioManager(base)
        self.stats = {"borrowed": 0.0, "interest_paid": 0.0, "deaths": 0}
        self.buttons = {
            action: [ButtonRegistry.ptr().findButton(n) for n in names]
            for action, names in S.KEYS.items()
        }
        self.globals = DirectObject()
        for key in S.KEYS["mute"]:
            self.globals.accept(key, self.audio.toggle_mute)

        self.scene = None
        self.accumulator = 0.0
        self.time = 0.0
        base.taskMgr.add(self._task, "terminus-main")

    def apply_daylight(self, daynight):
        """Sky colour and world lighting for the current point in the day / night cycle."""
        self.base.setBackgroundColor(*daynight.sky())
        self.lights[0].node().setColor(daynight.ambient())
        self.lights[1].node().setColor(daynight.sun())

    # --- input -----------------------------------------------------------------------
    def held(self, action):
        mw = self.base.mouseWatcherNode
        if mw is None:
            return False
        return any(b is not None and mw.isButtonDown(b) for b in self.buttons[action])

    # --- camera ----------------------------------------------------------------------
    def _update_lens(self):
        win = self.base.win
        aspect = 16 / 9
        if win is not None and win.getYSize() > 0:
            aspect = win.getXSize() / win.getYSize()
        if aspect != self.aspect:
            self.aspect = aspect
            self.lens.setFilmSize(S.VIEW_WIDTH_TILES, S.VIEW_WIDTH_TILES / aspect)

    def view_size(self):
        return S.VIEW_WIDTH_TILES, S.VIEW_WIDTH_TILES / self.aspect

    # --- scenes ----------------------------------------------------------------------
    def start(self, scene):
        self.scene = scene
        scene.enter()

    def change_scene(self, factory):
        """Fade out, exit the current scene, build the next with factory(), fade in."""
        if self.pending is not None:
            return
        self.pending = factory
        self.fade_dir = 1
        if self.scene is not None:
            self.scene.suspend()

    def _swap(self):
        factory, self.pending = self.pending, None
        if self.scene is not None:
            self.scene.exit()
        self.scene = None
        self.accumulator = 0.0
        self.audio.stop_all_loops()
        scene = factory()
        if scene is None:
            self.quit()
            return
        self.scene = scene
        scene.enter()
        self.fade_dir = -1

    def quit(self):
        if self.scene is not None:
            self.scene.exit()
            self.scene = None
        self.base.userExit()

    # --- the one task ----------------------------------------------------------------
    def _task(self, task):
        dt = min(ClockObject.getGlobalClock().getDt(), S.MAX_FRAME_DT)
        self.time += dt
        self._update_lens()
        self.audio.update(dt)

        if self.fade_dir != 0:
            self.fade += self.fade_dir * dt / S.FADE_TIME
            if self.fade >= 1.0 and self.fade_dir > 0:
                self.fade = 1.0
                if self.pending is not None:
                    self._swap()
            elif self.fade <= 0.0 and self.fade_dir < 0:
                self.fade = 0.0
                self.fade_dir = 0
            self.fade_card.setAlphaScale(max(0.0, min(1.0, self.fade)))
            self.fade_card.show() if self.fade > 0 else self.fade_card.hide()

        scene = self.scene
        if scene is not None and self.pending is None:
            self.accumulator += dt
            while self.accumulator >= S.PHYSICS_STEP and self.scene is scene:
                scene.fixed_update(S.PHYSICS_STEP)
                self.accumulator -= S.PHYSICS_STEP
            if self.scene is scene:
                scene.update(dt)
        return Task.cont


def main(extra_config=""):
    configure(extra_config)
    base = ShowBase()
    game = Game(base)
    game.start(TitleScene(game))
    base.run()
    sys.exit(0)


if __name__ == "__main__":
    main()
