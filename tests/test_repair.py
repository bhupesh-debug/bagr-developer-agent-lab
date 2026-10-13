"""Unit tests for EvidenceGate, SyntaxValidator, and PatchApplier."""
import pytest
from pathlib import Path
from src.repair.evidence_gate import (
    EvidenceGate,
    StructuredHypothesis,
    PatchApplier,
    SyntaxValidator,
)


def test_syntax_validator(tmp_path: Path):
    good_file = tmp_path / "good.py"
    good_file.write_text("x = 10\ny = 20\n", encoding="utf-8")
    ok, _ = SyntaxValidator.validate_file(good_file)
    assert ok is True

    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(:\n    pass\n", encoding="utf-8")
    ok, msg = SyntaxValidator.validate_file(bad_file)
    assert ok is False
    assert "SyntaxError" in msg


def test_patch_applier_exact(tmp_path: Path):
    target_file = tmp_path / "module.py"
    target_file.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")

    applied, msg = PatchApplier.apply_block_replacement(
        target_file,
        "    return a - b",
        "    return a + b",
    )
    assert applied is True
    assert "return a + b" in target_file.read_text(encoding="utf-8")


def test_evidence_gate_rollback_on_syntax_error(tmp_path: Path):
    target_file = tmp_path / "code.py"
    original_code = "def valid():\n    return 42\n"
    target_file.write_text(original_code, encoding="utf-8")

    gate = EvidenceGate(tmp_path)
    bad_hypothesis = StructuredHypothesis(
        symptom="Testing bad syntax",
        root_cause="Bad replacement",
        target_file="code.py",
        target_symbol="valid",
        original_target="    return 42",
        replacement_code="    return 42 +++ ??? (invalid syntax)",
    )

    res = gate.evaluate_hypothesis_and_patch(bad_hypothesis)
    assert res.passed is False
    assert res.stage_failed == "syntax"
    # Ensure rollback kept file intact
    assert target_file.read_text(encoding="utf-8") == original_code
