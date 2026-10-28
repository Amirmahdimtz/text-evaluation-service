# Stage10 — API & Authorization: Local Acceptance Record

**Date:** 2026-10-28  
**Stage:** 10  
**Disposition:** `DONE_LOCAL` for the isolated synthetic API/authorization/database gates only; **NOT enterprise Production readiness**.  
**Sources:** `Service_Architecture_Guide_FA.md` and `Text_Evaluation_Service_Implementation_Plan_FA.md` Stage10, plus D-015/D-017 and the Stage05–09 implementation and deferred test ledgers.

## Deliverables and architecture

The four Stage10 routes are auto-discovered under `/api/v1/text_evaluation` through existing `WebService`, preserving Host → Application (thin controller/DTO) → Core (EvaluationApiService) → Infrastructure (SQLAlchemy repositories/security). There are no invented interfaces, new inference providers, administrative endpoints or operational SSO connectors.

| Endpoint | Intended guarded behavior |
|---|---|
| `POST /api/v1/text_evaluation/evaluations` | Strict DTO, idempotency key, exact org/type/version-pinned published **candidate** rubric, authenticated original encrypted in same atomic DB transaction as Evaluation/Job/Audit, queue admission cap, response 202 |
| `GET /api/v1/text_evaluation/evaluations/{evaluation_id}` | Tenant + owner/explicitly assigned reviewer scope, status, encrypted criterion details decrypted only after authorization, no plaintext source and **never an officially approved score** |
| `GET /api/v1/text_evaluation/rubrics` | Authenticated, tenant-scoped published technical candidates with `approval_status=PROPOSED`, no drafts or invented commercial release |
| `POST /api/v1/text_evaluation/evaluations/{evaluation_id}/feedback` | Signed resource assignment, append-only transactionally encrypted `COMMENT`, reviewer-scoped monotonic revision and metadata audit; no `APPROVE` or `REJECT` workflow before OD-06 approval |

### Identity, encryption and HTTP controls

- `src/infrastructure/security/signed_identity.py`: public-key RS256 signature with fixed accepted algorithm; issuer, audience, required temporal claims, user, org, token identifier, allowlisted permission claims and canonical UUID assignments. Never trust `X-User`/`X-Org` headers; no unsigned/mock bypass in application code.
- `src/infrastructure/security/encrypted_content.py`: AES-256-GCM, unique 96-bit nonce and associated authenticated data including organization, owner, resource UUID and purpose; master secret loaded via `env://` `SecretResolver`. An independently derived HKDF/HMAC-SHA256 key is used for idempotency fingerprinting so fingerprint storage is not a direct plaintext dictionary-search oracle. Key rotation/enterprise KMS are not yet wired or approved.
- `src/host/request_body_guard.py`: pure ASGI bounded streaming reader before FastAPI/DTO parsing, strict JSON media type and no duplicate keys/nonfinite constants; `413` for oversized, `415` non-JSON, `422` invalid/ambiguous payload. Central request correlation and sanitized error codes with no-store headers.
- Existing Stage05 `PsqlDbContext` prevents DB contact except development loopback to a `tes_stage05_*` database. Both YAML environments include `http_security.enabled=false` and worker/LLM stay disabled. The Core API refuses use outside `development` absent an approved enterprise deployment adaptation. Environment variables and public-key/AEAD keys are **synthetic CI-only**, never committed.
- Atomic PostgreSQL cross-process user+tenant minute-window request rate counters; atomic tenant queue capacity via existing transaction-scoped advisory lock. Client-side header changes cannot grant a role or widen organization scope.
- `protected_texts` append-only encrypted records and `http_rate_limits` metadata introduced via additive Alembic revision `20261028_10` from Stage05, destructive downgrade prohibited. No shared/production database has been migrated.

### Source / test inventory

