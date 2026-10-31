# Stage 11 — Real CriterionInference Contract Verification

**Status:** `OFFLINE_VERIFIED / SIMORGH_CRITERION_INFERENCE_PENDING / STAGE11_BLOCKED` · 2026-10-28. This is **Stage 11 only**. The prior single minimal JSON-schema smoke was user-reported `PASS`; its authorization was consumed. Do not misclassify that tiny schema as a full rubric/evidence contract.

## Purpose

Exercise the **actual application contract** `CriterionInference.model_json_schema()` and `decode_criterion_response()` from `src/infrastructure/providers/llm/structured_response.py` rather than inventing a surrogate model schema. The single fixed synthetic Persian source uses criterion `clarity`; a successful response must report `assessed`, a bounded integer score, non-empty evidence, an exact quote from the synthetic source and matching Unicode codepoint offsets. The production parser must accept the generated JSON and reject duplicate keys, invalid scores, invalid offsets and unsupported/ambiguous responses. This is **contract compatibility only**, not a subjective AI quality score or model selection.

## Scope and impact

- Script: `scripts/verification/stage11_criterion_contract_smoke.py`. No production API, model configuration, database, secrets, worker or container changes.
- Default CLI is **no-network**. It requires an explicit `--execute-approved` flag for a real call and an independently approved operator/Infrastructure resource and test window. The user's earlier authorization covered **only the already-consumed, single tiny-schema request**; **do not treat this document as permission for an additional generation**.
- On explicit execution: exactly one host-loopback `127.0.0.1` GET to `/v1/models` for one advertised opaque ID; at most one POST to `/v1/chat/completions`, `response_format=json_schema` with the **actual Pydantic schema**, `temperature=0`, `max_tokens=320`, no tools, no retries, no auth or ambient proxy, bounded response and connection timeout. Not a strictly guaranteed whole-process wall clock limit.
- Only fixed **synthetic Persian** text is submitted. No confidential/company text, arbitrary CLI prompt, network scan, model download or additional GPU allocation. In the client output, original text, model ID, response, error payload, full internal endpoints and tokens are **not printed**. Server-side logs, routing, No-Egress and model provenance are **not independently verified** by this script.
- Fail-closed on non-200, ambiguous model list, malformed envelope, non-stop, wrong model ID, unexpected tool calls/refusal, nonassistant role, invalid JSON and quotes/offsets. Failures do **not** trigger retry.

## Operator commands — no inference without renewed permission

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main

# Offline only; no inference or network request.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage11_criterion_contract_smoke.py \
  tests/test_stage11_synthetic_inference_smoke.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_criterion_contract_smoke.py

# Equivalent module entry point (also network-free by default):
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.stage11_criterion_contract_smoke
```

**Only after a separate explicitly scoped approval** to send one **additional** synthetic, low-load inference to the existing approved internal endpoint:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_criterion_contract_smoke.py \
  --port 8000 --execute-approved
```

Run **once**; do not repeat after failure, do not scale token count or parallelism, and do not disable API auth if the endpoint requires it. The printed sanitized summary contains only overall status, HTTP status, elapsed milliseconds and verified evidence count/tokens (when applicable). Keep raw evidence, private package and model artifact manifests in organization-approved private storage only.

## Acceptance classification

- `PASS_SYNTHETIC_CRITERION_CONTRACT`: one synthetic, quoted evidence-bearing response passed the **real application validator**. Record only as **auxiliary partial evidence** for `S07-S11-01`, `S07-S11-04`, `S11-AI-06`, and `S08-S11-01`; none passes in full until the original Stage11 oracle and model/data approvals are satisfied.
- `CRITERION_CONTRACT_UNVERIFIED` / HTTP/timeout/invalid response: no PASS. Capture only the sanitized outcome, then stop. Never inspect raw prompt/model output via public CI/chat to debug.
- `DRY_RUN_NO_NETWORK`: local safety success, **not** live-model evidence.

**Gate:** 56 mandatory Stage11 tests still `PENDING_SERVER` until their specific real evidence is verified. Security No-Egress, expert-labeled three-domain model comparison, SSO/KMS, authentic enterprise E2E and RPO/RTO remain unknown; Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. Do not promote to Production.

## Simorgh CLI import regression and resolution — 2026-10-28

