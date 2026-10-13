# Experimental Data Dictionary & Metric Definitions

This data dictionary outlines the schema of experimental measurements recorded in `experiments/ablation_results.json` and `experiments/ablation_summary.csv`.

## 1. Summary Metrics Table Schema

| Field Name | Type | Range / Format | Description | Business & Research Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `condition_id` | String | Enum (`C1_KEYWORD`, `C2_EMBEDDING`, `C3_UNBUDGETED_GRAPH`, `C4_BAGR_FULL`) | Unique condition code for the experimental arm. | Experimental ablation baseline identifier. |
| `condition_name` | String | Free text | Descriptive label of the retrieval and verification strategy. | Human-readable condition title. |
| `pass_rate_pct` | Float | `[0.0, 100.0]` | Percentage of benchmark bug tasks where all unit tests passed on attempt 1. | Primary success metric (SWE-bench equivalent $\text{Pass}@1$). |
| `localization_acc_pct` | Float | `[0.0, 100.0]` | Percentage of tasks where the true faulty symbol was retrieved into the prompt context. | Diagnostic accuracy of the retrieval mechanism. |
| `mean_context_tokens` | Float | $\ge 0.0$ | Average number of prompt tokens provided to the LLM per repair attempt. | Prompt cost and memory footprint indicator. |
| `mean_latency_seconds` | Float | $\ge 0.0$ | Wall-clock execution time per issue resolution episode in seconds. | Developer feedback latency. |
| `peak_memory_mb` | Float | $\ge 0.0$ | Dynamic peak resident memory allocated by the agent pipeline (via `tracemalloc`). | Edge device RAM safety margin. |
| `context_efficiency_ratio` | Float | $\ge 0.0$ | $\text{CER} = \frac{\text{Pass Rate (\%)}}{\text{Mean Context Tokens} \times 10^{-3}}$ | Resolution capability generated per unit of context budget. |

## 2. Benchmark Task Metadata Schema (`benchmarks/registry.json`)

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Standardized benchmark code (e.g., `SWE-01`). |
| `name` | String | Package / repository identifier. |
| `path` | String | Relative filepath to the benchmark package. |
| `test_file` | String | Relative filepath to the test suite triggering the failure. |
| `issue_description` | String | Plain-text bug report describing observed symptoms and reproduction steps. |
| `ground_truth_symbol`| String | Target Python class or function containing the root-cause bug. |
| `expected_patch_type`| String | Nature of code modification required (boundary fix, key swap, exception check). |
