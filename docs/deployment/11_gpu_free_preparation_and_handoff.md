# Stage 11 — GPU-free preparation, local setup and engineering handoff

**Status:** `PREPARED_NOT_DEPLOYED`, 2026-11-02. This is a Stage 11 pre-execution document, **not** Stage 12 deployment or a claim of operational readiness. Source review baseline: source reviewed through the Stage11 GPU-free 2026-11-02 changes. The shared Simorgh vLLM was stopped by the operator to reserve GPU VRAM for another project.

## 1. Confirmed implementation boundary

| Component | Verified location | Current behavior / constraint |
|---|---|---|
| API entrypoint | `src/host/app.py` | `create_app()` / `python -m src.host.app`; defaults to loopback; HTTP middleware returns sanitized errors |
| Host config | `src/infrastructure/utils/config_reader.py`, `src/host/res/appsettings*.yaml` | `TES_ENVIRONMENT` chooses development vs generic YAML; `TES_STAGE11_SETTINGS_FILE` provides an **optional complete private YAML** for isolated development only; no per-field runtime override or implicit enablement |
| Default ports | `appsettings.development.yaml`, `appsettings.yaml` | Development API: `127.0.0.1:18080`; generic default: `127.0.0.1:8000` (**can collide with existing vLLM when restarted**) |
| Database | `src/infrastructure/context/sql_db/psql_dbcontext.py` | Requires `TES_ENVIRONMENT=development` and a loopback `postgresql+asyncpg` DSN for a database whose name begins `tes_stage05_`; no approved general deployment adapter |
| Migrations | `scripts/verification/run_stage05_migrations.py` | `current`, `check`, `upgrade`; guards the test DSN before touching PostgreSQL |
| Auth / encryption | `src/infrastructure/security/signed_identity.py`, `encrypted_content.py`, `secrets.py` | Signed JWT contract and AES-GCM tested with synthetic keys; `env://NAME` secret references only. Corporate IAM/KMS is recipient-owned and not implemented here |
| Worker | `src/host/evaluation_worker.py`, `src/core/services/text_evaluation/protected_evaluation_executor.py` | Disabled by default; development-only secure executor; guarded encrypted-source / pinned Rubric processing |
| Model | `src/infrastructure/providers/llm/local_llm_provider.py` | Internal literal-IP endpoint validation; no external fallback, no implicit model loading; model artifact identity and quality not verified |
| Packaging | repository tree | Exact Python requirements are present; **no Dockerfile, Compose stack or finalized deployment bundle** |

Source layering remains `Host -> Application -> Core -> Infrastructure`. Do not bypass the Worker, authentication or ciphertext restrictions for a demonstration.

## 2. Safe no-GPU checks on the already provisioned Simorgh checkout

Do not restart shared vLLM, start another model, change Docker networking, install dependencies in another project's environment, run migrations or start a background API/Worker on the shared host. The commands below are offline with respect to AI inference; `git pull` alone contacts GitHub to update source.

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pip check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage10_auth.py \
  tests/test_stage11_protected_worker.py \
  tests/test_stage08_engine.py \
  tests/test_stage11_persian_domain_smoke.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_persian_domain_smoke.py --domain speech
```

For the full **non-DB** Python suite:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests \
  --ignore=tests/test_stage05_postgres.py \
  --ignore=tests/test_stage06_rubric_postgres.py \
  --ignore=tests/test_stage09_postgres.py \
  --ignore=tests/test_stage10_postgres.py
```

`DRY_RUN_NO_NETWORK` confirms only harness input/rubric selection and request-budget declarations; it never confirms vLLM availability or output correctness. These commands have no `--execute-approved` option.

## 3. Clean Python installation on a separate approved test machine

Prerequisites: Linux, Python **3.12** (matching checked GitHub Actions), a clean source checkout, and an approved local Python wheelhouse if the host must not access the package index. Do not use this section to download packages on shared Simorgh while another project is running.

```bash
git clone https://github.com/Amirmahdimtz/text-evaluation-service.git
cd text-evaluation-service
python3.12 -m venv .venv
# APPROVED_WHEELHOUSE must point to a vetted, locally available dependency wheel directory.
.venv/bin/python -m pip install --no-index --find-links "$APPROVED_WHEELHOUSE" \
  -r requirements-dev.txt
.venv/bin/python -m pip check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage10_auth.py tests/test_stage11_protected_worker.py
```