- User-reported Simorgh checkout successfully fast-forwarded to commit `20233d1`; 70 unit/contract tests passed in **0.24s**. The *direct file-path* dry-run then failed before making any network request with `ModuleNotFoundError: No module named 'scripts'`. This **does not represent an inference/model failure**, and no additional server request was sent.
- Root cause: direct Python execution places `scripts/verification` rather than the repository root on `sys.path`; the smoke entry point uses absolute `scripts.verification.*` and `src.*` imports. Pytest supplies the repository root so it did not expose this issue.
- Fix: bootstrap only the trusted repository root for **direct script entry**, preserving existing absolute imports and production code. The module entry point `python -m scripts.verification.stage11_criterion_contract_smoke` is also supported. Two subprocess regression tests exercise both invocation forms, including the direct script using isolated Python (`-I -B`) without ambient Python paths.
- Fix verification on the assistant-host environment: **72 passed in 2.47s** for the existing/new suites; direct and module dry-runs returned `DRY_RUN_NO_NETWORK` with no credentials, HTTP request, model loading or GPU work. **User-server retest of the fixed direct CLI is pending; no new enterprise test was marked PASS.**
- The earlier single live synthetic response remains valid auxiliary evidence, but its scope was consumed. Running with `--execute-approved` still requires **new explicit operator/organizational authorization**. Stage 11 `BLOCKED`, 56 mandatory tests `PENDING_SERVER`, Stage 12 `NOT_STARTED`.

## Stage11 CI syntax issue — 2026-10-28

GitHub Actions did not start jobs for the three Stage11 offline workflows before this correction, although Python tests passed on Simorgh and the assistant host. An invalid inline `run:` value containing `--only-binary=:all:` caused YAML parsing failure, confirmed offline by PyYAML. The three workflows now use safe block scalar `run: |` for the pip command, and the criterion test file adds a regression suite that parses all three workflows and asserts no active inference flags in CI. **75 local tests passed** after the fix. New GitHub Actions results must be checked independently; real server criterion inference remains unauthorized/not run, with all 56 enterprise tests `PENDING_SERVER` and Stage11 `BLOCKED`.

## GitHub Actions outcomes after CLI/YAML fixes — 2026-10-28

Checked the actual GitHub Actions job-level results at commit `82595099e3ea67023b61e424542da16748403e75`. All three relevant offline Stage11 workflows returned **success**: criterion-contract run `40696993930`, preflight run `40696993921`, synthetic smoke run `40696993968`. Direct isolated script and Python module dry-run steps both passed inside the criterion CI job. All are **offline/mock tests**, **not** new model inference or organizational acceptance. Simorgh must still pull and execute the fixed CLI default dry-run; no real criterion inference permitted without a separate explicit approved request. Enterprise test ledger 56 `PENDING_SERVER`; Stage11 `BLOCKED`.

## Successful post-fix direct entrypoint verification on Simorgh — 2026-10-31

After pulling revision `f001794`, the operator ran the two offline suites and reported **75 passed in 0.62s**. The **direct file-path CLI** then returned the expected sanitized `DRY_RUN_NO_NETWORK` JSON status (including `stage11_gate=BLOCKED`), with **no `ModuleNotFoundError`**. This confirms the specific direct-entrypoint import regression was repaired **on the target server**, not only in developer mocks/CI. The CLI was invoked without `--execute-approved`, so it made **no actual inference POST**. This verifies the command path and default fail-closed behavior only; it does not validate real `CriterionInference` output or model/AI quality.

**Status:** `SIMORGH_DIRECT_CLI_REGRESSION_PASSED / REAL_CRITERION_INFERENCE_PENDING_APPROVAL`. The prior one-request synthetic inference permission has already been consumed. Do not rerun that inference or use `--execute-approved` without separate explicit authorization. The **56 original enterprise tests remain `PENDING_SERVER`**, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## Simorgh live full-criterion smoke returned unverified — 2026-10-31

The operator supplied the sanitized output from **one active invocation** on the already running Simorgh loopback endpoint with `--port 8000 --execute-approved`. Reported `http_status=200`, `elapsed_ms=6047`, `status=CRITERION_CONTRACT_UNVERIFIED`, `schema_version=stage11-criterion-contract-smoke-v1`, `model_id_logged=false`, `model_output_logged=false`, `synthetic_only=true`, `retries=0`, `max_inference_requests=1`, and `stage11_gate=BLOCKED`.

**Classification:** `FAIL_OPERATOR_REPORTED_AUXILIARY_REAL_CRITERION_SMOKE`. This does **not** mean the model passed the Pydantic criterion schema or had valid quote/codepoint evidence. HTTP 200 shows transport-level response only. The **6047 ms** measurement is a single request-to-headers observation, not p95 or an SLO. The earlier one-field `ack` JSON-schema smoke PASS remains separately valid. Full criterion output validity is **unknown/failed to verify**.

**Diagnosis limitation:** prior script collapsed unfinished generation, incomplete JSON, schema errors, wrong criterion, quote/offset errors and even a structurally valid `not_assessed` into the same generic outcome. The operator's redacted transcript therefore cannot retrospectively identify which happened. No raw response, private model ID or content should be requested in public logs/chat; no speculative model bug, output-token shortage or prompt change should be asserted as root cause.

