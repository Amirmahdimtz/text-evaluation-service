# Stage 11 — GPU-free preparation, local setup and engineering handoff

**Status:** `PREPARED_NOT_DEPLOYED`, 2026-11-02. This is a Stage 11 pre-execution document, **not** Stage 12 deployment or a claim of operational readiness. Source review baseline: `main` through `80c0635`. The shared Simorgh vLLM was stopped by the operator to reserve GPU VRAM for another project.

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

## 6. Service activation is NOT currently a turnkey step

Do **not** merely set three `enabled` flags in committed YAML or launch `python -m src.host.evaluation_worker`. The current `main` enforces:

- `http_security.enabled=false`, `worker.enabled=false`, `llm.enabled=false` by default.
- ConfigReader reads YAML; it does not bind per-field environment overrides. A separately approved *development-only* external YAML may be selected with `TES_STAGE11_SETTINGS_FILE` (an absolute, owner-only `0600` regular file outside the repo; not a symlink, maximum 64 KiB). It must contain the **complete existing Settings schema**, and any secrets must be `env://` references, never raw values. This file is rejected for `staging` and `production`. The selector `TES_ENVIRONMENT` alone cannot enable services.
- The API requires a configured trusted JWT issuer, RSA verification key reference, encryption key reference and quotas. The Worker also requires an organization scope and complete timeout/lease/concurrency policy. Secrets must stay in an authorized runtime secret source, not the repository.
- `PsqlDbContext`, the Worker Host and `ProtectedEvaluationExecutor` currently deny non-development deployment. The model provider requires a permitted private **literal-IP** endpoint with validated contract and pinned configured identity; it is not automatically found by a Docker alias.
- In the current API/report behavior, protected Worker results are **review-only**. The Python engine calculates a provisional score, but the stored/report `provisional_score` is currently `null`; a final published overall grade requires explicit rubric/scoring-policy resolution.

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
