# Stage11 — Low-load real shared-vLLM three-domain criterion probe

**Status:** `READY_FOR_OPERATOR` — offline tests may pass in CI, but no live
three-domain result exists until operator runs it. **No expert quality verdict.**
Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## Previous actual on-host evidence

The Simorgh operator demonstrated a real, single-request candidate
`CriterionInference` JSON-schema/offset decoding test: HTTP 200;
`FULL_CRITERION_CONTRACT_PASS`; guided score 3; one valid evidence span;
225 tokens. This was a guided **contract test**, not autonomous Persian
rubric assessment or evidence relevance/quality proof. Its source code was
in the conversation, not a committed repeatable probe. Earlier `shared-llm`
returned `{"ok":true}` under a trivial strict schema.

## New Stage11 operator probe (this document)

`scripts/verification/stage11_real_model_criterion_probe.py` uses **existing
production application classes**, `LocalLlmProvider` and
`CriterionEvaluationService`, and the actual
`tests/fixtures/stage06_candidate_rubrics.json` versioned technical
candidate rubrics; the `score_anchors`/evidence instructions come from the
pinned rubric. It does **not** instruct the model to select a score or a quote.

One criterion per domain, for a total of **exactly three sequential**
synthetic-only inferences:

| Domain | Real candidate criterion |
|---|---|
| `speech` | `speech_clarity` |
| `media` | `media_message_clarity` |
| `research` | `research_academic_writing` |

The endpoint and served model ID are fixed to the already operator-observed
`http://127.0.0.1:8000/v1` and `shared-llm`. No dynamic endpoint,
external route, tool, model installation, Docker or database access is used.
Concurrency is one, attempts/retries one/zero, max 512 completion tokens and
45-second timeout per request. The executable path is explicit
`--execute-live`, and the default is an entirely offline dry-run.
It rejects a caller with non-development `TES_ENVIRONMENT`, a private
`TES_STAGE11_SETTINGS_FILE`, a DB URL or a concurrent process-E2E
environment. It does not change any running service configuration. Local
`deny_external_egress=true` is not proof of actual firewall enforcement.

Output is deliberately limited to criterion code, status, optional candidate
criterion score, number of valid exact-match evidence spans and elapsed ms;
the script never prints or saves raw text, quotes, explanations, model output,
credentials or arbitrary exception strings. Only allowlisted provider error
codes may be printed. Authentic expert review is still required to judge
**semantic** evidence relevance and score quality.

Local dry run (no network):
```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  -q -p no:cacheprovider tests/test_stage11_real_model_criterion_probe.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.stage11_real_model_criterion_probe
```

Only after confirming an operationally authorized brief window on the
**shared** vLLM/GPU, request one criterion in each domain:
```bash
cd /srv/projects/text-evaluation-service
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.stage11_real_model_criterion_probe --execute-live
```

Expected high-level status `REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS`, only
if each result passes the existing typed provider decoder, criterion
validator and exact source quote/offset checks. A legitimate
`not_assessed` with null score and empty evidence can **pass the schema**
while still failing a future **quality** or coverage gate. A failure,
invalid offset or a schema mismatch remains a failure to be investigated,
not an inference that the code or GPU is broken.

The observed model's `max_model_len` is 8192 but the exact model weight,
tokenizer, chat template, hash, license, runtime version and serving options
still need provenance evidence. The configured revision string in this probe
is explicitly `unverified` and is **not** artifact attestation.
CPU/GPU telemetry and token usage cannot be inferred from this probe's
limited summarized output. The second model comparison, expert-labeled
three-domain dataset, real full encrypted API/Worker/vLLM/DB integration,
separate staging tenancy, No-Egress and capacity gates remain open.

No data owner approval or expert calibration threshold has been silently
assumed.

## Operator execution evidence: partial failure, not three-domain pass — 2026-11-03

Source `a35fd3a`, Simorgh operator, shared `shared-llm`: actual `--execute-live` returned `REAL_MODEL_THREE_DOMAIN_CONTRACT_PARTIAL_FAILURE`.

| Domain | Criterion | Contract | Status/diagnostic | Duration |
|---|---|---|---|---|
| speech | speech_clarity | valid | `not_assessed`, score null, no evidence | 1738 ms |
| media | media_message_clarity | failed | `LLM_CIRCUIT_OPEN` | 45007 ms |
| research | research_academic_writing | failed | `LLM_CIRCUIT_OPEN` (open breaker; not a confirmed upstream request) | 1 ms |

