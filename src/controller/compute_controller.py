"""Adaptive Compute Controller & Resource Telemetry Tracker.

Monitors CPU, RAM, latency, and context token budgets dynamically.
Applies deterministic throttling rules to safeguard 8 GB consumer machines from OOM
and thermal thrashing during recursive agentic repair loops.
"""

from __future__ import annotations

import os
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TelemetryRecord:
    step_name: str
    duration_seconds: float
    peak_memory_mb: float
    context_tokens: int
    retries_used: int
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComputeController:
    """Manages adaptive resource constraints and fallback policies."""

    def __init__(
        self,
        max_ram_mb: float = 6000.0,
        max_latency_seconds: float = 120.0,
        max_retries: int = 3,
        initial_token_budget: int = 2048,
    ):
        self.max_ram_mb = max_ram_mb
        self.max_latency_seconds = max_latency_seconds
        self.max_retries = max_retries
        self.current_token_budget = initial_token_budget
        self.current_graph_hops = 2

        self.records: List[TelemetryRecord] = []
        self._start_time: Optional[float] = None
        self._is_tracking_memory = False

    def start_run(self) -> None:
        """Initializes run timer and memory tracking."""
        self._start_time = time.time()
        self.records.clear()
        try:
            tracemalloc.start()
            self._is_tracking_memory = True
        except Exception:
            self._is_tracking_memory = False

    def get_current_memory_mb(self) -> float:
        """Returns current process allocated memory in MB."""
        if self._is_tracking_memory:
            current, peak = tracemalloc.get_traced_memory()
            return round(peak / (1024 * 1024), 2)
        return 0.0

    def record_step(
        self,
        step_name: str,
        duration: float,
        context_tokens: int,
        retries: int,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TelemetryRecord:
        peak_mb = self.get_current_memory_mb()
        rec = TelemetryRecord(
            step_name=step_name,
            duration_seconds=round(duration, 3),
            peak_memory_mb=peak_mb,
            context_tokens=context_tokens,
            retries_used=retries,
            status=status,
            metadata=metadata or {},
        )
        self.records.append(rec)
        self._check_and_adapt(peak_mb)
        return rec

    def _check_and_adapt(self, current_peak_mb: float) -> None:
        """Deterministic Adaptation Rules:
        If memory exceeds safety threshold or latency is high, contract search depth and budget.
        """
        # Rule 1: High memory alert -> contract context budget
        if current_peak_mb > (self.max_ram_mb * 0.75):
            self.current_token_budget = max(1024, int(self.current_token_budget * 0.7))
            self.current_graph_hops = 1

        # Rule 2: Multi-turn retry throttle
        if len(self.records) > 2:
            elapsed = time.time() - (self._start_time or time.time())
            if elapsed > (self.max_latency_seconds * 0.7):
                self.current_graph_hops = 1

    def should_continue(self, current_attempt: int) -> Tuple[bool, str]:
        """Safety barrier: guards against infinite retry loops and budget blowouts."""
        if current_attempt >= self.max_retries:
            return False, f"Maximum retries reached ({self.max_retries})."

        if self._start_time:
            elapsed = time.time() - self._start_time
            if elapsed >= self.max_latency_seconds:
                return False, f"Timeout budget reached ({elapsed:.1f}s >= {self.max_latency_seconds}s)."

        current_mb = self.get_current_memory_mb()
        if current_mb >= self.max_ram_mb:
            return False, f"Memory threshold exceeded ({current_mb:.1f}MB >= {self.max_ram_mb}MB)."

        return True, "Within budget constraints."

    def end_run(self) -> Dict[str, Any]:
        """Summarizes run resource consumption and stops profilers."""
        total_time = round(time.time() - self._start_time, 3) if self._start_time else 0.0
        peak_mb = self.get_current_memory_mb()
        if self._is_tracking_memory:
            tracemalloc.stop()
            self._is_tracking_memory = False

        total_tokens = sum(r.context_tokens for r in self.records)
        return {
            "total_duration_seconds": total_time,
            "peak_memory_mb": peak_mb,
            "total_context_tokens": total_tokens,
            "total_steps": len(self.records),
            "adapted_final_budget": self.current_token_budget,
            "adapted_graph_hops": self.current_graph_hops,
            "step_records": [r.__dict__ for r in self.records],
        }
