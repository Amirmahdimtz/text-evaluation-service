# Stage 05 — PostgreSQL Schema, Migration and Transaction Verification

**Started:** 2026-10-27  
**Final Stage05 local Gate:** `DONE / PASS` under D-017, based on real synthetic PostgreSQL CI at code SHA `52f7c57f752037c453a544ea6690d9863b38e6ef` (workflow run `40512243347`, job `122216854430`, success). **NOT** an organizational database, confidential-data encryption or Production approval. Later evidence below supersedes earlier PENDING snapshots. Stage06 NOT_STARTED.

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

## Final locally executed Stage05 acceptance — 2026-10-27

**Source:** GitHub Actions run [40512243347](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40512243347), job `122216854430`, code commit `52f7c57f752037c453a544ea6690d9863b38e6ef`, conclusion **SUCCESS**. Assistant retrieved both step-level results and the actual job log. Runner: GitHub-hosted Ubuntu 24.04, Python 3.12, temporary isolated PostgreSQL 17 service with **synthetic credentials and synthetic records only**. No Simorgh or corporate DB access.

| Acceptance evidence | Executed result |
|---|---|
| Python syntax, ORM metadata, UUID/FK/Unique/Check, UTC and DB URL fail-closed | **13/13 PASS** |
| Real PostgreSQL Alembic `upgrade head` | **PASS** |
| Real PostgreSQL `alembic check` ORM/DDL drift comparison | **PASS:** `No new upgrade operations detected.` |
| Real PostgreSQL concurrency/idempotency, rollback, cross-org FK, Claim SKIP LOCKED, lease/fencing, immutable Rubric, append-only audit, bounded reads/index/query plan | **4/4 PASS** |
| Complete `pytest tests` | **91/91 PASS** (the 13+4 above are **included** in these 91; do not add twice) |
| Stage03 regression suite | **38/38 PASS** |
| Stage02 regression suite | **12/12 PASS** |
| `python -m pip check` | **PASS:** No broken requirements found |
| Stage04 static/safety scan against Stage05 source | **PASS: 20 Python runtime files, pinned versions, redaction/secret source guards** |
| CI environment public Python package OSV audit | **PASS for tested dependency graph**, `No known vulnerabilities found` at execution time; scanner is *not* a Debian OS/image provenance review |

**Negative-case evidence:** PostgreSQL logged expected constraint/trigger errors for attempted duplicate key, invalid attempts, cross-scope FK, published Rubric update and append-only feedback mutation. Those statements were **intentional tests** and all Python tests passed; they are not application failures.

**Concurrency and transaction evidence:** two simultaneous claimers returned at most one leased job; two simultaneous same-org/owner/key submissions returned one new object and one idempotent replay; invalid multi-entity write left no Evaluation row; stale/mismatched fencing token and second completion failed; transaction contexts released their pooled sessions. The Query Plan was read and required scoped indexes exist. This small synthetic workload is not a Production throughput proof.

**Migration safety:** initial baseline revision `20261027_05` successfully installed in an empty isolated PostgreSQL schema, and `upgrade head` was rerun with synthetic records present without dropping records. Deliberately destructive downgrade remains blocked. No company PostgreSQL, shared service, secrets, real text, KMS or live AI data was touched.

**Concurrent repository change resolved:** An independently pushed commit `88321c5` briefly replaced the lazy test-only DbContext and introduced duplicate ORM models with plaintext columns, temporarily failing CI at test collection. Follow-on forward commits reconciled the conflict without force push or database operations; the canonical models are `src/infrastructure/models/text_evaluation.py`, compatibility import `evaluation_models.py` re-exports them, and the DbContext retains lazy test-only URL safeguards. The final code SHA above **passed** the full CI verification.

**D-017/Stage11 scope (NOT PASSED):** qualified company DBA/IAM/KMS owners must still validate the real DB TLS, encryption/backup/retention, identity/tenant isolation, Production-like multi-worker performance, and staging migration release plan. The five explicit pending IDs and approval oracles are in [Stage05 server ledger](05_stage05_deferred_stage11_ledger.md). `OD-07/08/10/11/12/13/15` remain OPEN. The physical candidate schema is tested, **not** an approved confidential-text storage policy; `protected_text_ref` is only an opaque UUID and the current `encrypted_details` columns do not implement encryption themselves. Production storage/use is blocked until approved crypto/key management and downstream services exist. Full OS CVE, source-image provenance and licenses remain separate open Stage04-to-Stage11 prerequisites.

