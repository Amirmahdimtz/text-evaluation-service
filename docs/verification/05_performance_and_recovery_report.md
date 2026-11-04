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

## 2026-11-04 — tokenizer-aware CPU profiling prepared, not yet measured

A new Stage11-only offline-safe instrument can time local-tokenizer
load, XGrammar TokenizerInfo creation, a separately constructed
GrammarCompiler, cold/warm JSON Schema grammar compilation and up
to 24 CPU fill_next_token_bitmask / accept_token steps on a fixed
synthetic JSON abstention. It uses the actual project-generated
criterion Schema and a separately owner-approved local tokenizer
directory; never the production API/model weights. The additional
child process is capped to one compiler thread and a 32 MiB grammar
cache, with process-level CPU/time signals. It never verifies the
serving process's effective backend, internal caches, GPU logits
masking or real per-token generation speed.

Prior real converter timings (1.724ms, 1.535ms) are not retested.
The tokenizer-aware CPU metric remains PENDING_SERVER until an
approved operator execution. The live 29.118s vs 2.327s request
comparison remains non-causal, with invalid outputs in both arms.
Do not tune serving runtime or quality contract from isolated
microbenchmarks. Stage11 BLOCKED, Stage12 NOT_STARTED.

## 2026-11-04 — real Simorgh tokenizer-aware XGrammar CPU profile

The operator ran the bounded Stage11 local CPU-only diagnostic:
13 focused tests PASS (0.95s) and
`CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED`.
Reported on the actual pinned vLLM 0.10.2 / XGrammar 0.1.23
container with 151,936 tokenizer vocabulary:
tokenizer load **455.070ms**, TokenizerInfo **764.613ms**,
cold compile **231.697ms**, warm compile **0.028ms**,
CPU bitmask-fill **1181.770ms total over 24 synthetic steps**
(max one step **256.853ms**), token accept **0.118ms total**.
Compiler init **0.029ms**, one thread, 32MiB separate cache.

This is meaningful CPU work in a *fresh, separately launched*
Python process, not in the shared vLLM serving request; GPU model
inference and GPU mask application were NOT measured. Effective
served backend, model/tokenizer identity and serving-cache hit/miss
remain UNVERIFIED. Mask-fill mean for this trace ~49.24ms/step
must not be multiplied by 256 to predict service latency;
per-step costs differ and the experiment has no first-use
distribution breakdown. The earlier 29.118s vs 2.327s pair
remains non-causal, with invalid output in both arms. No
production configuration, model, Schema or Provider changed.

On-host CPU microbenchmark: OBSERVED. Formal performance/quality
acceptance and actual request root-cause attribution:
PENDING_SERVER. Stage11 BLOCKED, Stage12 NOT_STARTED.

## 2026-11-04 — synthetic CPU mask: first-step vs subsequent-step diagnostic

The earlier on-server synthetic CPU-only experiment reported
24 mask fills / **1,181.770ms** total, maximum **256.853ms**
for one step. This did **not** identify which step was slow.
The Stage11 tokenizer diagnostic now separately exposes the
**first** fill and a summary of later fills (count, sum, average,
median, max and nearest-rank P95). Single-step runs reject the
comparison; zero-total runs do not emit a misleading percentage.

No new live timing is claimed in this change. The original
vLLM 0.10.2, XGrammar 0.1.23, 151936-vocab synthetic tokenizer
result remains the only real on-host observation. A follow-up
CPU-only subprocess probe requires separate shared-owner approval,
and cannot establish the real serving backend/cache, per-token GPU
mask application, model throughput or performance SLO. Real
production E2E latency attribution is `PENDING_SERVER`;
Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## 2026-11-04 — on-server first mask versus subsequent CPU mask fills

The operator ran the focused diagnostic on Simorgh after pulling
f352f4d: **17 passed in 1.08s**. The separate CPU-only child
with an existing local tokenizer returned
`CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED`. The reported
mask-fill distribution over **24 fixed synthetic JSON tokens**:
first **0.094ms (0.01%)**, remaining **23** total
**1149.408ms**, rest mean **49.974ms**, median **0.014ms**,
nearest-rank P95 **225.768ms**, maximum **247.760ms**,
all 24 total **1149.502ms**.
The tokenizer-loaded child also observed
cold compile **239.614ms**, warm compile **0.030ms**,
TokenizerInfo **802.633ms**, tokenizer load **458.834ms**,
and accept_token total **0.124ms**.

The actual first step was not the slowest. This demonstrates
intermittent large CPU mask-fill times somewhere among the later
synthetic token steps, not steady cost for every token. No precise
slow token index, grammar state, source cause, on-service per-request
backend selection, real model inference or GPU logit-mask cost
was measured. A P95 calculated over just 23 independent child
observations is **not** a production latency P95; the real
29.118s vs 2.327s historical pair remains non-causal with two
invalid responses. Do not infer target SLO or multiply the mean
to predict a full response. Formal capacity/quality gates
PENDING_SERVER; Stage11 BLOCKED; Stage12 NOT_STARTED.

