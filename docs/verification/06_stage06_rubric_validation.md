# Stage06 — Rubric Management & Versioning: Local Acceptance Record

**Date:** 2026-10-27  
**Stage:** 06  
**Status:** `DONE_LOCAL` — mandatory local validation and transactional acceptance tests PASS on isolated CI; no production or organization-published rubric is approved.  
**Authoritative sources:** `Service_Architecture_Guide_FA.md` and `Text_Evaluation_Service_Implementation_Plan_FA.md` v1.1.0 Stage06, Stage01 Rubric Catalog, existing Stage05 database/DI infrastructure, D-015/D-017.

## Delivered files

- `src/core/services/text_evaluation/rubric_schema.py` — Pydantic validation (weight sum 100, unique domain-prefixed codes, six score anchors 0..5, no unapproved fields/policies), canonical SHA-256.
- `src/core/services/text_evaluation/rubric_service.py` — `@inject`/constructor-injected `RubricService`; validated synthetic Draft, technical Publish/Retire and exact version binding.
- `src/infrastructure/repositories/text_evaluation/rubric_version_repository.py` — extended existing concrete `BaseRepository` provider with scoped exact Published lookups; transactional INSERT/Publish/Retire, short row lock `FOR UPDATE`, same-transaction metadata-only audit and uniqueness conflict handling.
- `tests/fixtures/stage06_candidate_rubrics.json` — 18 unchanged business-proposed criteria/weights/anchors extracted from Stage01 documentation, 6 each speech/media/research; **no SME-approved policy**.
- `tests/test_stage06_rubric_schema.py`, `tests/test_stage06_rubric_postgres.py`, and `.github/workflows/stage06-rubrics.yml` — validation/integrity/DI, concurrency/immutable DB and regressions.
- `docs/requirements/06_rubric_assessability.md` — assessability/non-assessability and open approval boundary.

No new SQLAlchemy table, DB column or Alembic migration was justified: Stage05 already has `rubric_versions`, same-org FK, uniqueness, nonmutable Published trigger and append-only AuditEvent. No Stage07 LLM client, Stage08 scoring or Stage10 HTTP endpoint has been created.

## Actual isolated CI execution

GitHub Actions [Stage06 run 40519890093](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40519890093) on code SHA `0d2d3eeb416c4491924e64d59e94427a10c9bc0b`: **`completed / success`** on Ubuntu 24.04, Python 3.12, ephemeral **PostgreSQL 17** and a synthetic local-only test database.

| Check | Real log result | Coverage |
|---|---|---|
| Stage05 preserved schema and safety validation | `13 passed in 0.17s` plus static guard checking **22 runtime source files** | SQLAlchemy model/migration contract, security guard |
| Stage06 synthetic rubric schema/DI validation | **`20 passed in 0.35s`** | 18 anchors/weights in three domains, missing/duplicate/invalid criteria, fingerprint, integrity, type and DI |
| Stage06 PostgreSQL publication tests | **`3 passed in 0.37s`** | Atomic Publish+Audit, concurrent publish race, checksum validation, DB immutable published state, org-scoped lookup, retire, version pinned by synthetic Evaluation FK, unique/conflict |
| Stage05 PostgreSQL regressions | **`4 passed in 0.37s`** | Prior database idempotency, constraints and queue fencing |
| Entire Python suite | **`114 passed in 1.46s`** | Stage04–06 regressions, includes tests already individually run above |
| Independent Stage03 regressions | `Ran 38 tests ... OK` | Existing Stage03 validation |
| Independent Stage02 regressions | `Ran 12 tests ... OK` | Existing Stage02 validation |
| Migration upgrade + Alembic metadata drift | **PASS**, workflow steps succeeded | Actual temporary PostgreSQL 17 schema |
| Dependency consistency | `No broken requirements found.` | Installed Python package dependencies |
| Python public OSV audit | `No known vulnerabilities found` | Only scanned public Python dependency metadata, not Linux OS packages |

Some **expected PostgreSQL error lines** in the CI log are from intentional negative tests (duplicate Rubric ID/version, published-trigger refusal, Stage05 FK/uniqueness violations). All assertions and jobs PASSED; these are not unhandled incidents or confirmed vulnerabilities.

The **first Stage06 workflow** run [40519655994](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40519655994) failed during workflow validation (no jobs). The workflow was replaced with the known working Stage05 CI structure; this was followed by an actually successful run. Do not report the first attempt as a successful test.