The wheelhouse must include the required transitive packages and exact versions. A failed package installation is **NOT_INSTALLED**, not an automatic authorization to fetch from public mirrors.

## 4. Only on an isolated, owner-approved development PostgreSQL

**Do not execute the migration commands against a shared database.** The code checks the development-only DSN before running Alembic; the guard does **not** provision PostgreSQL or create a database. A DBA/operator must separately provision a dedicated local, disposable **test** PostgreSQL database with a name beginning `tes_stage05_`, a scoped test role, and any required network isolation. Keep its DSN/credentials out of source control, logs and screenshots.

Once that isolated database exists and its owner approves migrations, provide the DSN privately in the process environment as `TES_STAGE05_DATABASE_URL`, with `TES_ENVIRONMENT=development`, then use:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.run_stage05_migrations current
# MIGRATION WRITES: isolated database only, with explicit owner approval.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.run_stage05_migrations upgrade
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  scripts.verification.run_stage05_migrations check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage05_postgres.py \
  tests/test_stage06_rubric_postgres.py \
  tests/test_stage09_postgres.py \
  tests/test_stage10_postgres.py
```

These tests may create/modify **test-only data**; their safe execution requires a dedicated database. GitHub Actions already runs equivalent isolated PostgreSQL 17 and synthetic-engine suites, not Simorgh's shared DB.

## 5. Reproducible isolated runtime preflight (NO network, NO GPU)

A new read-only CLI validates the **actual private development configuration** and
its locally injected key references without making a DB connection, starting an
API/Worker, opening an HTTP socket or invoking a model.

Before attempting a live demonstration, a separately approved isolated database,
private settings file, runtime-injected test JWT public key and AES key, and
an approved local model endpoint must exist. Use the current typed Settings schema
in `src/infrastructure/utils/config_reader.py`; do not commit private settings
or substitute real production credentials. The configuration must explicitly enable
HTTP security, worker and model; Worker max inflight and LLM concurrency/attempts
are restricted to 1 by this **Stage 11 preflight**, not by general production policy.

```bash
cd /srv/projects/text-evaluation-service
# Only after a dedicated test-only environment has been provisioned privately:
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_isolated_runtime_preflight.py
```

Expected success is `CONFIG_VALIDATED_NO_NETWORK` and states
`ISOLATED_DSN_FORMAT_ONLY` / `LOCAL_ENDPOINT_FORMAT_ONLY`. It checks
credentials *locally* but never prints their values. It does **not** prove DB
connectivity, authentic model availability, JWT issuer trust, actual network
no-egress, concurrency safety or deployment readiness. A failure returns
`STAGE11_ISOLATED_CONFIG_INVALID` without details.

The existing checked-in isolated PostgreSQL 17 CI is still the reproducible
software-integration proof for synthetic tests. Once the user separately approves
an isolated development startup with an operational local model, run the existing
`python -m src.host.app` and `python -m src.host.evaluation_worker` in
separate **supervised** terminals using the same private configuration and
isolated DB environment. Do not run these entrypoints while the shared GPU is
reserved by another project. API and Worker startup are **not** performed by
this preflight.



### Stage11 controlled subprocess E2E on Simorgh (explicit opt-in)

The actual independent-process test lives in
`tests/test_stage11_process_e2e.py`. It starts a **real** FastAPI Python
process, a **real** Worker Python process, and a synthetic loopback
OpenAI-compatible HTTP stub. It uses only a dedicated test PostgreSQL
database and synthetic Persian text and keys; it never connects to vLLM.

CI [run 41420277103](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41420277103)
executed **1 passing process E2E** in 3.37 seconds, then **453 passed,
1 skipped** in the full regression suite. The skip in the full suite is
intentional: the explicit opt-in environment variable is absent there.

A new guarded runner can reproduce this with a **new unique project name,
new synthetic credentials, a newly initialized `tes_stage05_*` database,
and a dynamically chosen loopback-only port**. It requires `postgres:17`
to be **already present locally** and `docker compose` v2 available.
It refuses preconfigured existing DB/private runtime variables, downloads
no images (`--pull never`), migrates only its new test database, and
stops its own PostgreSQL container after a pass or failure. The Docker
named volume is deliberately retained; no destructive cleanup occurs.

The first command is an entirely safe no-operation:

```bash
cd /srv/projects/text-evaluation-service
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_isolated_process_runner.py
```

**Only when the temporary host owner has permitted a small new CPU/RAM/disk
Docker container and its loopback port**, and the shared GPU remains
reserved for the other project, use the actual opt-in command:

```bash
cd /srv/projects/text-evaluation-service
docker image inspect postgres:17 >/dev/null
docker compose version
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_isolated_process_runner.py --execute-isolated
```

The Python runner prints only safe status and the unique test project
name. On completion it **stops** its own database and leaves its test
volume, so its storage needs later authorized disposal. If an earlier
private `TES_STAGE05_DATABASE_URL` or `TES_STAGE11_SETTINGS_FILE`
environment variable is set, the runner **refuses** to operate rather
than risk attaching to a different test environment. Do not unset such
variables blindly in an active session.

This is neither an instruction to run shared-vLLM GPU inference nor proof
of non-development/organizational production deployment. Do not claim a
Simorgh PASS until the host operator actually runs it and shares the
sanitized result.

### Optional dedicated PostgreSQL 17 test container (operator approval required)

The repository now contains `compose.stage11-isolated-db.yml` for a **separate,
test-only** PostgreSQL 17 container, with a dedicated named volume/network,
loopback-only host publishing, explicit `isolated` profile and **no default
username, password, database or port**. The operator must privately select
`TES_STAGE11_DB_USER`, `TES_STAGE11_DB_PASSWORD`,
`TES_STAGE11_DB_NAME` (prefix `tes_stage05_`) and a free
`TES_STAGE11_DB_PORT`. Do not store credentials in a shell history, Compose
file, public .env, Git or screenshots.

**This is a documented opt-in startup path, NOT a command to execute now on
the busy shared server.** After an owner-approved isolated environment is
available and the image has been pre-imported/authorized:

```bash
docker compose --project-name tes-stage11-isolated \
  -f compose.stage11-isolated-db.yml --profile isolated up -d postgres
