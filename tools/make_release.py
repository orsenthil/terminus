"""Build the source release zip for PyWeek: dist/terminus-<version>-source.zip.

    uv run python tools/make_release.py

The zip holds everything needed to play on Windows, macOS or Linux with Python 3.10+
(`pip install -r requirements.txt && python run_game.py`), plus the tests and tools.
"""

import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INCLUDE_FILES = [
    "run_game.py",
    "README.md",
    "music.md",
    "requirements.txt",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "setup.py",
]
INCLUDE_DIRS = {  # directory -> allowed file extensions
    "game": (".py",),
    "data/levels": (".txt", ".json"),
    "assets": (".ogg", ".wav", ".ttf", ".txt", ".md"),
    "tools": (".py", ".sh"),
    "tests": (".py",),
}
EXECUTABLE = (".sh",)


def version():
    # (tomllib only exists from Python 3.11; the game supports 3.10.)
    with open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8") as f:
        return re.search(r'^version\s*=\s*"([^"]+)"', f.read(), re.M).group(1)


def collect():
    files = [f for f in INCLUDE_FILES if os.path.isfile(os.path.join(ROOT, f))]
    for folder, exts in INCLUDE_DIRS.items():
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, folder)):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            for name in sorted(filenames):
                if name.endswith(exts):
                    files.append(os.path.relpath(os.path.join(dirpath, name), ROOT))
    return [f.replace(os.sep, "/") for f in files]


def main():
    ver = version()
    top = f"terminus-{ver}"
    out = os.path.join(ROOT, "dist", f"{top}-source.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    files = collect()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            info = zipfile.ZipInfo.from_file(os.path.join(ROOT, rel), f"{top}/{rel}")
            mode = 0o755 if rel.endswith(EXECUTABLE) else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(ROOT, rel), "rb") as f:
                z.writestr(info, f.read())
    audio = [f for f in files if f.startswith("assets/") and f.endswith((".ogg", ".wav"))]
    size = os.path.getsize(out) / 1e6
    print(f"wrote {os.path.relpath(out, ROOT)}: {len(files)} files, {size:.1f} MB")
    if not audio:
        print("note: no audio files in assets/; the release will be silent.", file=sys.stderr)


if __name__ == "__main__":
    main()
