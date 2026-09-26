"""Day / night cycle. Pure logic, no Panda3D."""

from game import settings as S


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b, strict=True))


def _smooth(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


class DayNight:
    """Cycles day -> dusk -> night -> dawn -> day.

    `night` is 0 in full day and 1 in full night, blending smoothly over `fade` seconds at
    the end of each half. `progress` runs 0..1 across the current half (for the sun and
    moon arcs).
    """

    def __init__(self, day=S.DAY_LENGTH, night=S.NIGHT_LENGTH, fade=S.DUSK_LENGTH, time=0.0):
        self.day = day
        self.night_length = night
        self.fade = fade
        self.time = time

    @property
    def cycle(self):
        return self.day + self.night_length

    @property
    def phase(self):
        return self.time % self.cycle

    @property
    def is_day_half(self):
        return self.phase < self.day

    @property
    def progress(self):
        p = self.phase
        return p / self.day if p < self.day else (p - self.day) / self.night_length

    @property
    def night(self):
        p = self.phase
        if p < self.day:  # day, fading to night over its last `fade` seconds
            return _smooth((p - (self.day - self.fade)) / self.fade)
        p -= self.day  # night, fading to day over its last `fade` seconds
        return 1.0 - _smooth((p - (self.night_length - self.fade)) / self.fade)

    @property
    def is_night(self):
        return self.night >= 0.5

    def update(self, dt):
        self.time += dt

    # --- palette ---------------------------------------------------------------------
    def sky(self):
        n = self.night
        if n < 0.5:
            return lerp(S.DAY_SKY, S.DUSK_SKY, n * 2)
        return lerp(S.DUSK_SKY, S.NIGHT_SKY, (n - 0.5) * 2)

    def ambient(self):
        return lerp(S.DAY_AMBIENT, S.NIGHT_AMBIENT, self.night)

    def sun(self):
        return lerp(S.DAY_SUN, S.NIGHT_SUN, self.night)

    def layer_scale(self):
        return lerp(S.DAY_LAYER_SCALE, S.NIGHT_LAYER_SCALE, self.night)

    def sand(self):
        return lerp(S.SAND_DAY, S.SAND_NIGHT, self.night)
