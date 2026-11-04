# Stage11 — vLLM 0.10.2 read-only phase-metrics inventory

**Scope:** Stage11 only; safe shared-service introspection without inference.
**State:** CODE_PREPARED / ON_HOST_PHASE_INVENTORY_PENDING_OPERATOR;
prior 45-second media request FAILED_REQUEST_TIMEOUT;
Stage11 BLOCKED; Stage12 NOT_STARTED.

## Actual evidence already available

The operator's single consented synthetic
`media_message_clarity` request took **45072ms**, returned
`LLM_CIRCUIT_OPEN` with underlying
`failure_kind=REQUEST_TIMEOUT`, and the diagnostic
did not receive a complete response. Its finish reason,
usage and JSON validity are `UNAVAILABLE`, **not
automatically invalid**.

The only phase-adjacent samples captured during that
previous attempt were **shared cumulative counters**:
generation_tokens_total +401, inter_token_latency
count +400 and sum +44.846746 seconds, prompt_tokens
+635, and num_preemptions +0. These imply a
**global cross-request mean** of approximately
112.117 ms per recorded inter-token interval
(44.846746/400), **not** a 112ms interval for the
media request. They do not identify queue, prefill,
decode, grammar-mask, HTTP overhead, per-request
output length, cancellation timing, effective
backend or actual latency distribution.

In that earlier interval,
`vllm:request_decode_time_seconds_count` and
`_sum` deltas were 0; that does **not** establish
zero decoding for the failed request, because the
metrics are shared and completion-time observation
semantics depend on vLLM runtime. The earlier
diagnostic did not collect queue/prefill/TTFT
histogram sums/counts. Historical per-request phase
duration **cannot be reconstructed from current
Prometheus lifetime snapshots**.

## Why these particular Metric names