docker compose --project-name tes-stage11-isolated \
  -f compose.stage11-isolated-db.yml --profile isolated ps
```

The Compose stack has **no API, Worker or vLLM container**: use the validated
Python host processes and `TES_STAGE05_DATABASE_URL` pointing only to this
dedicated loopback test DB (properly percent-encoding DSN credentials).
The dedicated test bridge is **not an internal:no-egress network**: Docker
`internal: true` prevents Host-side Python clients from reaching the published
PostgreSQL port on affected Docker engines (reproduced in GitHub CI). The
test-only bridge uses `driver: bridge` and `internal: false`, with a
strict **127.0.0.1-only port publish** and only synthetic credentials/data.
It is not a proof of corporate no-egress, host firewall enforcement, or
production networking. The actual host reachability on Simorgh remains
`PENDING_OPERATOR`; no production or shared DB should connect to this network.
The image tag is a development candidate, not a pinned release digest.
Do not use `docker compose down -v` or remove volumes: these actions delete
test-state data and require separately approved data disposal.

## 6. Service activation is NOT currently a turnkey step

Do **not** merely set three `enabled` flags in committed YAML or launch `python -m src.host.evaluation_worker`. The current `main` enforces:

- `http_security.enabled=false`, `worker.enabled=false`, `llm.enabled=false` by default.
- ConfigReader reads YAML; it does not bind per-field environment overrides. A separately approved *development-only* external YAML may be selected with `TES_STAGE11_SETTINGS_FILE` (an absolute, owner-only `0600` regular file outside the repo; not a symlink, maximum 64 KiB). It must contain the **complete existing Settings schema**, and any secrets must be `env://` references, never raw values. This file is rejected for `staging` and `production`. The selector `TES_ENVIRONMENT` alone cannot enable services.
- The API requires a configured trusted JWT issuer, RSA verification key reference, encryption key reference and quotas. The Worker also requires an organization scope and complete timeout/lease/concurrency policy. Secrets must stay in an authorized runtime secret source, not the repository.
- `PsqlDbContext`, the Worker Host and `ProtectedEvaluationExecutor` currently deny non-development deployment. The model provider requires a permitted private **literal-IP** endpoint with validated contract and pinned configured identity; it is not automatically found by a Docker alias.
- Protected Worker results remain **review-only**. The signed/scoped API now reconstructs a **candidate `provisional_score`** from a complete encrypted criterion set and the pinned immutable Rubric (including retired historical Rubrics); pending/legacy-incomplete/fully-abstained assessments still return `null`. The database's official `overall_score` is still `NULL`, and `publishable_as_official_score` is always `false`. The business-approved rounding/publication policy is still `OPEN_OD04`. See [scoring contract](../architecture/04_stage11_review_only_scoring_contract.md).

