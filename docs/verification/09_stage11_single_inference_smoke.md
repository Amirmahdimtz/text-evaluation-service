# Stage 11 — One-Shot Synthetic Structured-Output Inference Smoke

**Status:** `READY_FOR_OPERATOR_RUN / NOT_EXECUTED_ON_SIMORGH` (2026-10-28); Stage 11 overall `BLOCKED`; 56 organizational acceptance tests still `PENDING_SERVER`.

## Explicitly permitted scope

The user authorized one minimal **synthetic-only inference request** to the already-running vLLM-compatible service on Simorgh. This permission does **not** grant model deployment/download, new GPU memory allocation, Docker mutation, load/soak, network exploration, secret access, real-text use, security signoff, or any production change. If the existing service is shared with production or has an owner-defined request budget, the operator must comply with that owner policy and stop if permission is not sufficient.

The one-shot tool `scripts/verification/stage11_synthetic_inference_smoke.py` is intentionally separate from production API/Worker code. It reads one advertised model ID **in process only** from one local `GET /v1/models`, then makes **at most one** `POST /v1/chat/completions` to literal `127.0.0.1` on the explicitly selected loopback port. No proxies, remote hostname, redirect following, external fallback, retries, real source text, user credentials, or local Docker access. If metadata is ambiguous (zero/multiple models or invalid response), it **does not POST**. Earlier evidence observed exactly one model ID on local port 8000, redacted as a private/aliased identifier; the script never prints it.

The request uses a **fixed, developer-owned synthetic Persian prompt**, zero temperature, `max_tokens=64`, `stream=false`, no tools, and a tiny `response_format=json_schema` contract requiring JSON `{"ack":"ok"}`. No tool is given permission to accept arbitrary prompts or model names. Network IO timeouts: metadata socket 4s; inference socket 40s. This is a bounded socket timeout, not proof of a strict end-to-end wall-clock deadline. Metadata responses are limited to 16 KiB and inference envelopes to 32 KiB. Assistant-generated/user/company text is not an input. Only a small **sanitized JSON** status, HTTP status, elapsed milliseconds, and validated token count fields are shown; prompt/response content, private model ID, URLs, raw errors, headers and credentials are never printed or written to repository files. The server's own access logging policy is not verified by this script.

## Commands — run **once** on authorized Simorgh host

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_synthetic_inference_smoke.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verification/stage11_synthetic_inference_smoke.py --dry-run
# This next line performs the ONE approved real synthetic inference request.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verification/stage11_synthetic_inference_smoke.py --port 8000
```

Review the dry-run/test results before sending the one request. The script does not need `sudo`, Docker or model identifier arguments. **Do not rerun** after a failure or timeout under this one-request approval. No real text should be pasted into the tool. If port 8000 is no longer the explicitly approved loopback endpoint, do not guess or scan ports; stop and ask the service owner. Inspect any unexpected full stdout locally before sharing; share only sanitized status and counters.

## Acceptance oracle and limitations

- `PASS_SYNTHETIC_STRUCTURED_SMOKE` with HTTP 200 means the loopback endpoint accepted **one** synthetic JSON-schema chat completion, returned exactly one assistant choice for the requested advertised ID, `finish_reason=stop`, and parsed generated JSON **exactly** as `{"ack":"ok"}`. This is **limited Stage11 smoke evidence** for one simple schema, not proof of complete criterion schema support, safety, quality, accuracy or an approved model artifact.
- `INFERENCE_HTTP_REJECTED` with status 400 may indicate unsupported schema/generation settings; 401/403 mean access rejected; 429/503 indicate capacity/backpressure; 5xx are server failures. Do not infer exact causes from status alone. Errors never include raw upstream data. `INFERENCE_SCHEMA_UNVERIFIED` can indicate model mismatch, incomplete generation, invalid JSON or wrong structure. `INFERENCE_TRANSPORT_OR_TIMEOUT` is **not** success. A failed run must not be repeated without a separately approved attempt.
- This tool does not test actual production Provider DTO schema, rubric evaluation, no-egress, isolated enterprise IAM/KMS, real dataset quality, GPU capacity, latency percentile, concurrency or E2E. No Stage11 organization-required test ID is complete merely because this probe passes. Existing 56 deferred acceptance test IDs remain `PENDING_SERVER`, Stage11 `BLOCKED`, and Stage12 `NOT_STARTED` until each approved gate has verified evidence.

Evidence classification: prior Simorgh 13 host inventory tests and 30 container-metadata tests are distinct offline/metadata results; the 35 new synthetic smoke tool tests and dry-run are executable off-host without any actual inference. Actual Simorgh one-shot result must be entered here only after an operator supplies sanitized output; do not record `PASS` in advance.