The official [vLLM v0.10.2 Production Metrics
documentation](https://docs.vllm.ai/en/v0.10.2/usage/metrics.html)
documents:
- `vllm:request_queue_time_seconds` — waiting phase
- `vllm:request_prefill_time_seconds` — prefill
- `vllm:request_decode_time_seconds` — decoding
- `vllm:request_inference_time_seconds` — running
- `vllm:e2e_request_latency_seconds` — request end-to-end
- `vllm:time_to_first_token_seconds` — TTFT
- `vllm:num_requests_running/waiting/swapped` — current gauges

Prometheus histograms expose `_count` and `_sum`
when the exporter publishes them. All fields from
`/metrics` are **service-wide aggregates**; samples
from other tenants/requests can be mixed. A single
fresh snapshot represents current cumulative exporter
state, **not a historic request trace**, and
per-phase means may cover different sample groups.
Do not sum means into a supposed 45s timeline.

## New safe introspection path

The existing `stage11_vllm_diagnostics.read_metrics`
already implements one read-only local
`GET http://127.0.0.1:8000/metrics`, 3s timeout,
2MiB maximum response bytes, no proxy or redirect,
and an explicit numeric allowlist that drops label
values and all other text. The allowlist has been
extended with v0.10.2 phase histogram
`_count/_sum` samples and three queue gauges.

The new `stage11_vllm_phase_inventory.py` is
**no network by default**; opt-in
`--inspect-local-metrics` makes exactly one GET
using that already tested helper. Only a fixed,
redacted report is printed: whether each phase
metric is present, sample count, cumulative sum,
mean for those service-wide samples (if possible)
and the instantaneous global running/waiting/swapped
counts. No raw metrics, path, label, prompt, token,
model ID, header, secret, model process or other
tenant identifier is emitted. No Docker, GPU
execution, model inference, service modification
or metric scraping daemon is started.

Status meanings:
- `SHARED_LIFETIME_AGGREGATE`: service-wide
  historical numeric samples exist, **not** the
  media request's own queue/prefill/decode duration
- `ZERO_RECORDED_SAMPLES`: metric is exposed but
  currently reports zero; not proof that no inference
  ever occurred
- `NOT_PRESENT_IN_SNAPSHOT`: exporter did not
  include both required samples; not necessarily
  unsupported by vLLM
- `INCOMPLETE_METRIC` / `INVALID_AGGREGATE`:
  fail-closed, do not invent a phase duration
- `LOCAL_METRICS_UNAVAILABLE`: read failed/
  empty/oversized; no request retry

## Operator commands

After source update, run completely local tests and
the default no-network plan:

~~~bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_vllm_phase_inventory.py tests/test_stage11_vllm_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_vllm_phase_inventory
~~~

Only with the shared-runtime owner's permission for
read-only loopback metrics access, and while the
existing local vLLM endpoint is already up, run:

~~~bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_vllm_phase_inventory --inspect-local-metrics
~~~

This sends **one** localhost GET, **zero model
inference requests**. Never run the last failed
`--execute-live` media request again without a
fresh explicit approval. If private governance
does not allow exporter access or the port is
not 8000, **skip**; never expose a new public
port or change runtime settings to force the tool.

## Evidence still needed to truly split the 45s

**Owner-only / privacy-approved follow-up:**
consult existing retained per-request request-ID
timing and cancellation evidence (if available)
for the historical synthetic request: ingress
arrival/start/end timestamps, queue enter/schedule,
first token/prefill complete, last token/abort,
response completion/cancellation; model/tokenizer
identity, fallback/effective decoder and resource
pressure. This requires validated request-ID
correlation and authorized, redacted collection
**within the private system**. Never post raw vLLM
logs, metrics labels, prompts or IDs to GitHub/chat.

If no request-specific event trail was retained,
mark the historical decomposition `UNRECOVERABLE`;
do not manufacture queue/prefill/decode times from
shared counters. A newly authorized *future*
instrumented synthetic request would be necessary
for causal phase breakdown, with separate shared
GPU owner approval, no secrets and controlled stop
criteria.

**Current acceptance:** previous live criterion
`FAILED_REQUEST_TIMEOUT`; owner model/provenance,
effective request decoder and per-request lifecycle
`UNVERIFIED`; model/GPU/security/quality and
three-domain acceptance `PENDING_SERVER`;
Stage11 `BLOCKED`; Stage12 `NOT_STARTED`.

## CI evidence after the source change

[GitHub Actions run 41839339602](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41839339602)
completed SUCCESS on `5e977b4`: **59** Stage11
offline safety tests and **226** focused synthetic
software/Provider tests passed. The container-image
build and networkless API liveness/Worker denial
checks also succeeded. The CI did **not** connect
to Simorgh or generate an inference request; the
opt-in metrics GET and any owner-only request
telemetry inspection remain `PENDING_OPERATOR`.

## 2026-11-04 — actual Simorgh live exporter snapshot (operator observed)

After pulling `main` through `cf3f89c`, the operator ran
`tests/test_stage11_vllm_phase_inventory.py` and
`tests/test_stage11_vllm_diagnostics.py`: **38 passed in 0.31s**.
The separately approved read-only
`stage11_vllm_phase_inventory --inspect-local-metrics`
returned `READ_ONLY_SHARED_PHASE_INVENTORY`, with
**one loopback GET**, zero model inference requests
and zero GPU model execution.

These are **shared lifetime histogram aggregates**,
not observations attributable to the earlier media
criterion request:

| Phase metric | Count | Sum (seconds) | Shared mean (seconds) |
|---|---:|---:|---:|
| queue | 6 | 0.056605 | 0.009434 |
| prefill | 6 | 0.741958 | 0.123660 |
| decode | 6 | 62.235655 | 10.372609 |
| inference | 6 | 62.977613 | 10.496269 |
| end-to-end | 6 | 63.618374 | 10.603062 |
| time to first token | **12** | 1.762285 | 0.146857 |

**Observation:** across the six reported decode and end-to-end
histogram samples, decode sum / end-to-end sum is approximately
**97.8%**. This supports prioritizing decode profiling for the
*reported shared-service sample population*, but does **not**
show that the previously failed **45.072-second** media request
spent 97.8% of its own time decoding. Histogram buckets/labels
were deliberately discarded; counts may reflect different
recording semantics/populations. In particular, **TTFT count
12 differs from the other counts of 6**, so one must not
combine the histograms into a fabricated single-request
timeline, or assume 6 requests completed successfully.

The current service snapshot reported `running=0`,
`waiting=0`, `swapped=null`. This is a point-in-time
observation **after** the prior timeout, not evidence
that the queue was empty during that request.
`swapped=null` means no usable metric sample was
recorded, not that there were zero swapped requests.

**What was NOT learned:** the request-level queue time,
prefill time, decode time, TTFT, number of generated tokens,
whether the engine continued after client cancellation,
effective guided decoding backend, served model/tokenizer
identity, or the direct cause of the timeout remain
`UNVERIFIED/UNAVAILABLE`. The 45-second one-request
GPU authorization was already consumed. No new model
POST, service configuration change, reset, external
network call or GPU experiment occurred.

**Next action, private owner-only:** check whether
**already retained** request-correlated metadata contains
queue-enter/scheduled, prefill-complete/first-token,
completion-or-abort and client disconnect timestamps.
Use only redacted and authorized status/phase durations
from an existing trusted request ID (do not publish
that ID, raw logs, model text or private paths).
If such history was not retained, mark the old
45-second phase split `UNRECOVERABLE`; subsequent
per-request profiling needs a **new** explicitly
approved controlled GPU window. Stage11 `BLOCKED`;
Stage12 `NOT_STARTED`.

## 2026-11-04 — historical Docker logging configuration and bounded pattern scan

Operator-only, metadata-first Docker inspection on Simorgh reported:
`log_driver=json-file`, `log_path_configured=yes`,
container `started_at=2026-11-03T10:47:30.533226937Z`.
Per-container `max-size` and `max-file` options were
blank; this is **not independent proof** of full retention
or absence of daemon defaults, external rotation or deletion.

A separate bounded `docker logs` check for
2026-11-04T00:00:00Z–2026-11-05T00:00:00Z returned
`historical_logs_present=YES`. This attests to at least
some logs in that period, **not** the failed request's
own log record.

An operator-approved pattern-only scan of the **last
1200 log lines** within 2026-11-04 13:00–13:30 UTC
returned `BOUNDED_SCAN_COMPLETED` with:
`request_marker=NO`, `queue_timing=NO`,
`prefill_timing=NO`, `decode_timing=NO`,
`first_token_timing=NO`,
`abort_or_disconnect=NO`,
`periodic_engine_stats=YES`.
This establishes that the searched patterns did not
match the portion scanned, while at least one known
periodic engine-statistics phrase did. It does **not**
exclude different log formats, other records outside
the last-1200-line slice, or a separate private
request-tracing backend. Neither arbitrary log
lines nor private request content were supplied
to the assistant.

**Decision:** do not extract or publish raw Docker
logs, infer request identity/timing from periodic
engine statistics, or upgrade the failed request's
queue/prefill/decode decomposition to either PASS
or `UNRECOVERABLE` without verifying actual
retention and trace availability. Historical
per-request timings remain `UNAVAILABLE`; owner-only
trace existence `UNVERIFIED`. No GPU
request, service change or log configuration change.
Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.