**Offline-only diagnostic improvement:** commit `17583907f5a4fc2c483c1f7ba43481800d16531c` adds static `failure_class` categories and bounded numeric `usage_tokens` to a **future failed** single-request summary, without weakening `decode_criterion_response`, exposing generated text, or adding retries. Categories include `OUTPUT_TOKEN_LIMIT`, `SCHEMA_REJECTED`, `QUOTE_OFFSET_MISMATCH`, `CRITERION_CODE_MISMATCH`, `VALID_ABSTENTION_NO_ASSESSMENT` and safe envelope/JSON failure codes. `VALID_ABSTENTION_NO_ASSESSMENT` is legitimate model abstention but remains **insufficient evidence for this grounded-assessment smoke PASS**, not a forced numeric score.

The GitHub Actions [offline criterion CI run 41181109595](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41181109595) completed **success: 90 passed in 0.61s**, including direct and module CLI dry-runs. These mocks did not re-run the model and do not determine the preceding failure class.

**Authorization:** this active generation has **already occurred**; treat that execution allowance as consumed. **Do not rerun** `--execute-approved`, increase max tokens, inspect sensitive server log content, or conduct live benchmarks without a separately approved test scope and resource window. The default CLI remains `DRY_RUN_NO_NETWORK`.

**Enterprise gate:** all original 56 mandatory Stage11 acceptance IDs remain `PENDING_SERVER`, no model-quality score is produced, `Stage11=BLOCKED`, `Stage12=NOT_STARTED`.

## Updated diagnostic CLI validated on Simorgh, without new inference — 2026-10-31

Operator successfully fast-forwarded the repo `c8f10ba..63fb8e3` after an earlier temporary GitHub DNS failure. On Simorgh's `.venv`, the two Stage11 contract/smoke suites returned **90 passed in 0.67s**. This confirms the redacted failure-classification test harness is locally installed and its **mock tests** pass. It **does not** establish a specific failure class for the earlier HTTP 200/`CRITERION_CONTRACT_UNVERIFIED` request: that old run cannot be decoded retrospectively. No `--execute-approved` invocation occurred in this retest; further inference needs new scoped authorization.

A previously reported untracked nested `text-evaluation-service/` directory is of unknown origin and must **not** be deleted or staged without read-only inspection. All 56 original Stage11 enterprise tests remain `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## Real Simorgh second criterion smoke: evidence/offset mismatch — 2026-10-31

The authorized operator ran exactly one additional synthetic `--execute-approved` criterion request against local vLLM. The supplied **sanitized JSON** reported: `HTTP 200`, `elapsed_ms=6010`, `status=CRITERION_CONTRACT_UNVERIFIED`, `failure_class=QUOTE_OFFSET_MISMATCH`, `prompt_tokens=166`, `completion_tokens=113`, `total_tokens=279`, `retries=0`, `max_inference_requests=1`, `synthetic_only=true`, `model_id_logged=false`, `model_output_logged=false`, `stage11_gate=BLOCKED`.

**What the result actually proves:** the received candidate output reached the Pydantic criterion schema and expected criterion-code checks, but **at least one quoted evidence string did not equal** `original_text[start_offset:end_offset]`. The validator's previous single error code combined (a) a quote absent verbatim anywhere in the original and (b) a quote present with incorrect boundaries. **Which subcase occurred is not recoverable** from this redacted output; we must not speculate about bytes vs Unicode, tag offsets, character normalization or hallucinated quotations. `finish_reason` had to be `stop` to reach this validation. With 113 completion tokens against a 320-token cap, this event is **not evidenced as output truncation**. One elapsed time is not p95 or an SLO.

**Corrective code, without automatic evidence repair:** commit `fd072f1e18c866479c6462b0a026d1dbe660969e` changes the parser to keep strict fail-closed equality and distinguish `LLM_QUOTE_NOT_FOUND` vs `LLM_QUOTE_OFFSET_INVALID`; only static diagnostic labels `QUOTE_NOT_FOUND_IN_SOURCE` and `QUOTE_OFFSET_INCORRECT` are exposed by the smoke. It does **not** normalize, relocate, guess, repair or accept any mismatched quote/offset. The synthetic prompt now unambiguously specifies its entire source's exact Python Unicode codepoint length and half-open `[start,end)` positions excluding wrapper tags. The real `LocalLlmProvider` prompt now states the same offset convention for arbitrary sources, including original length, with no prompt logging. `PROMPT_VERSION` advances from `stage08-prompt-candidate-0.1` to `stage08-prompt-candidate-0.2` for traceability. This is a **proposed model instruction improvement**, not evidence that the real model will comply.

**Actual regression evidence on the code revision:** all seven GitHub Actions workflows succeeded, including isolated-PostgreSQL Stage10 E2E run `41182886734` with **391 passed**, Stage07 internal provider run `41182886707` with **53 passed** (its broad non-DB suite 376 passed/8 skipped), Stage08 offline run `41182886739` with **37 engine tests passed** and 376 passed/8 skipped, Stage09 worker run `41182886685` with **391 passed** full suite, Stage11 criterion offline run `41182886694` with **91 passed**; Stage05 `41182886717` and Stage06 `41182886745` also succeeded. These are synthetic/fixture tests, **not a repeat real-model test**.

**Next safe operator actions (offline only):**
```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage11_criterion_contract_smoke.py \
  tests/test_stage11_synthetic_inference_smoke.py \
  tests/test_stage07_local_llm.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_criterion_contract_smoke.py
