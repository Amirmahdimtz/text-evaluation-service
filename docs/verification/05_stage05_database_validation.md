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

## 2026-10-27 — Simorgh shell `python` command unavailable; operator-local Stage05 schema test NOT_RUN

The operator fast-forwarded a Simorgh checkout from `9cc28c1` to `556625d` on `main` successfully. Then both `python -m pip install -r requirements-dev.txt` and `python -m pytest -q tests/test_stage05_schema.py` failed immediately with `Command 'python' not found`; **no dependencies were installed by either command and no Stage05 test ran on this host**. This is a shell command/host interpreter availability issue, **not a pytest failure or a regression in the PostgreSQL implementation**. The separate [successful isolated PostgreSQL CI run 40512243347](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40512243347) remains valid. Do not treat the failed host attempt as a completed local test.

### Ubuntu/Linux preflight (read-only, safe on shared Simorgh)

```bash
cd /srv/projects/text-evaluation-service
command -v python3
python3 --version
python3 -m venv --help >/dev/null && echo VENV_AVAILABLE
```

If `python3` or working `venv` is missing, stop rather than installing system packages or altering the shared Ubuntu Python interpreter without the infrastructure owner's approval. Python package installation on Simorgh likewise requires authorization for local disk/network use; no external or private data should be transmitted. No need to repeat checks there solely to satisfy the Stage05 CI gate.

### Optional independent Linux developer-workstation verification (approved user-owned environment only)

From a private development machine with `python3` + `venv` installed, and approved public-only package download access:

```bash
git pull --ff-only origin main
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --only-binary=:all: -r requirements-dev.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage05_schema.py
```

`.venv/` is Git-ignored; the above never invokes `sudo pip`, changes global Python packages or connects to PostgreSQL. For **real PostgreSQL integration**, use only the separately provisioned and explicitly permitted local test URL `TES_STAGE05_DATABASE_URL` whose database name starts with `tes_stage05_` and execute the documented migration and integration tests. Never point Stage05 migration commands at the shared Simorgh database. If no isolated DB is available, leave user-host DB integration `NOT_RUN`; existing completed synthetic PostgreSQL CI is independent evidence.

**Current status:** Stage05 local acceptance `DONE` based on successful isolated CI, not based on the failed Simorgh Python command. Stage06 remains `NOT_STARTED`.

## 2026-10-27 — Simorgh Python3/venv PASS, public package CDN DNS unavailable

**Latest operator terminal evidence:** `command -v python3` returned `/usr/bin/python3`, version `Python 3.12.3`; `python3 -m venv --help` returned `VENV_AVAILABLE`. The operator then successfully created the Git-ignored `.venv` using `python3 -m venv .venv`. Inside it, `.venv/bin/python -m pip install --disable-pip-version-check --only-binary=:all: -r requirements-dev.txt` **failed** at the first dependency (`fastapi==0.148.0`) because `files.pythonhosted.org` DNS resolution returned `[Errno -3] Temporary failure in name resolution` after retries.

- The subsequent `.venv/bin/python -m pip check` printed `No broken requirements found`, but this only checks **whatever is already installed** and does **not** prove the requirements were installed after the failed command. No reliable complete dependency installation was shown.
- `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage05_schema.py` exited immediately with `No module named pytest`. **Simorgh independent Stage05 schema tests: NOT_RUN (BLOCKED_PUBLIC_PACKAGE_CDN_DNS)**, not test FAIL/PASS. No host PostgreSQL migration, network or service change occurred in the reported commands.
- The separately completed [CI 40512243347](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40512243347) remains real: Python 3.12, PostgreSQL 17 isolated service, 13 schema checks, 4 real database integration tests, full 91/91 pytest, upgrade+drift, Stage02/03 and public Python OSV had PASS. Stage05 local acceptance remains **DONE on CI evidence**, unaffected by this secondary failed host package-install attempt.
- **Next path, no unreviewed host changes:** use the already successful CI as the official Stage05 local gate. For optional independent execution, obtain an approved, integrity-checked wheelhouse/private mirror or execute on an authorized local developer workstation with functioning public package CDN DNS. A previously reachable public PyPI mirror **inside a Stage04 Docker build** does not prove host-side DNS connectivity or organizational approval; never automatically replace it in pip configuration on a shared host. Do not modify `/etc/resolv.conf`, Docker network/DNS, global pip, shared services, or real Postgres to make a redundant local check pass.
- **Reproducibility if an approved wheelhouse with ALL exact dependencies exists** (the Stage04 26-wheel evidence directory does not automatically include new Stage05 packages such as SQLAlchemy/Alembic/asyncpg): `.venv/bin/python -m pip install --no-index --find-links /path/to/approved-wheelhouse --only-binary=:all: -r requirements-dev.txt`; run `.venv/bin/python -m pip check`, then `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage05_schema.py` **only after successful installation**. The path is illustrative, not a claim that such a wheelhouse exists.

