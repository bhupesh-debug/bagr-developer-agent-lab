"""Local Gemma Inference Client & Structured Generator.

Connects to local Ollama runtime (`http://127.0.0.1:11434`) targeting Google Gemma models
(e.g., `gemma2:2b`), enforcing structured JSON hypothesis output, timeout controls,
and an inspectable deterministic replay fallback mode for ablation studies.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class LLMResponse:
    raw_text: str
    parsed_json: Optional[Dict[str, Any]]
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    duration_seconds: float
    is_mock: bool = False


class GemmaClient:
    """Interacts with local Gemma model via Ollama REST API."""

    def __init__(
        self,
        model_name: str = "gemma2:2b",
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 45,
        fallback_mode: bool = False,
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fallback_mode = fallback_mode

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable and model is listed."""
        if self.fallback_mode:
            return True
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                return any(self.model_name in m for m in models)
        except Exception:
            return False

    def generate_repair_hypothesis(
        self,
        issue_description: str,
        code_context: str,
        test_failure_trace: str = "",
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """Queries model to produce a structured JSON bug repair hypothesis and patch."""
        default_system = (
            "You are an expert autonomous software engineer. "
            "Analyze the issue description, retrieved code, and any test failures. "
            "Formulate a minimal, targeted fix. "
            "You MUST respond ONLY with valid JSON conforming to this schema:\n"
            "{\n"
            '  "symptom": "Brief summary of failure symptom",\n'
            '  "root_cause": "Exact root cause explanation",\n'
            '  "target_file": "relative/path/to/file.py",\n'
            '  "target_symbol": "function_or_class_name",\n'
            '  "original_target": "exact contiguous block of original code to replace",\n'
            '  "replacement_code": "new corrected code block replacing original_target"\n'
            "}"
        )
        sys_prompt = system_prompt or default_system

        user_content = (
            f"### ISSUE REPORT\n{issue_description}\n\n"
            f"### RETRIEVED REPOSITORY CONTEXT\n{code_context}\n\n"
        )
        if test_failure_trace:
            user_content += f"### PRIOR TEST FAILURE TRACEBACK\n{test_failure_trace}\n\n"

        user_content += "Produce the JSON repair object now."

        full_prompt = f"<start_of_turn>user\n{sys_prompt}\n\n{user_content}<end_of_turn>\n<start_of_turn>model\n"

        start_t = time.time()
        # If offline or fallback enabled, provide deterministic response
        if self.fallback_mode or not self.is_available():
            return self._deterministic_fallback_response(issue_description, code_context, start_t)

        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_ctx": 4096,
            },
        }

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                duration = round(time.time() - start_t, 3)
                raw_response = result.get("response", "")
                parsed = self._extract_json(raw_response)

                prompt_tokens = result.get("prompt_eval_count", len(full_prompt) // 4)
                eval_tokens = result.get("eval_count", len(raw_response) // 4)

                return LLMResponse(
                    raw_text=raw_response,
                    parsed_json=parsed,
                    model_name=self.model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=eval_tokens,
                    duration_seconds=duration,
                    is_mock=False,
                )

        except Exception as e:
            # Fall back gracefully on connection or timeout error
            return self._deterministic_fallback_response(
                issue_description, code_context, start_t, error_note=str(e)
            )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON dictionary even if wrapped in markdown formatting."""
        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return None

    def _deterministic_fallback_response(
        self,
        issue: str,
        context: str,
        start_time: float,
        error_note: str = "",
    ) -> LLMResponse:
        """Deterministic simulation for offline ablation runs and unit testing."""
        duration = round(time.time() - start_time, 3)
        # Parse context to determine target file heuristic
        target_file = "calculator.py"
        target_symbol = "calculate"
        file_match = re.search(r"File: `([^`]+)`", context)
        if file_match:
            target_file = file_match.group(1)

        symbol_match = re.search(r"### Entity: `([^`]+)`", context)
        if symbol_match:
            target_symbol = symbol_match.group(1)

        simulated_data = {
            "symptom": f"Issue detected: {issue[:60]}...",
            "root_cause": "Logic error identified in function body.",
            "target_file": target_file,
            "target_symbol": target_symbol,
            "original_target": "# target code",
            "replacement_code": "# replacement code",
        }

        return LLMResponse(
            raw_text=json.dumps(simulated_data, indent=2),
            parsed_json=simulated_data,
            model_name=f"{self.model_name} (deterministic fallback)",
            prompt_tokens=len(context) // 4,
            completion_tokens=85,
            duration_seconds=max(0.05, duration),
            is_mock=True,
        )
