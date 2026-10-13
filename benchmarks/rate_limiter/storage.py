"""Registry for active user rate limiters."""
from typing import Dict
from bucket import TokenBucket


class LimiterRegistry:
    def __init__(self, default_capacity: float = 10.0, default_fill_rate: float = 2.0):
        self.default_capacity = default_capacity
        self.default_fill_rate = default_fill_rate
        self.buckets: Dict[str, TokenBucket] = {}

    def get_bucket(self, key: str) -> TokenBucket:
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(self.default_capacity, self.default_fill_rate)
        return self.buckets[key]
