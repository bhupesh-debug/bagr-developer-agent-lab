"""Unit tests for LRU Cache."""
import pytest
from store import LRUCache


def test_basic_get_put():
    cache = LRUCache(capacity=2)
    cache.put("a", 100)
    assert cache.get("a") == 100
    assert cache.get("nonexistent") is None


def test_lru_eviction_when_value_differs_from_key():
    """Fails initially: Eviction deletes lru_node.key, but buggy code checked lru_node.value."""
    cache = LRUCache(capacity=2)
    cache.put("key1", "val1")
    cache.put("key2", "val2")
    # Access key1 so key2 becomes least recently used
    assert cache.get("key1") == "val1"
    # Insert key3, should evict key2
    cache.put("key3", "val3")

    assert len(cache.cache) == 2
    assert cache.get("key1") == "val1"
    assert cache.get("key3") == "val3"
    assert cache.get("key2") is None