**Gate verdict:** Stage05 `DONE / PASS_LOCAL` under confirmed D-017. Stage06 `NOT_STARTED`; its work requires a **new explicit user request**. Stage11/12 remain NOT_STARTED; no test or security gate marked PASS beyond actual execution.

## 2026-10-27 — Stage05 LOCAL acceptance gates passed on real isolated PostgreSQL (CI)

**Authoritative local-gate verdict:** `DONE` (test database only; no corporate/production approval). This update supersedes earlier `PENDING_CI`, `PENDING_LOCAL_DB` and provisional `IN_PROGRESS` statuses *only for the now-executed local Stage05 gate*. Earlier attempts, failures and pre-run reports are retained as historical snapshots.

**GitHub Actions execution evidence**: [Stage05 isolated PostgreSQL validation, run 40512243347](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40512243347) executed against code commit `52f7c57f752037c453a544ea6690d9863b38e6ef`; `status=completed`, `conclusion=success`. Real PostgreSQL 17 service was provisioned in an ephemeral `ubuntu-24.04` GitHub Actions job, with **synthetic** local-loopback database `tes_stage05_ci`. No Simorgh PostgreSQL or other shared organization DB was contacted. The scanner and OSV queries in this CI targeted public Python package metadata only.

| Executed job step / gate | Verifiable result |
|---|---|
| Install exact Python runtime/dev dependencies | `PASS`, pinned requirements resolved |
| Source compile, metadata/schema/security tests | `13 passed in 0.28s`; security guard reported `PASS: 20 runtime source files` |
| Real Alembic upgrade of empty isolated PostgreSQL | `PASS` |
| Alembic check of DB versus SQLAlchemy metadata | `PASS`; no reported schema drift |
| PostgreSQL integration/uniqueness/org FKs/immutability and bounded concurrency | `4 passed in 0.60s` (the tests cover real database locks, identity scope, idempotency, fencing and rollback checks) |
| Existing Stage03 regressions | `Ran 38 tests ... OK` |
| Existing Stage02 regressions | `Ran 12 tests ... OK` |
| Real dependency consistency | `No broken requirements found.` |
| Complete pytest suite | `91 passed in 2.21s` |
| CI Python OSV dependency audit | `No known vulnerabilities found` in the **audited Python dependency environment** |

The PostgreSQL CI log also contains expected `ERROR` entries generated by **negative constraint tests** (idempotency duplicate-key, immutable published rubric, append-only audit/feedback, invalid attempts, cross-scope FK). Those are deliberate rejected operations: the test job and all its checked steps completed with success. Do not interpret expected negative-case database logs as production incidents.

**Stage05 gate mapping:** Migration Up and no-drift metadata `PASS_CI_REAL_POSTGRES`; FK/Unique/status/tenant scope and published immutability `PASS_CI_REAL_POSTGRES`; CRUD+idempotency+atomic claim/heartbeat/fenced completion and parallel race/rollback checks `PASS_CI_REAL_POSTGRES`; query-plan verification using `EXPLAIN (FORMAT JSON)` `PASS_CI_REAL_POSTGRES`; per-operation AsyncSession and connection lifetime tests `PASS_CI_REAL_POSTGRES`; no shared/Production DB touched `PASS_BY_SCOPE`. The repeat-upgrade-with-existing-synthetic-data check is included in the four real-PostgreSQL integration tests.

**Implementation reality:** `src/infrastructure/models/text_evaluation.py` is the **single** canonical ORM schema and Alembic import root. `evaluation_models.py` is an alias-only compatibility module to prevent two ORM registries/duplicate tables. `PsqlDbContext` is lazy, requires a separately provided development-only loopback `TES_STAGE05_DATABASE_URL` with `tes_stage05_` database prefix, and never opens a DB during Stage04 web app startup. Future organization DB configuration must be designed and authorized in its actual deployment stage; do not circumvent the Stage05 test URL guard.

**Unchanged restrictions:** Stage05 created no real data, no Production/Simorgh DB migration, no irreversible downgrade, no released product endpoint and no model/worker integration. Encryption implementation, retention/delete policy, approved IAM, final Rubric publishing policy, deployed audit sink, enterprise OS/image CVE/provenance/licensing and real company server tests remain **`PENDING_SERVER` / OPEN** according to `D-017` and previously recorded Stage04 `S04-S11` ledger. Runtime scoring, worker and actual API capabilities are owned by later stages. This local DB test does not approve operational data security or production roll-out.

**Stage 05 status:** `DONE` for local schema/migration/repository acceptance, with explicit future corporate dependencies. **Stage 06:** `NOT_STARTED`; start only after a separate explicit user request.
