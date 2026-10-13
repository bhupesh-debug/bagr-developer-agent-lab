# RESEARCH PLAN: BUDGET-AWARE GRAPH-GUIDED REPAIR (BAGR)
**A Reproducible Software Engineering Agent for Small Language Models on Constrained Hardware**  
**Track:** Google - The Gemma 4 Developer Agent Paper Track  
**Author / Lab:** Gemma Local Developer Agent Research Lab  

---

## 1. Abstract & Research Hypothesis

### 1.1 The Fundamental Challenge
State-of-the-art autonomous coding agents (e.g., Devin, SWE-agent, OpenCodeInterpreter) depend heavily on frontier commercial cloud models with 100k+ token context windows and distributed server accelerators. When scaled down to edge hardware (e.g., 8 GB RAM consumer laptops) and quantized small open language models (such as Google Gemma 2B/4B parameters), conventional agent architectures suffer from catastrophic degradation:
1. **Context Smothering:** Long multi-file context windows exceed local memory bounds, degrading reasoning attention and causing out-of-memory crashes.
2. **Keyword Misdirection:** Lexical grep and naive BM25 retrieve syntactically matching lines across unrelated modules while missing deep semantic call chains.
3. **Hallucinatory Success:** Small models generate superficially plausible patches that introduce subtle syntax errors or regress unchanged unit tests.

### 1.2 Core Research Hypothesis
> **Hypothesis $H_1$:** Guiding context selection via an explicitly parsed multi-file **Repository Dependency Graph (RDG)** coupled with strict **Budget-Aware Context Distillation** enables a 2B parameter Gemma model to outperform unconstrained retrieval, achieving higher unit-test pass rates ($\text{Pass}@1$) with $>60\%$ lower context token consumption and $<3.5\text{ GB}$ peak memory.

---

## 2. Theoretical Formulation & Architecture

The BAGR architecture comprises four distinct, ablatable mechanisms:

$$\mathcal{M}_{\text{BAGR}} = \langle \mathcal{G}_{\text{repo}}, \mathcal{S}_{\text{budget}}, \mathcal{E}_{\text{gate}}, \mathcal{C}_{\text{adapt}} \rangle$$

### Mechanism A: Repository Dependency Graph ($\mathcal{G}_{\text{repo}}$)
We model a codebase as a directed typed multigraph:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \tau_v, \tau_e)$$
where:
- $\mathcal{V}$ denotes nodes representing files, classes, functions, and test cases.
- $\mathcal{E}$ denotes directed edges representing `imports`, `calls`, `inherits`, and `tests`.
- $\tau_v: \mathcal{V} \to \{\text{File}, \text{Class}, \text{Function}, \text{Test}\}$
- $\tau_e: \mathcal{E} \to \{\text{IMPORTS}, \text{CALLS}, \text{DEFINES}, \text{TESTS}\}$

### Mechanism B: Budget-Aware Context Selection ($\mathcal{S}_{\text{budget}}$)
Given an issue report query $Q$ with token budget $B_{\max}$ (e.g., 2,048 tokens):
1. **Initial Seed Discovery:** Candidate nodes $v \in \mathcal{V}$ are scored by token overlap and TF-IDF relevance:
   $$S_{\text{seed}}(v) = \text{sim}_{\text{lex}}(Q, \text{doc}(v))$$
2. **Graph Expansion:** For top seed nodes, we compute graph personalized PageRank or $k$-hop neighbor proximity:
   $$S_{\text{graph}}(u) = \sum_{v \in \text{Seeds}} \frac{1}{\text{dist}_{\mathcal{G}}(v, u) + \epsilon}$$
3. **Composite Ranking:**
   $$\text{Score}(u) = \alpha \cdot S_{\text{seed}}(u) + (1 - \alpha) \cdot S_{\text{graph}}(u)$$
4. **Knapsack Context Packing:** Nodes are greedily appended to the prompt until $\sum_{u} \text{Tokens}(u) \le B_{\max}$.

### Mechanism C: Evidence-Gated Repair Loop ($\mathcal{E}_{\text{gate}}$)
Small models cannot be trusted on unstructured output. We enforce a 3-stage validation contract:
1. **Hypothesis Declaration:** The agent must state the failure symptom and proposed root cause.
2. **Unified Diff Generation:** The model produces a syntactically constrained diff or replacement block.
3. **Verification Oracle:**
   $$\text{Applicability Check} \xrightarrow{\text{pass}} \text{AST Syntax Check} \xrightarrow{\text{pass}} \text{Isolated Pytest Execution}$$
   If any gate fails, an automated, compressed traceback (stripped of irrelevant stack frames) is fed back into a bounded retry loop ($K \le 3$).

### Mechanism D: Adaptive Compute Controller ($\mathcal{C}_{\text{adapt}}$)
Tracks real-time telemetry (RAM usage, inference latency per token, retry attempts). If RAM exceeds 80% threshold or latency spikes, the controller automatically contracts graph search depth from 2-hop to 1-hop and truncates file snippets to docstrings and signatures.

---

## 3. Ablation Grid & Experimental Matrix

We evaluate across four experimental conditions on a standardized suite of multi-file software engineering bugs:

| Condition ID | Description | Retrieval Mechanism | Context Budget | Verification Gate |
| :--- | :--- | :--- | :--- | :--- |
| **C1: Baseline Grep** | Lexical grep/keyword search | BM25 / Regex match | Unbounded / 4k | None (single shot) |
| **C2: Dense Embedding** | TF-IDF / Vector similarity | Cosine similarity | 2k fixed | AST Syntax only |
| **C3: Graph Only** | Full RDG without budget control | 2-hop graph closure | 8k (causes paging) | Pytest sandbox |
| **C4: BAGR (Full)** | Budget-Aware Graph-Guided Repair | Hybrid Lexical + RDG | Strict 2k adaptive | Evidence-Gated ($K=3$) |

---

## 4. Key Performance Indicators (KPIs)

1. **Bug Resolution Rate ($\text{Pass}@1$):** Percentage of benchmarks where all declaring and regression tests pass without human intervention.
2. **Localization Accuracy (Top-1 / Top-3):** Percentage of times the true buggy function is included in the retrieved context.
3. **Context Efficiency Ratio ($\text{CER}$):** $\text{CER} = \frac{\text{Pass Rate}}{\text{Average Prompt Tokens} \times 10^{-3}}$.
4. **Peak Memory Consumption (MB):** Highest recorded process RAM during graph build and inference.
5. **Mean Repair Latency (s):** Wall-clock time from issue ingestion to verified patch.
