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
