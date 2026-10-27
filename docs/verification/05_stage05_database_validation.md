# Stage 05 — PostgreSQL Schema, Migration and Transaction Verification

**Started:** 2026-10-27  
**Status:** `IN_PROGRESS` pending evidence-backed local PostgreSQL acceptance. This file is a living Stage05-only report; it does **not** authorize Stage06 or shared/Production migrations.

## Sources and architecture

- Project Sources: `Service_Architecture_Guide_FA.md` §§4,8,12; `Text_Evaluation_Service_Implementation_Plan_FA.md` v1.1.0, Stage05 §§5.1/5.3,7.3, and §§0.4–0.5.
- Previous proposals: `docs/architecture/02_detailed_design.md` transaction contract, `docs/architecture/03_api_and_contracts.md` scope/idempotency, `docs/architecture/05_architecture_decisions.md` ADR-02 and ADR-03.
- Current real repository had no SQLAlchemy context, persistence models, repositories or Alembic, and only a minimal FastAPI/DI foundation. Implemented an isolated Stage05 persistence layer instead of inventing a Production connection, SQL inside Controller or a new interface hierarchy.
- Layering: `Host → Application → Core → Infrastructure`; `@inject` on concrete repositories/context, no new HTTP Controller/Core use case (Stages06–10 own them). Shared async engine/factory initialized lazily per process; **a distinct AsyncSession per repository operation**. Short transactions with automatic rollback on failure, **never** hold DB transaction during model inference.

## Candidate ERD and relational constraints

All schema details below are **versioned candidate implementation**, not organization-approved persistence/retention/identity decisions (`OD-07/08/10/11/15` remain OPEN).

```text
rubric_versions (id, organization_id, evaluation_type)
       | 1
       | n  FK (rubric_version_id, organization_id, evaluation_type)
evaluations (id, organization_id) ─── 1:1 ─── evaluation_jobs
       |
       +── 1:n criterion_results
       +── 1:n evaluation_feedback
audit_events (org/actor/action/resource/timestamp only; no raw business text)
```

- `rubric_versions`: `UNIQUE(organization_id, evaluation_type, code, version)`; `draft / published / retired`, immutable published snapshot/checksum guarded by a PostgreSQL trigger (only status may transition `published → retired`). No fake published rubric is created outside synthetic DB tests; Stage06 implements review/publish.
- `evaluations`: Composite FK to a rubric with the *same organization and evaluation_type*. `UNIQUE(organization_id, owner_id, idempotency_key)` plus request-fingerprint collision policy; scoped index on org, owner and created date. **Protected original text is represented only by an opaque UUID locator**; no raw text/PDF/prompt or actual encrypted document storage has been implemented.
- `evaluation_jobs`: One job per evaluation, composite FK preserving organization scope. Validated status, attempts, fencing generation, worker, lease, retry date; partial index for pending/retryable claim.
- `criterion_results`: Composite org FK, `UNIQUE(evaluation_id, criterion_code)`, assessed score 0..5, not_assessed NULL; additional sensitive detail is represented in `BYTEA`, **not proven encrypted by the database alone**.
- `evaluation_feedback`: Scoped FK, append-only with `UNIQUE(evaluation_id, revision)`, reviewer identity and encrypted-details placeholder; no arbitrary review-text column; a qualified encryption/key/authorization policy is still mandatory.
- `audit_events`: Minimal actor/org/action/resource/correlation/time fields, **no text**, and DB trigger preventing UPDATE/DELETE. The DB-table vs internal sink choice remains a candidate under `OD-08`; its retention/tamper-resistant controls need approval.
- All timestamps use `timestamptz` and non-frozen `now()` defaults, including UTC-aware lease and publication dates; `onupdate` uses callable SQL expressions. Hard/soft deletion and expiry policy **NOT SELECTED** (no automatic TTL or purge). Referential integrity defaults to `ON DELETE RESTRICT`.

## Persistence and concurrency contract

- `PsqlDbContext` is `@inject` and singleton, with shared AsyncEngine/async_sessionmaker and no eager DB open during API startup. `TES_STAGE05_DATABASE_URL` must be `postgresql+asyncpg`, loopback-only and name-prefixed `tes_stage05_`; `TES_ENVIRONMENT` must be development. Other DB URLs are rejected with sanitized errors.
- `BaseRepository` implements bounded, org-scoped CRUD with owner scope compulsory for owner-bearing models. No unbounded repository reads or global Session.
- `EvaluationRepository.create_with_job_async`: checks same org/owner, requires a Published and type-matching rubric; atomic Evaluation+Job+minimal audit; keyed idempotent replay only when same fingerprint within org+owner, otherwise deterministic conflict. Database uniqueness handles races.
- `EvaluationJobRepository.claim_next_async`: a short `FOR UPDATE SKIP LOCKED` transaction, DB clock and explicitly provided policy `max_attempts`/lease duration, monotonically increasing fence, attempt UUID and worker ID. Evaluation and Job processing states update together. It does not wait for an AI call.
- `EvaluationJobRepository.heartbeat_async`: conditional update on organization, worker, token, generation and still-valid lease.
- `EvaluationRepository.finalize_with_results_async`: short fenced row-lock transaction; stale/expired/cross-org worker cannot commit; result/score/provenance, job terminal status and safe audit added atomically.
- `EvaluationFeedbackRepository.append_authorized_async`: requires an assigned-evaluation set, exact org scope and nonempty encrypted-detail **synthetic fixture**; feedback and audit in the same transaction. Stage10 must bind all authorization inputs to independently verified identity claims.
- **Stage09 still owns** bounded retry/backoff, expired-lease recovery, failure classification, worker lifecycle and actual inference orchestration. Do not claim those operations exist already. No approved numeric retry/lease/retention policy is invented.

