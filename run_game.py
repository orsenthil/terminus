"""Terminus (PyWeek). Start with `uv run run_game.py` or `python run_game.py`."""

import sys

MIN_PYTHON = (3, 10)

if sys.version_info < MIN_PYTHON:
    sys.exit(
        f"Terminus needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer "
        f"(you have {sys.version.split()[0]})."
    )

try:
    import panda3d  # noqa: F401
except ImportError:
    sys.exit(
        "Panda3D is not installed.\n"
        "Run `uv sync` then `uv run run_game.py`, or `pip install -r requirements.txt`."
    )

from game.main import main  # noqa: E402

if __name__ == "__main__":
    main()
