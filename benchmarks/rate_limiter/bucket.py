"""Token Bucket implementation."""
from clock import SystemClock


class TokenBucket:
    def __init__(self, capacity: float, fill_rate_per_sec: float, clock: SystemClock = None):
        self.capacity: float = float(capacity)
        self.tokens: float = float(capacity)
        self.fill_rate_per_sec: float = float(fill_rate_per_sec)
        self.clock: SystemClock = clock or SystemClock()
        self.last_update: float = self.clock.now()

    def _replenish(self) -> None:
        now = self.clock.now()
        elapsed = now - self.last_update
        # Logic Bug: Uses integer floor division instead of multiplying elapsed * fill_rate
        replenished = int(elapsed // self.fill_rate_per_sec)
        self.tokens = min(self.capacity, self.tokens + replenished)
        self.last_update = now

    def consume(self, amount: float = 1.0) -> bool:
        self._replenish()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False
