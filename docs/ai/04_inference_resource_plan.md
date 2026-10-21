# Stage 03 — Conditional Inference Resource Plan

> Status: `UNVERIFIED_HARDWARE / NO_CAPACITY_BASELINE` · 2026-10-21 · Estimates are analytical planning aids, not measurements, procurement specification or deployment approval. Applies to candidate vLLM only.

## 1. Required internal environment inventory

| Component | Actual value | Evidence owner |
|---|---|---|
| GPU model/count/VRAM / GPU topology | `UNVERIFIED` | Infrastructure/SRE |
| CPU cores/architecture and host RAM | `UNVERIFIED` | Infrastructure/SRE |
| Available storage, model registry/import bandwidth | `UNVERIFIED` | Infrastructure/SRE |
| GPU driver, CUDA toolkit/runtime, PyTorch build | `UNVERIFIED` | SRE/MLOps |
| OS, containers, install restrictions | `UNVERIFIED` | SRE/Security |
| Network segmentation, egress, air-gap, TLS/identity | `UNVERIFIED` | Security/Network |
| Approved model artifact and tokenizer directory/hash | `UNVERIFIED` | Supply Chain/Security |
| Model/request workload, length distribution, burst and SLO | `OPEN / OD-02/12` | Product Owner/SRE |
| Operational headroom and expansion capacity | `UNVERIFIED` | Infrastructure |

Without these facts a definite GPU SKU, concurrency, response time, number of servers or quantization cannot be selected.

## 2. Transparent memory estimates (not empirical VRAM)

Unquantized theoretical weight storage `parameters × bytes_per_parameter` (ignores framework kernels, tensors, alignment, temporary activations, allocator overhead). BF16/FP16 uses 2 bytes/parameter:

| Candidate | Public parameter count | Weight-only BF16 estimate | Native/context claims |
|---|---:|---:|---|
| Qwen2.5-7B-Instruct | ~7.62B | ~15.24 GB decimal (~14.19 GiB) | Advertised 131,072 tokens; deployment configuration-dependent |
| Qwen3-14B | ~14.8B | ~29.60 GB decimal (~27.57 GiB) | 32,768 native; >32k via YaRN up to advertised 131,072; untested |

**KV cache estimate** for full-context, non-sliding GQA BF16 under a simplified implementation:

`KV_bytes = 2 (K,V) × num_layers × num_kv_heads × head_dim × bytes_per_element × cached_tokens × concurrent_sequences`.

- Qwen2.5-7B-Instruct: 28 layers × 4 KV heads × 128 head dimension → 57,344 bytes/token (~56 KiB/token). One 32,768-token sequence ≈ 1.75 GiB KV.
- Qwen3-14B: 40 layers × 8 KV heads × 128 head dimension → 163,840 bytes/token (~160 KiB/token). One 32,768-token sequence ≈ 5.00 GiB KV.
- These calculations assume 2-byte cache elements and one full sequence, no cache reuse/paging savings, prefix caching, speculative decoding, fragmentation, block allocation, concurrency multiplication, TP partitioning or vLLM implementation variations. Actual peak GPU allocation may differ materially.
- Weight-plus-KV for one maximum-length Qwen3 request is therefore already roughly 32.57 GiB before all runtime overhead and headroom; it is **not** a validated minimum GPU VRAM specification. Quantized weights reduce only weight-storage portion; compatible engine, accuracy loss, KV dtype and kernel support remain unverified.
- Never assume the larger advertised YaRN context fits a deployed GPU or retains quality. Compare 8k, 16k, 32k and approved extended-context tiers, measuring actual tokenization and OOM.

No throughput or optimal concurrency can be derived reliably from parameter count. Suggested process: first baseline concurrency=1 with bounded short cases, then increase load only after monitoring free/peak VRAM and stability; abort before risky memory saturation. Admit jobs with internal server queue/admission controls sized from measurements, not this spreadsheet estimate.

## 3. Authorized on-prem read-only inventory

Run **on the internal server**, and store output in approved internal storage only:

```bash
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free --format=csv
uname -a
lscpu
free -h
df -h
python --version
python -m pip show vllm torch transformers
vllm --version
```

Missing commands return `UNVERIFIED`; never claim success. Record exact CUDA driver compatibility from the local approved driver/runtime output.

Before any import/serve, Security/SRE must separately approve local artifact transfer and check license, revision, tokenizer/chat templates, per-file SHA-256 and model-specific permissions. Model metadata lookup from upstream is **research only**, not authority to download or connect inference to the internet.

## 4. Conditional offline vLLM experiment (server only)

First verify the installed version's `vllm serve --help`, model support and any need for model-specific reasoning-parser and structured-output settings. Do not assume the following generic serving command supports either model unchanged:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export MODEL_DIR="/approved/internal/model-directory"
export MAX_MODEL_LEN="8192"
test -d "$MODEL_DIR" || exit 1
test -f "$MODEL_DIR/config.json" || exit 1
vllm serve "$MODEL_DIR" --host 127.0.0.1 --port 8000 --max-model-len "$MAX_MODEL_LEN"
```

Paths and model length above are **explicit illustrative parameters requiring organization-approved replacement**; do not execute on a real host without security approval. Bind to localhost during initial probe and expose only through later approved private networking; no exposed public interface, external downloads, provider fallbacks or uncontrolled prompt logs. `MAX_MODEL_LEN=8192` is an initial test tier **not** a published model limit or approved production setting.

For each pinned experimental run: log GPU utilization/VRAM sampled throughout, latency P50/P95 at explicit concurrent request counts, generated tokens per second, model failures, OOM and context truncations, with same approved synthetic dataset and parameters across candidates. Stop an experiment on error/resource cap per SRE safety policy. Exact timeouts, error budgets, GPU headroom and power limits await `OD-12/13` decisions.

## 5. Risk register, decisions and no-go conditions

| Risk | Severity / effect | Owner and decision |
|---|---|---|
| Inadequate or unknown GPU | HIGH: cannot establish load/context feasibility | Infrastructure/SRE → OD-13 |
| Unapproved model/weights/tokenizer | CRITICAL: license and supply-chain exposure | Legal/Security → artifact admission |
| External egress or raw-prompt logs | CRITICAL: confidentiality breach | Security/Network → no-egress controls |
| No expert dataset/quality gate | HIGH: cannot select a truthful model | AI Lead/SMEs/PO → OD-14 |
| Long-context KV/OOM or degraded accuracy | HIGH: invalid throughput and scores | MLOps/SRE + AI Lead → actual load tests |
| Thresholds and workload unknown | HIGH: no procurement/SLO capacity proof | PO/SRE → OD-02/12 |
| Quantization compatibility/quality unknown | MEDIUM/HIGH: silent accuracy regression | AI Lead/MLOps → separately pinned benchmark |

**Decision state: `BLOCKED` for capacity-based runtime/model selection; infrastructure plan `UNVERIFIED`.** The alternative is not to guess a 24/48/80GB GPU configuration. A purchase, production allocation, hardware increase, and network policy change each require the real inventory, benchmarks and the appropriate owner approval.

Traceability: [Candidate models](01_model_selection.md) · [Protocol](02_benchmark_protocol.md) · [Results](03_benchmark_results.md).