```
The last command **must** be `DRY_RUN_NO_NETWORK`. **Do not run** `--execute-approved` again automatically: the user's prior one-inference scope was consumed by this latest request. The current source is still available on GitHub; a Git pull to a controlled checkout does not require exposing real model or organization data.

**Unchanged Gate:** `AUXILIARY_LIVE_CRITERION_SMOKE_FAILED_TO_VERIFY`, all original 56 enterprise test IDs `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. New scoped operator/infrastructure authorization is required before any next real generation; no raw model payload, token/credential, private artifact identity or confidential source should be pasted into public evidence.

## Simorgh dry-run and local provider regression after quote-offset fix — 2026-10-31

On the operator's Simorgh working copy, `git pull --ff-only origin main` completed successfully and `git rev-parse --short HEAD` printed `a5fd771`. Actual reported command:
```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage11_criterion_contract_smoke.py \
  tests/test_stage11_synthetic_inference_smoke.py \
  tests/test_stage07_local_llm.py
```
**Result:** `144 passed in 1.47s`. The subsequent default, non-approved CLI invocation returned `DRY_RUN_NO_NETWORK` with no HTTP request to the model. This is `PASS_OPERATOR_REPORTED_SIMORGH_OFFLINE_CONTRACT_REGRESSION` only; it is **not** a new success of the real synthetic CriterionInference contract. The last real authorized request failed `QUOTE_OFFSET_MISMATCH`. Do **not** run `--execute-approved` on the basis of this offline pass; new approval is required. Original Stage11 56-ID test ledger remains `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## Successful Simorgh single-shot real CriterionInference contract — 2026-10-31

**Operator-supplied sanitized evidence:** The operator ran `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verification/stage11_criterion_contract_smoke.py --port 8000 --execute-approved` **once**, under a fresh one-request approval, after updating to the source with clarified Unicode quote-offset instructions. The script returned:

| Field | Observed |
| --- | --- |
| `status` | `PASS_SYNTHETIC_CRITERION_CONTRACT` |
| `http_status` | `200` |
| `assessment_status` | `assessed` |
| `criterion_schema_valid` | `true` |
| `grounded_evidence_valid` | `true` |
| `evidence_count` | `1` |
| `elapsed_ms` | `6449` |
| `usage_tokens.prompt_tokens` | `206` |
| `usage_tokens.completion_tokens` | `116` |
| `usage_tokens.total_tokens` | `322` |
| `retries` / `max_inference_requests` | `0` / `1` |
| `synthetic_only` / `model_id_logged` / `model_output_logged` | `true` / `false` / `false` |
| `stage11_gate` | `BLOCKED` |

The `max_tokens=320` argument limits **completion tokens**; `total_tokens=322` includes 206 prompt tokens and is therefore not a violation. The script verified a strict, assessed **single clarity criterion** and a quote exactly matching the original synthetic Persian input at its codepoint offsets. This shows real **schema + evidence** compatibility for one run, following previous failures, **not a quality benchmark or repeatability result**. The single `elapsed_ms` reading is not an SLO/p95 latency measurement. No model ID, generated text, organizational data, secrets or raw runtime output were recorded in the public evidence.

**Acceptance:** `PASS_AUXILIARY_REAL_SYNTHETIC_CRITERION_CONTRACT` with **one grounded evidence item**. The previous `QUOTE_OFFSET_MISMATCH` failure stays in the defect history; it has a new positive observation but has not been statistically resolved for repeatability. This specific one-shot permission has been **consumed**. Do not run `--execute-approved` again without a newly bounded operational approval.

**Next Stage11 gate work:** approve/pin the actual model artifact revision and legal/custody provenance, then conduct the two-candidate three-domain expert-labeled benchmark with separately approved GPU/time/data scopes; complete enforceable network No-Egress and authenticated protected API/Worker/PostgreSQL/LLM E2E plus capacity/recovery tests. Per the revised Implementation Plan, keep all **56 mandatory acceptance test IDs as `PENDING_SERVER`** until their full original acceptance oracles are demonstrated; `Stage11=BLOCKED`, `Stage12=NOT_STARTED`.
