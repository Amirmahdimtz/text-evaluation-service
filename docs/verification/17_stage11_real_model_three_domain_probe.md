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

## 2026-11-04 — operator confirms actual XGrammar conversion

The Simorgh operator reported a read-only probe of container ai-inference-vllm-1.
The verified executable was /usr/bin/python3, with vllm=0.10.2 and
xgrammar=0.1.23. The actual unchanged CriterionInference JSON Schema was
accepted by xgrammar.Grammar.from_json_schema. The converter emitted a warning
that a string combining pattern with minLength/maxLength/format may ignore the
length/format constraints; the actual criterion_code field combines a pattern
with minLength=2 and maxLength=100. Independent strict Pydantic validation,
expected criterion-code comparison and source quote/offset checks remain intact.

This confirms only schema-to-grammar acceptance, NOT selected request backend,
tokenizer-aware GrammarCompiler compilation/cache, per-token bitmask overhead,
model-request latency or expert quality. Earlier structured 29.118s and
unconstrained 2.327s results were an uncontrolled one-pair observation with
two incomplete outputs, so neither was a successful evaluation.

### CPU-only conversion timing diagnostic (no inference)

The new scripts/verification/stage11_xgrammar_cpu_profile.py reports a
code-generated schema SHA-256 and flags combined pattern/length constructs
offline. With --emit-runtime-script it emits a self-contained Python program,
embedding only the code-defined JSON Schema, that calls
xgrammar.Grammar.from_json_schema **twice** and reports only bounded timings,
version strings, schema SHA-256 and sanitized status values. It does not import
a tokenizer, load weights, request inference, use the network, start or alter
a service, or write files. It may still consume CPU/RAM in a shared container.

First run the offline checks on Simorgh:

~~~bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_xgrammar_cpu_profile.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_xgrammar_cpu_profile
~~~

**Only after separate shared-container owner permission** to run a short
CPU-only Docker exec, perform this one stdin-only diagnostic:

~~~bash
cd /srv/projects/text-evaluation-service
set -o pipefail
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.stage11_xgrammar_cpu_profile --emit-runtime-script \
  | docker exec -i -e PYTHONDONTWRITEBYTECODE=1 \
      ai-inference-vllm-1 /usr/bin/python3 -
~~~

CPU_GRAMMAR_CONVERSION_OBSERVED measures only the schema conversion,
NOT GrammarCompiler.compile_json_schema with the model tokenizer, cache hits,
masking or decode time. Even very fast conversion would not rule out other
guided-decoding bottlenecks. Runtime measurement PENDING_SERVER; no production
Schema, Provider, model, backend, token cap, timeout or GPU settings changed.
Stage11 BLOCKED; Stage12 NOT_STARTED.

**Actual focused CI evidence for the CPU profiling utility:**
GitHub Actions run 41805920106, commit 98a35d0, SUCCESS: 59 synthetic
Stage11 safety checks and 174 focused provider/probe/inspection/CPU-profile
tests passed. This confirms the real repository's offline CI integration;
the two-pass conversion timing has **not** been run inside Simorgh.

## 2026-11-04 — Simorgh CPU schema conversion timing observed

**Operator-provided real runtime output**, after successful fast-forward
pull through main commit b4ed305: focused XGrammar CPU-profile tests ran
twice on Simorgh (**12 passed in 0.34s** each). The default offline CLI
reported schema SHA-256
`da781d766a47140e7ba844d501fc35c7ae65ae5506a3975440118c77d0e2c584`,
one combined pattern+length schema constraint, no network or inference.

With separately invoked container exec, the emitted CPU-only probe ran
exactly two calls to `xgrammar.Grammar.from_json_schema`:
- `conversion_ms_first=1.724`
- `conversion_ms_second=1.535`
- `status=CPU_GRAMMAR_CONVERSION_OBSERVED`
- runtime `vllm=0.10.2`, `xgrammar=0.1.23`, schema hash matched
- `model_inference_requests=0`, `per_token_masking_measured=false`,
  `tokenizer_aware_compilation_measured=false`,
  `request_latency_measured=false`.

This completes the **narrow CPU schema-to-grammar conversion timing
diagnostic**, previously PENDING_SERVER; it does NOT close any original
full-model acceptance test. Measured conversion (~1.6ms for these two
runs) is too short to explain an earlier ~29.118s full structured
request **as schema conversion alone**. The actual serving path could
also perform tokenizer-aware compilation, cache work, token masking or
other work; no attribution to any of these is yet established. The
earlier fixed-order structured/unconstrained A/B remains non-causal,
both outputs incomplete. The XGrammar combined pattern/length warning
appeared twice; post-response Pydantic/source validation stays intact.

**Next:** obtain owner approval and an isolated, bounded measurement
plan for actual vLLM request-phase breakdown and effective backend,
not another speculative shared-GPU request. No runtime/model/Schema/
Provider/GPU mutation was performed. Stage11 BLOCKED; Stage12 NOT_STARTED.

## 2026-11-04 — no-inference tokenizer-aware compiler and CPU mask investigation

The operator-observed prior schema-to-Grammar conversion timings
(1.724ms / 1.535ms) do not measure the expensive tokenizer-aware
compilation and per-token mask steps. The pinned vLLM 0.10.2
XGrammar backend uses xgr.TokenizerInfo.from_huggingface, an
xgr.GrammarCompiler with cache, compile_json_schema, and a
request-specific GrammarMatcher for token bitmasks:
https://docs.vllm.ai/en/v0.10.2/api/vllm/v1/structured_output/backend_xgrammar.html

Added a narrow Stage11 diagnostic:
scripts/verification/stage11_xgrammar_tokenizer_profile.py
and tests/test_stage11_xgrammar_tokenizer_profile.py.

**Default:** offline schema fingerprint, no Docker, network, model/tokenizer
access or GPU calls. **Operator-only opt-in:** --emit-runtime-script
prints a self-contained Python program for running in an *additional*
one-shot Python process in the existing container, only with explicit
owner approval. This process requires the exact approved, already-present
local model/tokenizer directory via STAGE11_LOCAL_TOKENIZER_DIR and must
not disclose the local directory in shared logs or chat. It rejects
unverified vLLM/XGrammar versions, refuses remote tokenizer code and
external downloads, denies Python network sockets, hides the GPU from
this child, suppresses path-bearing error output, caps the child to
one compiler thread and 32 MiB grammar cache, and applies CPU (25s) and
best-effort wall (45s) signal budgets. It still consumes shared host
CPU/RAM, so owner approval is mandatory. A genuine memory hard cap is
not proven, and native-code responsiveness to Python's wall alarm is
not guaranteed.

