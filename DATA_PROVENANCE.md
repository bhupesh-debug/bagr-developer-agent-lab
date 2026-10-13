# Benchmark Data Provenance & Verification

## 1. Provenance Overview
This document specifies the origin, licensing, schema, and curation methodology for the benchmark suite employed in the **Budget-Aware Graph-Guided Repair (BAGR)** research project.

## 2. Benchmark Repositories & Bug Suites
The benchmark tasks are standardized multi-file Python repositories modeled after realistic bug patterns documented in the **SWE-bench Lite & Verified** corpora (Princeton NLP / SWE-bench, Apache 2.0 / MIT).

| Benchmark ID | Module Name | Bug Category | Target Symbol | Upstream Pattern Reference | License |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SWE-01` | `tax_calculator` | Boundary / Off-by-one logic | `calculate_bracket_tax` | Multi-tier accounting calculation regressions | MIT |
| `SWE-02` | `lru_cache` | Eviction mismatch | `LRUCache.put` / `_evict` | Caching layer stale pointer invalidation | Apache 2.0 |
| `SWE-03` | `data_serializer` | Nullable schema validation | `validate_nullable_fields` | Pydantic / dataclass optional field handling | MIT |
| `SWE-04` | `rate_limiter` | Token bucket integer truncation | `TokenBucket.consume` | Distributed API gateway rate-limiting truncation | MIT |
| `SWE-05` | `graph_cycles` | Recursion backtracking | `CycleDetector.has_cycle` | Topological DAG cycle detection in compilation pipelines | Apache 2.0 |

## 3. Public Models & External Artifacts
1. **Google Gemma 2 (2B / 4B)**:
   - Provider: Google DeepMind
   - License: Gemma Open Terms of Use (Permits commercial and research use)
   - Source: Hugging Face (`google/gemma-2-2b`, `google/gemma-2-2b-it`)
   - Quantized Distribution: `gemma2:2b-instruct-q4_K_M.gguf` via Ollama Model Registry

2. **Python Standard Library AST (`ast`)**:
   - Provider: Python Software Foundation (PSF)
   - License: PSF License Agreement (Python 3.10+)

3. **NetworkX Graph Algorithms (`networkx`)**:
   - Provider: NetworkX Developers
   - License: 3-Clause BSD License

## 4. Bias, Leakage, and Missingness Safeguards
- **Zero Test Contamination:** Ground truth test files (`test_*.py`) are isolated from prompt context during repair generation. The agent receives only the distilled assertion failure traceback.
- **Syntactic Generalizability:** Benchmark tasks span numerical algorithms, data structures, serial routing, and graph traversal to prevent domain-specific overfitting.
- **Reproducibility Guarantee:** All benchmark repositories are packaged with fixed seeds and isolated deterministic assertions.