**Status retained:** Stage05 DONE (validated isolated CI); separate Simorgh pytest NOT_RUN; organizational execution PENDING_SERVER under D-017; Stage06 NOT_STARTED.

## 2026-10-27 — Simorgh Python 3.12 mirror install and independent Stage05 schema verification PASS

**Operator-provided terminal transcript (latest attempt):** On `/srv/projects/text-evaluation-service` the operator first verified `getent ahostsv4 pypi.tuna.tsinghua.edu.cn` resolved to `101.6.15.130` with mirror host name `bfdmirrors.s.tuna.tsinghua.edu.cn`. The Git-ignored Python 3.12 `.venv` was reused; `.venv/bin/python -m pip install --disable-pip-version-check --only-binary=:all: --retries 0 --timeout 12 --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-dev.txt` **completed with `Successfully installed ...`**, including exactly pinned direct requirements FastAPI 0.148.0, Starlette 1.9.0, Pydantic 2.13.5, PyYAML 6.0.3, Uvicorn 0.48.0, SQLAlchemy 2.0.50, Alembic 1.18.4, asyncpg 0.32.0, httpx 0.28.1, httpx2 2.16.0 and pytest 9.0.3.

- Immediately afterwards, chained `.venv/bin/python -m pip check` returned **`No broken requirements found.`** This is a dependency-consistency check on the newly installed environment, not a vulnerability or provenance audit.
- The chained `.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage05_schema.py` returned **`13 passed in 0.31s`**. Classify as `PASS_USER_SERVER_REPORTED_SIMORGH_SCHEMA_13_OF_13`; it validates Stage05 schema/metadata, URL preflight and safety contracts on that Linux host. Earlier host attempts blocked by missing `python` alias and public Wheel-CDN DNS remain historical attempts, now superseded **for this specific independent schema test**.
- **Scope limitation:** This operator command did **not** run `tests/test_stage05_postgres.py`, Alembic upgrade, PostgreSQL integration, full-suite regression or OSV CVE audit on Simorgh. Do **not** infer it tested the shared PostgreSQL server. The isolated GitHub Actions CI 40512243347 remains the separate completed successful evidence for actual synthetic PostgreSQL 17 migration and 4 integration tests and 91-total-test regression suite.
- **Mirror provenance boundary:** Using the public university PyPI mirror to install publicly available code is not equivalent to verifying publisher signatures/independent Wheel SHA256 or receiving legal/enterprise authorization for deployment. No confidential application text, real credentials, private model inputs or private database connection appeared in the submitted command. No change to global pip/DNS/Docker/DB is reported.
- **Stage05 remains `DONE` for local gates.** Stage06 `NOT_STARTED`; protected infrastructure and final organizational supply-chain acceptance remain under the established D-017 ledgers. Do not repeat package installation or migrate any Simorgh shared database merely to close a gate already confirmed in CI.

## 2026-10-27 — Simorgh independent Stage05 non-PostgreSQL regression suite: 87/87 PASS

**Operator-supplied terminal evidence:** From `/srv/projects/text-evaluation-service` in the previously provisioned Python 3.12 Git-ignored `.venv`, executed:

```bash
.venv/bin/python -m pytest -q \
  -p no:cacheprovider \
  tests --ignore=tests/test_stage05_postgres.py
```

Observed output: **`87 passed in 1.90s`**, no reported failures or skips. Record `PASS_USER_SERVER_REPORTED_SIMORGH_NON_DB_87_OF_87`. This broader run includes the previously separately executed **13 Stage05 schema tests** and the existing non-PostgreSQL regression tests in `tests/`; **do not sum 13 and 87 as disjoint results**.

**Scope/limitations:** The command explicitly **excluded** `tests/test_stage05_postgres.py`, so no real PostgreSQL transactional, migration, concurrency or DB integration result is claimed for Simorgh. Separately, GitHub Actions [run 40512243347](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40512243347) had already passed **4 real PostgreSQL integration tests** on an isolated synthetic PostgreSQL 17 and reported **91 total pytest tests** on the reviewed Stage05 code SHA `52f7c57f752037c453a544ea6690d9863b38e6ef`. The arithmetic **87 non-DB + 4 DB = 91** is consistent with those two scopes, not a claim that both were run in one Simorgh command. Stage02/Stage03 standalone `unittest` suites remain separately evidenced from CI and previous Stage04 runs; this latest command does not independently rerun them.

**Current gate:** Stage05 remains `DONE` for the local design/DB acceptance gates per independent CI and independent Simorgh non-DB regression evidence. Enterprise database confidentiality, encryption, authorization, retained Stage04 artifact security requirements and organizational tests remain OPEN or `PENDING_SERVER` under D-017. Stage06 `NOT_STARTED`, to begin only on explicit user request. No application source, test implementation, migration, shared database, Docker network or secrets were changed for this evidence recording.
