"""Graph node representation."""
from typing import List


class Node:
    def __init__(self, name: str):
        self.name: str = name
        self.neighbors: List["Node"] = []

    def add_edge(self, neighbor: "Node") -> None:
        self.neighbors.append(neighbor)
