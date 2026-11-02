# Text Evaluation Service

Persian on-premise rubric-based text evaluation for `speech`, `media`, and `research`. The project uses FastAPI, an asynchronous PostgreSQL-backed job/Worker workflow, a configurable **internal** vLLM-compatible inference provider, source-grounded criterion evidence and deterministic Python scoring.

> **Engineering status (2026-11-02): Stage 11 BLOCKED / Stage 12 NOT_STARTED.** The application has passed synthetic/offline regressions and isolated PostgreSQL E2E tests. It has **not** passed the mandatory full real-model quality, complete on-premise application E2E, or recipient production certification. Do not present it as a turnkey production deployment.

## Source layout

- `src/host/`: HTTP/Worker entrypoints and fail-closed YAML settings.
- `src/application/text_evaluation/`: API controller and Pydantic DTOs.
- `src/core/services/text_evaluation/`: criteria, rubric, scoring, orchestration and Worker logic.
- `src/infrastructure/`: internal model provider, scoped PostgreSQL repositories, signed-identity and authenticated encryption.
- `tests/`: synthetic validation, contract, failure/recovery and isolated PostgreSQL integration.
- `scripts/verification/`: network-free default Stage 11 smoke/preflight scripts.

## GPU-free verification on an existing checkout

The following **does not start the API, Worker, database, vLLM, Docker or a GPU job**. Use the existing project `.venv` on Simorgh; do not run package installation or migrate a shared database as part of this check.

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pip check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests \
  --ignore=tests/test_stage05_postgres.py \
  --ignore=tests/test_stage06_rubric_postgres.py \
  --ignore=tests/test_stage09_postgres.py \
  --ignore=tests/test_stage10_postgres.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_persian_domain_smoke.py --domain speech
```

The final command's default result is `DRY_RUN_NO_NETWORK`, **not** a model-quality PASS. Do **not** add `--execute-approved` while vLLM is down or without a fresh resource-scoped permission.

## Installation and handoff

See [GPU-free setup and handoff instructions](docs/deployment/11_gpu_free_preparation_and_handoff.md) for Python installation on a **separate approved test machine**, the guarded isolated-DB procedure, actual API contract, known startup limitations and the bounded plan once GPU is available. See [Stage 11 product gap review](docs/verification/15_stage11_product_gap_review.md) and the [56-ID proposed responsibility matrix](docs/verification/14_stage11_product_handoff_scope_matrix.md).

**Important:** The checked-in configuration has `llm.enabled=false`, `worker.enabled=false`, `http_security.enabled=false`; the API binds to loopback, and the PostgreSQL context accepts only an isolated `tes_stage05_*` development database. There is **no Dockerfile or Compose stack** in the reviewed revision. Running `python -m src.host.app` by itself therefore does not activate a working evaluation service.

For a future approved *isolated development* demonstration, `TES_STAGE11_SETTINGS_FILE` may point to an absolute, owner-owned `0600` YAML file **outside this repository**. The file must contain the complete validated Settings schema and secret **references**, not secret values; it is not enabled by default. Production/staging cannot use this override. This does not grant approval to start vLLM or use a shared database. See the runbook for boundaries and tests.

Never commit or paste real customer texts, model IDs, signed tokens, secret values, DB connection strings or internal infrastructure details into this public repository.