The 45s media duration closely matches configured `timeout_seconds=45`, but upstream first-failure category is **not proven**. A provider with `circuit_failures=1` opens after any first transient HTTP 429/5xx, timeout or transport error; subsequent research call was rejected almost immediately. No retries and at most one request in flight. The previously guided single-criterion schema PASS remains valid but unrelated to autonomous model accuracy.

**Status:** `FAIL_USER_SERVER_REPORTED_UNFORCED_TRI_DOMAIN_CONTRACT`, with one valid abstention and two failed calls. Three-domain real-model quality remains `PENDING_SERVER`. The next script version should safely report an allowlisted upstream failure category and avoid attempting further criteria once circuit is open, without printing any private text or expanding shared-GPU load. Do not claim `PASS` or proceed to Stage12.

## Bounded first-failure diagnostics and fail-fast — 2026-11-03

The prior on-host run was `REAL_MODEL_THREE_DOMAIN_CONTRACT_PARTIAL_FAILURE`.
The provider already carries a sanitized first-error `failure_kind`.
The probe now prints it only for `REQUEST_TIMEOUT`,
`TRANSPORT_ERROR`, `HTTP_429`, `HTTP_500`, `HTTP_502`,
`HTTP_503` or `HTTP_504`; otherwise `UNAVAILABLE`. No raw
exception text, prompt or response is printed.

The first `LLM_CIRCUIT_OPEN` stops all further criteria, so output
includes `requests_planned`, `requests_attempted`,
`requests_not_attempted` and `stopped_after_circuit_open`. These
counts are Python criterion evaluations, not confirmed HTTP requests.
Neither configured timeout nor shared-service concurrency changed.

[GitHub Actions 41641990500](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41641990500):
59 preflight tests and 28 probe tests passed, including real local
Provider + CriterionService via HTTPX in-memory mock for HTTP 429/503,
timeout and transport error. `DRY_RUN_NO_NETWORK` also passed.
**No revised real GPU inference was performed**.

For a single authorized on-host diagnostic, update the code and use
the same opt-in `--execute-live` command documented above. If the
failure kind is `REQUEST_TIMEOUT`, determine why inference was slow
before increasing timeouts or scheduling new runs. Never stop or
reconfigure the vLLM shared with another project without explicit
approval. Stage11 `BLOCKED`; Stage12 `NOT_STARTED`.

### Single-domain low-load follow-up

With a separately authorized short usage window on the **shared** inference
service, diagnose the previously failing media criterion with **one**
criterion request only; the script does not start a new model:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.stage11_real_model_criterion_probe --domain media
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.stage11_real_model_criterion_probe --execute-live --domain media
```

In the default dry run `requests_planned=1` and no HTTP request is sent.
In the explicit live run a maximum of **one** rubric evaluation is
attempted, with one concurrent request, zero retries, one fixed synthetic
Persian text and 45-second deadline. Output exposes only known fixed
failure category codes. Do not confuse a successful schema validation
or a valid abstention with expert-validated model accuracy. There are no
automatic reruns or changes to shared GPU/PostgreSQL.

[Offline CI run 41642911358](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41642911358):
**59 existing Stage11 checks passed, 30 probe tests passed** including
single-domain selection, dry-run, sanitized failures and actual Provider
MockTransport paths. The live single-domain diagnostic is
`PENDING_OPERATOR`.


## Simorgh time-correlated timeout evidence and optional non-thinking experiment — 2026-11-03

The operator ran one real synthetic media criterion with read-only 3-second Prometheus sampling. From 13:44:23 through 13:45:05, `num_requests_running=1`, `num_requests_waiting=0`, and `kv_cache_usage_perc` increased from 0.006 to 0.011. The request ended with `REQUEST_TIMEOUT` at 45,093 ms and `probe_exit=2`. The preceding 13:44:20 sample showed idle GPU queue. These correlated snapshots strongly support execution inside the model engine rather than queue congestion; they do **not** independently identify the precise runtime bottleneck or whether the running request was the only service user. No accepted score/evidence resulted.

The local `LocalLlmProvider` already exposes `thinking_mode`. The opt-in `disabled` mode now sends the Qwen3-supported request parameter `chat_template_kwargs: {enable_thinking: false}`; `runtime_default` (used by normal operations and prior runs) remains unchanged. The Stage11 probe accepts `--disable-thinking` only together with `--domain`, keeping this comparison to a **single** synthetic criterion. No vLLM container settings, other tenant settings, model weights, secrets, GPU concurrency, retry budget or 45-second timeout were changed. Compatibility on the actually installed vLLM is still `PENDING_OPERATOR`.

After authorization from the shared service owner, run:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage07_local_llm.py tests/test_stage11_real_model_criterion_probe.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --domain media --disable-thinking
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --execute-live --domain media --disable-thinking
```

