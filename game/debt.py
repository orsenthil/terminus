"""Debt: time borrowed from the future, compounding on a fixed period. Pure logic."""

from game import settings


class Debt:
    def __init__(
        self,
        rate=settings.INTEREST_RATE,
        period=settings.INTEREST_PERIOD,
        cap=settings.DEBT_CAP,
    ):
        self.rate = rate
        self.period = period
        self.cap = cap
        self.principal = 0.0
        self.interest = 0.0
        self.timer = 0.0  # seconds since the last interest tick
        # Lifetime stats (survive clear()).
        self.total_borrowed = 0.0
        self.total_interest_accrued = 0.0
        self.total_interest_paid = 0.0

    @property
    def total(self):
        return self.principal + self.interest

    @property
    def in_debt(self):
        return self.total > 1e-6

    @property
    def at_cap(self):
        return self.total >= self.cap - 1e-6

    @property
    def time_to_tick(self):
        return self.period - self.timer

    def borrow(self, amount):
        """Borrow up to `amount`, limited by the cap. Returns the amount actually borrowed."""
        amount = max(0.0, min(amount, self.cap - self.total))
        if amount <= 0.0:
            return 0.0
        if not self.in_debt:
            self.timer = 0.0
        self.principal += amount
        self.total_borrowed += amount
        return amount

    def update(self, dt):
        """Advance the interest clock. Returns how many interest ticks happened."""
        if not self.in_debt:
            self.timer = 0.0
            return 0
        self.timer += dt
        ticks = 0
        while self.timer >= self.period:
            self.timer -= self.period
            grown = min(self.total * self.rate, self.cap - self.total)
            self.interest += max(0.0, grown)
            self.total_interest_accrued += max(0.0, grown)
            ticks += 1
        return ticks

    def repay(self, amount):
        """Pay off interest first, then principal. Returns the amount actually used."""
        amount = max(0.0, min(amount, self.total))
        from_interest = min(amount, self.interest)
        self.interest -= from_interest
        self.total_interest_paid += from_interest
        self.principal -= amount - from_interest
        if self.total < 1e-6:
            self.principal = 0.0
            self.interest = 0.0
            self.timer = 0.0
        return amount

    def clear(self):
        """Settle everything at once (the Collector takes it all). Returns what was owed."""
        return self.repay(self.total)

    def snapshot(self):
        return (self.principal, self.interest, self.timer)

    def restore(self, snap):
        self.principal, self.interest, self.timer = snap