- `src/application/text_evaluation/text_evaluation_controller.py` and `src/application/text_evaluation/dtos/text_evaluation_dto.py` (auto discovered API, strict request/response contracts and synthetic-only OpenAPI examples).
- `src/core/services/text_evaluation/evaluation_api_service.py` (authorization, HMAC-bound idempotency, encrypted business workflow).
- `src/infrastructure/security/signed_identity.py`, `src/infrastructure/security/encrypted_content.py`, `src/host/request_body_guard.py`; `src/host/app.py` error projection and middleware wiring.
- `src/infrastructure/models/text_evaluation.py`, `src/infrastructure/alembic/versions/20261028_10_protected_text.py`, existing Evaluation/Feedback/Rubric repositories, `http_rate_limit_repository.py`.
- `requirements.txt`: runtime `PyJWT==2.15.1`, `cryptography==50.0.2`. Both were upgraded after an actual CI OSV scan reported 45 known findings against the initially introduced pins (`PyJWT 2.10.1`, `cryptography 46.0.3`). Later CI: **no known vulnerabilities in the scoped Python packages**.
- `tests/test_stage10_auth.py`, `tests/test_stage10_postgres.py`, `.github/workflows/stage10-api.yml`; older Stage05 migration tests made compatible with the additive latest Alembic revision.

## Executed acceptance tests

The authoritative **final successful**, source-tested Stage10 run is [GitHub Actions 40656653349](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40656653349), on SHA `24ced033c4deac0f117779ed12f4c1875349a98d`, **completed/success**, Python 3.12 and ephemeral PostgreSQL 17. An earlier successful [Stage10 CI 40656268346](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40656268346), on SHA `a2da5f03e093003782412b23f9376ea2aca5fd43`, performed on Ubuntu 24.04, Python 3.12, isolated PostgreSQL 17 and synthetic, locally generated keys/token/requests:

| Real check | Observed result |
|---|---|
| Strict signed-token Auth/crypto/OpenAPI/DTO tests | **9 passed in 0.72s, no warnings** (short synthetic HS256 forgery fixture corrected) |
| End-to-end signed HTTP → encrypted DB/Job → actual Stage09 Worker with synthetic executor → private report → assigned reviewer encrypted feedback | **2 passed in 0.91s** on real isolated PostgreSQL |
| Stage09 synthetic Worker regression | 21 passed |
| Stage05 Schema / Stage06 candidate Rubric validation | 13 / 20 passed |
| Stage05 / Stage06 / Stage09 isolated PG regression | 4 / 3 / 5 passed |
| Full Python suite (includes the previous 9 + 2 + all earlier tests) | **240 passed in 3.28s, no warnings** |
| Stage03 and Stage02 standalone unittest | 38 and 12 PASS |
| Isolated Alembic upgrade and SQLAlchemy metadata drift | PASS |
| Stage04 static security guard | PASS (38 runtime sources) |
| `pip check` | `No broken requirements found.` |
| Python public OSV scan after dependency upgrades | `No known vulnerabilities found` |

**No test count should be double-counted.** E2E intentionally uses a synthetic authorized executor (not a live vLLM), and synthetic original/review text only. JWT verification exercises the in-test private key; an approved corporate IdP and revocation facility are NOT connected. Internal encryption uses env-ref key for synthetic acceptance; enterprise KMS/envelope encryption and rotation are NOT proved.

Previously failed CI cycles identified: hardcoded Stage05 Alembic head assertion, Starlette IncludedRouter route reflection mismatch, malformed test fixture, incorrect BaseRepository owner-scope use for tenant read, missing criterion AEAD purpose, signed reviewer UUID format, vulnerable dependency pins, and FastAPI body-stream replay. Each was corrected and retested; no failed run is misrepresented as successful.

## Acceptance boundary

**Local Stage10 gates:** Core/Controller DTO, exact responses, auth deny-by-default, IDOR/tenant/owner/assignment controls, synthetic encryption, key-bound fingerprints, idempotency conflict/replay, rate and queue bounds, offline JSON rejection, encrypted feedback, real isolated DB transaction and Worker stub **PASS**. The application has no configured enterprise SSO/IdP, revoked-token store, approved KMS, actual model, protected-text executor wired to real data, real ingress TLS/mTLS or production API exposure. Their Stage11 checks **PENDING_SERVER**; Rubric commercial approval (OD-03/04/06), formal scoring and Stage12 final organizational signoff remain OPEN.

