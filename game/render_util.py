"""Procedural geometry helpers: boxes, cards, triangles, frusta and text.

Everything is built in the XZ plane (X right, Z up) with Y as depth, which works both in
the 3D world and on render2d/aspect2d.
"""

import math

from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
    TextNode,
    TransparencyAttrib,
    Vec3,
)

from game import settings as S


class MeshBuilder:
    """Accumulates coloured, lit triangles into a single Geom."""

    def __init__(self, name="mesh"):
        self.name = name
        self.vdata = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
        self.vw = GeomVertexWriter(self.vdata, "vertex")
        self.nw = GeomVertexWriter(self.vdata, "normal")
        self.cw = GeomVertexWriter(self.vdata, "color")
        self.prim = GeomTriangles(Geom.UHStatic)
        self.count = 0

    def tri(self, a, b, c, color, normal=None):
        a, b, c = Vec3(*a), Vec3(*b), Vec3(*c)
        face = (b - a).cross(c - a)
        if normal is not None:
            normal = Vec3(*normal)
            if face.dot(normal) < 0:
                b, c = c, b
        else:
            normal = face
        if normal.length_squared() > 0:
            normal.normalize()
        for p in (a, b, c):
            self.vw.addData3(p)
            self.nw.addData3(normal)
            self.cw.addData4(*color)
        self.prim.addVertices(self.count, self.count + 1, self.count + 2)
        self.count += 3

    def quad(self, a, b, c, d, color, normal=None):
        self.tri(a, b, c, color, normal)
        self.tri(a, c, d, color, normal)

    def box(self, x0, y0, z0, x1, y1, z1, color, top_color=None, back=False):
        top_color = top_color or color
        side = tuple(min(1.0, ch * 0.85) for ch in color[:3]) + (color[3],)
        bottom = tuple(ch * 0.6 for ch in color[:3]) + (color[3],)
        self.quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), color, (0, -1, 0))
        self.quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), top_color, (0, 0, 1))
        self.quad((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), bottom, (0, 0, -1))
        self.quad((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1), side, (-1, 0, 0))
        self.quad((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), side, (1, 0, 0))
        if back:
            self.quad((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1), side, (0, 1, 0))

    def rect(self, x0, z0, x1, z1, color, y=0.0):
        self.quad((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1), color, (0, -1, 0))

    def flat_tri(self, p0, p1, p2, color, y=0.0):
        """Triangle in the XZ plane from (x, z) points, facing the camera (-Y)."""
        self.tri((p0[0], y, p0[1]), (p1[0], y, p1[1]), (p2[0], y, p2[1]), color, (0, -1, 0))

    def frustum(self, r0, r1, z0, z1, color, segments=24, cx=0.0, cy=0.0):
        """Open-ended cone section around the Z axis (radius r0 at z0, r1 at z1)."""
        for i in range(segments):
            a0 = 2 * math.pi * i / segments
            a1 = 2 * math.pi * (i + 1) / segments
            p00 = (cx + r0 * math.cos(a0), cy + r0 * math.sin(a0), z0)
            p01 = (cx + r0 * math.cos(a1), cy + r0 * math.sin(a1), z0)
            p10 = (cx + r1 * math.cos(a0), cy + r1 * math.sin(a0), z1)
            p11 = (cx + r1 * math.cos(a1), cy + r1 * math.sin(a1), z1)
            mid = (a0 + a1) / 2
            slope = (r0 - r1) / max(1e-6, (z1 - z0))
            normal = (math.cos(mid), math.sin(mid), slope)
            self.quad(p00, p01, p11, p10, color, normal)

    def disc(self, r, z, color, segments=24, up=True, cx=0.0, cy=0.0):
        normal = (0, 0, 1 if up else -1)
        for i in range(segments):
            a0 = 2 * math.pi * i / segments
            a1 = 2 * math.pi * (i + 1) / segments
            self.tri(
                (cx, cy, z),
                (cx + r * math.cos(a0), cy + r * math.sin(a0), z),
                (cx + r * math.cos(a1), cy + r * math.sin(a1), z),
                color,
                normal,
            )

    def node(self):
        geom = Geom(self.vdata)
        geom.addPrimitive(self.prim)
        gnode = GeomNode(self.name)
        gnode.addGeom(geom)
        return NodePath(gnode)


def _finish(np, color):
    if len(color) > 3 and color[3] < 1.0:
        np.setTransparency(TransparencyAttrib.MAlpha)
    return np


def make_box(x0, y0, z0, x1, y1, z1, color, top_color=None, name="box"):
    mb = MeshBuilder(name)
    mb.box(x0, y0, z0, x1, y1, z1, color, top_color)
    return _finish(mb.node(), color)


def make_card(x0, z0, x1, z1, color, name="card", y=0.0):
    mb = MeshBuilder(name)
    mb.rect(x0, z0, x1, z1, color, y)
    np = mb.node()
    np.setTwoSided(True)
    return _finish(np, color)