The isolated HTTP health routes `/health/live` and `/health/ready` are not proof of full application functionality or model health. The development API port `18080` and vLLM port `8000` must not be repurposed without coordination.

**Engineering work before a fully runnable demonstration:** the new file-selector removes the need to edit checked-in settings for an approved isolated development run, but a **live** demonstration still needs a separately provisioned `tes_stage05_*` test database, configured secret references and JWT issuer, authorized model availability and an operator-controlled execution window. It is not production wiring. Decide and implement the expected provisional-versus-official reporting contract; build and verify a reproducible packaging/startup procedure based on the selected deployment target. These are concrete product gaps, **not** demands for organization-wide SSO/KMS/firewall procurement.

## 7. When GPU becomes free (separately authorized later)

1. Confirm the other project's activity has ended; obtain owner-approved model restart and a low-impact observation window. Do not assume stopped vLLM or instantaneous `nvidia-smi` utilization grants permission.
2. Privately inventory existing model/runtime identity, tokenizer/chat template, permitted endpoint, resource budget and abort conditions; avoid second concurrent model load.
3. Run the **default no-network** Persian harness separately for `speech`, `media` and `research`. Any `--execute-approved` run is a new opt-in **model request** requiring a fresh explicit permission, one domain per run, capped at six sequential requests, no retry. After any failure, stop and inspect sanitized error categories.
4. Benchmark against a versioned, authorized three-domain expert-labeled dataset and a separately scoped sequential second model candidate if the original Gate still requires one. Record scores, evidence relevance, abstention, denominators, latency and GPU VRAM; no fabricated accuracy or source evidence.
5. Exercise authenticated API -> encrypted isolated DB -> fenced Worker -> real local vLLM -> exact quote/Unicode offsets -> encrypted scoped report. Verify error handling and no unauthorized text leakage.
6. Finish product-specific acceptance, then hand over recipient-owned infrastructure/operational obligations according to the [56-ID responsibility proposal](../verification/14_stage11_product_handoff_scope_matrix.md). Stage 11 stays `BLOCKED` until the revised product Gate is explicitly accepted and proven; Stage 12 is not started.

## 8. Handoff bundle and evidence status

- Exact Git commit SHA, dependency pins (`requirements.txt` / `requirements-dev.txt`), Python and PostgreSQL versions used by the accepted run.
- Reproducible isolated DB schema/migration revision, setup and non-destructive recovery instructions; never include real credentials or private DSNs.
- API paths and signed identity requirements in [Stage10 API runbook](10_api_security_runbook.md); Worker operation/fencing in [Stage09 runbook](09_worker_operations_runbook.md).
- Rubric JSON/checksums, prompt version, model/tokenizer/runtime immutability reference and approved model artifacts retained **privately**. Current candidate rubrics and model revision are **not final acceptance**.
- CI and operator evidence: GitHub Actions `41405074852` **424 tests PASS** (isolated PostgreSQL / synthetic engine); Simorgh `ce5e930` **66 PASS** and `e7699be` **16 PASS** (operator-provided offline outcomes). **No real model E2E quality PASS**.
- Recipient responsibility: corporate ingress TLS/SSO, runtime keys and rotation, firewall/no-egress policy enforcement, backup and retention, availability/on-call and production change approvals. Product-side secure validation, encryption and data scoping remain ours.
- [Product gap and acceptance review](../verification/15_stage11_product_gap_review.md) is the priority checklist; do not conflate the Stage 11 engineering handoff draft with a Stage 12 approved production release.

### 2026-11-02 — isolated Compose host connectivity correction

The prior real on-host attempt returned `ISOLATED_PROCESS_E2E_FAILED`, so its result remains **FAIL** until retested. GitHub CI reproduced a `postgres_readiness` failure with `internal:true` Docker networking. The corrected test-only Compose manifest uses a unique bridge network and an explicit `127.0.0.1` bind for PostgreSQL; local Python processes can now reach the port in CI. The `--execute-isolated` Runner was successfully exercised with **actual Docker startup and shutdown** in [CI `41425225692`](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41425225692): `ISOLATED_PROCESS_E2E_PASS`. This is **synthetic-only** validation; standard bridge networking may allow container egress, so no real data should be used and no organizational network-control acceptance is claimed. The original failed Simorgh project retains its named volume and must not be cleaned without authorization. A new on-host result is pending.
