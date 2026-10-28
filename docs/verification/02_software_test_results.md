# Stage 11 — Software Verification Results

**Status:** `BLOCKED` / real on-premise tests `NOT_RUN`. Date: 2026-10-28. Baseline `9db6025a6a2639928c6536e23c028684caea22f5`.

## Previously executed evidence (not new Stage 11 tests)

| Environment and provenance | Reported observed result | What it proves / does not prove |
|---|---|---|
| GitHub Actions [Stage10 run 40656653349](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40656653349) on source `24ced033c4deac0f117779ed12f4c1875349a98d` | 240 Python tests passed, isolated PostgreSQL 17, migrations/drift, local synthetic API/Worker model stub, 38 Stage03 + 12 Stage02 unittest | Local code and isolated synthetic integration, **not** real vLLM/SSO/KMS/no-egress or organizational DB |
| Operator-reported Simorgh terminal evidence, checkout `dbcf3f2` | 9 focused Auth tests passed (0.87 s); 226 offline pytest tests passed (2.37 s); pinned PyJWT/cryptography installed, pip check clean | Local non-PostgreSQL regressions; nine are included in 226. **14 PostgreSQL tests excluded on Simorgh** |
| Stage 11 enterprise software, security, model, dataset and recovery | `NOT_RUN` | No corporate acceptance claims |

The operator-reported Simorgh tests and CI were already recorded in [Stage10 validation](10_stage10_api_validation.md). No actual Stage 11 test was executed by the assistant.

## Required Stage 11 E2E and software checks (all `PENDING_SERVER`)

1. Approved corporate IdP/JWKS, signed reviewer assignment and revocation; 401/403/404 and tenant/owner IDOR including feedback and rubric operations.
2. Approved staging DB identity/TLS/least privilege, tenancy and encrypted protected-source resolver, KMS/envelope rotation and backup restrictions.
3. Full authenticated HTTP submission → persisted encrypted source+job → worker decrypts under scoped service identity → **real on-premise pinned model** → independently validated criterion evidence/score → scoped report/feedback/audit. No unapproved official score.
4. Lease fencing/crash recovery, idempotency across replicas, queue admission/backpressure and complete/fail atomicity with test-only isolated DB.
5. Schema/Alembic changes only in authorized staging with non-destructive approved change window and backup; no migrations on shared/production DB.
6. Permission failures, retry exhaustion, partial model output, malformed/oversize requests, cancellation, service outages; ensure error/log/trace sanitization.
7. Re-run all local unit/contract suites after any authorized integration code change, recording source SHA and exact commands.

**Important product blocker:** `src/host/evaluation_worker.py` deliberately exits with `WORKER_SECURE_EXECUTOR_NOT_CONFIGURED`; `src/infrastructure/context/sql_db/psql_dbcontext.py` only accepts local `tes_stage05_*` development DBs; `EvaluationApiService` refuses non-development use. These are safety controls, **not** evidence of successful enterprise integration. Do not bypass them by changing runtime flags or shared database settings.

## Execution evidence

- Stage 11 executed Run IDs: **none**.
- Stage 11 software PASS/FAIL measured: **none**.
- Blocking approvals and dependencies: [release blockers](06_release_blockers.md); detailed test IDs: [strategy](01_test_strategy_and_traceability.md).

## Independent Simorgh read-only Stage11 preflight — 2026-10-28

The operator fast-forwarded the local checkout to `e29537b`, ran the new standalone Python preflight safety suite (**13 passed in 0.04s**) and successfully executed the read-only host/GPU inventory command. This is **user-reported host-local test and observation evidence**, **not** completion of an enterprise acceptance test. No live vLLM, corporate DB, IAM, KMS, external egress validation, inference, load, or Recovery test occurred. The source `S11-AI-01` hardware-inventory prerequisite is partially informed, but the pinned runtime/capacity oracle remains unmet and `PENDING_SERVER`. All 56 actual Stage11 gate tests remain `PENDING_SERVER`. [Observed hardware summary](07_stage11_readonly_preflight.md).

## Simorgh Stage11 container metadata observation — 2026-10-28

The operator pulled commit `095f318`, executed the container-metadata tool's **30 offline tests (30 passed in 0.06 s)**, and ran the opt-in bounded host-local metadata command. Docker container state and installed vLLM package version returned `UNVERIFIED / NOT_OBSERVED`; root cause unknown due to intentional diagnostic suppression. The local `GET /v1/models` metadata endpoint advertised **one** model ID, redacted by the tool as a non-exact match for either known public candidate name. No actual inference, model artifact/revision validation, credential inspection or network isolation proof occurred. The read-only Docker state diagnostic is in [the runbook](08_stage11_container_metadata.md). The 30 passed tests are **not** additional Stage11 acceptance gates; all 56 mandatory enterprise test IDs remain `PENDING_SERVER`.


## Simorgh verified running-container vLLM package observation — 2026-10-28

The operator pulled main commit `86f7d87` and ran the existing bounded metadata script on the named existing Docker container: `container_running=true`, installed `vllm` **Python distribution version `0.10.2`**, proof label `PACKAGE_METADATA_INSIDE_RUNNING_CONTAINER`. The optional loopback request was deliberately skipped in this invocation; earlier metadata indicated one advertised model but not its identity or container binding. No new offline tests were reported for this specific run. This proves **only installed package metadata and the running Boolean**, not live serving process version parity, model weights, Structured Output, model accuracy, security posture or enterprise readiness. `S07-S11-01` and the other **55** enterprise test IDs remain `PENDING_SERVER`; no benchmark, inference or load test was performed. See [bounded runbook](08_stage11_container_metadata.md).