## 2026-11-04 — synthetic CPU mask slow-step locator

The on-host fixed synthetic CPU trace reported 24 fills
totalling 1149.502ms, first 0.094ms, later median 0.014ms,
later max 247.760ms. It did not identify the slow steps.
The Stage11-only diagnostic now emits 1-based step indices
for fixed synthetic mask fills >10ms and >100ms; no token
content, IDs, grammar state or user data is logged.
These indices have not yet been observed on Simorgh.
They cannot prove a particular XGrammar state or the
source of the earlier vLLM latency gap. Owner authorization
is required for a new isolated CPU-only diagnostic.
Stage11 BLOCKED, Stage12 NOT_STARTED.

## 2026-11-04 — Simorgh synthetic CPU mask fill positions observed

Operator-provided evidence from main `a11d520`:
**20** focused tokenizer-profiler tests passed in **1.16s**.
The separate fixed synthetic JSON CPU-only probe returned
`CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED`. Both threshold
lists contained exactly **[15,16,17,18,19]**, i.e. five
contiguous mask-fill positions strictly >100ms and
also >10ms. The other 19 positions were at or below 10ms.
Total **1150.577ms** over 24 fills; first **0.087ms**,
remaining 23 sum **1150.490ms**, mean **50.021ms**,
median **0.011ms**, nearest-rank P95 **226.338ms**,
max **246.710ms**. Cold compile **231.962ms**,
warm **0.024ms**, TokenizerInfo **764.192ms**,
tokenizer load **450.091ms**, token accept total
**0.116ms**; pinned vLLM 0.10.2 / XGrammar 0.1.23.

This disproves first-step-only overhead *in this trace*,
and precisely locates which fixed synthetic steps exhibit
intermittent CPU cost. It **does not identify why** they
cost more, nor measure live vLLM backend, request throughput,
GPU logits masking, or a serving SLO. An unknown mapping
of the cached tokenizer to live serving artifacts remains
open. Previous 29.118s / 2.327s paired requests remain
noncausal and incomplete. No production changes or new
automated performance gates have been satisfied. Stage11
`BLOCKED`; Stage12 `NOT_STARTED`.

## 2026-11-04 — paired bounded synthetic mask CPU diagnostic preparation

Before this change the last real Simorgh CPU probe
identified [15,16,17,18,19] as strictly >100ms,
first fill 0.087ms, 24 fills total 1150.577ms.
The enhanced probe will reuse one compiled grammar
and local tokenizer for **two fresh matchers**, at most
24 synthetic token fills each, reporting both sets of
slow positions and redacted coarse JSON region labels
based on validated fast-tokenizer offsets. A missing/
mismatched map produces UNVERIFIED, not guessed labels.
No model inference, user text, GPU masking, private
path, token ID or decoded token is emitted.

This additional CPU work **requires explicit shared-service
owner approval**; no such new result is observed yet.
The old live vLLM comparison remains non-causal and
invalid. Real server backend/model identity and
GPU performance remain PENDING_SERVER; Stage11 BLOCKED.

## 2026-11-04 — reproduced synthetic CPU string-region mask spikes

Simorgh operator: 26 focused tests PASS in 1.30s
after pulling cddce58. The opt-in CPU-only child
produced two fresh matcher traces with identical
slow mask positions [15,16,17,18,19] for >10ms
and >100ms; 24-step totals **1159.124ms**
and **1146.884ms** respectively. First fill
**0.072ms** and **0.011ms**; later median
**0.010ms** and **0.009ms**. Validated
tokenizer offsets mapped steps 15-18 into
the **third synthetic JSON field's VALUE**
and step 19 to CROSS_REGION. Because sample
keys are constructed in alphabetically sorted
schema order, ordinal 3 corresponds to
`reason`, a synthetic string value.

Warm compile **0.027ms**, cold compile
**227.487ms** in the same independent process.
This is reproducible **synthetic CPU mask cost**
associated with that string location, not
a measured live request or proven internal
grammar bottleneck. Metadata-only launch
inspection found no explicit guided-backend
flag and reported default AUTO, effective
backend UNVERIFIED. No GPU mask timing, live
backend selection or service SLO was observed.
Historical 29.118s vs 2.327s requests remain
non-causal, incomplete and invalid.
Stage11 BLOCKED; Stage12 NOT_STARTED.

## 2026-11-04 — bounded reason sensitivity plan, no new latency data

