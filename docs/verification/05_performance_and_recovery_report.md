# Stage 11 — Performance, Concurrency and Recovery Results

**State:** `NO_PRODUCTION_REPRESENTATIVE_MEASUREMENTS / PENDING_SERVER`. Prepared 2026-10-28. No live GPU/load/restore/fault-injection run performed.

## Required approved environment

Named Infra/SRE/DBA/MLOps owners, resource isolation from existing services, corporate staging and approved synthetic load, verified model revisions and artifact manifest, protected test-only DB with safe backup, reviewed throttling and concurrency caps, network and monitoring authorization, defined stop conditions, actual approved SLO/latency/throughput/RPO/RTO and rollback procedure.

Stage03 resource estimates are analytical only. Historical GPU observations in Stage04 were not capacity tests and are not current capacity commitments. In particular, do not start a second heavy model on a shared GPU without measured free VRAM and SRE approval.

## Measurement ledger

| Real acceptance metric | Source identifiers | Actual measurement | Acceptance limit |
|---|---|---|---|
| API latency p50/p95/p99, success/error rate | `S10-S11-07` | `NOT_MEASURED` | `OD-12 OPEN` |
| Model TTFT/latency and token throughput | `S07-S11-05`, `S11-AI-10` | `NOT_MEASURED` | `OD-12/13 OPEN` |
| GPU peak VRAM/utilization, context limit, OOM rate | `S11-AI-01/10`, `S08-S11-03` | `NOT_MEASURED` | `OD-12/13 OPEN` |
| Queue age/depth/wait, retries/dead letter | `S09-S11-01/02/04` | `NOT_MEASURED` | `OD-10/12 OPEN` |
| Multi-worker fencing, lease recovery, DB connection safety | `S05-S11-03`, `S09-S11-01/06` | `NOT_MEASURED` | `OD-10 OPEN` |
| Bounded load/spike/soak, shutdown and backpressure | `S04-S11-10`, `S09-S11-02/06` | `NOT_MEASURED` | `OD-12 OPEN` |
| Backup/restore measured RPO/RTO and recovery | `S04-S11-08/10`, `S05-S11-02/05` | `NOT_MEASURED` | `OD-08/12 OPEN` |

## Safe order for future measurements

Obtain signed permission and exact stop/abort criteria before load or failure injection. Capture zero-load baseline under pinned versions; increase request rate and GPU concurrency only within approved bounds, monitor saturation; safely test timeouts, crash/restart, retry/fencing, DB/network errors, restore and steady-state soak **only in isolated staging**. Record exact denominators, full latency distribution and censoring/timeouts, GPU/DB/wait/queue counters, competing workload isolation, incident/alerts and redacted trace references. Failure is not normalized away as success.

**Conclusion:** There is no measured throughput, latency, VRAM, durability or DR acceptance yet. No sizing/procurement or Production-ready claim may be made.

## Host-local passive hardware observation — operator report, 2026-10-28

The [read-only Stage11 preflight](07_stage11_readonly_preflight.md) was run by the Simorgh operator on commit `e29537b` and observed 1 NVIDIA RTX 3090 with 24,576 MiB reported VRAM total, 18,847 MiB used and driver 570.124.06, plus 24 logical CPUs, 96,513 MiB total RAM (79,782 MiB available) and 359.03 GiB free on the root filesystem. This is a **single metadata snapshot**, not reserved inference capacity, sustained throughput, p95 latency, model runtime identification, CUDA compatibility, GPU stress test, safety headroom, or production SLO evidence. Only 5,729 MiB arithmetic VRAM difference appeared free; DO NOT start another model based on it. `S11-AI-01`, `S07-S11-05`, and `S11-AI-10` remain `PENDING_SERVER`; all measured acceptance cells above remain `NOT_MEASURED`. Require isolated staging, explicit approved limits and infrastructure ownership before any load or actual inference.

## One-request real inference timing (not capacity or latency baseline) — operator report, 2026-10-28

The Simorgh one-shot synthetic structured-output smoke reported **`elapsed_ms=149`** for a single POST request with HTTP 200, 70 prompt tokens, 10 completion tokens (80 total), `finish_reason=stop` and strict tiny schema validation. This timer covers the smoke tool's POST path and excludes the separate metadata GET; it is **one observation**, not p50/p95/p99, throughput, GPU peak VRAM, concurrency capacity, SLA compliance, steady-state performance, or model initialization latency. No operator-authorized additional request, load, soaks, fault injection or recovery drill occurred. Existing 24-GiB RTX 3090 single-snapshot inventory and 149ms one-shot timing **cannot** justify a second model load or production SLO signoff. Capacity, monitoring, error budgets, DR/RPO/RTO and remaining organizational tests are still `PENDING_SERVER` / `NOT_MEASURED`. [Smoke evidence](09_stage11_single_inference_smoke.md).
