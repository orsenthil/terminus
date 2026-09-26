import pytest
from panda3d.core import loadPrcFileData


@pytest.fixture(scope="session")
def headless_base():
    """One windowless ShowBase for the whole session (ShowBase can only exist once)."""
    loadPrcFileData("", "window-type none")
    loadPrcFileData("", "audio-library-name null")
    from direct.showbase.ShowBase import ShowBase

    base = ShowBase()
    if base.camera is None:  # no window, no default camera: give scenes something to move
        base.camera = base.render.attachNewNode("camera")
    # Deterministic 60 fps clock so fades and physics advance per taskMgr.step().
    from panda3d.core import ClockObject

    clock = ClockObject.getGlobalClock()
    clock.setMode(ClockObject.MNonRealTime)
    clock.setFrameRate(60)
    yield base
    base.destroy()