Added an explicitly opt-in Stage11 fixed-synthetic CPU
experiment: two baseline and two reason-variant matcher
traces, maximum 96 mask fills, one compiled grammar and
existing CPU/wall/thread/cache limits. The variants
compare short and equal-length-different synthetic
`reason` values. The output contains only aggregate
times, slow-step indices and bounded JSON structural
categories with validated offsets. Tokenization may
change, so any association is exploratory, not causal.
No new Simorgh measurements were performed. The 1159.124ms
and 1146.884ms last-observed baseline times are unchanged.
Effective backend/provenance, real GPU performance and
production SLO remain PENDING_SERVER. Stage11 BLOCKED.

## 2026-11-04 — controlled CPU reason-value sensitivity observed on Simorgh

The operator ran **58** focused offline tests (1.80s PASS) and the
one-shot Stage11 CPU reason-variant diagnostic, without GPU inference.
First baseline fixed-synthetic trace: 24 fills **1159.961ms**,
>100ms steps [15,16,17,18,19], complete reason-value four steps
**931.077ms** (~80.3% of total); second baseline **1154.664ms**,
same >100ms steps and reason-value four steps **926.463ms**.
Short synthetic reason: **473.408ms** total, two >100ms steps
[15,16], one reason-value step **247.710ms**.
Different text of equal character length:
**1148.708ms** total, five >100ms steps [15,16,17,18,19],
four reason-value steps **923.114ms**.
All structural tokenizer alignment statuses were ALIGNED.
First-trace cold compile **235.052ms**, warm **0.025ms**.

This strongly supports a fixed-synthetic CPU string-region
association, not a measured request-level XGrammar backend,
a production latency p95, or a verified bottleneck in the
shared vLLM service. The 24-token prefix and tokenizer
segmentation can differ across reason variants, so output
length/total mask sums are not a controlled service speedup
estimate. Owner-supplied served artifact comparison was skipped;
actual serving model/tokenizer/backend and real GPU performance
remain UNVERIFIED/PENDING_SERVER. Stage11 BLOCKED.

## 2026-11-04 — Simorgh 512-token media criterion request timeout

Operator's **one** approved actual `media_message_clarity`
request, disabled thinking, structured JSON Schema and
max_output_tokens=512, failed after **45072ms** with
`LLM_CIRCUIT_OPEN` / `REQUEST_TIMEOUT`.
Configured provider request timeout 45 seconds, one
concurrent request, one attempt (zero retries).
No complete model response arrived in the diagnostic
wrapper; finish reason, JSON syntax and usage
`UNAVAILABLE`. These are **unknown**, not negative
JSON validity assertions.

Shared vLLM metrics changed over the interval:
generation_tokens_total +401; inter-token latency
count +400; inter-token latency sum +44.846746 seconds;
prompt_tokens_total +635; num_preemptions_total +0.
All are shared global counters and cannot identify
which request generated the tokens. They are compatible
with time being spent in incremental decoding but do
not prove per-request throughput or XGrammar/GPU masking
attribution. Live guided backend/model/tokenizer
provenance remains unverified, and CPU mask-fill spikes
in the synthetic reason field explain at most a
different isolated CPU microbenchmark.

**Stop rule triggered; one-request approval consumed.**
No retry, token-budget increase, timeout increase,
model change or new GPU request without fresh
explicit owner resource approval and per-request
lifecycle evidence. Stage11 BLOCKED, Stage12 NOT_STARTED.

## 2026-11-04 — phase-metrics evidence boundary for previous 45.072s timeout

The previous operator-observed synthetic `media_message_clarity`
request exceeded the 45-second Provider timeout and returned
`LLM_CIRCUIT_OPEN / REQUEST_TIMEOUT`; no complete HTTP response,
request finish reason or generation usage was observed.
Global `vllm:inter_token_latency_seconds` counters increased
by **400** observations and **44.846746 seconds**, which is
a **shared-service** aggregate average of approximately
**0.112117s per recorded interval**, **not** a per-request
decode speed. Shared `generation_tokens_total` rose by 401,
`prompt_tokens_total` by 635; no counts can be assigned
to the failed media request. Earlier request-decode
histogram count and sum delta were zero, which does
not establish zero actual decoding for a timed-out request.
Queue, prefill and TTFT totals for that historical
interval were not captured.

Added a Stage11-only redacted Phase Metrics Inventory
using one explicit, bounded, read-only local `/metrics`
GET, or an inert offline default. Based on documented
vLLM **0.10.2** queue/prefill/decode/inference/E2E/TTFT
histograms (count/sum), it reports ONLY current
**shared lifetime** sample counts/sums/means and
current aggregate running/waiting/swapped gauges.
It cannot reconstruct the failed request's phases.
Missing metrics, zero recorded samples and inconsistent
aggregates are separately labeled, never guessed.
See `20_stage11_vllm_phase_metrics_inventory.md`.
No model POST, GPU execution, vLLM restart, settings
change or private log inspection performed.
Stage11 BLOCKED; Stage12 NOT_STARTED.
