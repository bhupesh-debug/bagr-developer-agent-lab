"""Cycle detection in directed graphs using DFS recursion."""
from typing import List, Set
from node import Node


class CycleDetector:
    def __init__(self):
        self.visited: Set[str] = set()
        self.rec_stack: Set[str] = set()

    def has_cycle(self, start_node: Node) -> bool:
        """Determines whether a directed cycle exists starting from start_node."""
        self.visited.clear()
        self.rec_stack.clear()
        return self._dfs(start_node)

    def _dfs(self, current: Node) -> bool:
        self.visited.add(current.name)
        self.rec_stack.add(current.name)

        for neighbor in current.neighbors:
            if neighbor.name not in self.visited:
                if self._dfs(neighbor):
                    return True
            elif neighbor.name in self.rec_stack:
                return True

        # Logic Bug: Forgot to backtrack and remove current.name from self.rec_stack!
        # self.rec_stack.remove(current.name) is omitted, causing diamond DAG paths to be falsely marked as cycles!
        return False
