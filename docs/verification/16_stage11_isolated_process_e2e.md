# Stage11 — Real API + Worker processes on isolated PostgreSQL, synthetic model

**Date:** 2026-11-02. **Acceptance classification:** `PASS_CI_REAL_PROCESSES_SYNTHETIC_MODEL`; `PENDING_OPERATOR_SIMORGH`; real local vLLM `PENDING_SERVER`. Stage11 `BLOCKED` / Stage12 `NOT_STARTED`.

## Purpose and accurate evidence boundary

This integration test runs **actual independent OS processes** for `python -m src.host.app` (FastAPI/uvicorn) and `python -m src.host.evaluation_worker` (durable Worker), backed by a **real PostgreSQL 17** test database in a GitHub Actions service container. The model endpoint is a local, deterministic, explicitly synthetic HTTP server on an OS-assigned loopback port, **not** a real LLM, vLLM, GPU or model-quality evaluation.

The test validates a signed RS256 JWT, synthetic immutable Rubric seed, encrypted protected-source request/queue creation, Worker claim and actual process execution, six loopback HTTP criterion-response roundtrips, persisted encrypted evidence, bounded source offsets, resulting review-only `provisional_score` of 80, coverage 1.0, `overall_score=NULL` in PostgreSQL, and wrong-organization 404. It also verifies the process exit conditions and always terminates its spawned child processes. The six synthetic inference responses **do not prove** the semantic correctness or accuracy of any AI model.

The integration test is skipped unless **`TES_STAGE11_PROCESS_E2E=1`** is explicitly set. It checks the existing guarded `TES_STAGE05_DATABASE_URL` validation before any subprocess starts. An isolated PostgreSQL database with migrations must be ready before running the test directly.

## Actually executed CI

| Source commit | GitHub Actions run | Real observed result | Interpretation |
|---|---|---|---|
| `aea86c604aa646108997e66ea0f0122336eb181f` | [41420277103](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41420277103) | **1 real-process E2E passed in 3.37s**; full suite **453 passed, 1 skipped in 6.51s** | PostgreSQL isolated; actual API/Worker subprocesses; deterministic loopback synthetic model only |
| `60bd6bcb3c9bfe212d0981f35d953946277eea85` | [41420824477](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41420824477) | **7 runner safety tests passed**, **1 real-process E2E passed in 1.97s**, full suite **460 passed, 1 skipped in 3.60s** | New default-no-op operator runner and explicit opt-in controls; no Docker command executed by the runner during CI |

The single skipped case in `pytest tests` is intentional: it is the same process E2E without the opt-in environment variable. The dedicated CI step **did execute and pass** the test separately.

## On-host, no-GPU operator execution (not yet performed)

The on-host test now has an operator-safe, explicit orchestration script:
`scripts/verification/stage11_isolated_process_runner.py`.

1. In the existing Simorgh project checkout, run `git pull --ff-only origin main`.
2. Run the script **without arguments**. Expected `DRY_RUN_NO_DOCKER_NO_NETWORK`; no changes.
3. Verify Docker Compose v2 is available and `postgres:17` is **already imported locally**, with no model/GPU or other container conflicts. The operator must have permission for a small isolated CPU/RAM/storage test container; the shared GPU remains untouched.
4. Run `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verification/stage11_isolated_process_runner.py --execute-isolated`. This requires **no preexisting database**, and intentionally rejects any existing `TES_STAGE05_DATABASE_URL`, `TES_STAGE11_SETTINGS_FILE`, `TES_STAGE11_DB_PASSWORD`, or `TES_STAGE11_DB_PORT` in the caller environment.
5. The script allocates a unique Docker Compose project, **synthetic, random new DB credentials**, `tes_stage05_*` database name and a loopback-only port, then performs only that database's migrations; it launches and verifies the actual two subprocesses with a local synthetic model stub.
6. On success/failure, it stops only its project PostgreSQL container and **retains** the Docker volume (no `down -v`, no deletion). Its log contains only synthetic test identifiers/status, not credentials or real text. A retained test volume requires later authorized cleanup if desired.

If the image is not available locally, the runner aborts; it does **not pull** a container image or model. If `docker compose` is unavailable or the chosen port is occupied, it fails without modifying the shared production database or existing vLLM; an operator should first inspect the failure and resource reservations. Credentials are transiently stored only in the process/container test runtime and must not be shared.

**Exact safe commands:**

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_isolated_process_runner.py