## Versioned Alembic and safe local execution

- `src/infrastructure/alembic/versions/20261027_05_initial_schema.py` contains explicit PostgreSQL DDL, named unique/FK/check constraints, partial indexes and published/append-only triggers. Revision `20261027_05` has no previous database schema in this repository.
- `src/infrastructure/alembic/env.py` explicitly registers models in shared `Base.metadata`; offline SQL generation is disabled to prevent unsafe/incorrect unverified deployments.
- `scripts/verification/run_stage05_migrations.py` supports only `current` and `upgrade`. **Downgrade always raises** until a separately authorized non-destructive forward-fix/backup strategy is reviewed.
- The URL preflight forbids all non-local and non-test-named DB targets. **Never run this script against the existing shared Simorgh PostgreSQL service or on Production.**

For a user-owned isolated local database, after installing exact pinned dependencies:

```bash
git pull --ff-only origin main
python -m pip install -r requirements-dev.txt
# In a local temporary shell, set TES_ENVIRONMENT=development and
# TES_STAGE05_DATABASE_URL=postgresql+asyncpg://<isolated-local-user>:<local-secret>@127.0.0.1:5432/tes_stage05_<database>
# Do not paste actual passwords in chat, terminals' shell history, scripts or logs.
python -m scripts.verification.run_stage05_migrations upgrade
python -m scripts.verification.run_stage05_migrations current
python -m pytest -q tests/test_stage05_schema.py tests/test_stage05_postgres.py
python -m pytest -q tests
```

**IMPORTANT:** The example URL above contains only placeholders. Provision an isolated development PostgreSQL database beforehand with appropriate ownership and permissions; do not assume any shared service or credentials exist. If connection/driver/DB are absent, record `NOT_RUN/PENDING_LOCAL_DB`. Tests synthesize only fake Rubric IDs, worker identities and ciphertext placeholders — never real confidential text.

## Testing and acceptance evidence

| Acceptance item | Required actual proof | Current status |
|---|---|---|
| Python syntax, metadata tables, naming/type/constraints, UTC timestamps, URL fail-closed and migration policy | Execute `tests/test_stage05_schema.py` in reviewed exact package graph | `PENDING_CI` |
| Migration upgrade from empty DB and repeat with existing synthetic data | Ephemeral real PostgreSQL instance, verify `alembic_version` | `PENDING_LOCAL_DB` |
| Scoped CRUD, FKs, unique and restrictive constraints | Integration queries and positive/negative synthetic fixtures | `PENDING_LOCAL_DB` |
| Idempotency/racing Job Claim/Heartbeat/Fencing/atomic finalize | Concurrent isolated PostgreSQL tests and stale token rejection | `PENDING_LOCAL_DB` |
| Regression 74 previous tests + Stage02/03 | Run exact updated Python dependency graph after Stage05 changes | `PENDING_CI` |
| Query plan for read/claim and session lifetime | `EXPLAIN` on isolated PostgreSQL, leak/rollback checks | `PENDING_LOCAL_DB` |
| Real private data encryption, external IAM, shared DB/Production migration, restored backups | Approved organizations' integration environment only | `PENDING_SERVER` under D-017/OD-07/08 and Stage11/12 |

A GitHub Actions workflow `.github/workflows/stage05-postgres.yml` provisions ephemeral Postgres on a hosted isolated CI runner and uses **only synthetic data**. This is not a substitute for approved real organizational-server tests. The first workflow run failed during YAML parsing (no jobs started); its pip-install step was fixed and a new run was triggered. Record its **actual conclusion and log** before claiming local gate PASS.

## Required Stage05 exit criteria

1. Migration `upgrade` and metadata/reference constraints truly pass on isolated PostgreSQL.
2. Scoped CRUD and negative authorization/uniqueness checks pass.
3. Two-client concurrency, fence and stale completion checks pass.
4. No real/private DB was accessed; no session leaks or unreviewed destructive operations.
5. Real test counts, CI and/or user-local results and exact commit SHAs recorded.
6. Remaining company-only controls explicitly `PENDING_SERVER` for Stage11, not fabricated PASS.

**Stage05 shall remain `IN_PROGRESS` or `BLOCKED` until every locally executable Gate above is actually evidenced. Do not automatically start Stage06.**
