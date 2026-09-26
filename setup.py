"""Standalone builds of Terminus for Windows, macOS and Linux, using Panda3D's build_apps.

    uv run --group build python setup.py bdist_apps

Writes one archive per platform into dist/. Players unzip it and run Terminus; no Python
needed. (Name, version and dependencies come from pyproject.toml.)
"""

from setuptools import setup

setup(
    packages=[],
    py_modules=[],
    options={
        "build_apps": {
            "gui_apps": {"Terminus": "run_game.py"},
            "include_modules": ["game.*"],
            "include_patterns": [
                "assets/fonts/*",
                "assets/music/*.ogg",
                "assets/music/*.wav",
                "assets/sfx/*.ogg",
                "assets/sfx/*.wav",
                "data/levels/*",
                "README.md",
            ],
            "plugins": ["pandagl", "p3openal_audio"],
            # macOS players run the source release (see README): apps built by Panda3D 1.10
            # are rejected by Apple Silicon code signing and Gatekeeper.
            "platforms": ["win_amd64", "manylinux2014_x86_64"],
            "log_filename": "$USER_APPDATA/Terminus/output.log",
            "log_append": False,
        }
    },
)
