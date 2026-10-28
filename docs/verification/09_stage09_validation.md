# Stage09 — Durable Worker & Queue Local Acceptance

Date: 2026-10-28. Stage 09 verdict: DONE_LOCAL / accepted synthetic implementation gates, NOT corporate deployment authorization.

## Scope and authoritative baseline

Sources: Service_Architecture_Guide_FA.md (Host → Application → Core → Infrastructure, constructor DI, @inject, Async SQLAlchemy repositories) and Text_Evaluation_Service_Implementation_Plan_FA.md Stage09 §§5.3, 9 and D-017. Reused Stage05 canonical Evaluation, EvaluationJob, CriterionResult and AuditEvent ORM and Alembic schema; no duplicate model, migration or extra abstraction introduced.

## Delivered implementation

- src/core/services/text_evaluation/evaluation_worker_service.py: @inject concrete worker service, explicit WorkerPolicy bounds, queue admission guard, per-run concurrency limit, scoped claim/heartbeat/fencing lifecycle, execution timeout, retry classification/backoff, cancellation, graceful bounded drain, last processing duration and sanitized error status.
- src/infrastructure/repositories/text_evaluation/evaluation_job_repository.py: existing BaseRepository retains transactional SKIP LOCKED claim and fenced heartbeat; adds expired-lease recovery, retry-to-terminal transitions, attempt-token invalidation, per-tenant queue metrics (ready, delayed, processing, expired, terminal, retried, oldest age), safe metadata-only audit. Uses DB clock and per-operation short AsyncSession/transaction.
- src/infrastructure/repositories/text_evaluation/evaluation_repository.py: safe scoped worker metadata (references only, not plaintext); extends fenced atomic completion for provisional partial/needs_human_review results with overall_score NULL. Existing completed+numeric Stage05 method remains backward compatible. Adds optional tenant admission cap to create_with_job_async using PostgreSQL transaction-scoped advisory lock and idempotency check: concurrent independent producers cannot exceed the opted-in cap. The future Stage10 submit path MUST pass the cap explicitly.
- src/host/evaluation_worker.py: correct DI bootstrap, signal-aware shutdown, async DB/LLM cleanup and approved-executor composition function; main refuses to start if disabled or secure executor unavailable. Stage09 deliberately does not invent protected-text decryption/KMS or unauthorized inference. Production data execution is NOT wired.
- src/infrastructure/utils/config_reader.py and both appsettings YAML: optional worker policy with strict config, worker enabled=false by default. No arbitrary effective GPU capacity/SLO/lease/retry approval has been claimed.
- tests/test_stage09_worker.py and tests/test_stage09_postgres.py: in-process failure injection, race, recovery and real PostgreSQL transactions.
- .github/workflows/stage09-worker.yml: pytest, migration+schema drift, Postgres 17, prior Stage05/06 suites, full regression and scoped Python public OSV dependency scan.

## Actual executed CI evidence

[GitHub Actions run 40651492153](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40651492153), code SHA ac2c2153166d5e9cea5004335d0d207d8a1d568b, completed/success, Ubuntu 24.04, Python 3.12, ephemeral isolated PostgreSQL 17 and synthetic-only executor. All counts observed directly in workflow logs.

| Gate | Actual result |
|---|---|
| Stage09 offline Worker/Fault Injection tests | 21 passed in 0.80s |
| Stage09 genuine PostgreSQL recovery, claim, fencing, admission, atomic reviewed result | 5 passed in 0.97s |
| Stage05 PostgreSQL regression suite | 4 passed in 0.59s |
| Stage06 PostgreSQL integration suite | 3 passed in 0.60s |
| Stage06 rubric schema | 20 passed in 0.63s |
| Stage05 schema | 13 passed in 0.29s |
| Entire Python test suite (includes all focused suites) | 229 passed in 3.39s |
| Stage03 standalone unittest | 38 PASS |
| Stage02 standalone unittest | 12 PASS |
| Alembic upgrade and metadata drift on isolated PG17 | PASS |
| Static Stage04 security guard | PASS, 30 source files |
| pip check | No broken requirements found |
| pip-audit public dependency metadata via OSV | No known vulnerabilities found (Python package scope only) |

The 21 and 5 Stage09 tests, 4 Stage05 and 3 Stage06 DB tests are INCLUDED within the full 229; do not add them. Prior CI attempt 40650787323 failed on a synthetic-test-only Decimal-versus-float assertion; subsequently fixed and repeatedly passed. No crash, load or security-test success is inferred from a mere green test without underlying scenarios.

The real PostgreSQL Stage09 tests prove: concurrent SKIP LOCKED only one claim per Job, database-clock expiry, recovery token revocation and old worker fencing, a new attempt completes a single immutable criterion result with score NULL and review status, no checked-out database connection during the synthetic executor, exponential capped retry and terminal poison, tenant aggregate queue metrics, global advisory-lock admission for two concurrent producers and idempotent same-fingerprint replay. No confidential text, genuine KMS, actual GPU or organization DB was contacted.

## Gate disposition and security limitations

Stage09 Stage5/9 local queue/recovery/fencing/duplicate-write/short-transaction/backpressure/Stub/Shutdown tests: PASS_CI_SYNTHETIC (no real organization external services). Operational IAM, protected-text loading/decryption, deployment of the complete executable Worker, real vLLM/GPU, multi-host Load/Soak/SLO, corporate no-egress and credential infrastructure: NOT_RUN / PENDING_SERVER or Stage10 integration. Stage09 entrypoint is INTENTIONALLY fail-closed and its approved-executor function is not yet wired to organization protected storage. Do not advertise it as a deployed complete processor.

The backpressure cap is guaranteed only for submissions passing max_active_jobs to the atomic repository method. The read-only can_accept_async helper is advisory; future Stage10 must use atomic admission under the verified authentication scope. No model-generated provisional score is promoted to official overall_score; review-only completion leaves overall_score NULL.

No company-controlled Postgres, secrets, GPUs, Docker, vLLM or production services were modified. Requirements with approved operational thresholds and error-review ownership remain open. For server/enterprise obligations see 09_stage09_deferred_stage11_ledger.md. Stage10 NOT_STARTED until explicit user request.

## User-local independent tests (safe on Simorgh)

    cd /srv/projects/text-evaluation-service
    git pull --ff-only origin main
    .venv/bin/python -m pip check
    .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage09_worker.py
    .venv/bin/python -m pytest -q -p no:cacheprovider tests --ignore=tests/test_stage05_postgres.py --ignore=tests/test_stage06_rubric_postgres.py --ignore=tests/test_stage09_postgres.py

The command above does not run PostgreSQL integration and has not been executed on Simorgh by the assistant. Real isolated PostgreSQL tests were already actually executed and passed in GitHub Actions run 40651492153, with no need to touch the shared Simorgh server.

Status: DONE_LOCAL only. Stage10: NOT_STARTED.
