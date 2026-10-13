"""BAGR Autonomous Developer Agent.

Integrates:
A. Repository Graph (RepoGraph)
B. Budget-Aware Context Selection (BudgetSelector)
C. Evidence-Gated Repair (EvidenceGate)
D. Adaptive Compute Controller (ComputeController)

Provides an end-to-end autonomous repair workflow capable of running on edge hardware.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.controller.compute_controller import ComputeController
from src.graph.repo_graph import RepoGraph
from src.llm.gemma_client import GemmaClient, LLMResponse
from src.repair.evidence_gate import EvidenceGate, StructuredHypothesis, ValidationResult
from src.retrieval.budget_selector import BudgetSelector, RetrievedSnippet


@dataclass
class AgentRunReport:
    issue: str
    strategy: str
    resolved: bool
    attempts_made: int
    duration_seconds: float
    peak_memory_mb: float
    total_context_tokens: int
    retrieved_snippets: List[Dict[str, Any]]
    final_validation: Optional[Dict[str, Any]]
    applied_patch: Optional[Dict[str, Any]]
    ablation_condition: str = "BAGR_FULL"


class BAGRAgent:
    """Budget-Aware Graph-Guided Repair Autonomous Agent."""

    def __init__(
        self,
        repo_path: str | Path,
        model_name: str = "gemma2:2b",
        token_budget: int = 2048,
        max_retries: int = 3,
        fallback_mode: bool = False,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.model_name = model_name
        self.token_budget = token_budget
        self.max_retries = max_retries

        # Subsystems
        self.controller = ComputeController(
            max_ram_mb=6500.0,
            max_latency_seconds=180.0,
            max_retries=max_retries,
            initial_token_budget=token_budget,
        )
        self.llm_client = GemmaClient(model_name=model_name, fallback_mode=fallback_mode)
        self.evidence_gate = EvidenceGate(self.repo_path)

        self.repo_graph: Optional[RepoGraph] = None
        self.selector: Optional[BudgetSelector] = None

    def initialize_graph(self) -> Dict[str, Any]:
        """Builds multi-file repository graph."""
        start_t = time.time()
        self.repo_graph = RepoGraph(self.repo_path).build()
        self.selector = BudgetSelector(self.repo_graph, max_tokens=self.token_budget)
        summary = self.repo_graph.summary()
        self.controller.record_step(
            step_name="graph_construction",
            duration=time.time() - start_t,
            context_tokens=0,
            retries=0,
            status="completed",
            metadata=summary,
        )
        return summary

    def solve_issue(
        self,
        issue_description: str,
        test_file: Optional[str] = None,
        retrieval_strategy: str = "bagr",
        ablation_condition: str = "BAGR_FULL",
    ) -> AgentRunReport:
        """Executes the complete autonomous repair cycle."""
        self.controller.start_run()
        start_wall_time = time.time()

        if self.repo_graph is None or self.selector is None:
            self.initialize_graph()

        # Step 1: Context Retrieval according to condition strategy
        retrieval_start = time.time()
        if retrieval_strategy == "keyword":
            snippets = self.selector.retrieve_keyword_only(issue_description, self.token_budget)
        elif retrieval_strategy == "embedding":
            snippets = self.selector.retrieve_dense_embedding(issue_description, self.token_budget)
        elif retrieval_strategy == "unbudgeted_graph":
            # Graph retrieval with generous 8k budget (simulating unconstrained baseline)
            snippets = self.selector.retrieve_graph_guided(
                issue_description, token_budget=8192, graph_hops=2
            )
        else:  # 'bagr' default
            snippets = self.selector.retrieve_graph_guided(
                issue_description,
                token_budget=self.controller.current_token_budget,
                graph_hops=self.controller.current_graph_hops,
            )

        context_prompt = self.selector.format_context_prompt(snippets)
        total_tokens = sum(s.token_count for s in snippets)

        self.controller.record_step(
            step_name="context_retrieval",
            duration=time.time() - retrieval_start,
            context_tokens=total_tokens,
            retries=0,
            status="completed",
            metadata={"retrieval_strategy": retrieval_strategy, "snippet_count": len(snippets)},
        )

        # Step 2: Evidence-Gated Bounded Repair Loop
        last_failure_trace = ""
        resolved = False
        final_validation: Optional[ValidationResult] = None
        applied_patch: Optional[StructuredHypothesis] = None
        attempt = 0

        while attempt < self.max_retries:
            attempt += 1
            can_continue, reason = self.controller.should_continue(attempt - 1)
            if not can_continue:
                break

            gen_start = time.time()
            llm_resp = self.llm_client.generate_repair_hypothesis(
                issue_description=issue_description,
                code_context=context_prompt,
                test_failure_trace=last_failure_trace,
            )

            self.controller.record_step(
                step_name=f"llm_inference_attempt_{attempt}",
                duration=time.time() - gen_start,
                context_tokens=llm_resp.prompt_tokens,
                retries=attempt,
                status="generated",
                metadata={"is_mock": llm_resp.is_mock},
            )

            if not llm_resp.parsed_json:
                last_failure_trace = f"JSON Parse Error: Model returned non-JSON text: {llm_resp.raw_text[:200]}"
                continue

            parsed = llm_resp.parsed_json
            hypothesis = StructuredHypothesis(
                symptom=parsed.get("symptom", "Unspecified"),
                root_cause=parsed.get("root_cause", "Unspecified"),
                target_file=parsed.get("target_file", ""),
                target_symbol=parsed.get("target_symbol", ""),
                original_target=parsed.get("original_target"),
                replacement_code=parsed.get("replacement_code", ""),
            )

            # Step 3: Multi-Stage Evidence Verification Gate
            val_start = time.time()
            validation_result = self.evidence_gate.evaluate_hypothesis_and_patch(
                hypothesis, test_file=test_file
            )
            final_validation = validation_result

            self.controller.record_step(
                step_name=f"evidence_gate_attempt_{attempt}",
                duration=time.time() - val_start,
                context_tokens=0,
                retries=attempt,
                status="passed" if validation_result.passed else f"failed_{validation_result.stage_failed}",
                metadata={
                    "stage_failed": validation_result.stage_failed,
                    "tests_passed": validation_result.tests_passed,
                    "tests_failed": validation_result.tests_failed,
                },
            )

            if validation_result.passed:
                resolved = True
                applied_patch = hypothesis
                break
            else:
                last_failure_trace = (
                    f"Gate Failed: {validation_result.stage_failed}\n"
                    f"Error: {validation_result.error_message}\n"
                    f"Details:\n{validation_result.distilled_traceback}"
                )

        run_summary = self.controller.end_run()

        return AgentRunReport(
            issue=issue_description,
            strategy=retrieval_strategy,
            resolved=resolved,
            attempts_made=attempt,
            duration_seconds=round(time.time() - start_wall_time, 3),
            peak_memory_mb=run_summary["peak_memory_mb"],
            total_context_tokens=run_summary["total_context_tokens"],
            retrieved_snippets=[s.__dict__ for s in snippets],
            final_validation=final_validation.__dict__ if final_validation else None,
            applied_patch=applied_patch.__dict__ if applied_patch else None,
            ablation_condition=ablation_condition,
        )