The probe reports separate tokenizer load, TokenizerInfo conversion,
compiler init, cold compile and cache warm compile times, then advances
a GrammarMatcher across at most 24 tokens of a **fixed synthetic JSON
abstention** (locally tokenized; never model-generated). It measures
CPU fill_next_token_bitmask and accept_token durations. No text,
tokens, local paths, schema body or model identifiers are printed.
It does not access the vLLM serving process's compiler or cache and
does NOT measure GPU logits masking, real GPU decoding, throughput,
real request latency or actual backend choice. The probe uses
max_threads=1 and cache_limit_bytes=32MiB (not proven equal to the
actual serving process's configuration), and any_whitespace=True,
so real production timings must not be inferred from this subprocess.

**Operator offline validation (no container):**

~~~bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  -q -p no:cacheprovider tests/test_stage11_xgrammar_tokenizer_profile.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.stage11_xgrammar_tokenizer_profile
~~~

**Only after separate shared-container-owner authorization and the
operator identifying the exact matching installed tokenizer path
*inside the container*, privately set the host-side forwarding variable**
(the path must not be posted to the assistant or committed):

~~~bash
read -r -p 'Approved in-container tokenizer path: ' STAGE11_LOCAL_TOKENIZER_DIR
export STAGE11_LOCAL_TOKENIZER_DIR
cd /srv/projects/text-evaluation-service
set -o pipefail
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.stage11_xgrammar_tokenizer_profile --emit-runtime-script \
  | docker exec -i -e PYTHONDONTWRITEBYTECODE=1 \
      -e STAGE11_LOCAL_TOKENIZER_DIR \
      ai-inference-vllm-1 /usr/bin/python3 -
unset STAGE11_LOCAL_TOKENIZER_DIR
~~~

Do not use a remote HF model ID. A tokenizer without local
config.json or unsupported/custom code will fail closed; do not
download/install anything to work around a failure in the shared
container. A successful
CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED only quantifies isolated
CPU operations on a synthetic JSON token sequence; the real vLLM
request path and end-to-end performance diagnosis remain
PENDING_SERVER. No additional inference approval is implied.
Stage11 BLOCKED, Stage12 NOT_STARTED.

**Repository CI evidence:** GitHub Actions [run 41809757700](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41809757700)
completed SUCCESS at commit 365ef1a5: 59 Stage11 offline
safety checks PASS, 184 focused offline tests PASS. The actual
tokenizer-aware diagnostic inside Simorgh and GPU token-mask
application remain PENDING_SERVER; neither was executed by CI.

## 2026-11-04 — operator CPU tokenizer probe import failure; no GPU activity

The Simorgh operator pulled main through f561895 and ran
tests/test_stage11_xgrammar_tokenizer_profile.py: **10 passed in 0.73s**
on that host. Offline CLI returned OFFLINE_TOKENIZER_PROFILE_PLAN
with zero Docker calls, inference requests, tokenizer loads and
network. A separate owner-invoked CPU-only probe used one local
tokenizer-cache candidate for Qwen3-8B-AWQ and reported
REQUIRED_RUNTIME_IMPORT_UNAVAILABLE; package metadata still read
vLLM 0.10.2 and XGrammar 0.1.23. No actual tokenizer-aware grammar
compilation or CPU token masking was performed; this is not a model
compatibility failure, nor proof the candidate tokenizer matches
the serving model.

A defect was identified in the **diagnostic script**, not the
production provider: it had overwritten socket.socket with a Python
function to block networking *before* importing XGrammar/Transformers.
Independent clean-Python reproduction showed that replacing this
class with a function can break stdlib ssl module initialization.
Because the on-server diagnostic concealed all import exceptions
under one fixed status, this is a plausible explanation, **not a
proven unique root cause** for the operator's import failure.

The Stage11-only probe now preserves socket.socket as a subclassable
class and denies connect/connect_ex/send/sendto/sendmsg/sendall,
create_connection and getaddrinfo without weakening the offline,
local_files_only, trust_remote_code=False guards. XGrammar and
Transformers failures have distinct redacted statuses:
XGRAMMAR_IMPORT_FAILED and TRANSFORMERS_IMPORT_FAILED. A synthetic
regression test explicitly imports a module subclassing socket.socket;
separate negative tests cover sanitized import failures and blocked
attempted outbound connect. Model/serving/container settings, model
files, passwords, secrets and inference traffic were not changed.

**Operator, after the same independent shared-container owner
permission and confirmation that the cached tokenizer is approved:**
pull the new main; run
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_xgrammar_tokenizer_profile.py`
and the default no-network CLI. Only then rerun the same previously
approved bounded synthetic tokenizer CPU diagnostic using a private
in-container tokenizer directory. Do not post paths or model files.
Actual tokenizer-aware compiler timings and GPU token-mask cost
remain PENDING_SERVER, Stage11 BLOCKED, Stage12 NOT_STARTED.

## 2026-11-04 — operator confirms tokenizer-aware CPU grammar timings

**Real Simorgh operator evidence:** checked out main through commit
b3f4278, executed the focused offline tests (13 PASS, 0.95s), and
ran the owner-gated one-shot tokenizer-aware CPU probe inside the
existing shared `ai-inference-vllm-1` container. Its status was
`CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED`, with vLLM 0.10.2,
XGrammar 0.1.23, vocabulary size 151,936, and the exact unchanged
application schema SHA-256:
`da781d766a47140e7ba844d501fc35c7ae65ae5506a3975440118c77d0e2c584`.

| Independent child-process CPU measurement | Observed |
|---|---:|
| Local tokenizer load | 455.070 ms |
| XGrammar TokenizerInfo creation | 764.613 ms |
| GrammarCompiler initialization (1 thread, 32 MiB cache) | 0.029 ms |
| Tokenizer-aware compile, cold | 231.697 ms |
| Same grammar compile, warm/cache | 0.028 ms |
| Fill token bitmask over 24 synthetic JSON token steps | 1181.770 ms total |
| Max single bitmask-fill step | 256.853 ms |
| CPU accept_token over 24 steps | 0.118 ms total |

Mean bitmask-fill step over this **specific** 24-step synthetic
trace was ~49.24ms (1181.77/24), but the 256.853ms maximum shows
substantial per-step variation. No first-step-vs-rest distribution
was emitted by this version; neither mean nor maximum may be
extrapolated to a real 256-token completion. No measured vLLM
request in this experiment, no GPU execution, no tokenizer-specific
serving cache observation, and no actual GPU logits-mask
application. The private tokenizer-cache candidate was
Qwen3-8B-AWQ; **whether it is the effective model/tokenizer used
by the serving process remains UNVERIFIED**.

**Interpretation:** the narrow schema-only conversion cost
previously observed (~1.5-1.7ms) is low. Tokenizer-aware cold
compilation (~232ms) is substantially greater but well below the
29.118s historical single structured request; warm compiler cache
lookup was ~0.028ms. CPU token-mask filling can be nontrivial even
without inference, making it a plausible component of structured
request latency. However the 24 synthetic token steps, a fresh
child process, shared-server activity, possible first-use work,
different token streams, unknown effective backend, and lack of
per-token GPU instrumentation prohibit **causal attribution** of
the previous structured/unconstrained gap. Both historical model
responses remained incomplete and invalid.

**Next diagnostic** (requires a new, specific shared-runtime owner
approval for any runtime measurement): separate first mask fill
from subsequent fills, report bounded distribution and warm-up,
verify actual serving backend and model/tokenizer provenance with
redacted authorized operator attestation; only then design a
controlled end-to-end latency/validity trial. Do not install,
restart, reconfigure, change the schema, drop strict validation
or submit an unapproved GPU request. This CPU subprocess probe is
OBSERVED/PASS only as a **narrow diagnostic**, not any formal
quality/performance acceptance gate. Stage11 BLOCKED, Stage12
NOT_STARTED.

## 2026-11-04 — first mask vs subsequent fills: bounded Stage11 follow-up

**Scope:** Only the previously approved Stage11 diagnostic script
`scripts/verification/stage11_xgrammar_tokenizer_profile.py` and its
existing focused tests have been enhanced. The actual Simorgh evidence
before this change was 13 focused tests passing and the existing
owner-invoked synthetic CPU profile: 24 mask fill steps totalling
1,181.770ms (maximum step 256.853ms), cold compile 231.697ms, warm
compile 0.028ms, XGrammar 0.1.23, vLLM 0.10.2. Those numbers **cannot**
tell whether the expensive mask step was first or later, and are not
a real vLLM/GPU request benchmark.

The tool now reports:
- `cpu_synthetic_mask_fill_first_ms`: first synthetic mask-fill time;
- `cpu_synthetic_mask_fill_first_share_percent`: share of total fill
  duration (null when total rounded observations are zero);
- `cpu_synthetic_mask_fill_rest_steps` and
  `cpu_synthetic_mask_fill_rest_total_ms`;
- `cpu_synthetic_mask_fill_rest_mean_ms`, `...rest_median_ms`,
  `...rest_max_ms`, `...rest_p95_nearest_rank_ms`.

P95 uses the nearest-rank definition over *at most 23* subsequent
synthetic observations; it is descriptive, **not** a production P95
or statistically representative performance SLO. Existing total/max
and token-accept metrics stay unchanged. If fewer than two synthetic
mask steps are available, the child fails closed with
`SYNTHETIC_MASK_STEPS_INSUFFICIENT` instead of reporting a
misleading first-vs-rest comparison. No per-token content or
token IDs are printed.

Synthetic, offline tests add deterministic first-vs-rest summaries,
zero-duration handling, insufficient-step rejection and integration
assertions over the existing XGrammar/Transformers stubs.
The existing safeguards remain: a fixed synthetic JSON abstention
and the actual code-generated Schema, no model inference, no remote
download, offline tokenizer flags, redacted error categories, 24-step
maximum, one compile thread, limited cache, CPU/wall signal budgets.
No Production Provider/Schema, vLLM service, GPU allocation, Secrets,
model files or docker settings changed.

**Offline operator checks:**

~~~bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_xgrammar_tokenizer_profile.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_xgrammar_tokenizer_profile
~~~

Only with *fresh shared-container owner authorization* and private
confirmation of the already-existing **matching** tokenizer path,
the same previous CPU-only opt-in probe may be rerun by the operator.
Do not run GPU inference, download model artifacts or reveal the
private model filesystem path. The serving backend, in-process
compiler/cache, real GPU token masking and attribution of the old
29.118s / 2.327s gap remain `PENDING_SERVER`.

**Gate:** Offline diagnostic enhancement is a narrowly scoped
preparation, not closure of any Stage11 model/performance/security
acceptance ID. Stage11 `BLOCKED`; Stage12 `NOT_STARTED`.

**Verified CI:** [GitHub Actions 41814799628](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41814799628)
SUCCESS on commit `7f53610`, with 59 Stage11 offline safety and
191 focused synthetic diagnostic/Provider tests passing. No
on-server first/rest mask cost or GPU inference was measured.

## 2026-11-04 — Simorgh real first-versus-rest CPU mask observations

**Operator-reported execution after pulling main through f352f4d:**
`tests/test_stage11_xgrammar_tokenizer_profile.py` had **17 passed
in 1.08s**. The default command returned
`OFFLINE_TOKENIZER_PROFILE_PLAN`, confirming no inference/network/
Docker operations in its default path.

The operator then independently ran the bounded, one-shot CPU-only
XGrammar tokenizer probe using an existing local tokenizer candidate
inside the shared container. The redacted result was
`CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED`:
- vLLM 0.10.2, XGrammar 0.1.23; vocab 151936;
- unchanged code-defined CriterionInference schema fingerprint:
  `da781d766a47140e7ba844d501fc35c7ae65ae5506a3975440118c77d0e2c584`;
- tokenizer load **458.834ms**, TokenizerInfo **802.633ms**;
- isolated cold compilation **239.614ms**, warm **0.030ms**;
- **24** CPU synthetic fill_next_token_bitmask operations total
  **1149.502ms**, first **0.094ms**, first share **0.01%**;
- subsequent **23** fill operations total **1149.408ms**,
  mean **49.974ms**, median **0.014ms**, nearest-rank P95
  **225.768ms**, maximum **247.760ms**;
- CPU accept_token total **0.124ms**;
- independent compiler thread limit 1, cache limit 32MiB,
  model_inference_requests=0, network_requests=0;
- effective_live_backend_verified=false,
  shared_service_cache_measured=false,
  gpu_token_mask_application_measured=false,
  real_request_latency_measured=false.

**Supported interpretation:** in this specific synthetic CPU-only
trace the first mask fill was almost free. Large spikes occurred
*later*; mean much greater than median indicates a right-skewed
distribution. The output does not report per-position timings or
token/grammar state, so it cannot isolate the exact transitions,
identify how many slow steps were present, or distinguish
grammar-state complexity, delayed native initialization, scheduling
or other possible causes. The nearest-rank P95 over just 23 steps
is a descriptive order statistic, **not a request latency P95**.
Do not extrapolate these times to 256 generated model tokens.

The older single structured-vs-unconstrained 29.118s vs 2.327s
pair used *different model-produced token sequences* with
uncontrolled shared load and both incomplete/invalid contracts.
The new CPU-only trace does not prove that live vLLM selected
XGrammar or that GPU logits masking is the bottleneck. The local
Qwen3-8B-AWQ tokenizer candidate has not been cryptographically
matched to the in-process serving model.

**Next, subject to new shared-runtime owner permission:**
a bounded no-inference, fixed-synthetic-output diagnostic could
report only slow-step indices or aggregate counts, never token
content, raw model text or paths; independently verify selected
serving backend/model, then plan a controlled real request-phase
measurement. No further container test, GPU inference, server
modification or production Schema/Provider edit was performed
by the assistant from this evidence. Narrow CPU first/rest test
OBSERVED; real serving performance and acceptance gates
PENDING_SERVER. Stage11 BLOCKED; Stage12 NOT_STARTED.

## 2026-11-04 — bounded synthetic CPU mask step indices

The Stage11 CPU-only tokenizer profiler now reports two additional
arrays: `cpu_synthetic_mask_fill_steps_gt_10ms` and
`cpu_synthetic_mask_fill_steps_gt_100ms`. Values are 1-based indices
into at most 24 fixed synthetic JSON tokenizer steps. Thresholds
are strict greater-than comparisons against already-rounded (3
decimal) millisecond observations. No raw tokens, token IDs, model
output, tokenizer paths or matcher state is printed.

This prepares identification of locations of occasional CPU mask
latency spikes in a synthetic trace, but an index is not evidence
of a particular XGrammar state, nor does it establish the live
serving backend or GPU inference latency. The previous operator
run observed 24 fills totaling 1149.502ms, median later fill
0.014ms and maximum later fill 247.760ms; it did not record
indices. The new indices are PENDING_SERVER until another
separately authorized owner-gated CPU-only container run.
Stage11 BLOCKED, Stage12 NOT_STARTED. No production code,
schema or GPU/runtime service was modified.

## 2026-11-04 — operator-observed Simorgh slow mask step positions

**Observed on the server, not inferred from CI:** after fast-forwarding
`main` through `a11d520`, the operator ran
`tests/test_stage11_xgrammar_tokenizer_profile.py`: **20 passed in
1.16s**. A separately invoked, one-shot fixed-synthetic-output CPU
profile inside the existing vLLM container reported
`CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED`. The two new fields were
identical:
`cpu_synthetic_mask_fill_steps_gt_10ms=[15,16,17,18,19]` and
`cpu_synthetic_mask_fill_steps_gt_100ms=[15,16,17,18,19]`.

**Technical evidence:**
- Exactly five **consecutive 1-based steps**, 15 through 19,
  each exceeded 100ms. All other 19 of the 24 sampled steps
  were at or below 10ms (on 3-decimal rounded timings).
  There were no sampled steps strictly between 10ms and 100ms.
- The 24 fills totaled **1150.577ms**. The first fill was
  **0.087ms** (0.01% of total), later 23 fills totaled
  **1150.490ms** (mean **50.021ms**, median **0.011ms**,
  nearest-rank P95 **226.338ms**, maximum **246.710ms**).
  Individual timings at positions 15-19 were **not** emitted.
- Local tokenizer load **450.091ms**; TokenizerInfo
  **764.192ms**; cold compile **231.962ms**; warm
  compile **0.024ms**; token accepts **0.116ms** total;
  vLLM 0.10.2, XGrammar 0.1.23, vocabulary 151936;
  `CriterionInference` schema SHA-256
  `da781d766a47140e7ba844d501fc35c7ae65ae5506a3975440118c77d0e2c584`.
- The bounded fixed-synthetic profiler submitted zero
  inference requests, did not measure GPU mask application,
  reported no verified effective serving backend and did
  not measure the shared in-process serving cache.

**Interpretation:** the first-mask-only and uniform-per-step-cost
hypotheses do not explain this *particular* synthetic trace.
Five contiguous later positions dominated total CPU mask-fill time.
They identify a *location* in the fixed synthetic token stream,
not an actual XGrammar state, accepted text span, root cause or
per-token GPU inference slowdown. An unverified tokenizer-to-live-model
mapping and independently launched child mean that the old
29.118s versus 2.327s one-pair comparison remains noncausal,
with both model responses invalid. The five slow-step indices
must not be described as production P95 or an accepted SLO.

**Next evidence need:** first establish, by authorized, redacted
serving-owner attestation, that the model/tokenizer and guided
decoding backend are actually those used by live vLLM. Separately,
a bounded *CPU-only* repeat could correlate these numerical
step indices with non-sensitive structural categories of the
fixed synthetic JSON, while preserving no token/ID/user-text
output. Such repeat requires its own approved execution window.
Do not reconfigure vLLM, change the JSON Schema, expand token
budgets, run GPU inference, install models or claim a speed fix
without controlled live evidence.

**Status:** on-host synthetic slow-step localization
`OBSERVED`; all model-backed security/performance/quality
acceptance gates remain `PENDING_SERVER`, Stage11 `BLOCKED`,
Stage12 `NOT_STARTED`.

## 2026-11-04 — bounded paired CPU matcher trace and synthetic JSON structure

The most recent **actual** Simorgh operator result on main
a11d520 was 20 focused tests PASS in 1.16s, and
`CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED` with five
contiguous fixed-synthetic CPU mask-fill positions [15,16,17,18,19]
strictly >100ms (24 first-trace steps total 1150.577ms).
That observation did not identify their JSON structural
region or whether the same positions would be slow again.

The Stage11-only opt-in diagnostic has now been extended,
*without modifying the production Provider/Schema or the
running vLLM engine*, to perform at most **two sequential
24-step fixed synthetic matcher traces**. It reuses the
same already-compiled grammar and local tokenizer, but
constructs a fresh GrammarMatcher/token bitmask for
each trace. There are at most **48 synthetic CPU fill and
accept calls total**, zero inference calls, no GPU model
execution, no model download, and no user data. The
previous first-trace metrics and indices remain present.
New redacted fields describe repeat2 total/first/median,
slow step positions at >10ms and >100ms, and a bounded
two-trace count.

To help interpret the five slow steps without releasing
token IDs, token content or strings, the diagnostic requests
a fast-tokenizer `offset_mapping` for the *same fixed
synthetic JSON string*, verifies input IDs match the
existing encoding, and classifies characters using only
SYNTAX, KEY, VALUE or CROSS_REGION plus one-based **field
ordinal**. It reports these labels **only for slow (>100ms)
steps** in each trace. On unavailable, out-of-range or
mismatched offsets it emits `UNVERIFIED` with no labels,
while preserving the measured CPU timings. No string,
token ID, raw offset pair, private path or grammar
matcher state is exposed. These labels refer to the
*next fixed synthetic token* at the matcher position,
NOT the actual internal XGrammar state or source of
slowdown.

The second sequential trace can distinguish a one-off
process/compiler warm-up hypothesis from repeated spikes
in the same *independent* matcher, but it cannot prove
in-process vLLM serving behavior, backend choice, GPU
masking overhead or causality of the old one-pair
29.118s vs 2.327s invalid outputs. The two traces do
not constitute a production latency P95 or model quality
benchmark. The runtime remains pinned to the observed
vLLM 0.10.2 / XGrammar 0.1.23; thread and grammar
cache budgets remain 1 thread and 32MiB, with the
existing bounded CPU and wall-time limits. **The new
two-trace experiment has NOT been executed on Simorgh;
it requires specific owner approval for the expanded
CPU-only 48-step workload.**

Existing separate preparation for checking launch
metadata: `scripts/verification/stage11_guided_backend_inspect.py`
is a dry-run by default. Its opt-in `--container`
only examines redacted Docker launch argument flags
under separate Docker-inspect permission. It **cannot**
prove the effective live per-request backend when
`auto` is used. Actual serving/tokenizer provenance
must be separately attested by the runtime owner; do
not inspect environment, process arguments, logs,
tokens or model files beyond approval.

**Status:** new paired/structure experiment and any
live backend attribution `PENDING_SERVER`; Stage11
`BLOCKED`, Stage12 `NOT_STARTED`.

## 2026-11-04 — Simorgh two independent CPU matcher traces and backend preflight

**Operator-supplied results after pulling main through cddce58:**
`tests/test_stage11_xgrammar_tokenizer_profile.py` returned
**26 passed in 1.30s**. The approved CPU-only synthetic probe
returned `CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED` with
**two successive fresh matchers over the same compiled grammar
and fixed synthetic JSON**. The separately authorized
metadata-only guided backend inspector also ran successfully.

| Metric | Trace 1 | Trace 2 |
|---|---:|---:|
| CPU bitmask fill, 24 steps total | 1159.124ms | 1146.884ms |
| First mask fill | 0.072ms | 0.011ms |
| Subsequent mask-fill median | 0.010ms | 0.009ms |
| Slow positions >10ms | [15,16,17,18,19] | [15,16,17,18,19] |
| Slow positions >100ms | [15,16,17,18,19] | [15,16,17,18,19] |
| Structural offset alignment | ALIGNED | ALIGNED |

Both fast-tokenizer offset maps yielded the **same coarse
synthetic JSON labels**: steps 15-18 map to `VALUE`,
`field_ordinal=3`; step 19 is `CROSS_REGION`
with null ordinal. These labels describe the next fixed
synthetic JSON token region, **not** the internal XGrammar
automaton state. No token strings, token IDs, raw offsets,
user/model text or tokenizer filesystem path was emitted.

The third fixture field is **`reason`**, because the script
serializes the schema with `sort_keys=True` and iterates
the alphabetically ordered `properties` map when building
the fixed JSON sample (see
`scripts/verification/stage11_xgrammar_tokenizer_profile.py`,
`build_runtime_script`). Thus, the repeated high-cost
CPU fills lie within/around the synthetic **string value
of `reason`**. This makes string-value handling
a focused diagnostic hypothesis, NOT a demonstrated
underlying XGrammar bug or production root cause.

Additional CPU observations for this run:
tokenizer load **449.674ms**; TokenizerInfo
**785.676ms**; compiler init **0.024ms**;
cold compile **227.487ms**; warm compile
**0.027ms**; first-trace subsequent max
**246.297ms**, nearest-rank P95 **229.249ms**;
first-trace token accepts **0.112ms**;
second-trace accepts **0.097ms**.
Container package metadata vLLM **0.10.2**,
XGrammar **0.1.23**, vocabulary **151936**,
unchanged application schema SHA-256
`da781d766a47140e7ba844d501fc35c7ae65ae5506a3975440118c77d0e2c584`.

**Guided backend metadata:** read-only inspection returned
`launch_metadata_status=LAUNCH_FLAG_ABSENT`,
`declared_backend=NOT_DECLARED_DOCUMENTED_DEFAULT_AUTO`,
`disable_any_whitespace_flag=NOT_DECLARED_DOCUMENTED_DEFAULT_FALSE`,
and `effective_request_backend=UNVERIFIED`.
Static schema inspection listed no keywords in its *specific*
vLLM-0.10.2 unsupported-keyword list; actual compiler validation
was `NOT_RUN` by that separate tool. Neither output
proves the in-process serving backend, model revision,
tokenizer fingerprint, or grammar-cache state.

**Scope of evidence:** the two consistent independent CPU
traces strengthen the observation that occasional mask-fill
cost is associated with a particular synthetic string
region; they do not measure live vLLM inference,
GPU logits mask application, service-level latency,
per-token grammar state, or causal relation to the
historical structured 29.118s / unconstrained 2.327s
ordered pair (both incomplete and invalid).
CPU diagnostic `OBSERVED`; formal production-quality,
No-Egress and performance acceptance remain
`PENDING_SERVER`. Stage11 `BLOCKED`,
Stage12 `NOT_STARTED`.

**Next authorized verification:** service owner should privately
attest actual loaded model/tokenizer revision and chosen
guided decoder for one request. A bounded CPU-only
fixed-synthetic study varying the *type/location* of
string-value regions could then test the string-state
hypothesis, but it requires a separately approved
experiment and must preserve strict output validation,
redaction, no-egress requirements and shared-resource limits.
No inference, operational changes or GPU tests were
performed by the assistant in processing this report.

## 2026-11-04 — prepared Stage11 reason-sensitivity and owner artifact checks

**Historical Simorgh observation, not a new measurement:** both
24-step fixed synthetic XGrammar CPU matchers showed >100ms
mask fills at steps 15-19. Offset labels put steps 15-18 in
the VALUE of the third sorted fixture field, `reason`.
The effective live guided decoder and served model/tokenizer
still remain UNVERIFIED after launch metadata showed default AUTO.

Prepared two **additional** fixed synthetic valid `reason`
fixtures behind the explicit
`--emit-runtime-script --reason-sensitivity` option on the
existing Stage11 CPU tokenizer profiler: short reason and
different text of equal character length. This preserves the
real Pydantic schema, compiles the same grammar once, keeps
two historical baseline matchers, and uses two additional
fresh matchers (four <=24-step traces, <=96 mask fills).
It returns timing/position aggregates, fully offset-aligned
reason-value totals when available, and no token values or
model data. The CPU=25s, wall=45s, compiler thread=1 and
cache=32MiB limits remain. New actual CPU measurements
need a distinct shared-container owner approval.

Added a **separate opt-in read-only** local config/tokenizer
byte comparison helper
`scripts/verification/stage11_serving_artifact_match.py`.
Two absolute directories must be privately owner-approved,
with the served path independently established from trusted
deployment evidence. Result only reports allowlisted file
equality booleans and counts; no paths, hashes, contents,
weight files or model inference. Matching files by
themselves are **NOT** evidence that live vLLM selected them.

See `docs/verification/18_stage11_serving_artifact_attestation.md`
for both procedures and limits. Neither experiment has been
run on Simorgh yet. Real served model provenance, request-
effective guided backend, GPU mask cost and structured
response validity PENDING_SERVER. Stage11 BLOCKED,
Stage12 NOT_STARTED.

## 2026-11-04 — Simorgh approved CPU reason sensitivity: actual operator evidence

**Observed:** operator pulled `main` through `fb6eb64`, ran
`tests/test_stage11_xgrammar_tokenizer_profile.py`,
`tests/test_stage11_serving_artifact_match.py`, and
`tests/test_stage11_guided_backend_inspect.py`: **58 PASS in 1.80s**.
The bounded opt-in `--reason-sensitivity` CPU-only child returned
`CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED` with unchanged schema hash
`da781d766a47140e7ba844d501fc35c7ae65ae5506a3975440118c77d0e2c584`;
vLLM **0.10.2**, XGrammar **0.1.23**, vocabulary **151936**,
one compiler thread, 32MiB compiler cache, and zero model inference
or network requests. The results concern **the cached tokenizer
candidate, not the proved effective serving artifact**.

| Synthetic CPU mask-fill trace | Sum (ms) | Steps >100ms | Complete reason-value steps | Reason-value cost (ms) |
|---|---:|---|---:|---:|
| baseline fixed JSON | 1159.961 | [15,16,17,18,19] | 4 | 931.077 |
| second independent baseline matcher | 1154.664 | [15,16,17,18,19] | 4 | 926.463 |
| REASON_SHORT | 473.408 | [15,16] | 1 | 247.710 |
| REASON_SAME_LENGTH | 1148.708 | [15,16,17,18,19] | 4 | 923.114 |

All four traces reported structurally aligned tokenizer offsets for
the reported slow positions. Baseline first fill **0.076ms**;
first baseline subsequent median **0.010ms**, maximum
**247.741ms**. Cold grammar compile **235.052ms**, warm
**0.025ms**, TokenizerInfo **780.412ms**, tokenizer load
**448.744ms**. Second baseline first fill **0.021ms**, rest
median **0.009ms**.

For `REASON_SHORT`, step 15 lies fully within the third sorted JSON
field's VALUE (`reason`), while step 16 crosses a structural
boundary. For `REASON_SAME_LENGTH`, steps 15–18 are
VALUE(`reason`) and step 19 CROSS_REGION, exactly like baseline.
The baseline fully aligned reason-value steps account for
**931.077 / 1159.961 ≈80.3%** of mask-fill duration;
this does not include the cross-region 19th step.
The results are consistent with repeated expensive CPU mask
computation at fixed synthetic string-value positions; they do
**not** establish the implementation-level cause or actual
service-level latency effect. The variants differ in tokenization
and how much of the JSON appears within the 24-token cap, so
total-time ratios are **not an isolated causal comparison**.

**Artifact comparison not run:** The operator's shell returned
after prompting for the owner-confirmed served directory, with
no output headed `OWNER_SUPPLIED_ARTIFACT_FILES_COMPARED`
or any other artifact comparison report. Do **not** count
matching file bytes as tested, and do not infer that the
cached Qwen3-8B-AWQ artifact was used by live vLLM. No new
request-level guided backend proof was supplied; the earlier
launch-only probe returned default `auto` with
`effective_request_backend=UNVERIFIED`.

**Next gates, owner-dependent:** privately establish authoritative
serving model/tokenizer revision and per-request backend from approved
deployment/runtime evidence. Only then approve a controlled GPU
request trial with equal synthetic prompts, explicit completion
validity checks, safe redacted timing phases and strict stop criteria.
Do not optimize schema, change vLLM configuration or lower validation
requirements based solely on a synthetic CPU-only profile.
Narrow CPU hypothesis `OBSERVED`; provenance and backend
`UNVERIFIED`; model/GPU/security/quality/performance gates
`PENDING_SERVER`; Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.


## 2026-11-05 — prompt-only compact-response diagnostic candidate

The operator's authorized one-shot 256-token media trial returned HTTP completion
at 29,145ms, but `finish_reason=length` and invalid/truncated JSON.
One shared exporter request-completion sample observed about 29.07s decoding
versus 0.033s prefill; sampled GPU utilization was 0–8%.
These are not causal evidence of XGrammar or model quality.

A **Stage11-only opt-in prompt variant** is now implemented in the existing
real-model diagnostic and no production DI/configuration is changed. It
appends concision instructions solely to the existing
`response_guidance` field, preserving the original candidate Rubric
checksum, score anchors, applicability/evidence requirements, strict
eight-field `CriterionInference` schema, model provider decoder,
exact quote/Unicode offsets and rejection on incomplete generation.
It prefers a shorter Persian reason and fewer unsupported list items,
but **never permits removal of rubric-required evidence**.
This is a hypothesis about output length, not proven latency optimization.
Its identifier is `compact_response_candidate_v1`; standard prompt
remains the default.

**Offline safe validation** (zero GPU/model HTTP calls):

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_real_model_criterion_probe.py tests/test_stage11_vllm_diagnostics.py tests/test_stage07_local_llm.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --domain media --disable-thinking --diagnostics --max-output-tokens 512 --compact-response
```

**Future separate authorization required:** after shared vLLM owner approval
for exactly one additional synthetic, single-domain request (max 512
completion tokens, 45s, no retries, in-flight=1, unchanged backend/runtime,
explicit resource/stop budget), an authorized operator may add
`--execute-live` to the last command once. This is **not** automatic
permission or a request to repeat the failed probe. On error, timeout,
resource alarm or incomplete schema **STOP**, preserve the sanitized
response/timings and do not retry. No raw prompts/responses, model identifiers,
secrets or logs may be published.

**Success criterion:** `contract=valid` and a complete schema- and
original-quote-valid response, not merely HTTP 200 or JSON syntax;
an abstention is not expert-confirmed scoring. Compare elapsed
time and output token count against the prior *non-equivalent*
256-token/truncated and 512-token/timed-out observations with
explicit limitations. Confirm actual served artifact/backend and
expert-reviewed three-domain quality separately. Until actual
on-host execution, `COMPACT_VARIANT=OFFLINE_PREPARED`,
real improvement `UNVERIFIED`, Stage11 `BLOCKED`,
Stage12 `NOT_STARTED`.

### 2026-11-05 — compact-response offline CI verification

[GitHub Actions 41990803105](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41990803105)
completed **SUCCESS** for commit `794579e72d16ecfc7a26d1af54da96bad1b6aa47`:
**59** existing safety checks and **241** focused synthetic/provider/diagnostic
checks passed. The API-only candidate image built, and its default networkless
loopback health and disabled-Worker checks passed. Added tests exercise the
real candidate Rubric instructions (all non-guidance fields unchanged),
strict eight-field response type, invalid prompt rejection, no-network
dry-run and compact-mode provider selection. All tests are offline with
stubs; no real on-prem GPU request or real compact-mode completion occurred.

**Status:** `COMPACT_VARIANT=OFFLINE_CI_VERIFIED`; latency/criterion correctness
on Simorgh `PENDING_SERVER`; Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.


## 2026-11-05 — experimental source-indexed evidence prompting after real offset failure

Operator on Simorgh fast-forwarded to `428b3fc`: **154 local
offline tests passed**. One additional authorized synthetic compact-response
media request returned `finish_reason=stop`, `json_syntax=valid`,
428 completion tokens, 739 prompt tokens, and **31,034ms** criterion
wall time. The strict provider rejected it with
`LLM_SCHEMA_REJECTED` / `EVIDENCE_OFFSET_INVALID`,
`PROBE_EXIT=2`. This indicates a quote was present in the original
synthetic source but its claimed Unicode offsets were inconsistent.
No acceptance-quality assessment was obtained. The before/after
**shared-service** exporter reported one E2E sample of 30.995317s,
decode 30.956226s, prefill 0.036045s, queue 0.000198s,
and +428 generation tokens; not proof of exclusive attribution.
The error category does not expose the quote or the actual offsets.

Root issue at this contract boundary: a generator can reproduce
a correct quote but fail to count exact Python Unicode codepoint
positions (including Persian zero-width non-joiners).
**Do not silently re-find or repair a model-provided offset.**
A new **Stage11 diagnostic-only** `--indexed-evidence` flag adds
short, deterministically extracted, pre-validated candidate
quote/start_offset/end_offset triples to `response_guidance`.
The source remains unchanged; the same strict Pydantic schema,
Rubric/score anchors, original-quote equality check and
`not_assessed` safety are enforced. The model is told to select
only semantically relevant existing anchors or abstain.
This tests *whether supplying trusted offsets improves validity*,
not whether the model can locate arbitrary evidence autonomously.
It is not a production fix, not a quality benchmark, and it
does not establish reference relevance.

The candidate is limited to one synthetic `media` criterion;
standard behavior and the prior compact flag remain unchanged.
The dry-run sends no network/model requests:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_real_model_criterion_probe.py tests/test_stage11_vllm_diagnostics.py tests/test_stage07_local_llm.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --domain media --compact-response --indexed-evidence --disable-thinking --diagnostics --max-output-tokens 512
```

Any actual `--execute-live` use requires a **new explicit**
shared-GPU owner approved one-request window (one synthetic POST,
no retries, 512 max output tokens, one in-flight, 45s timeout,
unchanged model/runtime/other tenants) and a resource stop plan.
Do not repeat the previous 31s request or adjust the shared server.
Success requires a schema-valid and exactly quoted source-grounded
result, not merely HTTP 200 or syntax-valid JSON; a valid abstention
is still not evidence of expert-rated score accuracy. If it fails,
record only the redacted category and stop. Stage11 `BLOCKED`,
three-domain real quality and full E2E `PENDING_SERVER`,
Stage12 `NOT_STARTED`.


## 2026-11-05 — quote-only evidence and deterministic offset derivation candidate

Operator repeated the authorized single-domain synthetic indexed-evidence
media run with current `main`: **165 focused local tests PASS**,
`DRY_RUN_NO_NETWORK` preflight, one actual 512-token-cap model POST
produced `finish_reason=stop`, syntax-valid JSON, **419 output
tokens**, **987 input tokens** in **31,018ms**; the strict decoder
again rejected it with `EVIDENCE_OFFSET_INVALID`. One shared
vLLM E2E histogram sample was 30.978029s, decode 30.942628s,
prefill 0.033472s and queue 0.000096s. No accepted model
criterion; no verified speedup or expert quality.

This falsifies the narrow hypothesis that merely providing
pre-indexed offset suggestions makes this model reliably
copy Unicode offsets. The next candidate therefore tests a
**different model/validator contract boundary**, not a relaxed
validator:

- Stage11-only `--quote-only-evidence` changes the **model-side**
  constrained JSON Schema to expect `source_kind` and an exact
  original-source `quote` without asking the model to calculate
  offsets. It is paired with `--compact-response`.
- Python maps each quote to a start/end range **only if it occurs
  exactly once** in the unchanged source, using exact Unicode
  codepoint string indices. Absent or ambiguous quotes, malformed
  evidence objects, model-supplied offsets, contradictory status,
  wrong criteria and missing Rubric-required evidence **fail closed**.
  No fuzzy matching, normalization, repair of generated offsets
  or synthetic score is allowed.
- The resulting complete eight-field `CriterionInference`
  still passes through the **existing strict production decoder**
  and the existing `CriterionEvaluationService`; ordinary
  production schema and endpoint remain untouched. This is a
  **Stage11 diagnostic experiment**, not a production contract
  change or proof that the model selected relevant evidence.
- All original synthetic data confidentiality bounds, single
  media criterion, local `127.0.0.1:8000`, 512 completion
  token cap, 45s deadline, one request and zero retries stay
  unchanged. No model/server/GPU settings are modified.

Offline-only preflight:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_real_model_criterion_probe.py tests/test_stage11_vllm_diagnostics.py tests/test_stage07_local_llm.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --domain media --disable-thinking --diagnostics --compact-response --quote-only-evidence --max-output-tokens 512
```

Any `--execute-live` **requires a fresh, bounded, separately
approved window** from the shared GPU/runtime owner. Do not assume
prior request authorizations remain valid. One request max, stop on
errors or model/resource contention; never automatically retry.
Actual quality, original quote relevance and full three-domain
validation still require expert-reviewed evidence. Pending live
verification: `PENDING_SERVER`; Stage11 `BLOCKED`,
Stage12 `NOT_STARTED`.


## 2026-11-05 — one real media quote-only contract passes

The Simorgh operator updated to `a2d5e5b`, ran **181 offline focused
tests (PASS in 1.43s)** and a `DRY_RUN_NO_NETWORK`. With separately
authorized **one** synthetic media criterion request in strict
JSON-schema/quote-only experimental mode, actual `media_message_clarity`
returned **contract=valid**, `status=assessed`, **provisional score 2/5**,
**one verified exact quote+offset**, **31,700ms** criterion wall time,
`finish_reason=stop`, 315 completion and 782 prompt tokens,
`PROBE_EXIT=0`. This is the first **observed real media single-criterion
contract success via the new quote-only diagnostic**, not proof that
the evidence is semantically relevant, the score is expert-correct
or any production path now uses this contract.

**Do not call this a three-domain PASS.** The legacy probe status
string `REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS` appeared because
`_run_cases` used one result label regardless of `--domain`;
this run explicitly had `requests_planned=1` and only media.
A follow-up fixes single-domain result codes and preserves
three-domain status only for all-three scope. The same experimental
quote-only approach can now be selected independently for `speech`,
`media`, or `research`, but **no speech/research live result exists**.

Shared vLLM before/after exporter had +1 completed request,
E2E **31.659440s**, decode **31.415452s**, prefill
**0.199588s**, queue **0.042499s**, and +315 generated
tokens. Shared exporter values are not independently
request-correlated. **31.7s is not a throughput/latency PASS**,
and one score is not a golden quality benchmark.

Future **single-domain** operator test requires an explicitly
new shared-owner permitted GPU window/resource budget for
*each* request, with no retries and no server config changes.
Candidate dry-run has zero model calls and only one selected
criterion. Full staging E2E/No-Egress/quality/model
identity/alternative model and 56 mandatory Stage11 gates
remain PENDING_SERVER. Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.


## 2026-11-05 — research cross-field rule failure and conditional prompt experiment

The Simorgh operator pulled through `9b4ec67`: **214 focused offline tests
PASS (1.53s)**. Exactly one approved synthetic research criterion
in the experimental quote-only schema completed after **35,887ms**
with `finish_reason=stop`, syntax-valid JSON, 296 completion tokens
and exit code 2. The strict model-level validator rejected it:
`LLM_SCHEMA_REJECTED` with the fixed category
`MODEL_RULE_ABSTENTION_HAS_SCORE_OR_EVIDENCE`.
The returned `status=not_assessed` was combined with a non-null score
or non-empty evidence. The safe category **does not distinguish which
of those two values** was present; neither should be inferred or logged.
One shared-service E2E/decode histogram increment was 35.843329s
/ 35.807389s, with prefill 0.033190s and queue 0.000099s.
Shared exporter deltas are not isolated request traces. The unrelated
`/srv/projects/text-similarity/app` SSH-gated command in the operator's
terminal output belongs to another repository and was not inspected,
modified or counted toward this project's gate.

**Targeted Stage11 diagnostic-only alternative:** a separately gated
`--research-consistent-status` prompt variant augments the **system
instruction** with explicit mutually exclusive branches: assessed
requires supported exact quote evidence and integer score; abstention
requires null score and empty evidence, with an informative reason.
Never force a score, fabricate evidence, reinterpret absent evidence,
or silently repair a contradictory model output. The model still
uses the existing quote-only experimental JSON schema and final
strict production validator; no production provider, business Rubric,
DI or runtime changes. It is not a conditional JSON Schema feature
claim, only an opt-in prompt hypothesis.

This variant permits exactly one `research` synthetic criterion,
`--disable-thinking --diagnostics --compact-response
--quote-only-evidence --research-consistent-status`, 512 max output
tokens, no retries, one in-flight and 45s timeout. The default
is a no-network dry-run. Any live invocation requires a **new**
explicitly authorized shared GPU one-shot resource window; not
covered by consumed prior permissions. If incomplete, invalid,
or conflicting, stop and retain sanitized results. **Passing
schema never proves semantic accuracy, true abstention quality,
expert relevance or production readiness**.

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_vllm_diagnostics.py tests/test_stage11_real_model_criterion_probe.py tests/test_stage07_local_llm.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --domain research --disable-thinking --diagnostics --compact-response --quote-only-evidence --research-consistent-status --max-output-tokens 512
```

Stage11 `BLOCKED`, Stage12 `NOT_STARTED`; real model quality,
provenance, accepted three-domain benchmark, No-Egress, signed
API/Worker/DB/LLM E2E and performance tests `PENDING_SERVER`.
