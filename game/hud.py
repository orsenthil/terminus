"""HUD on aspect2d: life water clock, debt meter with interest ring, mute icon, messages."""

import math

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib

from game import settings as S
from game.objects import WaterDisplay
from game.render_util import MeshBuilder, make_card, make_ring, wide


class HUD:
    def __init__(self, base, show_debt=True):
        self.base = base
        self.nodes = []
        self.show_debt = show_debt

        # --- life hourglass (top-left) ---
        self.glass_root = base.a2dTopLeft.attachNewNode("hud_glass")
        self.glass_root.setPos(0.2, 0, -0.33)
        self.nodes.append(self.glass_root)
        w, h = 0.12, 0.2
        mb = MeshBuilder("hud_glass")
        mb.flat_tri((-w, h), (w, h), (0, 0), (0.25, 0.3, 0.45, 0.8))
        mb.flat_tri((-w, -h), (0, 0), (w, -h), (0.25, 0.3, 0.45, 0.8))
        wood = (0.42, 0.46, 0.56, 1)  # dark metal frame
        mb.rect(-w - 0.03, h, w + 0.03, h + 0.035, wood)
        mb.rect(-w - 0.03, -h - 0.035, w + 0.03, -h, wood)
        mb.rect(-w - 0.03, -h, -w - 0.015, h, wood)
        mb.rect(w + 0.015, -h, w + 0.03, h, wood)
        bg = mb.node()
        bg.setTransparency(TransparencyAttrib.MAlpha)
        bg.setTwoSided(True)
        bg.reparentTo(self.glass_root)
        self.water = WaterDisplay(self.glass_root, w * 0.9, h * 0.92, S.WATER_DAY, y=-0.01)
        self.warn = 0.0

        # --- debt meter ---
        self.debt_root = base.a2dTopLeft.attachNewNode("hud_debt")
        self.debt_root.setPos(0.42, 0, -0.22)
        self.nodes.append(self.debt_root)
        self.bar_w = 0.62
        make_card(0, -0.03, self.bar_w, 0.03, (0.1, 0.05, 0.08, 0.8)).reparentTo(self.debt_root)
        self.bar_principal = make_card(0, -0.025, 1, 0.025, (0.6, 0.08, 0.08, 1))
        self.bar_principal.reparentTo(self.debt_root)
        self.bar_interest = make_card(0, -0.025, 1, 0.025, (1.0, 0.45, 0.1, 1))
        self.bar_interest.reparentTo(self.debt_root)
        self.debt_label = OnscreenText(
            text="DEBT",
            parent=self.debt_root,
            pos=(0, 0.05),
            scale=wide(0.052),
            fg=S.TEXT_COLOR,
            align=TextNode.ALeft,
            shadow=(0, 0, 0, 0.8),
            mayChange=True,
        )
        self.debt_text = OnscreenText(
            text="",
            parent=self.debt_root,
            pos=(0, -0.09),
            scale=wide(0.05),
            fg=S.TEXT_COLOR,
            align=TextNode.ALeft,
            shadow=(0, 0, 0, 0.8),
            mayChange=True,
        )
        self.ring_root, self.ring = make_ring(0.045, 0.014, (1.0, 0.55, 0.2, 1), 24, "hud_ring")
        self.ring_root.reparentTo(self.debt_root)
        self.ring_root.setPos(self.bar_w + 0.08, 0, 0)
        self.pops = []
        self.flash = 0.0
        if not show_debt:
            self.debt_root.hide()

        # --- mute icon (top-right) ---
        self.speaker = base.a2dTopRight.attachNewNode("hud_speaker")
        self.speaker.setPos(-0.12, 0, -0.1)
        self.nodes.append(self.speaker)
        mb = MeshBuilder("speaker")
        c = S.TEXT_COLOR
        mb.rect(-0.04, -0.018, -0.015, 0.018, c)
        mb.flat_tri((-0.015, 0.0), (0.02, -0.04), (0.02, 0.04), c)
        mb.quad((-0.015, 0, -0.018), (0.02, 0, -0.04), (0.02, 0, 0.04), (-0.015, 0, 0.018), c)
        icon = mb.node()
        icon.setTwoSided(True)
        icon.reparentTo(self.speaker)
        mb = MeshBuilder("waves")
        for i, r in enumerate((0.035, 0.055)):
            mb.rect(0.02 + r, -0.012 - i * 0.01, 0.028 + r, 0.012 + i * 0.01, c)
        self.waves = mb.node()
        self.waves.setTwoSided(True)
        self.waves.reparentTo(self.speaker)
        mb = MeshBuilder("cross")
        red = S.DEBT_RED
        mb.quad((0.035, 0, -0.03), (0.045, 0, -0.03), (0.085, 0, 0.03), (0.075, 0, 0.03), red)
        mb.quad((0.075, 0, -0.03), (0.085, 0, -0.03), (0.045, 0, 0.03), (0.035, 0, 0.03), red)
        self.cross = mb.node()
        self.cross.setTwoSided(True)
        self.cross.reparentTo(self.speaker)
        self.set_muted(False)

        self.level_text = OnscreenText(
            text="",
            parent=base.a2dTopRight,
            pos=(-0.22, -0.115),
            scale=wide(0.052),
            fg=S.TEXT_COLOR,
            align=TextNode.ARight,
            shadow=(0, 0, 0, 0.8),
            mayChange=True,
        )
        self.message = OnscreenText(
            text="",
            parent=base.a2dBottomCenter,
            pos=(0, 0.14),
            scale=wide(0.06),
            fg=S.TEXT_COLOR,
            shadow=(0, 0, 0, 0.9),
            mayChange=True,
        )
        self.message_time = 0.0
        self.texts = [self.debt_label, self.debt_text, self.level_text, self.message]

        # Step-by-step guide panel (top centre) for puzzles such as timer locks.
        self.guide_root = base.a2dTopCenter.attachNewNode("hud_guide")
        # Sits between the debt meter (left) and the level name (right).
        self.guide_root.setPos(0.16, 0, -0.1)
        self.nodes.append(self.guide_root)
        self.guide_half_w = 0.82
        self.guide_bg = make_card(
            -self.guide_half_w, -0.1, self.guide_half_w, 0.02, (0.05, 0.03, 0.08, 0.8)
        )
        self.guide_bg.reparentTo(self.guide_root)
        self.guide_lines = []
        self.guide_key = None
        self.guide_root.hide()

    def set_level_name(self, name):
        self.level_text.setText(name)

    def set_muted(self, muted):
        if muted:
            self.waves.hide()
            self.cross.show()
        else:
            self.waves.show()
            self.cross.hide()

    def set_guide(self, title, steps, current, footer=""):
        """Show a puzzle panel: the title, then (optionally) numbered steps with `current`
        highlighted, then a footer line. title=None hides the panel."""
        key = (title, tuple(steps), current, footer)
        if key == self.guide_key:
            return
        self.guide_key = key
        for line in self.guide_lines:
            line.destroy()
        self.guide_lines = []
        if title is None:
            self.guide_root.hide()
            return
        self.guide_root.show()
        rows = [(title, S.GOLD, 0.05)]
        for i, step in enumerate(steps):
            if i < current:
                rows.append((f"{i + 1}. {step}   (done)", (0.6, 0.6, 0.6, 1), 0.046))
            elif i == current:
                rows.append((f">> {i + 1}. {step}", (1.0, 0.95, 0.6, 1), 0.046))
            else:
                rows.append((f"{i + 1}. {step}", S.TEXT_COLOR, 0.046))
        if footer:
            rows.append((footer, (0.75, 0.75, 0.85, 1), 0.044))
        # Each line wraps to the panel's width, so long hints never spill out of it.
        inner = 2 * self.guide_half_w - 0.08
        z = -0.04
        for text, color, scale in rows:
            line = OnscreenText(
                text=text,
                parent=self.guide_root,
                pos=(-self.guide_half_w + 0.04, z),
                scale=wide(scale),
                fg=color,
                align=TextNode.ALeft,
                shadow=(0, 0, 0, 0.9),
                wordwrap=inner / (scale * S.TEXT_WIDTH),
            )
            self.guide_lines.append(line)
            z -= 0.072 + 0.06 * (line.textNode.getNumRows() - 1)
        height = -z + 0.02
        self.guide_bg.setSz(height / 0.12)
        self.guide_bg.setZ(0.02 - 0.02 * height / 0.12)

    def show_message(self, text, seconds=2.5):
        self.message.setText(text)
        self.message_time = seconds

    def interest_pop(self):
        pop = OnscreenText(
            text="+10%",
            parent=self.debt_root,
            pos=(self.bar_w - 0.05, 0.05),
            scale=wide(0.06),
            fg=(1.0, 0.4, 0.2, 1),
            shadow=(0, 0, 0, 0.9),
            mayChange=True,
        )
        self.pops.append([pop, 1.2])

    def update(self, dt, t, life, debt, borrowing):
        total = life.top + life.bottom
        top_frac = life.top / total if total > 0 else 0.0
        self.water.set_fill(top_frac, 1.0 - top_frac if total > 0 else 0.0, not life.empty)
        if life.top < 10.0 and not life.empty:
            p = 0.5 + 0.5 * math.sin(t * (10 if life.top < 5 else 6))
            self.glass_root.setColorScale(1.0, 0.6 + 0.4 * p, 0.6 + 0.4 * p, 1)
        else:
            self.glass_root.setColorScale(1, 1, 1, 1)
        wobble = 0.03 * math.sin(t * 30) if borrowing else 0.0
        self.glass_root.setR(wobble * 57)

        if self.show_debt or debt.in_debt:
            self.debt_root.show()
            cap = debt.cap
            pw = self.bar_w * min(1.0, debt.principal / cap)
            iw = self.bar_w * min(1.0, debt.interest / cap)
            self.bar_principal.setScale(max(pw, 1e-4), 1, 1)
            self.bar_interest.setScale(max(iw, 1e-4), 1, 1)
            self.bar_interest.setX(pw)
            if debt.in_debt:
                self.debt_text.setText(f"{debt.principal:.1f}s + {debt.interest:.1f}s interest")
            else:
                self.debt_text.setText("nothing owed")
            frac = debt.time_to_tick / debt.period if debt.in_debt else 0.0
            lit = int(math.ceil(frac * len(self.ring)))
            for i, seg in enumerate(self.ring):
                seg.show() if i < lit else seg.hide()
            if debt.at_cap:
                self.flash += dt
                on = int(self.flash * 6) % 2 == 0
                self.debt_label.setText("DEBT  -  LIMIT REACHED" if on else "DEBT")
                self.debt_label.setFg((1, 0.3, 0.2, 1) if on else S.TEXT_COLOR)
            else:
                self.flash = 0.0
                self.debt_label.setText("DEBT")
                self.debt_label.setFg(S.TEXT_COLOR)

        for pop in self.pops:
            pop[1] -= dt
            pop[0].setZ(0.05 + (1.2 - pop[1]) * 0.08)
            pop[0].setAlphaScale(max(0.0, min(1.0, pop[1])))
        for pop in [p for p in self.pops if p[1] <= 0]:
            pop[0].destroy()
            self.pops.remove(pop)

        if self.message_time > 0:
            self.message_time -= dt
            self.message.setAlphaScale(max(0.0, min(1.0, self.message_time * 2)))
            if self.message_time <= 0:
                self.message.setText("")

    def destroy(self):
        for line in self.guide_lines:
            line.destroy()
        self.guide_lines = []
        for pop in self.pops:
            pop[0].destroy()
        self.pops = []
        for t in self.texts:
            t.destroy()
        for n in self.nodes:
            n.removeNode()
