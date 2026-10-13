"""Unit tests for BudgetSelector and context knapsack packing."""
import pytest
from pathlib import Path
from src.graph.repo_graph import RepoGraph
from src.retrieval.budget_selector import BudgetSelector, estimate_tokens


def test_token_estimation():
    text = "def hello_world():\n    return 'Hello, World!'\n"
    tokens = estimate_tokens(text)
    assert 5 <= tokens <= 25


def test_budget_selector_packing(tmp_path: Path):
    file1 = tmp_path / "pricing.py"
    file1.write_text(
        "def calculate_total(price: float, tax: float) -> float:\n"
        "    \"\"\"Calculates order total.\"\"\"\n"
        "    return price + tax\n",
        encoding="utf-8"
    )

    graph = RepoGraph(tmp_path).build()
    selector = BudgetSelector(graph, max_tokens=2048)

    # Keyword retrieval
    snippets_kw = selector.retrieve_keyword_only("calculate total order tax")
    assert len(snippets_kw) > 0
    assert "calculate_total" in snippets_kw[0].name

    # Graph guided retrieval
    snippets_graph = selector.retrieve_graph_guided("calculate total order tax")
    assert len(snippets_graph) > 0
    assert snippets_graph[0].token_count <= 2048

    # Formatted prompt
    prompt = selector.format_context_prompt(snippets_graph)
    assert "### Entity:" in prompt
    assert "calculate_total" in prompt
