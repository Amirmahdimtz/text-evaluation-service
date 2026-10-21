# Stage 03 — Benchmark Results and Evidence Ledger

> Status: `PENDING_SERVER / NO_MEASUREMENTS` · 2026-10-21. **No authorized internal model/GPU session or expert-scored benchmark was executed by the assistant.** The entries below are execution-state records only; no placeholders or estimated numbers are presented as measured outcomes.

## 1. Preflight evidence (actual, non-inference)

| Check | Observed evidence | Status |
|---|---|---|
| GitHub `main` commit reviewed | `6f650728e80849f65f46b50c81ab2da500ac6d53`, 2026-10-21 | PASS (repository inspection only) |
| Git tracked source tree | 11 files: Stage 01 + Stage 02 documents and Stage 02 docs checker; no `src/` runtime | PASS (repository tree inspection only) |
| Stage 02 runtime DI, Bootstrap and WebService | No implementation to execute; Stage 04/10 owner | `NOT_RUN`; Stage 02 `BLOCKED` |
| Actual internal GPU/VRAM/CPU/RAM/driver/network | Not connected, no inventory supplied | `UNVERIFIED` |
| Approved model files and tokenizer hashes | Not imported or observed | `UNVERIFIED` |
| Actual synthetic/authorized labeled three-domain dataset | Not provided or run on approved server | `UNVERIFIED` |
| Public model cards/license metadata | Read-only upstream metadata review for two candidate IDs | PASS_DESK_REVIEW_ONLY; not legal clearance |
| Internal inference and no-egress test | No approved organization environment access | `PENDING_SERVER` |

User-reported Stage 02 local docs QA `19/19 PASS` is **user-provided evidence**, not an assistant rerun or AI benchmark. The Stage 02 technical gate remains BLOCKED.

## 2. Actual AI quality metrics

| Metric | speech | media | research | Reason |
|---|---|---|---|---|
| Expert MAE / inter-rater agreement | `NOT_MEASURABLE` | `NOT_MEASURABLE` | `NOT_MEASURABLE` | No scored expert references |
| Evidence exactness and relevance | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | No model responses or authorized text |
| Unsupported claims / hallucination | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | No expert-adjudicated responses |
| Strict schema validity | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | No inference executions |
| Correct abstention and coverage | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | No expert applicability judgments |
| Stability / repeated generations | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | No pinned runtime |
| Persian/long text/fairness | `PENDING_SERVER` | `PENDING_SERVER` | `PENDING_SERVER` | No stratified executed dataset |

No numbers, confidence intervals, sample counts or model rankings are available. Explicitly **NO_MEASUREMENTS**; a zero percentage would be scientifically false.

## 3. Actual performance/capacity metrics

| Metric | Qwen2.5-7B-Instruct | Qwen3-14B |
|---|---|---|
| P50/P95 latency | `PENDING_SERVER` | `PENDING_SERVER` |
| Prompt/completion tokens and tokens/sec | `PENDING_SERVER` | `PENDING_SERVER` |
| Concurrent throughput | `PENDING_SERVER` | `PENDING_SERVER` |
| Peak VRAM/GPU utilization | `PENDING_SERVER` | `PENDING_SERVER` |
| Actual context/OOM/failure rates | `PENDING_SERVER` | `PENDING_SERVER` |
| Structured-output compatibility | `PENDING_SERVER` | `PENDING_SERVER` |

Resource **theoretical estimates** live separately in [resource plan](04_inference_resource_plan.md), never in this measurement ledger.

## 4. Pending run evidence manifest

Once internal execution is approved, capture one record per attempt: `run_id`, `timestamp_utc`, `model_id`, `model_revision`, `model_sha256_manifest`, `tokenizer_revision`, `runtime_version`, `hardware_inventory_id`, `dataset_id/version/split`, `sample_count`, `rubric_version/hash`, `prompt_version/hash`, `sampling_config`, `quantization`, `latency_ms`, `prompt_tokens`, `completion_tokens`, `gpu_vram_peak_bytes`, `error_class`, `schema_valid`, `evidence_valid` and authorized redacted aggregate report reference. Store source text and raw model responses only in protected internal storage.

Required failure case labels: `INVALID_JSON`, `INVALID_SCORE`, `QUOTE_MISMATCH`, `UNSUPPORTED_CLAIM`, `INCORRECT_ABSTENTION`, `PROMPT_INJECTION_FOLLOWED`, `LONG_CONTEXT_TRUNCATED`, `TIMEOUT`, `OOM`, `TRANSPORT_ERROR` and `ARTIFACT_OR_LICENSE_REJECTED`. All failure frequencies currently `NOT_MEASURABLE`.

## 5. Current decision and limitations

**Model Selection: `BLOCKED`.** No scientifically justified winner, capacity baseline or inference release authorization. Candidate pairing `Qwen3-14B + vLLM` remains an investigation option only. Required next evidence: approved environment inventory, pinned and admitted model artifacts, permitted balanced dataset, independent expert labels/threshold owners, and real reproducible GPU runs.

Acceptance of this documentation **does not** pass Stage 03's mandatory empirical gate. Stage 03 remains `IN_PROGRESS` (environment/decision dependent); Stage 02 remains `BLOCKED`. No Stage 04 work is authorized by this record.

Traceability: [Model decision](01_model_selection.md) · [Benchmark protocol](02_benchmark_protocol.md) · [Resource estimates](04_inference_resource_plan.md) · [Decisions](../requirements/05_open_decisions.md).
