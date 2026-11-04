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

## Stage11 bounded response-and-metrics diagnostics — 2026-11-03

New **opt-in** single-domain diagnostic distinguishes (a) **actual server-reported per-response** `prompt_tokens`/`completion_tokens`/`total_tokens` and `finish_reason` only after the complete HTTP JSON envelope arrives, from (b) **unattributed shared Prometheus deltas** sampled immediately before and after the request. Response JSON syntax (`valid`/`invalid`/`UNAVAILABLE`) is separate from existing schema/rubric validation. On client timeout, finish-reason and per-response token counts are **UNAVAILABLE**, not zero or inferred from the metrics delta. Histogram counters can reset and other tenants can contribute; output states `SHARED_SERVICE_UNATTRIBUTED`.

Default Stage11 probe remains 512 output tokens and 45s timeout, one concurrent request, no retry. Only a single selected synthetic criterion with `--diagnostics --max-output-tokens 256` can opt into a reduced cap, as a potential latency experiment. An incomplete response with `finish_reason=length` remains a **FAILED contract**. Metrics GET is loopback-only, two reads maximum, each ≤3s and ≤2 MiB, no environment proxy or redirects. No shared GPU, database or container settings were changed.

[CI run 41656742019](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41656742019): **59+131 offline tests PASS**, with in-memory Provider/HTTP mocks. Actual low-token live measurements are still `PENDING_SERVER`, and Stage11 capacity/performance acceptance gates remain `BLOCKED`.

## Simorgh real 256-token diagnostic — 2026-11-03

Measured local response time **23.427s**, response usage **558 prompt / 256 completion / 814 total tokens**, `finish_reason=length`; completion was at the configured 256-token cap and produced invalid JSON, rejected as `LLM_INCOMPLETE_GENERATION`. Read-only shared-service metrics changed by `+256` generated tokens and `+23.352864s` decode time (inter-token count `+255`, sum `+23.352864s`). As a descriptive per-window reciprocal, `256/23.352864≈10.96 tokens/s` (not an accredited sustained throughput baseline). Extrapolating the decode duration to 512 tokens at the same rate gives **about 46.7s** before overhead, beyond the probe's 45s timeout. **It is a model-based estimate, not a measured 512-token latency.** Earlier 512-token requests were right-censored by the 45s client timeout, and no completed per-request usage was available for them.

There was no automatic retry or model/container/server configuration change. A shorter output budget reduces latency but is **not a valid fix** when it truncates JSON. The minimum safe completion budget for this rubric/schema and the latency distribution remain `UNMEASURED`; any future change needs isolated, authorized measurement and structural/semantic validation. Shared Prometheus deltas are `SHARED_SERVICE_UNATTRIBUTED`, despite matching the one response's usage. Stage11 performance gate remains `BLOCKED`.


## Stage11 prompt 0.3 real media timeout — 2026-11-03

**Operator-run live synthetic media diagnostic after Prompt version 0.3:** exactly one `media_message_clarity` criterion, `--execute-live --domain media --disable-thinking --diagnostics`, max 512 completion tokens, 45-second client timeout, no retries. At **45,034 ms** the Provider reported `LLM_CIRCUIT_OPEN` with `failure_kind=REQUEST_TIMEOUT`. Response metadata was **not received**: `finish_reason=UNAVAILABLE`, `json_syntax=UNAVAILABLE`, `reported_usage=null`. No complete JSON, score or evidence resulted.

The **shared-service, unattributed** before/after Prometheus deltas were `generation_tokens_total +401`, `prompt_tokens_total +635`, `inter_token_latency_seconds_count +400`, `inter_token_latency_seconds_sum +44.876778s`, `request_generation_tokens_count +0`, `request_decode_time_seconds_count +0`, `request_success_total +0`, `num_preemptions_total +0`. This is consistent with sustained generation throughout the timeout window without completed model response. Mean interval 44.876778/400 ≈ 0.11219 seconds/token, reciprocal ≈ 8.91 tokens/s for the **sampled shared-window intervals only**. Generated-token delta +401 is not verified per-request completion usage, and a timeout is not a measured `finish_reason=length`.

Prior version 0.2 media test with a **256-token cap** returned `prompt_tokens=558` for its completed response and failed at `length`/invalid JSON in 23.427s; the new **512-token-capped** test has shared-window `prompt_tokens_total +635`. These are not controlled apples-to-apples prompt-token measurements; the larger observed input delta certainly does **not** demonstrate prompt compression. Version 0.3 has **NOT** shown an operational improvement; do not assert that concise wording reduced output cost or latency. Keep unchanged timeout/cap/runtime for now, investigate the observed decoding throughput and bounded output needs offline, and require separate approved low-load experiments and real quality evidence before changing anything shared.

Stage11 `BLOCKED`; Stage12 `NOT_STARTED`. Not a p95, capacity result, or model-accuracy test.


## Stage11 offline JSON bytes and pending decoder-speed comparison — 2026-11-03

Six synthetic `CriterionInference` examples were serialized with standard
and compact `json.dumps(ensure_ascii=False)`. Both representations passed
the strict typed output decoder with exact quote-offset equality. The media
assessed case used 427 versus 405 UTF-8 bytes (5.15% shorter); abstention
247 versus 232 UTF-8 bytes (6.07% shorter). Across all cases the savings
were 15–22 bytes, **not Qwen token counts**. These samples do not establish
a minimum *semantic* response budget for a real criterion or the ability to
complete under 45 seconds. There is no measured speedup.

