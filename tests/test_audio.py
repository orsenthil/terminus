import math
import os
import struct
import wave

from game import settings as S
from game.audio import AudioManager, resolve_cue_path


def test_every_cue_is_safe_with_no_files(headless_base, tmp_path, capsys):
    audio = AudioManager(headless_base, assets_dir=str(tmp_path))
    for cue in S.AUDIO_CUES:
        if cue in S.MUSIC_LOOPS:
            audio.play_music(cue, fade=0.5)
            audio.set_layer_volume(cue, 0.5)
        else:
            audio.play_music(cue)
        audio.play_sfx(cue)
        audio.start_loop(cue)
        audio.update(0.1)
        audio.stop_loop(cue)
    audio.set_layer_volume("level_debt", 1.0)
    audio.set_master_volume(0.3)
    audio.set_music_volume(0.3)
    audio.set_sfx_volume(0.3)
    assert audio.toggle_mute() is True
    assert audio.toggle_mute() is False
    audio.stop_music()
    audio.update(5.0)
    out = capsys.readouterr().out
    # At most one warning per missing cue, however often it's used.
    for cue, rel in S.AUDIO_CUES.items():
        assert out.count(f"missing {rel},") == 1, cue


def _write_wav(path, seconds=0.1):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        frames = b"".join(
            struct.pack("<h", int(8000 * math.sin(i * 0.1))) for i in range(int(22050 * seconds))
        )
        w.writeframes(frames)


def test_dropped_in_files_are_found(headless_base, tmp_path):
    os.makedirs(tmp_path / "sfx")
    os.makedirs(tmp_path / "music")
    _write_wav(tmp_path / "sfx" / "jump.wav")
    _write_wav(tmp_path / "music" / "title.wav")
    assert resolve_cue_path("jump", str(tmp_path)).endswith("jump.wav")
    assert resolve_cue_path("land", str(tmp_path)) is None
    audio = AudioManager(headless_base, assets_dir=str(tmp_path))
    assert "jump" in audio.sounds
    audio.play_sfx("jump")
    audio.play_music("title", fade=0.2)
    assert "title" in audio.music_tracks


def test_ogg_is_preferred_over_wav(tmp_path):
    os.makedirs(tmp_path / "sfx")
    (tmp_path / "sfx" / "jump.ogg").write_bytes(b"")
    (tmp_path / "sfx" / "jump.wav").write_bytes(b"")
    assert resolve_cue_path("jump", str(tmp_path)).endswith("jump.ogg")
