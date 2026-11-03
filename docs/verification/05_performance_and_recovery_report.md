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

## Simorgh shared vLLM passive GPU/model-list snapshot — 2026-10-31

Operator-reported, non-inference read-only inspection: `nvidia-smi` GPU0 returned **24576 MiB total, 18847 MiB used, instantaneous GPU utilization 0%**. Arithmetic `5729 MiB` difference is **not** a safe capacity allocation, an estimate of free continuous KV cache, or proof that other users are idle. `GET 127.0.0.1:8000/v1/models` returned **HTTP 200** and **one advertised model** (ID redacted); `inference_requests=0`. One endpoint's model count does not inventory all other projects, processes or ports. No load, latency sampling, VRAM pressure test, or non-interference evidence has been gathered. Capacity/availability results stay `NOT_MEASURED`; shared GPU approval/quotas are `PENDING`. [Shared runtime plan](13_stage11_shared_vllm_reuse.md).

## Shared GPU before/after one approved synthetic criterion — 2026-10-31

The Simorgh operator completed one newly approved real `CriterionInference` synthetic POST on the existing shared vLLM endpoint (`HTTP 200`, exact evidence/schema PASS, `6485 ms`, `116` completion tokens, no retries). The attached **two instantaneous GPU0 observations**, each via the non-invasive `nvidia-smi` metadata query, were:

| Time relative to the request | VRAM used | GPU utilization snapshot |
| --- | ---: | ---: |
| Before | 18847 MiB | 0% |
| After | 18847 MiB | 67% |

**Interpretation:** The same recorded VRAM amount at two points shows no **observed net memory increase** at those instants; it does not bound peak/transient VRAM allocation. The after-sample 67% does not identify whose kernel consumed GPU or which other project was queued. A single `6485 ms` request is **not throughput, p50/p95, resource isolation or other projects' latency/error impact**. Preserve all original performance acceptance cells as `NOT_MEASURED` and Stage11 as `BLOCKED`; request actual operator-authorized competing-project monitoring before asserting non-interference. See [shared vLLM runbook](13_stage11_shared_vllm_reuse.md).


## Stage11 measured shared vLLM single-request media timeout — 2026-11-03

One Simorgh operator-run synthetic `media_message_clarity` evaluation on the existing shared local Qwen3-8B-AWQ reported `REQUEST_TIMEOUT` at **45.093 seconds** (`LLM_CIRCUIT_OPEN`, one request attempt, zero retries). During the attempt, Prometheus snapshots every three seconds showed `num_requests_running=1` and `num_requests_waiting=0`, while `kv_cache_usage_perc` rose approximately `0.006→0.011`. This demonstrates extended in-engine processing for an observed request in a low-queue window; it does not prove prefill/decode breakdown, total generated tokens, Thinking mode, GPU utilization during execution or the root cause. Instantaneous idle GPU measurements taken before this run cannot be extrapolated to the run itself.

This is a failed single-request observation, **not** a measured p50/p95 SLO or capacity benchmark. Shared-vLLM aggregate latency for 3 completed historical requests was 8.857 seconds, but these are not isolated to Stage11. Before making any workload/resource decision, use a separately authorized, single synthetic non-thinking diagnostic and then review token generation rate and relevance. No timeout/concurrency or shared server changes were made. Stage11 `BLOCKED`.


## Simorgh non-thinking timeout comparison — 2026-11-03

A follow-up opt-in synthetic `media_message_clarity` evaluation with
`thinking_mode=disabled` and `chat_template_kwargs.enable_thinking=false`
reported `REQUEST_TIMEOUT` after 45.054s, with the fixed 45s deadline,
one local evaluator attempt and no retries. The previous default-thinking
run timed out at 45.093s. Both are **right-censored by the same timeout**,
so the 0.039s difference is not a valid latency comparison, percentile,
or proof that the runtime applied the Qwen3 switch. The deployed runtime
was not modified, and no token-throughput samples were captured during
this non-thinking attempt. The earlier independently sampled running=1,
waiting=0, rising KV fraction applied to the default-thinking run, not
necessarily the non-thinking follow-up. Diagnosing token generation and
the constrained JSON decoding path remains `PENDING_SERVER`; the shared
GPU and database must remain untouched. No Stage11 performance gate passed.


## Stage11 cumulative vLLM token-throughput snapshot — 2026-11-03

Simorgh operator supplied a **read-only, shared-server** `/metrics` scrape:
`generation_tokens_total=1930`,
`prompt_tokens_total=2925`,
`inter_token_latency_seconds_count=1923`,
`inter_token_latency_seconds_sum=186.947`,
`request_generation_tokens_count=3`,
`request_generation_tokens_sum=174`,
`request_decode_time_seconds_count=3`,
`request_decode_time_seconds_sum=7.558`.

Arithmetic: observed cumulative mean inter-token interval
`186.947/1923≈0.0972s/token`, i.e. reciprocal ≈`10.29 tokens/s`
**for the observed token-interval population**. Extrapolating
`512*0.0972≈49.8s` reveals a plausible *budget/deadline mismatch*
with the diagnostic probe's `max_output_tokens=512` and 45s timeout,
even without queue delay. This is a **rough extrapolation**, not a
measured throughput, token count or execution breakdown of the failed
`media_message_clarity` request. The `request_generation_tokens`
histogram recorded 3 requests totaling 174 generated tokens (mean 58).
The counter/histogram populations need not be identical, so the
`1930-174=1756` difference **must not** be interpreted as a count of
wasted tokens, a number of failed requests or per-request output.

Earlier operator samples during a different media probe showed
`running=1`, `waiting=0` with rising KV cache; multiple media
probes have failed at the 45s client deadline, including a
non-thinking variant. The shared-service metrics have no per-project
or per-request attribution and no synchronized before/after counter
deltas. Thus *high output token count relative to deadline* is the
current leading **engineering hypothesis**, not an accepted root cause.
Do **not** change the shared model, timeout, output cap or GPU policies
on this evidence alone. First design a single approved bounded
per-request generation/termination diagnostic with non-sensitive data,
and validate response-contract completeness and output cap against a
representative workload.

Stage11 model/capacity benchmarks remain `PENDING_SERVER`, Stage11
`BLOCKED`, Stage12 `NOT_STARTED`. Reference: vLLM v0.10.2
Production Metrics documentation.
