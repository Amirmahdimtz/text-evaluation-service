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
