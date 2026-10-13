"""Evidence-Gated Repair Engine & Multi-Stage Validation Oracle.

Forces small models (Gemma 2B/4B) through a formal 3-stage verification contract:
Stage 1: Patch Applicability (unified diff / contiguous block matching)
Stage 2: AST Syntax Validation (ast.parse verifies no syntax or indentation corruptions)
Stage 3: Subprocess Pytest Sandbox Execution (captures true test pass/fail + distilled tracebacks)
"""

from __future__ import annotations

import ast
import difflib
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StructuredHypothesis:
    symptom: str
    root_cause: str
    target_file: str
    target_symbol: str
    replacement_code: str
    original_target: Optional[str] = None
    unified_diff: Optional[str] = None


@dataclass
class ValidationResult:
    passed: bool
    stage_failed: Optional[str] = None  # 'applicability', 'syntax', 'tests', None
    error_message: str = ""
    distilled_traceback: str = ""
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    execution_time_seconds: float = 0.0


class PatchApplier:
    """Safely applies code modifications and maintains rollback snapshots."""

    @staticmethod
    def apply_block_replacement(
        file_path: Path,
        target_content: str,
        replacement_content: str,
    ) -> Tuple[bool, str]:
        """Replaces exact target content or best fuzzy match in file."""
        if not file_path.exists():
            return False, f"Target file does not exist: {file_path}"

        original = file_path.read_text(encoding="utf-8", errors="replace")

        # 1. Exact string match
        if target_content in original:
            updated = original.replace(target_content, replacement_content, 1)
            file_path.write_text(updated, encoding="utf-8")
            return True, "Exact match replacement succeeded."

        # 2. Whitespace-normalized match
        norm_target = "\n".join(line.rstrip() for line in target_content.strip().splitlines())
        norm_orig = "\n".join(line.rstrip() for line in original.splitlines())

        if norm_target in norm_orig:
            # Reconstruct replacement
            pattern = re.escape(norm_target)
            pattern = re.sub(r"\\\s+", r"\\s+", pattern)
            updated = re.sub(pattern, replacement_content, original, count=1)
            file_path.write_text(updated, encoding="utf-8")
            return True, "Normalized whitespace match replacement succeeded."

        return False, "Target content block could not be located in file."

    @staticmethod
    def apply_unified_diff(file_path: Path, diff_text: str) -> Tuple[bool, str]:
        """Applies a unified diff patch to target file."""
        if not file_path.exists():
            return False, f"File {file_path} not found"

        original_lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
        # Parse diff lines
        diff_lines = diff_text.strip().splitlines(keepends=True)
        try:
            # Use git apply if in git repo, else fallback
            res = subprocess.run(
                ["git", "apply", "-"],
                input=diff_text,
                text=True,
                capture_output=True,
                cwd=file_path.parent,
                timeout=5,
            )
            if res.returncode == 0:
                return True, "Git apply succeeded."
        except Exception:
            pass

        return False, "Unified diff could not be cleanly applied."


class SyntaxValidator:
    """Verifies Python AST validity."""

    @staticmethod
    def validate_file(file_path: Path) -> Tuple[bool, str]:
        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
            ast.parse(code, filename=str(file_path))
            return True, "Syntax valid."
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg} -> '{e.text.strip() if e.text else ''}'"
        except Exception as e:
            return False, f"AST Parse Error: {str(e)}"


