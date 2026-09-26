"""AudioManager: placeholder-safe music and SFX.

Every cue in settings.AUDIO_CUES maps to a file under assets/. If the file (or a .wav with
the same stem) is missing, one warning is printed and the cue silently does nothing.
"""

import os

from panda3d.core import AudioSound, Filename

from game import settings as S


def resolve_cue_path(cue, assets_dir=S.ASSETS_DIR):
    """Return the path of an existing file for `cue` (.ogg preferred, then .wav), or None."""
    rel = S.AUDIO_CUES[cue]
    stem, _ = os.path.splitext(rel)
    for ext in (".ogg", ".wav"):
        path = os.path.join(assets_dir, stem + ext)
        if os.path.isfile(path):
            return path
    return None


class AudioManager:
    def __init__(self, base, assets_dir=S.ASSETS_DIR):
        self.base = base
        self.assets_dir = assets_dir
        self.master = S.MASTER_VOLUME
        self.music_volume = S.MUSIC_VOLUME
        self.sfx_volume = S.SFX_VOLUME
        self.muted = False
        self.warned = set()
        self.sounds = {}  # cue -> AudioSound (only cues whose files exist)
        self.music_tracks = {}  # playing music cue -> [sound, fade_volume, target, layer_volume]
        self.stings = []  # one-shot music cues currently sounding
        self.loops = set()
        for cue, rel in S.AUDIO_CUES.items():
            if rel.startswith("sfx/"):
                self._load(cue)

    # --- loading ---------------------------------------------------------------------
    def _load(self, cue):
        if cue in self.sounds:
            return self.sounds[cue]
        if cue not in S.AUDIO_CUES:
            self._warn(cue, f"[audio] unknown cue {cue!r}, playing silence")
            return None
        path = resolve_cue_path(cue, self.assets_dir)
        if path is None:
            self._warn(cue, f"[audio] missing {S.AUDIO_CUES[cue]}, playing silence")
            return None
        fn = Filename.fromOsSpecific(path)
        is_music = S.AUDIO_CUES[cue].startswith("music/")
        try:
            sound = self.base.loader.loadMusic(fn) if is_music else self.base.loader.loadSfx(fn)
        except Exception as exc:  # a broken file must never crash the game
            self._warn(cue, f"[audio] could not load {path}: {exc}")
            return None
        if sound is None:
            self._warn(cue, f"[audio] could not load {path}, playing silence")
            return None
        self.sounds[cue] = sound
        return sound

    def _warn(self, cue, message):
        if cue not in self.warned:
            self.warned.add(cue)
            print(message)

    def _gain(self, kind):
        if self.muted:
            return 0.0
        return self.master * (self.music_volume if kind == "music" else self.sfx_volume)

    # --- music -----------------------------------------------------------------------
    def play_music(self, cue, fade=1.0):
        """Crossfade to `cue` (looped). Layers listed in MUSIC_LAYERS start with it, silent."""
        if cue not in S.MUSIC_LOOPS:
            self.play_sting(cue)
            return
        wanted = [cue] + S.MUSIC_LAYERS.get(cue, [])
        if cue in self.music_tracks:
            for name in wanted:
                if name in self.music_tracks:
                    self.music_tracks[name][2] = 1.0
            return
        for other, track in self.music_tracks.items():
            if other not in wanted:
                track[2] = 0.0  # fade out
        for name in wanted:
            sound = self._load(name)
            if sound is None:
                continue
            layer_vol = 1.0 if name == cue else 0.0
            start = 0.0 if fade > 0 else 1.0
            self.music_tracks[name] = [sound, start, 1.0, layer_vol, max(fade, 1e-3)]
            sound.setLoop(True)
            sound.setVolume(start * layer_vol * self._gain("music"))
            sound.setTime(0.0)
        # Start all wanted tracks back to back so layers stay aligned.
        for name in wanted:
            if name in self.music_tracks:
                self.music_tracks[name][0].play()

    def stop_music(self, fade=1.0):
        for track in self.music_tracks.values():
            track[2] = 0.0
            track[4] = max(fade, 1e-3)

    def play_sting(self, cue):
        sound = self._load(cue)
        if sound is None:
            return
        sound.setLoop(False)
        sound.setVolume(self._gain("music"))
        sound.play()
        self.stings.append(sound)

    def set_layer_volume(self, cue, volume):
        track = self.music_tracks.get(cue)
        if track is not None:
            track[3] = max(0.0, min(1.0, volume))

    # --- sfx -------------------------------------------------------------------------
    def play_sfx(self, cue):
        sound = self._load(cue)
        if sound is None:
            return
        sound.setLoop(False)
        sound.setVolume(self._gain("sfx"))
        sound.play()

    def start_loop(self, cue):
        if cue in self.loops:
            return
        self.loops.add(cue)
        sound = self._load(cue)
        if sound is None:
            return
        sound.setLoop(True)
        sound.setVolume(self._gain("sfx"))
        sound.play()

    def stop_loop(self, cue):
        if cue not in self.loops:
            return
        self.loops.discard(cue)
        sound = self.sounds.get(cue)
        if sound is not None:
            sound.stop()

    def stop_all_loops(self):
        for cue in list(self.loops):
            self.stop_loop(cue)

    # --- volume ----------------------------------------------------------------------
    def set_master_volume(self, v):
        self.master = max(0.0, min(1.0, v))
        self._apply_volumes()

    def set_music_volume(self, v):
        self.music_volume = max(0.0, min(1.0, v))
        self._apply_volumes()

    def set_sfx_volume(self, v):
        self.sfx_volume = max(0.0, min(1.0, v))
        self._apply_volumes()

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_volumes()
        return self.muted

    def _apply_volumes(self):
        for cue in self.loops:
            sound = self.sounds.get(cue)
            if sound is not None:
                sound.setVolume(self._gain("sfx"))
        for sound in self.stings:
            sound.setVolume(self._gain("music"))
        self.update(0.0)

    # --- per-frame -------------------------------------------------------------------
    def update(self, dt):
        gain = self._gain("music")
        for cue in list(self.music_tracks):
            sound, vol, target, layer, fade = self.music_tracks[cue]
            step = dt / fade
            vol = min(target, vol + step) if vol < target else max(target, vol - step)
            self.music_tracks[cue][1] = vol
            sound.setVolume(vol * layer * gain)
            if target == 0.0 and vol <= 0.0:
                sound.stop()
                del self.music_tracks[cue]
        self.stings = [s for s in self.stings if s.status() == AudioSound.PLAYING]