No real source text, production key, Simorgh shared PostgreSQL, GPU or vLLM was touched. Stage11 `NOT_STARTED` until explicit user request. See [Stage10 D-017 deferred ledger](10_stage10_deferred_stage11_ledger.md) and [security runbook](../deployment/10_api_security_runbook.md).

## Independent Simorgh user-local tests (no DB, no real model)

On 2026-10-28, the Simorgh operator reported a successful independent Stage10 offline run on the checkout at `/srv/projects/text-evaluation-service` (branch `main`, previously fast-forwarded to `dbcf3f2`). Following a previous `ModuleNotFoundError: jwt` caused by missing dependencies, `PyJWT==2.15.1` and `cryptography==50.0.2` were installed from a third-party package mirror, and `pip check` reported `No broken requirements found`. The operator's actual terminal logs show:

- `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage10_auth.py` — **9 passed in 0.87s**.
- `.venv/bin/python -m pytest -q -p no:cacheprovider tests --ignore=tests/test_stage05_postgres.py --ignore=tests/test_stage06_rubric_postgres.py --ignore=tests/test_stage09_postgres.py --ignore=tests/test_stage10_postgres.py` — **226 passed in 2.37s** (includes the nine focused tests; do not sum these counts).
- **14 PostgreSQL integration tests excluded** on this host: four Stage05, three Stage06, five Stage09, two Stage10. They remain **NOT_RUN_ON_SIMORGH**, although the CI full suite including them previously passed on an isolated database. No company DB, live model, real identities, or production cryptographic keys were used by these reported tests.
- The mirror download succeeded, but package supply-chain provenance and organizational approval of that external mirror have **not** been independently verified by the assistant. Do not infer production deployment approval from the development environment.

The commands below are reference commands for re-running the checks after dependencies are available; any subsequent installation should use an organization-approved package source:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
.venv/bin/python -m pip install --disable-pip-version-check --only-binary=:all: -r requirements-dev.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage10_auth.py
.venv/bin/python -m pytest -q -p no:cacheprovider tests \
  --ignore=tests/test_stage05_postgres.py \
  --ignore=tests/test_stage06_rubric_postgres.py \
  --ignore=tests/test_stage09_postgres.py \
  --ignore=tests/test_stage10_postgres.py
```

**Safety:** Use only approved package index/provenance; the installation contacts a package source and must be locally approved. Test modules above do not connect to the protected company database or GPU, do not decrypt real text and do not start a production API.

## Final authenticated Stage10 source test attestation

- **Source-tested commit:** `24ced033c4deac0f117779ed12f4c1875349a98d`. GitHub Actions [40656653349](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40656653349): `completed / success`.
- **Actual logs:** Stage05 schema `13 passed in 0.22s`; Stage10 Auth/Crypto/DTO `9 passed in 0.72s`; Stage09 service `21 passed in 0.64s`; Stage06 candidate schema `20 passed in 0.54s`; Stage06 DB `3 passed in 0.47s`; Stage09 DB `5 passed in 0.75s`; Stage10 HTTP+PG E2E `2 passed in 0.91s`; Stage05 DB `4 passed in 0.46s`; **full suite `240 passed in 3.28s`** with no warnings; Stage03 38 unittest and Stage02 12 unittest PASS; Migration Upgrade/Drift PASS; Stage04 safety guard 38 files PASS; `pip check` PASS; **Python OSV `No known vulnerabilities found`** in checked metadata.
- The earlier warning was solely a short **synthetic test-only** HS256 forgery key used to test that RS256-only verifier rejects a disallowed algorithm. It was corrected in the final source-tested commit; the final GitHub Actions results have zero warnings. No production HMAC signing is accepted by the verifier.
- Every HTTP/PG E2E invocation used self-generated synthetic RSA keys/AEAD secret and text, real isolated PostgreSQL, and the actual Stage09 Worker with injected **synthetic** executor. This does **not** demonstrate a real approved LLM, protected KMS, SSO, inference network or production authorization.
- Stage10 `DONE_LOCAL` is restricted to the listed technical local gates. Stage11 `NOT_STARTED` and its seven enterprise gates remain `PENDING_SERVER`, and Stage12 commercial approval is not granted.