## Gate resolution

| Mandatory Stage06 gate | Actual disposition |
|---|---|
| Rubric requires version, validated criteria and anchors | `PASS_CI`: Pydantic strict candidate schemas, integrity checking and negative tests |
| Published version immutable | `PASS_CI_REAL_POSTGRES`: Stage05 trigger and failed direct mutation test; technical Retired retains original snapshot |
| All three domains valid/versioned/testable | `PASS_CI`: 3×6 proposed anchored criteria + tests; **not business-approved** |
| Concurrency and transaction/Audit | `PASS_CI_REAL_POSTGRES`: same-transaction writes, publish race one success, actor metadata audit and unique version handling |
| Evaluation pinned to a Rubric version | `PASS_CI_REAL_POSTGRES`: validated Service binding and immutable composite FK used for a synthetic Stage05 Evaluation |
| Operational IAM, corporate approval, AI evaluation quality, policy numbers | `PENDING_SERVER` or `OPEN`, **not** claimed PASS; see D-015/D-017, OD-03/04/06/07/08/14 and Stage11 |

**Stage06: `DONE_LOCAL` / closure of mandatory local technical gates.** This is not a certificate for real confidential text use, a commercially published Rubric or Production deployment. Stage07 `NOT_STARTED` and may only start when explicitly requested.

## Optional User Local commands (on a safe development checkout)

```bash
git pull --ff-only origin main
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage06_rubric_schema.py
.venv/bin/python -m pytest -q -p no:cacheprovider tests --ignore=tests/test_stage05_postgres.py --ignore=tests/test_stage06_rubric_postgres.py
```

Real database integration tests only on a separately provisioned, explicitly authorized **synthetic PostgreSQL** on loopback with name prefixed `tes_stage05_`:

```bash
# Only after approval and isolated test DB creation:
# TES_ENVIRONMENT=development
# TES_STAGE05_DATABASE_URL=postgresql+asyncpg://<isolated-user>:<secret>@127.0.0.1:5432/tes_stage05_<db>
.venv/bin/python -m scripts.verification.run_stage05_migrations upgrade
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage06_rubric_postgres.py
```

Do **not** use the shared Simorgh PostgreSQL or modify corporate Secrets/Networking/Production to run these commands. The GitHub Actions isolated CI evidence already proves the Stage06 local integration gate.

## 2026-10-27 — Simorgh independent Stage06 non-database tests: 20/20 and 107/107 PASS

**Source:** operator-provided Simorgh terminal transcript from `/srv/projects/text-evaluation-service`. `git pull --ff-only origin main` succeeded, fast-forwarding local checkout `556625d` to `03ca994` with Stage06 code, fixtures, tests and documents.

```text
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage06_rubric_schema.py
20 passed in 0.57s

.venv/bin/python -m pytest -q -p no:cacheprovider tests --ignore=tests/test_stage05_postgres.py --ignore=tests/test_stage06_rubric_postgres.py
107 passed in 1.76s
```

- **Classification:** `PASS_USER_SERVER_REPORTED_STAGE06_SCHEMA_20_OF_20` and `PASS_USER_SERVER_REPORTED_NON_DB_SUITE_107_OF_107`; the output showed no failures or skips. The separate 20 Stage06 tests are **included within** the broader 107, not an additional group to sum.
- **Scope:** Both PostgreSQL test modules were explicitly excluded from the 107-test run, so **no real PostgreSQL transaction, Alembic migration or integration test was executed on Simorgh** by these commands. The isolated [GitHub Actions PostgreSQL 17 run 40519890093](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40519890093) separately passed 3 Stage06 DB tests, 4 Stage05 DB tests and 114 total pytest tests. The difference of 7 tests is consistent with the explicitly excluded DB modules; the environments and executions must not be conflated.
- **Security and deployment:** No corporate/shared DB, secrets, Production deployment, GPU/LLM runtime, customer data or official Rubric publication were accessed or authorized. The Stage06 local acceptance gate remains `DONE` on accumulated CI and operator evidence, with corporate IAM/approval, Rubric business policy (`OD-03/04/06`) and protected-data tests `OPEN/PENDING_SERVER` under D-015/D-017. Stage07 remains `NOT_STARTED`.
- **No re-execution claim:** This is a documentation-only recording of the user-run test transcript; the assistant did not run tests on Simorgh.
