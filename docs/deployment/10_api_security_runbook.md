# Stage10 API & Authorization — Safe Stage11 Integration Runbook

**Status:** DOCUMENTED_ONLY / NOT_EXECUTED on any organization network or production system, 2026-10-28. Stage10 local synthetic acceptance runs on ephemeral CI PostgreSQL only.

## Endpoint contract (FastAPI auto-discovery)

The four API routes under `/api/v1/text_evaluation` support authenticated encrypted submission (202 + idempotency), private report/status, published-technical-candidate Rubric listing and authorized encrypted reviewer `COMMENT`. No `APPROVE`, export, admin, user impersonation, cancellation or delete route is approved or implemented. OpenAPI is generated for offline test inspection only; public documentation and OpenAPI URLs are disabled in FastAPI `create_app()`.

The API returns only approved sanitized `error_code` and opaque correlation ID. Typical response codes: 401 authentication required; 403 explicit scope denied; 404 hidden wrong tenant/owner; 409 idempotency conflict; 413 oversized body; 415 wrong content type; 422 strict DTO/JSON rejection; 429 rate limit or queue quota; 503 missing/misconfigured security services. `Cache-Control: no-store` prevents HTTP response caching by default.

## Authorized staging prerequisites

1. **Do not change shared Simorgh PostgreSQL or production settings.** Obtain explicit IAM, Security, Data Steward/DBA and SRE approvals and an organization-approved isolated staging deployment. Stage05 guarded development database URL and current localhost-only ingress are *intentional*; promote only through separately reviewed deployment configuration.
2. Configure a known issuer/audience and trust anchor for RS256 signatures through approved environment-backed secret reference. Test JWKS/key rotation and revocation, disabled user, reviewer assignment revocation and audience confusion. The service currently validates explicitly configured RSA public keys, **not a live OIDC discovery/JWKS refresh flow**, and does not implement token revocation. Do not treat authentication to a synthetic private key as corporate IdP approval.
3. Use internal KMS approved master/envelope keys, restricted key version access, rotation and secure retirement; prove ciphertext GCM integrity and AAD tenant/owner/resource/purpose binding. The local code accepts explicit `env://` secret refs; production KMS/HSM provider and rotation workflows are intentionally **not implemented**. No real keys in files, GitHub secrets for public CI, logs or documentation.
4. Define security-approved request-body limits, per-tenant quotas, subject-scoped rate limits, signed resource assignments and isolation/retention. The local API counters use PostgreSQL atomic minute windows; time-window retention and owned alert thresholds need operational design. The queue cap is atomic only when the Stage10 caller passes the configured limit.
5. Deploy only after a trusted encrypted protected-text source resolver is wired into the future production Worker. Stage10 E2E uses a synthetic executor; Stage09 ordinary Worker Host intentionally stays disabled. Never claim successful real AI inference from this suite.
6. Add enterprise gateway TLS/mTLS, network-level full inference endpoint filtering, No-Egress, request-size and HTTP smuggling checks, proxy/WAF headers and standard observability. Config currently binds Host to `127.0.0.1` and enables neither real TLS nor corporate ingress.
7. Prove forbidden paths: missing/expired/forged signed tokens, org/owner assignment IDOR, replayed same/different idempotency keys, unusual Unicode/duplicate JSON, large streamed/chunked bodies, unauthorized reviewer `COMMENT`, concurrent quota transactions and malformed encrypted details. Verify error and operational logs never include raw text, keys, tokens or model responses.
8. Run actual penetration/load/soak, recovery, audit and D-017 Stage11 tests only with named authorization. Record each S10-S11-01..07 with actual evidence; incomplete remains PENDING_SERVER. D-015 formal organizational business signoff belongs to Stage12.

## Current local evidence and commands

[Stage10 GitHub Actions final successful run 40656653349](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40656653349), source SHA `24ced033c4deac0f117779ed12f4c1875349a98d`: 9/9 focused Auth/Crypto tests, 2/2 real isolated PostgreSQL signed HTTP → actual Worker using synthetic executor → authorized report/feedback E2E, 240/240 full pytest tests, 38 Stage03 + 12 Stage02 unittest, Alembic drift, `pip check`, and clean Python OSV after dependency upgrades. No warnings. No live model or enterprise services were tested.

For user-local safe tests:

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
# Use only a security-approved package mirror/wheelhouse for the following installation.
.venv/bin/python -m pip install --disable-pip-version-check --only-binary=:all: -r requirements-dev.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage10_auth.py
.venv/bin/python -m pytest -q -p no:cacheprovider tests \
  --ignore=tests/test_stage05_postgres.py \
  --ignore=tests/test_stage06_rubric_postgres.py \
  --ignore=tests/test_stage09_postgres.py \
  --ignore=tests/test_stage10_postgres.py
```

No `alembic upgrade` command should be run against Simorgh’s shared DB. The new `20261028_10` migration was tested on ephemeral isolated GitHub Actions PostgreSQL 17, not deployed to the organization.
