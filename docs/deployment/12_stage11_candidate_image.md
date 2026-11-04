# Stage11 — Offline API Image Candidate and Critical-Path Handoff

**Scope:** Stage11 engineering candidate; **NOT** an approved deployment,
running service, signed artifact, or production-ready image.
Stage11 `BLOCKED`; Stage12 `NOT_STARTED`.

## Why this work is on the critical path

The source review in `docs/verification/15_stage11_product_gap_review.md`
identifies `G11-P01` (secure non-test-only runtime) and
`G11-P05` (repeatable packaging) as software-owned deployment gaps.
The existing signed API → encrypted PostgreSQL → separate Worker →
**synthetic** local model has already passed on the operator's isolated
Simorgh Docker test database. Re-running that proof does not validate
the real vLLM backend and does not solve the remaining runtime
distribution gap. No second vLLM model, GPU reservation or shared
container change is part of this task.

`Dockerfile.stage11-candidate` builds an allowlisted, minimal
**API-only** Python 3.12 runtime image from the repo's pinned
`requirements.txt` and `src/` tree. It neither copies local private
configuration/secrets nor downloads model weights. The image runs as
unprivileged UID/GID 10001 and retains the existing fail-closed
application entrypoint. Its default configuration still disables
LLM, Worker and HTTP security, and binds to loopback.

The Stage11 preflight CI builds the candidate from a documented
Python 3.12 patch-version base tag and checks it with
`docker run --network none --read-only --cap-drop ALL`.
The verification imports the actual FastAPI app and confirms
that the security/Worker/inference flags are disabled.
It does **not** access a database, vLLM, real text, shared GPU,
organizational network, model artifacts or secrets.

**Limitations (deliberate):** This is not a runnable multi-service
deployment stack; no Worker container/process is started, no
PostgreSQL networking is configured, no network port is published,
and no organizational TLS/SSO/KMS/no-egress boundary is certified.
Even if CI successfully builds the candidate, it is **NOT**
an accepted release image. Its base image is pinned to a
specific tag, not an approved immutable digest; digest,
SBOM/CVE/license scan, signed registry provenance,
independent supply-chain attestation and approved private
distribution remain G11-P01/P05 release prerequisites.
The existing database and Worker layers still require a
controlled development-only test database; do not remove
those restrictions merely to make this image deployable.

## Owner critical path — no repeated CPU XGrammar diagnostics

1. **Approve scope, environment and resource budget (Wave 0):**
   authorized owner of shared Simorgh vLLM/staging and a
   bounded stop policy; synthetic model traffic only until
   data rights and release gates are approved. Store private
   approvals in approved internal storage, not GitHub/chat.
2. **Attest actual vLLM runtime (Wave 1):**
   provide owner-verified model/tokenizer/quantization revision,
   private manifest checksums and legal/license status; identify
   actual request-level guided decoding backend and fallback
   via trusted deployment/runtime evidence. Prior Docker launch
   inspection showed documented default `auto`, which
   **cannot verify XGrammar was selected**. The cached
   tokenizer file comparison tool has not produced an operator
   result and cannot prove live model provenance on its own.
3. **Authorize one bounded full-path E2E (Wave 2/4):**
   with explicit GPU permission, run signed synthetic HTTP
   request → encrypted isolated DB → fenced Worker → verified
   internal vLLM → source quote/offset validator → signed
   scoped report. Compare actual strict JSON validity, token
   counts, finish reason, request duration and security
   constraints; stop on timeout/OOM/unexpected data movement.
   Do not silently substitute direct model API smoke.
4. **Quality and release gates (Waves 2–6):**
   independent Persian expert labels for speech/media/research,
   two candidate model evaluation per approved plan,
   enforced network/identity/data policies, capacity/recovery
   against accepted thresholds, and original 56-ID traceability.
   Owner decisions OD-04/12/13/14 remain OPEN unless
   independently resolved.

**Release rules:** No GPU inference, model download,
Production/Stage12 deployment, backing DB migration,
secrets changes, force-push, cache mutation or service
restart may be inferred from the software image build.
No confidential material may be emitted to public CI,
GitHub or chat.

## Safe offline commands (CI or separately approved local machine)

~~~bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_stage11_candidate_image_contract.py
docker build --file Dockerfile.stage11-candidate --tag tes-stage11-api-candidate:local .
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 64 --memory 512m \
  --entrypoint python tes-stage11-api-candidate:local -c \
  'from src.host.app import app; assert app.openapi_url is None; print("IMAGE_IMPORT_FAIL_CLOSED_PASS")'
~~~

The build may fetch approved **public Python development dependencies
and the Python base image** from outside; run it only where
downloads are permitted. It does not access the private inference
runtime. Do not run Docker builds on shared Simorgh without the
owner's CPU/RAM/storage and network permission. CI testing proves
only the correctness of this engineering candidate.
