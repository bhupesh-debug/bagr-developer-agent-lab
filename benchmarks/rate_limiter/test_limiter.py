"""Unit tests for token bucket rate limiter."""
import pytest
from bucket import TokenBucket
from clock import SystemClock


class MockClock(SystemClock):
    def __init__(self, start_time: float = 1000.0):
        self.current = start_time

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def test_immediate_consumption():
    clock = MockClock()
    bucket = TokenBucket(capacity=5.0, fill_rate_per_sec=2.0, clock=clock)
    assert bucket.consume(3.0) is True
    assert bucket.tokens == 2.0


def test_fractional_fill_rate_replenishment():
    """Fails initially: Advancing 0.5s at 2.0 tokens/sec should replenish 1.0 token."""
    clock = MockClock()
    bucket = TokenBucket(capacity=5.0, fill_rate_per_sec=2.0, clock=clock)
    # Drain completely
    assert bucket.consume(5.0) is True
    assert bucket.tokens == 0.0

    # Advance 0.5s. Replenish should be 0.5 * 2.0 = 1.0 token.
    # Bug does int(0.5 // 2.0) = 0.
    clock.advance(0.5)
    assert bucket.consume(1.0) is True