The third command is a dry run; only the fourth sends exactly one inference request. A completed JSON contract does not establish independent Persian scoring quality; an HTTP 4xx would indicate request/runtime incompatibility rather than justify changing the shared service. 

Actually executed offline on GitHub Actions 2026-11-03: Stage07 run 41648095259 `SUCCESS`, 66 provider checks passed and 484 non-database tests passed (11 skipped); Stage11 preflight run 41648095226 `SUCCESS`, 59 guard tests and 99 focused provider/probe tests passed. Live `--disable-thinking` result remains `PENDING_SERVER`. Stage11 `BLOCKED`; Stage12 `NOT_STARTED`.


## Bounded per-criterion response and Prometheus delta diagnostics — 2026-11-03

A Stage11-only opt-in diagnostic was added after real synthetic media failures
with `REQUEST_TIMEOUT` at approximately 45s, including the
`--disable-thinking` run. This is a troubleshooting aid, **not** a
production-mode adjustment or proof of autonomous evaluation quality.

`--diagnostics` **requires** one `--domain`. It creates a separate
read-only loopback HTTP client with `trust_env=False`,
`follow_redirects=False`, a 3s whole-request timeout and a 2 MiB
response cap; at most two `GET /metrics` requests are made (before/after).
One **synthetic** rubric criterion is evaluated, max_concurrency=1,
max_attempts=1, with the same 45s deadline as before. No extra inference
requests, model changes, DB access, secret logging or container lifecycle
operations. The optional `--max-output-tokens 256` is accepted **only**
with `--diagnostics` and a specific `--domain`; default remains 512.
A 256-token limit may produce `finish_reason=length` and must be treated
as `LLM_INCOMPLETE_GENERATION`, not a successful result.

Only if the provider receives a complete HTTP response, the diagnostic
captures the allowlisted `finish_reason` (`stop`, `length`,
`tool_calls`, `content_filter`, otherwise `OTHER`/`UNAVAILABLE`),
the JSON **syntax** category (`valid`, `invalid`, `UNAVAILABLE`) and
server-reported `prompt_tokens`, `completion_tokens`,
`total_tokens` as validated non-negative integers or null.
**JSON syntax valid is not schema-valid or rubric-valid.** The actual
`CriterionEvaluationService` and `LocalLlmProvider` fail-closed
contract still determines `results[].contract`. No content, quotes,
prompts, explanations, upstream raw errors, private labels or credentials
are printed. If the client times out before receiving the response,
`reported_usage=null`, `json_syntax=UNAVAILABLE` and
`finish_reason=UNAVAILABLE`; those values must **not be inferred**.

`shared_metrics_delta` contains before/after differences for a fixed
allowlist of vLLM counters/histogram sums and counts. It **aggregates
across all labels and all tenants**; the associated
`metrics_attribution=SHARED_SERVICE_UNATTRIBUTED` prohibits treating
the delta as the individual request's true token count. A telemetry
read failure reports `metrics_status=UNAVAILABLE`; counter resets
report `COUNTER_RESET_OR_INVALID`; neither can turn an otherwise valid
LLM contract into a fabricated failure or success.

