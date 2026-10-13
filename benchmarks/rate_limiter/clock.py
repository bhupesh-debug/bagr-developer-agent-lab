"""Clock interface for time management."""
import time


class SystemClock:
    def now(self) -> float:
        return time.time()
