"""Unit tests for Repository Dependency Graph (RepoGraph)."""
import pytest
from pathlib import Path
from src.graph.repo_graph import RepoGraph, ASTEntityExtractor


def test_repo_graph_building(tmp_path: Path):
    # Create sample multi-file repository
    file1 = tmp_path / "module_a.py"
    file1.write_text(
        "def compute_tax(amount: float) -> float:\n"
        "    return amount * 0.1\n\n"
        "class TaxCalculator:\n"
        "    def run(self, val):\n"
        "        return compute_tax(val)\n",
        encoding="utf-8"
    )

    file2 = tmp_path / "test_module_a.py"
    file2.write_text(
        "from module_a import TaxCalculator, compute_tax\n\n"
        "def test_compute():\n"
        "    assert compute_tax(100) == 10.0\n",
        encoding="utf-8"
    )

    graph = RepoGraph(tmp_path).build()
    summary = graph.summary()

    assert summary["total_nodes"] > 3
    assert summary["total_edges"] > 2
    assert summary["parsing_errors_count"] == 0

    # Test k-hop neighborhood
    nodes = list(graph.graph.nodes())
    seeds = [n for n in nodes if "compute_tax" in n]
    assert len(seeds) > 0

    neighborhood = graph.get_k_hop_neighborhood(seeds, k=2)
    assert len(neighborhood) >= len(seeds)

    # Test Personalized PageRank
    ppr = graph.personalized_pagerank(seeds)
    assert len(ppr) == len(nodes)
    for s in seeds:
        assert ppr[s] > 0.0