On Simorgh, after an authorized bounded single-request window, run:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_real_model_criterion_probe.py tests/test_stage11_vllm_diagnostics.py tests/test_stage07_local_llm.py
# Offline preview; MUST return DRY_RUN_NO_NETWORK
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --domain media --disable-thinking --diagnostics --max-output-tokens 256
# Only if shared-service owner separately approves one synthetic inference
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --execute-live --domain media --disable-thinking --diagnostics --max-output-tokens 256
```

If the reduced cap causes incomplete generation, record it as a **failed**
contract; never force scores or repair malformed JSON in the diagnostic.
No unattended reruns. If another tenant is busy, defer the live probe.
Return only the sanitized JSON report for analysis; do not share full
Prometheus output or model contents.

**Actual offline validation:** [GitHub Actions 41656742019](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41656742019),
`SUCCESS` on code commit `566a37761ed12caf96763a86beb6cf5eb0987417`:
**59 Stage11 preflight passed**, **131 focused Provider/probe/metrics tests
passed**, default no-network dry-run passed. MockTransport tests cover
valid response usage, `length`, malformed JSON, timeouts, allowlist
redaction, counter resets, no redirects/proxies, localhost-only metrics
and the size bound. All results are **synthetic/offline**; no GPU
inference, completed-response token usage or real model quality was
measured by this change.

The new live diagnostic remains `PENDING_SERVER`; Stage11 `BLOCKED`,
Stage12 `NOT_STARTED`.


## Operator live evidence: 256-token completion stopped at length — 2026-11-03

Simorgh operator ran 131 local focused tests (`PASSED`, 1.20s), confirmed
`DRY_RUN_NO_NETWORK` for `--domain media --disable-thinking --diagnostics
--max-output-tokens 256`, then submitted **one** synthetic live evaluation
with the explicit `--execute-live` flag.

The server returned a complete response after **23,427ms** with
`finish_reason=length`, `json_syntax=invalid`, and **real response usage**
`prompt_tokens=558`, `completion_tokens=256`, `total_tokens=814`.
The production Provider rejected it with `LLM_INCOMPLETE_GENERATION`.
The code did not retry or open a circuit. This is a **FAILED** evaluation;
no rubric score or evidence can be accepted. The 256-token cap is
insufficient to complete this structured output under the tested
model, prompt and runtime settings.

Before/after shared Prometheus counters showed `+256`
`generation_tokens_total`, `+255` inter-token samples and
`+23.352864s` accumulated inter-token latency, `+1` completed
request-generation sample, `+256` output tokens and
`+23.352864s` request Decode. These values match the HTTP usage
but are **SHARED_SERVICE_UNATTRIBUTED** and are not formally per-request
traces. There were no preemptions observed in this window.

Approximate observed output rate is `256/23.352864≈10.96 tokens/s`.
A linear projection to 512 output tokens gives ~46.7s before overhead,
longer than the probe's 45s timeout. This extrapolation is NOT a
measurement of the earlier 512-token runs; their failure kind remains
`REQUEST_TIMEOUT`, and no per-response token counts are known.

**Operator guidance:** Do not run another unplanned GPU request, increase
the shared timeout, change container configuration or treat incomplete
JSON as valid. The next engineering task is a reviewed offline
investigation of whether response verbosity can be reduced without
changing rubric semantics, followed by a separately authorized
capacity/quality diagnostic. Keep Stage11 `BLOCKED`, Stage12
`NOT_STARTED`.


## Stage11 concise prompt candidate 0.3 (2026-11-03)

The operator-approved offline Prompt revision changes only
`CriterionEvaluationService` instructions. The new version
`stage08-prompt-candidate-0.3` requests shorter, non-redundant Persian
reasons and observations while retaining all output JSON keys, rubric
anchors, exact evidence quotes and offsets, required justification, and
null-score abstention. No response schema, provider, runtime, output cap,
deadline or shared server was changed.

GitHub Actions [41662617861](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41662617861):
41 Engine checks PASS, 520 non-database regressions PASS, 11 skipped.
No new real-model throughput, quality or contract PASS is claimed.

Operator offline commands:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage08_engine.py tests/test_stage07_local_llm.py tests/test_stage11_real_model_criterion_probe.py tests/test_stage11_vllm_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --domain media --disable-thinking --diagnostics
```

With separate operator authorization, add `--execute-live` to the
last command to submit **one** synthetic media evaluation. It retains
512 max output tokens, 45s timeout and no retries. A valid abstention
does not demonstrate quality; incomplete JSON, length termination or
timeout is still FAILED. Historical 256-token truncation and
512-token timeouts remain evidence, not successful measurements.
Stage11 BLOCKED; Stage12 NOT_STARTED.

## Real prompt v0.3 single-domain timeout evidence — 2026-11-03

The operator pulled through commit `71d9509`, ran `172` focused tests successfully and verified dry-run without network, then ran one explicit synthetic media criterion using `--execute-live --domain media --disable-thinking --diagnostics` with default max output 512 and 45s timeout. The live attempt failed at 45,034ms with `REQUEST_TIMEOUT` and opened the local circuit. `finish_reason`, JSON syntax and per-request reported usage are **UNAVAILABLE** (not `length` or 0). No accepted score/evidence.

Read-only shared metrics changed by +401 generated tokens, +635 prompt tokens and +44.876778 seconds across 400 inter-token samples, with no completed response histogram increment. This suggests extended generation/decoding in the monitored window but cannot prove how many tokens the project request itself generated. Relative to prior capped 256-token test (complete HTTP, length stop, invalid JSON, 23.427s), there is **no confirmed improvement** from new prompt wording. Do not continue repeated live tests or change the shared server/timeout without approval and a bounded hypothesis.

