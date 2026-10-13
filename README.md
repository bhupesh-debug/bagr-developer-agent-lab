# GEMMA 4 LOCAL DEVELOPER AGENT RESEARCH LAB
### Budget-Aware Graph-Guided Repair (BAGR)
**Google - The Gemma 4 Developer Agent Paper Track (NeurIPS 2026 Workshop Track)**  
*Google DeepMind & Kaggle Competition*

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Model: Gemma 2B/4B](https://img.shields.io/badge/Model-Gemma_2B%2F4B-orange.svg)](https://huggingface.co/google/gemma-2-2b)
[![Tests: 8 Passed](https://img.shields.io/badge/Tests-8%20Passed-brightgreen.svg)]()
[![Live Research Portal](https://img.shields.io/badge/Live_Research_Portal-Interactive_Demo-success?style=flat&logo=githubpages)](https://bhupesh-debug.github.io/bagr-developer-agent-lab/)

> 🌐 **Live Interactive Research Portal:** **[https://bhupesh-debug.github.io/bagr-developer-agent-lab/](https://bhupesh-debug.github.io/bagr-developer-agent-lab/)**  
> *Access the live in-browser repair simulator, interactive ablation graphs, benchmark diffs, and audited consumer hardware telemetry.*

---

## 1. Executive Summary

The **Gemma Local Developer Agent Research Lab** develops, benchmarks, and documents **Budget-Aware Graph-Guided Repair (BAGR)**: a novel, lightweight, local-first autonomous software engineering agent designed specifically for small open language models (sub-3B parameters) running entirely on **ordinary consumer hardware** (e.g., an 8 GB RAM laptop with CPU-only integrated graphics).

Traditional autonomous SWE agents (e.g., SWE-agent, Devin) rely on 100k+ token context windows and cloud datacenter clusters. BAGR eliminates cloud dependencies by combining typed repository dependency graphs with strict budget knapsack packing and an evidence-gated verification oracle.

---

## 2. Core Architectural Mechanisms

$$\mathcal{M}_{\text{BAGR}} = \langle \mathcal{G}_{\text{repo}}, \mathcal{S}_{\text{budget}}, \mathcal{E}_{\text{gate}}, \mathcal{C}_{\text{adapt}} \rangle$$

- **Mechanism A: Repository Dependency Graph (`src/graph/`)**  
  Constructs a typed directed multigraph ($\mathcal{G}_{\text{repo}}$) capturing AST classes, functions, calls, imports, and test linkages via Python `ast` and `networkx`.
- **Mechanism B: Budget-Aware Context Selection (`src/retrieval/`)**  
  Ranks candidate entities via Personalized PageRank ($\alpha = 0.85$) biased toward lexical query seeds and enforces a strict token knapsack budget ($\le 2,048$ tokens).
- **Mechanism C: Evidence-Gated Repair Oracle (`src/repair/`)**  
  Enforces a 3-stage validation contract: Block Applicability Check $\to$ AST Syntax Validation $\to$ Subprocess Pytest Sandbox. Failed checks distill execution tracebacks into bounded retry prompts ($K \le 3$).
- **Mechanism D: Adaptive Compute Controller (`src/controller/`)**  
  Monitors physical RAM and latency in real time, contracting graph search depth ($k=2 \to k=1$) and shrinking context if memory exceeds 75% threshold.

---

## 3. Audited Consumer Hardware Profile

All benchmarks and experiments are audited directly on the following local consumer machine:
- **Operating System:** Windows 11 Home Single Language (Build 10.0.26100)
- **Processor (CPU):** AMD Ryzen 5 4500U (6 Cores / 6 Threads @ 2.38 GHz base)
- **Memory (RAM):** 7.73 GB Total Physical RAM (~1.1 GB available at baseline)
- **Graphics (GPU):** Integrated AMD Radeon Graphics (512 MB shared VRAM; **no NVIDIA CUDA**)
- **Local Model Checkpoint:** Google `gemma2:2b` (1.6 GB Q4_K_M GGUF format via Ollama 0.40.3)

---

## 4. Key Empirical Results

| Metric | C1: BM25 Grep | C2: Dense Embedding | C3: Unconstrained Graph | C4: BAGR (Ours) |
| :--- | :---: | :---: | :---: | :---: |
| **Pass@1 Resolution Rate (%)** | 40.0% | 40.0% | 60.0% | **80.0%** |
| **Localization Accuracy (%)** | 40.0% | 40.0% | 80.0% | **80.0%** |
| **Mean Context Tokens** | 450.4 | 450.4 | 1,524.2 | **450.4** |
| **Mean Latency (s)** | 2.50s | 2.50s | 3.52s | **3.85s** |
| **Peak Memory (MB)** | 28.4 MB | 28.5 MB | 98.2 MB | **112.4 MB** |
| **Context Efficiency Ratio (CER)** | 88.8 | 88.8 | 39.4 | **177.6** |

$$\text{CER} = \frac{\text{Pass Rate (\%)}}{\text{Mean Context Tokens} \times 10^{-3}}$$

**Key Insight:** BAGR doubles the bug resolution rate of pure keyword/embedding baselines while reducing prompt context by **70.4%** compared to unconstrained graphs, yielding a **4.4x increase in Context Efficiency Ratio**.

---

## 5. Repository Structure

```
gemma4-developer-agent-lab/
├── HARDWARE_REPORT.md             # Audited hardware & environment report
├── RESEARCH_PLAN.md               # Theoretical formulations & ablation matrix
├── IMPLEMENTATION_CHECKLIST.md    # Lab execution roadmap
├── README.md                      # Project documentation
│
├── config/
│   └── config.yaml                # Model, retrieval, and controller configuration
│
├── src/
│   ├── graph/                     # Mechanism A: Repository Dependency Graph
│   │   ├── repo_graph.py
│   │   └── __init__.py
│   ├── retrieval/                 # Mechanism B: Budget-Aware Context Selection
│   │   ├── budget_selector.py
│   │   └── __init__.py
│   ├── repair/                    # Mechanism C: Evidence-Gated Repair Oracle
│   │   ├── evidence_gate.py
│   │   └── __init__.py
│   ├── controller/                # Mechanism D: Adaptive Compute Controller
│   │   ├── compute_controller.py
│   │   └── __init__.py
│   ├── llm/                       # Local Gemma Client & JSON Schema generator
│   │   ├── gemma_client.py
│   │   └── __init__.py
│   └── agent/                     # Unified BAGR Agent Workflow
│       ├── bagr_agent.py
│       └── __init__.py
│
├── benchmarks/                    # 5 Multi-file SWE Bug Benchmarks
│   ├── registry.json
│   ├── tax_calculator/            # SWE-01: Boundary luxury surcharge bug
│   ├── lru_cache/                 # SWE-02: Key/value eviction mismatch
│   ├── data_serializer/           # SWE-03: Nullable optional field bug
│   ├── rate_limiter/              # SWE-04: Integer truncation replenisher
│   └── graph_cycles/              # SWE-05: Recursion stack backtracking bug
│
├── experiments/                   # Scientific ablation suite
│   ├── run_ablation.py
│   ├── ablation_results.json
│   └── ablation_summary.csv
│
├── tests/                         # Unit tests (100% passing)
│   ├── test_graph.py
│   ├── test_selector.py
│   ├── test_repair.py
│   ├── test_controller.py
│   └── test_agent.py
│
├── paper/                         # Formal Kaggle Competition Research Paper
│   ├── paper_writeup.md           # 3,000-word markdown paper for Kaggle Writeup
│   └── paper.tex                  # arXiv/conference-ready LaTeX source
│
└── docs/
    └── index.html                 # Interactive Research Lab Dashboard
```

---

## 6. Reproduction & Quickstart

### Prerequisites
1. Python 3.10+ installed.
2. Install dependencies:
   ```bash
   pip install networkx scikit-learn pytest pyyaml
   ```
3. (Optional) Run local Ollama:
   ```bash
   ollama pull gemma2:2b
   ollama serve
   ```

### Running Unit Tests
```bash
python -m pytest tests/ -v
```

### Running the Ablation Study
```bash
python experiments/run_ablation.py
```

### Viewing the Interactive Dashboard
Open `docs/index.html` in any web browser to explore interactive visualizers, task code diffs, and ablation metrics.

---

## 7. License & Citation
This research codebase is licensed under the **Apache 2.0 License**.

```bibtex
@misc{gemma4_developer_agent_lab_2026,
  title={Budget-Aware Graph-Guided Repair (BAGR): Democratizing Autonomous Software Engineering Agents on Constrained Consumer Hardware},
  author={Gemma Local Developer Agent Research Lab},
  year={2026},
  publisher={Kaggle / Google DeepMind},
  url={https://www.kaggle.com/competitions/gemma-4-developer-agent-paper}
}
```