A Stage11-only bounded two-arm diagnostic now compares exactly the same
synthetic media requests with `response_format=json_schema` on one arm
versus absent `response_format` on the other. Its default is zero-network,
and it requires explicit live/owner-approval flags to run. Only the fixed
schema constraint differs between wire payloads; this was checked using
in-process HTTPX transport. Each arm has max 256 output tokens, 45s
client deadline, one concurrent request and zero retries. Fail fast on
timeout, with no model text logging and no production Provider changes.
A single ordered pair on shared GPU cannot establish *causal* Structured
Decoding overhead, because outputs may have different content/completion
behavior and background load is uncontrolled.

[GitHub Actions 41667673237](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41667673237)
SUCCESS: 59 preflight tests and 143 focused offline tests. Real decoder
speed comparison is `PENDING_SERVER`; capacity and Stage11 remain BLOCKED.

## 2026-11-04 — shared GPU one-pair decoder experiment observed

Simorgh one ordered pair, both with max 256 completion tokens,
`prompt_tokens=635`, `completion_tokens=256`, disabled Thinking
requested, no retries. The `json_schema` request took **29.118s**;
the unconstrained request took **2.327s**, about **12.51x** lower
elapsed time for the unconstrained arm. These are full request
durations, NOT isolated guided decoder CPU costs or steady-state GPU
tokens/sec. Both responses reached `finish_reason=length`, had
`json_syntax=invalid` and were rejected as
`LLM_INCOMPLETE_GENERATION`.

This result elevates structured decoding overhead from an untested
hypothesis to **strongly supported but unproven** for this deployed
setup. Fixed-order shared GPU, one attempt per arm and potentially
different model output text prevent causal attribution. Do not
extrapolate to production capacity, user-visible quality or
performance SLO. No baseline-valid JSON completion was observed
from either arm. Existing schema/validation cannot be removed.
Further live experimentation requires a separately justified
and approved controlled setup. Stage11 `BLOCKED`.

## ## Stage11 vLLM 0.10.2 backend static verification — 2026-11-04

Pinned vLLM v0.10.2 uses `--guided-decoding-backend` (default
`auto`). Its V1 processor tests XGrammar compatibility and falls
back to Guidance for schemas that XGrammar rejects; request-level
backend changes are unsupported on V1. The actual application schema
has 8 top-level fields, 4 arrays limited to 32 items, 1 `$ref`,
1 nullable `anyOf` and 2 objects with
`additionalProperties=false`. Its **static known-unsupported
keyword** scan for v0.10.2 returned none. No grammar
compilation/latency execution was made; this is not a benchmark.

The earlier observed 29.118s structured versus 2.327s
unconstrained two-arm timing difference remains real but
non-causal and **neither arm passed the model contract**.
Actual selected backend, compilation time, per-token grammar
masking cost and source of the observed gap remain `UNVERIFIED`.

Offline [CI 41796324266](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41796324266)
59 + 162 PASS. Only read-only sanitized Docker launch-flag
inspection is prepared for the approved operator; no GPU, runtime,
timeout, model or production configuration changes.
Stage11 performance gate `BLOCKED`.

## 2026-11-04 — actual Grammar conversion accepted, not yet timed

The operator confirmed /usr/bin/python3, vllm=0.10.2 and xgrammar=0.1.23
inside the existing shared inference container. Grammar.from_json_schema
accepted the unchanged application CriterionInference schema. A real warning
indicated a combined string pattern and min/max length or format constraint
cannot all be enforced by the grammar. The application retains post-response
Pydantic and evidence validation.

The CPU-only two-pass conversion profiling tool
scripts/verification/stage11_xgrammar_cpu_profile.py is ready for an
explicitly authorized operator run. This does not measure the tokenizer-aware
compiler/cache or per-token bitmask application, so the prior 12.51x timing
difference remains non-causal and unlocalized. CPU conversion timing
PENDING_SERVER; Runtime/Production settings unchanged; Stage11 BLOCKED.

## 2026-11-04 — measured on-server XGrammar schema conversion

Operator executed the new two-pass CPU-only probe in the existing
`ai-inference-vllm-1` container (verified vLLM 0.10.2,
XGrammar 0.1.23, unchanged CriterionInference schema hash
`da781d766a47140e7ba844d501fc35c7ae65ae5506a3975440118c77d0e2c584`).
`Grammar.from_json_schema` took **1.724ms** on call one and
**1.535ms** on call two. No inference calls; no token-aware compiler,
bitmask decoding or request latency measured. This narrow conversion
cost cannot by itself explain the prior **29.118s** structured request;
it neither proves token masking is responsible nor establishes that
the actual vLLM request used XGrammar. The two historical capped
requests did not produce complete valid JSON.

Operator also reported two identical focused offline runs, each
**12 passed in 0.34s**, after pulling b4ed305. No new full
performance benchmark, load test or model evaluation was done.
Backend attribution and decoder cost remain PENDING_SERVER; Stage11
BLOCKED, Stage12 NOT_STARTED.