docker image inspect postgres:17 >/dev/null
docker compose version

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_isolated_process_runner.py --execute-isolated
```

If there are preconfigured database credentials or a currently active server deployment in the session, execute this only from a clean new environment after verifying scope; never remove environment variables from a service process in use. Do not run any migration against a shared database.

## Still open

- `G11-P01` needs a verified, documented, approved host deployment, package and resource baseline beyond a self-contained test harness. No production application stack/Compose bundle is claimed.
- `G11-P02` local **real vLLM** full signed API/Worker/DB report path is still `PENDING_SERVER` while GPU is reserved for another project.
- `G11-P03` actual quality of the three Persian domains against expert-labeled data, provenance and GPU benchmarks remains `PENDING_SERVER`.
- `G11-P04` policy on **official** rounding/publication and minimum coverage remains `OPEN_OD04`; the displayed 80 in this test is only a Python-derived synthetic provisional candidate.
- Original 56 mandatory Stage11 IDs and responsibility classification remain traceable; synthetic CI success does not mark real-model or organization environment checks PASS.

## Failed Simorgh operator run and reproduced Docker network issue — 2026-11-02

Operator updated `8fecbbd..4190150`, observed `DRY_RUN_NO_DOCKER_NO_NETWORK`,
then ran opt-in `--execute-isolated` with Docker Compose v5.6.1.
Project `tes-stage11-413cbc50dfe4` was created, stopped, volume retained,
and `STAGE11_ISOLATED_RUN_ABORTED` returned. **No test PASS occurred on
Simorgh.** The original runner suppressed the precise error phase.

Reproducing the actual Compose invocation in [CI run
41424875201](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41424875201)
confirmed the failure at **`postgres_readiness`** after a successful
`compose up`: the Host Python client cannot connect to the published port on
this `internal:true` Docker bridge. That CI run is `FAILED` and must not
be recorded as success. The script now reports fixed, redacted failure phases,
never a secret, DSN or traceback; attempts to stop its uniquely named
container even when Compose startup partly fails.

The test-only Compose network is changed to an ordinary dedicated bridge with
`127.0.0.1` host-only PostgreSQL publishing. Because this permits container
egress under default Docker networking, the manifest uses **only synthetic test
credentials/data**, not confidential user input, and no production no-egress
validation is inferred. The repaired Docker orchestration must pass CI and then
be explicitly rerun by the authorized operator before marking the Simorgh
scenario passed. Previous failed test volume is retained: no deletion was
performed or authorized.

## Root-cause remediation and on-host follow-up — 2026-11-02

The first actual Simorgh operator run (source `4190150`, project `tes-stage11-413cbc50dfe4`) **FAILED** after container startup; the script stopped that test DB and retained the volume. A new, credential-redacting `failure_phase` field reproduced the failure as `postgres_readiness` in CI [`41424875201`](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41424875201), then the test-only network was changed from `internal:true` (unreachable for Host clients in that CI environment) to a dedicated bridge with **strict loopback-only host publishing**. This permits Docker bridge egress and therefore **does not** constitute No-Egress certification. Only synthetic sources and transient keys are permitted.

CI [`41425225692`](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41425225692) successfully executed the **actual guarded Docker Compose Runner** end to end, not merely the CI service-container process test: database ready, migrations applied, separate FastAPI + Worker synthetic six-criterion evaluation, container stop, volume retained; **12 runner safety passes**, **1 isolated-process E2E pass**, **465 full-suite passes, 1 intentional skip**. No GPU, model runtime, real text, or Simorgh shared DB was accessed.

**On-host verification on corrected `main`:** requires renewed operator confirmation of resource availability on the shared host. The runner still refuses preconfigured DB/private-runtime variables, pulls no image, defaults to dry-run, prints no sensitive exception details and never deletes test volumes. Use the [scoped commands in the deployment runbook](../deployment/11_gpu_free_preparation_and_handoff.md); only `ISOLATED_PROCESS_E2E_PASS` in the actual Simorgh output would close `PENDING_OPERATOR`. Retained old test volume must not be deleted automatically.

## Repaired Simorgh real-process synthetic test: operator PASS — 2026-11-02

The operator successfully updated `4190150..43dd97c`, ran static Runner/Compose checks (**13 passed in 0.07s**) and **actually executed** `stage11_isolated_process_runner.py --execute-isolated` on Simorgh. A new uniquely scoped test database project `tes-stage11-f045d3ff2cdd` passed the exact milestones `CHECKING_ISOLATED_POSTGRES`, `MIGRATING_ISOLATED_TEST_DATABASE`, `RUNNING_SYNTHETIC_API_WORKER_E2E`, `ISOLATED_PROCESS_E2E_PASS` with `gpu_requests=0`, then `ISOLATED_TEST_DATABASE_STOPPED_VOLUME_RETAINED`.

**Result classification:** `PASS_USER_SERVER_REPORTED_SYNTHETIC_E2E` and the corrected-code `PENDING_OPERATOR` gate for this specific local synthetic process integration is now **fulfilled**. The previously failed test (`tes-stage11-413cbc50dfe4`) and its retained Volume remain historical evidence; do not delete either test Volume without explicit authorization. This confirms on-host test-container startup and real process orchestration **only with the local deterministic model stub**. It does not validate real vLLM, three-domain Persian AI quality, production packaging, SSO/KMS, model provenance, or No-Egress. Stage11 remains `BLOCKED`, Stage12 `NOT_STARTED`.
