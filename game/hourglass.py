"""Hourglass (a water clock in the game): the top chamber drains into the bottom.

Pure logic, no Panda3D."""


class Hourglass:
    """An hourglass with `top` (time remaining) and `bottom` (time spent), in seconds.

    `capacity` (optional) bounds how much the glass can hold; `add` clamps to it.
    """

    def __init__(self, top=0.0, bottom=0.0, capacity=None):
        self.capacity = capacity
        self.top = max(0.0, float(top))
        if capacity is not None:
            self.top = min(self.top, capacity)
        self.bottom = max(0.0, float(bottom))

    @property
    def empty(self):
        return self.top <= 0.0

    @property
    def total(self):
        return self.top + self.bottom

    @property
    def fraction(self):
        """Share of the contents still in the top chamber (0..1)."""
        total = self.total
        return self.top / total if total > 0 else 0.0

    def update(self, dt):
        """Drain for dt seconds. Returns the amount that moved."""
        moved = min(self.top, max(0.0, dt))
        self.top -= moved
        self.bottom += moved
        if self.top < 1e-9:
            self.top = 0.0
        return moved

    def flip(self):
        self.top, self.bottom = self.bottom, self.top

    def add(self, seconds):
        """Add to the top chamber, clamped to capacity. Returns the amount added."""
        seconds = max(0.0, seconds)
        if self.capacity is not None:
            seconds = min(seconds, max(0.0, self.capacity - self.top))
        self.top += seconds
        return seconds

    def remove(self, seconds):
        """Remove from the top chamber (never below zero). Returns the amount removed."""
        seconds = min(max(0.0, seconds), self.top)
        self.top -= seconds
        return seconds
