"""LRU Cache Store implementation."""
from typing import Any, Dict, Optional
from node import CacheNode
from serializer import serialize_key


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity: int = capacity
        self.cache: Dict[str, CacheNode] = {}
        self.head: CacheNode = CacheNode("__HEAD__", None)
        self.tail: CacheNode = CacheNode("__TAIL__", None)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _add_to_front(self, node: CacheNode) -> None:
        node.next = self.head.next
        node.prev = self.head
        if self.head.next:
            self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: CacheNode) -> None:
        prev_node = node.prev
        next_node = node.next
        if prev_node:
            prev_node.next = next_node
        if next_node:
            next_node.prev = prev_node

    def get(self, key: Any) -> Optional[Any]:
        skey = serialize_key(key)
        if skey not in self.cache:
            return None
        node = self.cache[skey]
        self._remove_node(node)
        self._add_to_front(node)
        return node.value

    def put(self, key: Any, value: Any) -> None:
        skey = serialize_key(key)
        if skey in self.cache:
            node = self.cache[skey]
            node.value = value
            self._remove_node(node)
            self._add_to_front(node)
            return

        new_node = CacheNode(skey, value)
        self.cache[skey] = new_node
        self._add_to_front(new_node)

        if len(self.cache) > self.capacity:
            lru_node = self.tail.prev
            if lru_node and lru_node != self.head:
                self._remove_node(lru_node)
                # Logic Bug: Attempts to delete by value instead of key
                if lru_node.value in self.cache:
                    del self.cache[lru_node.value]
                elif lru_node.key in self.cache:
                    del self.cache[lru_node.key]
