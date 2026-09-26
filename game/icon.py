"""The window / dock icon: an hourglass drawn in code with PNMImage (no image assets)."""

import os
import struct
import sys
import tempfile

from panda3d.core import Filename, PNMImage

from game import settings as S

ICON_SIZE = 256


def _inside_rounded_square(x, y, size, radius):
    cx = min(max(x, radius), size - 1 - radius)
    cy = min(max(y, radius), size - 1 - radius)
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius**2


def make_icon_image(size=ICON_SIZE):
    """Night-blue rounded square with a water clock: blue water above, purple (night) below."""
    img = PNMImage(size, size, 4)
    img.fill(0, 0, 0)
    img.alphaFill(0)
    u = size / 256.0  # design at 256 px, scale for other sizes
    radius = 48 * u
    sky_top, sky_bottom = (0.16, 0.12, 0.36), (0.04, 0.03, 0.12)
    wood, glass = (0.42, 0.45, 0.52), (0.22, 0.27, 0.42)
    water, purple = S.WATER_DAY[:3], S.WATER_NIGHT[:3]
    cx = size / 2
    top, bottom = 58 * u, 198 * u  # inner glass extent
    mid = (top + bottom) / 2
    half_w = 62 * u
    for y in range(size):
        for x in range(size):
            if not _inside_rounded_square(x, y, size, radius):
                continue
            k = y / (size - 1)
            color = tuple(a + (b - a) * k for a, b in zip(sky_top, sky_bottom, strict=True))
            # Wooden caps and side posts.
            if (top - 22 * u <= y < top or bottom < y <= bottom + 22 * u) and abs(
                x - cx
            ) <= half_w + 18 * u:
                color = wood
            elif top <= y <= bottom and half_w + 6 * u <= abs(x - cx) <= half_w + 16 * u:
                color = wood
            elif top <= y <= bottom:
                # Hourglass bulbs: width shrinks linearly toward the neck.
                w = half_w * abs(y - mid) / (mid - top) + 5 * u
                if abs(x - cx) <= w:
                    color = glass
                    if top + 44 * u <= y < mid:
                        color = water  # the water still to fall
                    elif y > mid and y >= bottom - 46 * u:
                        color = purple  # the water already spent
                    elif y >= mid - 2 * u and abs(x - cx) <= 3 * u:
                        color = water  # the falling stream
            img.setXelA(x, y, color[0], color[1], color[2], 1.0)
    return img


def _png_to_ico(png_path, ico_path, size=ICON_SIZE):
    """Wrap a PNG in a single-image .ico container (Windows only accepts .ico icons)."""
    with open(png_path, "rb") as f:
        png = f.read()
    dim = 0 if size >= 256 else size  # 0 means 256 in the ICO directory
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), 6 + 16)
    with open(ico_path, "wb") as f:
        f.write(header + entry + png)


def icon_path():
    """Write the icon to the temp directory (every launch, so it never goes stale).
    Returns a .png path, or a .ico path on Windows."""
    base = os.path.join(tempfile.gettempdir(), "terminus_icon")
    try:
        make_icon_image().write(Filename.fromOsSpecific(base + ".png"))
        if sys.platform == "win32":
            _png_to_ico(base + ".png", base + ".ico")
            return base + ".ico"
    except OSError:
        return None
    return base + ".png"
