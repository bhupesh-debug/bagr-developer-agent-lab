"""Unit tests for cycle detector."""
import pytest
from node import Node
from detector import CycleDetector


def test_simple_cycle():
    a = Node("A")
    b = Node("B")
    a.add_edge(b)
    b.add_edge(a)

    detector = CycleDetector()
    assert detector.has_cycle(a) is True


def test_diamond_dag_not_a_cycle():
    """Fails initially: Diamond DAG (A->B, A->C, B->D, C->D) has NO cycle, but bug flags it as cycle."""
    a = Node("A")
    b = Node("B")
    c = Node("C")
    d = Node("D")

    a.add_edge(b)
    a.add_edge(c)
    b.add_edge(d)
    c.add_edge(d)

    detector = CycleDetector()
    assert detector.has_cycle(a) is False
