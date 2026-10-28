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
