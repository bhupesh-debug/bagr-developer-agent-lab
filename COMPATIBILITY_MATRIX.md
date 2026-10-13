# Compatibility Matrix & Inference Runtime Assessment

**Research Project:** Budget-Aware Graph-Guided Repair (BAGR)  
**Host Environment:** Windows 11 Home, AMD Ryzen 5 4500U, 7.73 GB RAM, No Discrete GPU  
**Audit Date:** 2026-10-12  

---

## 1. Local Model Family & Checkpoint Compatibility

| Model Checkpoint | Format / Quantization | Parameter Count | Resident Memory | Runtime Engine | Execution Mode | Verification Status | Notes |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| **Google `gemma2:2b`** | GGUF `Q4_K_M` | 2.61B | 1.63 GB | Ollama 0.40.3 | CPU (AVX2 Vector) | **VERIFIED ACTIVE** | Primary research target. Model SHA `8ccf136fdd52`, verified responding at `http://127.0.0.1:11434`. |
| **Google `gemma-2-2b-it`** | Safetensors FP16 | 2.61B | 5.20 GB | HuggingFace / Transformers | CPU / RAM Thrashing | **UNSUPPORTED ON 8GB RAM** | Requires >5.2 GB resident RAM. Leaves <2.5 GB for OS; triggers paging. |
| **Google `gemma-2-9b`** | GGUF `Q4_K_M` | 9.24B | 5.80 GB | Ollama | CPU (High Latency) | **NOT RECOMMENDED** | OOM risk under multi-turn context; latency > 45s/turn on 6-core APU. |
| **Google Gemma 4 (Spec)** | Quantized GGUF / ONNX | $\le 4\text{B}$ | $\le 2.5\text{ GB}$ | Provider-Neutral Adapter | CPU AVX2 | **COMPATIBLE (ADAPTER READY)** | Addressed via neutral `GemmaClient` interface with JSON schema output constraints. |
| **Qwen 2.5 / 3 (4B)** | GGUF `Q4_K_M` | 3.8B | 2.45 GB | Ollama | CPU | **VERIFIED BENCHMARK** | Present locally (`359d7dd4bcda`) for cross-model comparative validation. |

---

## 2. Software Dependencies & Toolchain Matrix

| Dependency | Minimum Version | Verified Active Version | Purpose in BAGR Architecture | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Python** | 3.10+ | 3.14.3 (64-bit) | Base programming language runtime | **VERIFIED PASS** |
| **NetworkX** | $\ge 3.2.0$ | 3.6.1 | Repository Dependency Graph (RDG) & PageRank | **VERIFIED PASS** |
| **NumPy** | $\ge 1.26.0$ | 2.4.3 | Matrix operations & array indexing | **VERIFIED PASS** |
| **SciPy** | $\ge 1.11.0$ | 1.17.1 | Power iteration & sparse PageRank solver | **VERIFIED PASS** |
| **Pydantic** | $\ge 2.6.0$ | 2.12.5 | Structured JSON hypothesis parsing & schema validation | **VERIFIED PASS** |
| **PyYAML** | $\ge 6.0.1$ | 6.0.3 | Hierarchical configuration parser (`config.yaml`) | **VERIFIED PASS** |
| **psutil** | $\ge 5.9.8$ | 7.0.0 | Dynamic RAM & process telemetry monitoring | **VERIFIED PASS** |
| **pytest** | $\ge 8.0.0$ | 9.1.1 | Subprocess test sandboxing & regression verification | **VERIFIED PASS** |

---

## 3. Sandboxing & Security Boundaries

* **Subprocess Execution Ceiling:** Pytest sandbox executes with a hard 20-second timeout and isolated environment variables.
* **Network Egress:** Disabled during test execution; no cloud API dependencies.
* **Air-Gapped Privacy:** 100% of code parsing, graph indexing, model inference, and patch verification occurs locally on the client host.
