# IMPLEMENTATION CHECKLIST & LAB ROADMAP

**Project:** Gemma Local Developer Agent Research Lab (BAGR)  
**Target:** Google DeepMind / Kaggle Gemma 4 Developer Agent Paper Track  

---

## Phase 1: Environment & Foundational Governance (Complete)
- [x] Inspect OS, CPU, RAM, GPU/VRAM, disk space, and installed dev tools.
- [x] Verify local LLM runtime (Ollama with `gemma2:2b` verified and loaded).
- [x] Create `HARDWARE_REPORT.md` with true measured specifications.
- [x] Create `RESEARCH_PLAN.md` with theoretical formulas and ablation matrix.
- [x] Create `IMPLEMENTATION_CHECKLIST.md`.

## Phase 2: Core Engineering Architecture (`src/`)
- [ ] `src/graph/repo_graph.py`: Multi-file AST parser & typed dependency graph generator (`networkx`).
- [ ] `src/retrieval/budget_selector.py`: Hybrid lexical-graph ranking with strict token knapsack pruning.
- [ ] `src/repair/evidence_gate.py`: Structured hypothesis gate, diff patch applier, AST syntax validator, and isolated pytest sandbox.
- [ ] `src/controller/compute_controller.py`: Telemetry tracker, memory guard, and adaptive fallback controller.
- [ ] `src/llm/gemma_client.py`: Ollama API client (`gemma2:2b`), token estimator, and deterministic offline oracle.
- [ ] `src/agent/bagr_agent.py`: Unified BAGR Agent pipeline combining all four cooperating mechanisms.

## Phase 3: Benchmark Suite (`benchmarks/`)
- [ ] Multi-file SWE Bug 1: `ecommerce_tax`: Off-by-one regional tax calculation across config and pricing engine.
- [ ] Multi-file SWE Bug 2: `cache_invalidation`: Stale LRU cache key mismatch during multi-threaded updates.
- [ ] Multi-file SWE Bug 3: `data_serializer`: Schema validation regression handling nullable fields in nested JSON.
- [ ] Multi-file SWE Bug 4: `token_bucket_limiter`: Race condition in rate limiter time window calculation.
- [ ] Multi-file SWE Bug 5: `graph_cycle_detector`: Recursion error on self-referential graph edges.

## Phase 4: Ablation Experimentation & Empirical Verification (`experiments/`)
- [ ] Build automated runner `experiments/run_ablation.py`.
- [ ] Execute Condition 1: Pure Keyword (BM25/grep) baseline.
- [ ] Execute Condition 2: Dense Embedding baseline.
- [ ] Execute Condition 3: Unconstrained Graph baseline.
- [ ] Execute Condition 4: Full BAGR pipeline.
- [ ] Export empirical metrics: Pass@1, Context Tokens, Peak RAM, Latency to `experiments/results.json` and CSV.

## Phase 5: Verification & Unit Testing (`tests/`)
- [ ] Unit tests for AST parser & Graph builder.
- [ ] Unit tests for Budget selector & Knapsack packing.
- [ ] Unit tests for Patch applier & Sandbox executor.
- [ ] Run test suite with `pytest` and record 100% pass rate.

## Phase 6: Formal Research Paper & Interactive Artifacts (`paper/`, `docs/`)
- [ ] Write 3,000-word conference-style paper in `paper/paper_writeup.md` compliant with Kaggle Writeup guidelines.
- [ ] Generate arXiv-ready LaTeX version in `paper/paper.tex`.
- [ ] Build interactive research dashboard in `docs/index.html` with real-time ablation charts and graph visualization.
- [ ] Deliver final synthesis to user.
