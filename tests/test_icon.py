from game.icon import icon_path, make_icon_image


def test_icon_is_an_opaque_rounded_square():
    img = make_icon_image(64)
    assert img.getXSize() == img.getYSize() == 64
    assert img.getAlpha(0, 0) == 0  # rounded corner is transparent
    assert img.getAlpha(32, 32) == 1


def test_icon_file_is_written():
    path = icon_path()
    assert path is not None and path.endswith(".png")
