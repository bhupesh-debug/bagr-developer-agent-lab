"""Unit tests for ComputeController."""
import pytest
from src.controller.compute_controller import ComputeController


def test_controller_telemetry_and_adaptation():
    ctrl = ComputeController(max_ram_mb=500.0, max_latency_seconds=10.0, max_retries=3)
    ctrl.start_run()

    # Step 1
    ctrl.record_step("step1", duration=0.1, context_tokens=100, retries=0, status="ok")
    can_cont, _ = ctrl.should_continue(current_attempt=1)
    assert can_cont is True

    # Check retry limit
    can_cont_retry, reason = ctrl.should_continue(current_attempt=3)
    assert can_cont_retry is False
    assert "Maximum retries" in reason

    summary = ctrl.end_run()
    assert summary["total_steps"] == 1
    assert summary["total_context_tokens"] == 100