class TestSandbox:
    """Executes pytest in an isolated subprocess with strict timeouts and output compression."""

    @staticmethod
    def run_tests(
        repo_root: Path,
        test_path: Optional[str] = None,
        timeout_seconds: int = 20,
    ) -> ValidationResult:
        cmd = [sys.executable, "-m", "pytest"]
        if test_path:
            cmd.append(test_path)
        cmd.extend(["-v", "--tb=short", "--disable-warnings"])

        import time
        start_t = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            duration = round(time.time() - start_t, 3)
            stdout = proc.stdout + "\n" + proc.stderr

            passed = proc.returncode == 0
            # Parse test counts
            passed_match = re.search(r"(\d+) passed", stdout)
            failed_match = re.search(r"(\d+) failed", stdout)

            num_passed = int(passed_match.group(1)) if passed_match else (1 if passed else 0)
            num_failed = int(failed_match.group(1)) if failed_match else (0 if passed else 1)
            total = num_passed + num_failed

            distilled_tb = TestSandbox._distill_traceback(stdout) if not passed else ""

            return ValidationResult(
                passed=passed,
                stage_failed=None if passed else "tests",
                error_message="All tests passed successfully." if passed else "Unit tests failed.",
                distilled_traceback=distilled_tb,
                tests_run=total,
                tests_passed=num_passed,
                tests_failed=num_failed,
                execution_time_seconds=duration,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                passed=False,
                stage_failed="tests",
                error_message=f"Test execution timed out after {timeout_seconds}s.",
                distilled_traceback="TIMEOUT: Infinite loop or deadlock suspected.",
                execution_time_seconds=float(timeout_seconds),
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                stage_failed="tests",
                error_message=f"Subprocess failure: {str(e)}",
                distilled_traceback=str(e),
                execution_time_seconds=round(time.time() - start_t, 3),
            )

    @staticmethod
    def _distill_traceback(output: str) -> str:
        """Strips framework boilerplate, returning only essential failure lines."""
        lines = output.splitlines()
        distilled: List[str] = []
        capture = False

        for line in lines:
            if "FAILED" in line or "FAILURES" in line or "ERROR" in line:
                capture = True
            if capture:
                distilled.append(line)
            if len(distilled) > 25:
                distilled.append("... [Traceback truncated for LLM context budget] ...")
                break

        return "\n".join(distilled) if distilled else output[-600:]


class EvidenceGate:
    """Coordinates the 3-stage validation gate with automatic file rollback."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()

    def evaluate_hypothesis_and_patch(
        self,
        hypothesis: StructuredHypothesis,
        test_file: Optional[str] = None,
    ) -> ValidationResult:
        """Applies patch, runs Gate 1 (Apply), Gate 2 (AST), Gate 3 (Pytest), then restores or commits."""
        target_path = self.repo_root / hypothesis.target_file
        if not target_path.exists():
            return ValidationResult(
                passed=False,
                stage_failed="applicability",
                error_message=f"Target file {hypothesis.target_file} does not exist.",
            )

        # Create rollback backup in memory
        backup_content = target_path.read_text(encoding="utf-8", errors="replace")

        try:
            # 1. Gate 1: Applicability
            applied = False
            msg = ""
            if hypothesis.original_target:
                applied, msg = PatchApplier.apply_block_replacement(
                    target_path,
                    hypothesis.original_target,
                    hypothesis.replacement_code,
                )
            elif hypothesis.unified_diff:
                applied, msg = PatchApplier.apply_unified_diff(target_path, hypothesis.unified_diff)
            else:
                # Direct overwrite of file if replacement represents entire file
                target_path.write_text(hypothesis.replacement_code, encoding="utf-8")
                applied = True
                msg = "Direct content written."

            if not applied:
                target_path.write_text(backup_content, encoding="utf-8")
                return ValidationResult(
                    passed=False,
                    stage_failed="applicability",
                    error_message=f"Gate 1 Failed: {msg}",
                )

            # 2. Gate 2: AST Syntax Validation
            syntax_ok, syntax_err = SyntaxValidator.validate_file(target_path)
            if not syntax_ok:
                # Rollback
                target_path.write_text(backup_content, encoding="utf-8")
                return ValidationResult(
                    passed=False,
                    stage_failed="syntax",
                    error_message=f"Gate 2 Failed: {syntax_err}",
                    distilled_traceback=syntax_err,
                )

            # 3. Gate 3: Subprocess Pytest Sandbox
            test_res = TestSandbox.run_tests(self.repo_root, test_path=test_file)
            if not test_res.passed:
                # Rollback to keep environment clean
                target_path.write_text(backup_content, encoding="utf-8")
                test_res.stage_failed = "tests"
                return test_res

            # Passed all gates! Keep modifications active.
            return test_res

        except Exception as e:
            target_path.write_text(backup_content, encoding="utf-8")
            return ValidationResult(
                passed=False,
                stage_failed="system",
                error_message=f"Validation exception: {str(e)}",
            )
