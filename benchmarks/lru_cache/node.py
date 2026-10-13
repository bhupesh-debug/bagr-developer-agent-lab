"""Doubly linked list node for cache storage."""
from typing import Any, Optional


class CacheNode:
    def __init__(self, key: str, value: Any):
        self.key: str = key
        self.value: Any = value
        self.prev: Optional["CacheNode"] = None
        self.next: Optional["CacheNode"] = None