def make_triangle(p0, p1, p2, color, name="tri", y=0.0):
    mb = MeshBuilder(name)
    mb.flat_tri(p0, p1, p2, color, y)
    np = mb.node()
    np.setTwoSided(True)
    return _finish(np, color)


def make_ring(radius, thickness, color, segments=24, name="ring"):
    """A flat annulus in the XZ plane, split into `segments` separate child nodes."""
    root = NodePath(name)
    parts = []
    for i in range(segments):
        a0 = 2 * math.pi * i / segments + math.pi / 2
        a1 = 2 * math.pi * (i + 0.8) / segments + math.pi / 2
        r0, r1 = radius - thickness, radius
        mb = MeshBuilder(f"{name}{i}")
        mb.quad(
            (r0 * math.cos(a0), 0, r0 * math.sin(a0)),
            (r1 * math.cos(a0), 0, r1 * math.sin(a0)),
            (r1 * math.cos(a1), 0, r1 * math.sin(a1)),
            (r0 * math.cos(a1), 0, r0 * math.sin(a1)),
            color,
            (0, -1, 0),
        )
        np = mb.node()
        np.setTwoSided(True)
        np.reparentTo(root)
        parts.append(np)
    return root, parts


def make_hourglass_3d(height=2.0, radius=0.7, water_color=(0.45, 0.8, 1.0, 1), name="hourglass"):
    """A lit 3D water clock: dark metal caps and posts, glass bulbs, and water that lies
    flat in each bulb with a thin stream through the neck."""
    metal = (0.3, 0.32, 0.38, 1)
    glass = (0.7, 0.85, 1.0, 0.35)
    h = height / 2
    root = NodePath(name)
    frame = MeshBuilder(name + "_frame")
    for z0, z1 in ((-h - 0.15, -h), (h, h + 0.15)):
        frame.frustum(radius * 1.25, radius * 1.25, z0, z1, metal)
        frame.disc(radius * 1.25, z1, metal, up=True)
        frame.disc(radius * 1.25, z0, metal, up=False)
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.3
        px, py = radius * 1.05 * math.cos(a), radius * 1.05 * math.sin(a)
        frame.box(px - 0.05, py - 0.05, -h, px + 0.05, py + 0.05, h, metal)
    frame.node().reparentTo(root)

    def bulb_radius(z):  # radius of the glass at height z (neck at z=0)
        return 0.08 + (radius - 0.08) * abs(z) / h

    water = MeshBuilder(name + "_water")
    low = -h + h * 0.4  # water level in the lower bulb
    water.frustum(bulb_radius(-h) * 0.95, bulb_radius(low) * 0.95, -h, low, water_color)
    water.disc(bulb_radius(low) * 0.95, low, water_color)
    high = h * 0.5  # water level in the upper bulb
    water.frustum(0.07, bulb_radius(high) * 0.95, 0.02, high, water_color)
    water.disc(bulb_radius(high) * 0.95, high, water_color)
    water.frustum(0.02, 0.02, low, 0.02, water_color, segments=6)
    water.node().reparentTo(root)
    bulbs = MeshBuilder(name + "_glass")
    bulbs.frustum(radius, 0.08, -h, 0, glass)
    bulbs.frustum(0.08, radius, 0, h, glass)
    gnp = bulbs.node()
    gnp.setTransparency(TransparencyAttrib.MAlpha)
    gnp.setTwoSided(True)
    gnp.setDepthWrite(False)
    gnp.setBin("transparent", 10)
    gnp.reparentTo(root)
    return root


def wide(scale):
    """Text scale stretched horizontally by TEXT_WIDTH, for OnscreenText."""
    return (scale * S.TEXT_WIDTH, scale)


def make_text(
    parent, text, pos=(0, 0, 0), scale=0.5, color=(1, 1, 1, 1), align="center", card=None
):
    tn = TextNode("text")
    tn.setText(text)
    tn.setAlign(
        {"center": TextNode.ACenter, "left": TextNode.ALeft, "right": TextNode.ARight}[align]
    )
    tn.setTextColor(*color)
    tn.setShadow(0.05, 0.05)
    tn.setShadowColor(0, 0, 0, 0.8)
    if card is not None:
        tn.setCardColor(*card)
        tn.setCardAsMargin(0.4, 0.4, 0.25, 0.2)
        tn.setCardDecal(True)
    np = parent.attachNewNode(tn)
    np.setPos(*pos)
    np.setScale(scale * S.TEXT_WIDTH, 1, scale)
    np.setLightOff()
    np.setTransparency(TransparencyAttrib.MAlpha)
    # World text floats above everything; no depth so glyphs and shadow never z-fight.
    np.setDepthTest(False)
    np.setDepthWrite(False)
    np.setBin("fixed", 50)
    return np
