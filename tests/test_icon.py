import os
import sys

from game.icon import icon_path, make_icon_image


def test_icon_is_an_opaque_rounded_square():
    img = make_icon_image(64)
    assert img.getXSize() == img.getYSize() == 64
    assert img.getAlpha(0, 0) == 0  # rounded corner is transparent
    assert img.getAlpha(32, 32) == 1


def test_icon_file_is_written():
    path = icon_path()
    # Windows only accepts .ico window icons; everywhere else gets a .png.
    expected = ".ico" if sys.platform == "win32" else ".png"
    assert path is not None and path.endswith(expected)
    assert os.path.isfile(path)


def test_windows_ico_wraps_the_png(tmp_path):
    import struct

    from panda3d.core import Filename

    from game.icon import _png_to_ico

    png, ico = tmp_path / "i.png", tmp_path / "i.ico"
    make_icon_image(64).write(Filename.fromOsSpecific(str(png)))
    _png_to_ico(str(png), str(ico), 64)
    data = ico.read_bytes()
    reserved, kind, count = struct.unpack("<HHH", data[:6])
    assert (reserved, kind, count) == (0, 1, 1)
    assert data[22:30] == b"\x89PNG\r\n\x1a\n"  # the PNG follows the 6 + 16 byte header