The stage remains `BLOCKED` until separately required actual quality, provenance, No-Egress, performance and E2E gates are satisfied; Stage12 `NOT_STARTED`.


## Stage11 JSON size and decoder comparison diagnostics — 2026-11-03

The operator requested two distinct tests, bounded to Stage11:

1. **Offline semantic-preserving JSON serialization comparison:**
   `scripts/verification/stage11_output_budget.py` creates six
   synthetic `CriterionInference` objects (assessed/abstained for each
   domain), serializes the identical object with normal versus compact
   UTF-8 JSON and passes both through the actual strict decoder,
   including exact quote/offset verification. For the media sample,
   assessed `427 -> 405` bytes (22 bytes saved) and abstained
   `247 -> 232` bytes (15 bytes saved). All six passed identical
   type/contract checks; output sizes are **bytes, NOT model token counts**.
   These are synthetic structural examples: they do **not** establish
   expert semantic evidence sufficiency, smaller actual Qwen completions,
   or meaningful quality/latency improvement.
2. **Real decoder-overhead experiment prepared, not executed:**
   `scripts/verification/stage11_structured_decoding_compare.py`
   plans one ordered pair with the **same model, prompt, case, temperature,
   thinking mode, and max 256 output tokens**. First arm uses the
   production `response_format=json_schema`; second omits
   `response_format` and is **unconstrained**. This is a diagnostic-only
   Provider subclass; production decoding/validation remains unchanged.
   Both responses pass through the existing strict decoder, so a JSON
   syntax-only output, missing fields, invalid quotes or `length`
   termination is **FAILED**, not accepted. The second arm only executes
   if the first completed its HTTP response with a valid or
   schema/incomplete-generation diagnostic; a timeout or other upstream
   problem fails fast. At most two **sequential** synthetic calls, one
   in-flight, 45s per call, zero retries; no server or database changes.
   Metrics remain `SHARED_SERVICE_UNATTRIBUTED`.

**Known experimental limits:** Two ordered requests on a shared GPU do not
prove a causal decoder penalty, p95, or quality equivalence. The
unconstrained mode is intentionally not a production candidate; its model
output may be invalid because the schema is not provided as an API
constraint. If either arm times out, completion token usage is unavailable
and the speed comparison is inconclusive. Further replicated,
counterbalanced tests would require a separately approved workload.

**Actually executed CI, not GPU:**
[run 41667673237](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41667673237)
`SUCCESS`: 59 prior Stage11 preflight tests PASS, 143 focused
Provider/probe/JSON-budget/decoder-comparison tests PASS, both CLI
dry-runs verified `DRY_RUN_NO_NETWORK`. Production Provider, its
Schema, and shared vLLM settings were not changed.

