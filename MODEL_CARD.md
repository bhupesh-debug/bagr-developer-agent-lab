# Model Card: Google Gemma 2B/4B in BAGR Architecture

## 1. Model Details
- **Architecture Name:** Budget-Aware Graph-Guided Repair (BAGR)
- **Base Foundation Model:** Google Gemma 2 (2B / 4B Parameter variant)
- **Quantization:** 4-bit Medium (`Q4_K_M` GGUF)
- **Inference Runtime:** Ollama / `llama.cpp` on x86-64 CPU vector instructions (AVX2/FMA)
- **Context Window:** Constrained to $\le 2,048$ tokens (budget-enforced via greedy knapsack)
- **License:** Gemma Open Terms of Use & Apache 2.0 (code wrapper)
- **Release Date:** October 2026
- **Primary Reference Track:** Google - The Gemma 4 Developer Agent Paper Track (NeurIPS 2026 Workshop Track)

## 2. Intended Use & Domain Scope
- **Primary Intended Use:** Fully offline, deterministic, and verifiable multi-file repository bug repair on consumer hardware (e.g., 8 GB RAM laptops with no discrete GPU).
- **Target Tasks:** Synthesizing targeted code diffs to fix unit test failures, regression bugs, off-by-one errors, and interface mismatches.
- **Out-of-Scope Use Cases:** Unsupervised arbitrary code execution outside test sandboxes; broad-scale code generation without test suites; malicious vulnerability exploitation.

## 3. Hardware Profile & Resource Footprint
- **Target Hardware:** AMD Ryzen 5 4500U (6 Cores, 2.38 GHz base), 7.73 GB RAM, integrated graphics (no CUDA).
- **Resident Model Size:** ~1.63 GB resident RAM during inference.
- **Peak System RAM during Pipeline:** $\le 115\text{ MB}$ dynamic overhead beyond base model weights.
- **Total Operational System RAM:** $\le 2.2\text{ GB}$, leaving over 5.5 GB available for OS and background tasks.
- **Inference Latency:** Mean $2.5\text{s} - 3.8\text{s}$ per repair hypothesis turn on CPU.

## 4. Training & Adaptation Methodology
- **Zero-Shot External Graph Guidance:** Unlike fine-tuned coding models that require massive compute to retrain, BAGR uses the frozen base Gemma weights.
- **Structural Retrieval:** A multi-file Repository Dependency Graph (RDG) using Abstract Syntax Tree (AST) visitors extracts code symbols, call relationships, and test linkages.
- **Token Budget Knapsack:** Personalized PageRank ($\alpha = 0.85$) ranks relevant symbols, and a greedy knapsack algorithm packs the most critical symbol bodies into prompt context without exceeding token ceilings.

## 5. Evaluation & Performance Metrics
Evaluated on the standardized 5-task multi-file software engineering benchmark suite (`SWE-01` through `SWE-05`):
- **Pass@1 Resolution Rate:** **80.0%** (outperforming BM25 keyword at 40.0% and TF-IDF embedding at 40.0%).
- **Localization Accuracy:** **80.0%** top-1 target symbol localization.
- **Context Token Footprint:** **450.4 tokens** mean context (a 70.4% reduction vs unconstrained graphs).
- **Context Efficiency Ratio (CER):** **177.6** ($4.5\times$ higher than unconstrained retrieval).
- **Syntax Integrity:** 100% of generated patches verified prior to test execution via AST parsing.

## 6. Ethical Considerations & Safety
- **Air-Gapped Privacy:** Code, proprietary business logic, and IP never leave the local machine.
- **Deterministic Sandboxing:** All test executions occur in isolated Python subprocesses with a 20-second timeout ceiling to mitigate accidental infinite loops or resource starvation.
