"""Generate placeholder beep WAVs for every SFX cue (standard library only).

    uv run python tools/make_placeholder_sfx.py

Files go to assets/sfx/<cue>.wav. They are placeholders for testing sound timing and are
not committed (see .gitignore). Real .ogg files with the same names take precedence.
"""

import math
import os
import struct
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import settings as S  # noqa: E402

RATE = 22050

# cue: (start Hz, end Hz, seconds, loops)
TONES = {
    "jump": (440, 880, 0.12, False),
    "land": (180, 90, 0.08, False),
    "pickup": (880, 1320, 0.15, False),
    "borrow_loop": (220, 220, 1.0, True),
    "interest_tick": (660, 330, 0.25, False),
    "flip_glass": (520, 780, 0.18, False),
    "gate_open": (200, 400, 0.4, False),
    "gate_close": (400, 150, 0.35, False),
    "lock_start": (600, 600, 0.12, False),
    "lock_success": (660, 1320, 0.5, False),
    "lock_fail": (300, 120, 0.45, False),
    "shrine_pour_loop": (330, 330, 1.0, True),
    "collector_hit": (120, 60, 0.5, False),
    "death": (400, 80, 0.8, False),
    "menu_move": (700, 700, 0.05, False),
    "menu_select": (700, 1050, 0.12, False),
}


def tone(f0, f1, seconds, loops):
    n = int(RATE * seconds)
    phase = 0.0
    out = bytearray()
    for i in range(n):
        t = i / n
        freq = f0 + (f1 - f0) * t
        phase += 2 * math.pi * freq / RATE
        env = 1.0 if loops else min(1.0, i / 200) * (1.0 - t) ** 1.5
        sample = 0.35 * env * (math.sin(phase) + 0.3 * math.sin(2 * phase))
        out += struct.pack("<h", int(max(-1.0, min(1.0, sample)) * 32767))
    return bytes(out)


def main():
    out_dir = os.path.join(S.ASSETS_DIR, "sfx")
    os.makedirs(out_dir, exist_ok=True)
    for cue, rel in S.AUDIO_CUES.items():
        if not rel.startswith("sfx/"):
            continue
        f0, f1, secs, loops = TONES[cue]
        path = os.path.join(out_dir, cue + ".wav")
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(tone(f0, f1, secs, loops))
        print("wrote", os.path.relpath(path, S.ROOT_DIR))


if __name__ == "__main__":
    main()
