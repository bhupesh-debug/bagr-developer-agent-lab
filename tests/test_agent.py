"""Unit tests for end-to-end BAGRAgent."""
import pytest
from pathlib import Path
from src.agent.bagr_agent import BAGRAgent


def test_agent_end_to_end_mock(tmp_path: Path):
    file1 = tmp_path / "calc.py"
    file1.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    test_file = tmp_path / "test_calc.py"
    test_file.write_text("from calc import add\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")

    agent = BAGRAgent(repo_path=tmp_path, fallback_mode=True)
    summary = agent.initialize_graph()
    assert summary["total_nodes"] > 0

    report = agent.solve_issue(
        issue_description="Verify addition logic",
        test_file="test_calc.py",
        retrieval_strategy="bagr",
    )
    assert report.attempts_made >= 1
    assert report.strategy == "bagr"
    assert report.duration_seconds > 0.0
