# Architecture Specification: Budget-Aware Graph-Guided Repair (BAGR)

## 1. System Philosophy & Objectives
BAGR is designed to democratize autonomous software engineering agents by operating entirely on consumer hardware (x86-64 CPU, 8 GB RAM, no GPU) with sub-3B parameter open models (Google Gemma 2B). It replaces massive context windows and cloud GPUs with structured AST program analysis, graph-based context packing, and an evidence-gated verification loop.

## 2. Four-Component Architecture

$$\mathcal{M}_{\text{BAGR}} = \langle \mathcal{G}_{\text{repo}}, \mathcal{S}_{\text{budget}}, \mathcal{E}_{\text{gate}}, \mathcal{C}_{\text{adapt}} \rangle$$

```
+-----------------------------------------------------------------------------------+
|                            BAGR SYSTEM ARCHITECTURE                               |
+-----------------------------------------------------------------------------------+
                               [Issue Report]
                                     |
                                     v
                       +-----------------------------+
                       |    Seed Keyword Discovery   |
                       +-----------------------------+
                                     |
    [Local Codebase]                 v
           |           +-----------------------------+
           +---------->| Mechanism A: Repo Graph     | (AST Visitor: Files, Classes,
                       | (Multi-File RDG Engine)     |  Functions, Calls, Imports)
                       +-----------------------------+
                                     |
                                     v
                       +-----------------------------+
                       | Mechanism B: Budget Packing | (Personalized PageRank +
                       | (Knapsack Context Selector) |  <= 2048 Token Knapsack)
                       +-----------------------------+
                                     |
                                     v
                       +-----------------------------+
                       | Local Google Gemma Model    | (Ollama gemma2:2b Q4_K_M
                       | (Structured JSON Repair)    |  CPU AVX2 Vector Execution)
                       +-----------------------------+
                                     |
                                     v
                       +-----------------------------+
                       | Mechanism C: Evidence Gate  | (Applicability -> AST Syntax ->
                       | (3-Stage Verification)      |  Pytest Sandbox Isolation)
                       +-----------------------------+
                                 /         \
                      [PASS]    /           \    [FAIL]
                               v             v
                     [Verified Patch]   +-----------------------------+
                                        | Mechanism D: Adaptive Ctrl  | (Distilled Traceback,
                                        | (Dynamic Contraction)       |  K <= 3 Retries)
                                        +-----------------------------+
                                                     |
                                                     +---- Loops to Context Selector
```

### Mechanism A: Multi-File Repository Dependency Graph (`src/graph/`)
- Traverses Python ASTs (`ast.NodeVisitor`) to parse all declarations and dependencies.
- **Node Types:** `FileNode`, `ClassNode`, `FunctionNode`, `TestNode`.
- **Edge Types:** `DEFINES`, `CALLS`, `IMPORTS`, `TESTS`.
- **Complexity:** $O(|\mathcal{V}| + |\mathcal{E}|)$, taking $<0.25\text{s}$ to index multi-file repositories.

### Mechanism B: Budget-Aware Context Selection (`src/retrieval/`)
- Computes lexical seed relevance across node signatures and docstrings.
- Propagates structural importance using Personalized PageRank ($\alpha = 0.85$).
- Enforces hard token budget ($\le 2,048$ tokens) using greedy knapsack packing.
- When an entity exceeds capacity, it degrades gracefully to signature + docstring.

### Mechanism C: Evidence-Gated Repair Oracle (`src/repair/`)
- **Stage 1 (Applicability):** Exact/normalized contiguous block replacement matching.
- **Stage 2 (Syntax Validation):** `ast.parse()` ensures zero `SyntaxError` regressions.
- **Stage 3 (Pytest Sandbox):** Subprocess isolation with a 20-second hard timeout.
- Distills $>100$ lines of verbose Pytest output into $<25$ lines of root-cause traceback.

### Mechanism D: Adaptive Compute Controller (`src/controller/`)
- Continuously profiles memory (`tracemalloc`, `psutil`) and wall-clock latency.
- Contracts graph radius ($k=2 \to k=1$) if system RAM allocation passes 75% safety ceiling ($6,500\text{ MB}$).
- Caps retry loops at $K=3$ attempts.