Operator offline tests:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_decoding_comparison.py tests/test_stage11_real_model_criterion_probe.py tests/test_stage11_vllm_diagnostics.py tests/test_stage07_local_llm.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_output_budget
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_structured_decoding_compare
```

**Only if the shared-GPU owner explicitly authorizes TWO bounded
sequential synthetic requests**, invoke the final command with
`--execute-live --shared-gpu-approved` appended. No live command is
automated or authorized by an offline test success. Keep Stage11
`BLOCKED`; Stage12 `NOT_STARTED`.

## 2026-11-04 — shared GPU one-pair decoder experiment observed

The Simorgh operator pulled main through commit `235f088`, confirmed
the default `stage11_structured_decoding_compare` command returned
`DRY_RUN_NO_NETWORK`, then explicitly ran the bounded comparison with
`--execute-live --shared-gpu-approved`. It made **two sequential,
synthetic-only** `media_message_clarity` requests, with concurrency 1,
max output 256 tokens each, disabled Thinking requested, 45s deadline,
no retries, and matching input/model/parameter values except the
presence of `response_format=json_schema`.

| Observed response | `json_schema` | `unconstrained` |
|---|---:|---:|
| request duration | 29,118ms | 2,327ms |
| prompt tokens (reported) | 635 | 635 |
| completion tokens (reported) | 256 | 256 |
| `finish_reason` | `length` | `length` |
| JSON syntax | invalid | invalid |
| strict contract | FAILED: `LLM_INCOMPLETE_GENERATION` | FAILED: `LLM_INCOMPLETE_GENERATION` |

Elapsed-time difference was 26,791ms; ratio `29118/2327≈12.51`
for these two observed requests. Both stopped on the identical
256-token output cap without a complete JSON response, so neither is
a successful rubric assessment or evidence-backed score. The
unconstrained arm did **not** solve correctness.

The timing difference is **strong diagnostic evidence** that the
structured JSON-schema path may be a substantial source of latency
on the deployed pinned runtime/model combination. It does **not**
isolate the parser/backend cost causally: the generated token sequences
can differ; the first request could have been affected by warm-up,
shared tenants, caches or changing load; one fixed-order pair has no
replicates or counterbalancing. The comparator itself explicitly
reported `TWO_ARM_TIMING_OBSERVED_NOT_CAUSAL`,
`structured_decoding_overhead_proven=false`, and
`quality_benchmark=false`.

No further live requests, GPU/service setting changes, Schema or
Provider modifications are authorized by this observation. Next
engineering step: **offline** inspect the exact vLLM 0.10.2 guided
decoding backend, the effective schema characteristics and their
possible costs; design an approved, controlled performance and
validity experiment only after resource-owner sign-off. Do not
deploy unconstrained inference in production; always retain typed
Schema and evidence validation. Stage11 `BLOCKED`; Stage12
`NOT_STARTED`.

## 2026-11-04 pinned vLLM 0.10.2 guided-decoding backend review

**Exact-version external source review (not a running-container inspection):**
- vLLM v0.10.2 CLI uses `--guided-decoding-backend`, valid values
  `auto`, `xgrammar`, `guidance`, `outlines`, `lm-format-enforcer`,
  with documented default `auto`.
  Source: https://docs.vllm.ai/en/v0.10.2/configuration/engine_args.html
- In vLLM V1, the request processor resolves `auto` by first checking
  XGrammar support, then trying Guidance if XGrammar rejects the schema.
  Selecting the backend differently per request is not supported by V1;
  engine configuration and grammar acceptance are separate concepts.
  Source: https://docs.vllm.ai/en/v0.10.2/api/vllm/v1/engine/processor.html
- The v0.10.2 XGrammar validation code lists unsupported schema features
  including numeric `multipleOf`, array `uniqueItems/contains`,
  string `format`, and object `patternProperties`.
  Source: https://docs.vllm.ai/en/v0.10.2/api/vllm/v1/structured_output/backend_xgrammar.html

**Actual project/schema inspection:** the unchanged production
`LocalLlmProvider` sends `response_format.type=json_schema`
with `CriterionInference.model_json_schema()` and `strict=True`.
`stage11_guided_backend_inspect` evaluated this real code-generated
schema **offline**, recording 8 top-level fields, one definition,
one `$ref`, one `anyOf`, four arrays with `maxItems=32`,
two object `additionalProperties=false` constraints, and **no
known unsupported XGrammar keyword by the v0.10.2 static rule set**.
This does not prove XGrammar grammar compilation, actual backend
selection, decode performance or semantic Pydantic cross-field rules.
The latter remain enforced by the application's strict decoder.

**Actual CI:** first run 41796144954 failed one test exposing an empty
container-name input being silently treated as no opt-in. Fixed that
edge case and reran:
[41796324266](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41796324266)
`SUCCESS`: 59 Stage11 preflight tests passed, 162 focused
Provider/probe/backend-inspection tests passed. Default CLI emitted
`READ_ONLY_BACKEND_PREFLIGHT`, no Docker access and zero inference.
No live runtime backend was observed by the assistant.

**Operator-authorized, no-inference metadata-only next step:**

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_guided_backend_inspect.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_guided_backend_inspect
# Only with shared-owner approval for Docker read-only metadata access:
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_guided_backend_inspect --container ai-inference-vllm-1
```

The opt-in mode uses exactly two `docker inspect` metadata lookups:
`Config.Entrypoint` and `Config.Cmd`. It never prints raw command,
model identifier, image reference, Secret, environment, process list,
logs or paths; Docker permission failure becomes `UNVERIFIED`. Do not
run `sudo` unless the shared-runtime owner separately approves
the explicit `--sudo-docker` option (noninteractive `sudo -n` only).
Shell-wrapped commands are deliberately not parsed.

**Interpretation:** A configured `auto` is not proof that the request
resolved to XGrammar. The running engine's actual selected backend and
which part of 29.118s was grammar compilation versus decode are still
`UNVERIFIED`. Do not change the shared server, restart vLLM or send
new GPU requests to answer this. Stage11 `BLOCKED`, Stage12
`NOT_STARTED`.
