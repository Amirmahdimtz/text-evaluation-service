# Stage 11 — Protected Encrypted-Source Worker Integration

**Status:** `CODE_AND_OFFLINE_POSTGRES_E2E_PASSED / ON_PREM_SECURE_E2E_PENDING` (2026-10-31). This is a deliberately narrow completion of **code gap B11-06** in an isolated, synthetic **development** environment, **not** an enterprise staging deployment, signed model acceptance, production enabling or a final Stage11 gate.

## Source change and trusted execution path

Commit `e63b2ca42688ff5a3629579b6e5e586555ad5f62` implements the following using the existing architecture:

1. A signed internal HTTP request creates an `Evaluation` and encrypted `ProtectedText` with an immutable published **technical candidate** `RubricVersion` in the existing PostgreSQL-backed durable job flow.
2. `EvaluationWorkerService` obtains the context with existing lease/fencing controls. `EvaluationRepository.load_protected_worker_material_async` reads the source ciphertext and scoped published Rubric only for the matching evaluation, owner, organization and `processing` state.
3. `ProtectedEvaluationExecutor` verifies explicitly configured **development-only** worker/HTTP/LLM/egress controls and the exact configured encryption `key_id` before using `EncryptedContentService` AES-256-GCM to decrypt the protected source in memory. It refuses missing/wrong-key/tenant context or broken Rubric checksum.
4. The existing `TextEvaluationService` uses the local `CriterionEvaluationService` and `LocalLlmProvider` when a valid **approved private** development endpoint is explicitly configured. It validates quotes and half-open Unicode offsets, assesses with the pinned candidate Rubric, and computes **provisional only** scoring in Python. `research_novelty` remains conservative.
5. Each criterion's reason/evidence/recommendations is encrypted with the same tenant, owner, evaluation and `kind=criterion` authenticated context. The Worker persists only `CriterionResult.encrypted_details`, status/coverage and declared (not proven) model/prompt revisions, with `overall_score=None` and `needs_human_review`/`partial`. Stale attempts remain subject to the repository's existing fenced atomic finalization. The API's existing authenticated report decrypts only within authorized scope.
6. The actual engine/provider's HTTP connection pool is closed via explicit async cleanup on the executor, criterion service and engine; the Worker still closes the DB context even if cleanup fails. No extra Provider instance is created merely for cleanup.

No new DB table, migration, interface, message broker, SSO service, KMS product or uncontrolled configuration flag was introduced. Existing `@inject`, DI discovery, service and repository patterns are retained.

**Fail-closed scope:** current `appsettings.yaml` and `appsettings.development.yaml` still have `worker.enabled=false`, `llm.enabled=false`, `http_security.enabled=false`. The Host worker may start this executor only after all flags are explicitly and validly enabled in the **development environment**, and `PsqlDbContext` remains hard-restricted to the `tes_stage05_*` loopback-only isolated development PostgreSQL URL. Staging/production are **not enabled**, pending approved secure deployment wiring and organizational services. Do not toggle flags against a shared Simorgh DB, configure live credentials in repository files, or misrepresent a synthetic executor as live model evidence. New code does not solve key-version retention/rotation.

## Real test evidence on public synthetic-only CI

Source revision: `e63b2ca42688ff5a3629579b6e5e586555ad5f62`, branch `main`. Verified job-level `success` in all five GitHub Actions workflows:

| Workflow | GitHub Actions run | Result |
|---|---|---|
| Stage10 secure API and isolated PostgreSQL E2E | [41178699423](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41178699423) | `SUCCESS`; real ephemeral PostgreSQL migrations, signed API, protected Worker synthetic engine, negative access, full `pytest tests` **374 passed in 4.89s** |
| Stage08 offline deterministic evaluation engine | [41178699459](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41178699459) | `SUCCESS`; non-DB test suite **359 passed, 8 skipped in 2.64s** |
| Stage05 isolated PostgreSQL validation | [41178699356](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41178699356) | `SUCCESS` |
| Stage06 isolated Rubric versioning validation | [41178699330](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41178699330) | `SUCCESS` |
| Stage09 durable Worker and PostgreSQL recovery | [41178699354](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41178699354) | `SUCCESS` |

The full CI suite includes the new `tests/test_stage11_protected_worker.py` negative cases and the isolated `tests/test_stage10_postgres.py::test_stage11_protected_executor_from_signed_api_through_isolated_postgres`. The latter exercises **actual ciphertext storage/decryption, existing signed JWT HTTP API, fenced job processing and scoped report retrieval**, but uses an **in-process synthetic test engine**. It does **not** send prompts to Simorgh, invoke a live model, or test corporate SSO/KMS/No-Egress. PostgreSQL constraint errors visible in CI service logs are intentional negative tests; the checked job outcome is `success`.

## Safe operator verification (no live inference, no shared DB changes)

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage11_protected_worker.py \
  tests/test_stage09_worker.py

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage11_criterion_contract_smoke.py \
  tests/test_stage11_synthetic_inference_smoke.py

# Still network-free unless expressly opted in and separately authorized:
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  scripts/verification/stage11_criterion_contract_smoke.py
```

Do **not** invoke `tests/test_stage10_postgres.py` on a shared or nonisolated database; it is designed for a properly configured isolated PostgreSQL instance and its fixture runs Alembic migrations. For real corporate-on-prem tests, verify approvals, provider artifact/license/pin, protected test identities, authorized key custody and staging DB isolation first; then run test-specific explicit authorized commands. Never paste raw source, keys, private registry/image/model IDs or enterprise logs into public GitHub/chat.

## Remaining Gate obligations

- B11-06: development protected-worker code integration **PASS** with synthetic execution, but on-prem protected enterprise API → actual authorized model E2E **`PENDING_SERVER`**, and the current Host/DB environment safeguards deliberately deny staging/production. Approved production-capable deployment wiring and IAM/DB/KMS remain needed before running with real protected organizational data.
- B11-01..05, B11-07..10: approvals, exact real model artifact provenance, two-model / three-domain expert benchmark, enforceable No-Egress, enterprise IAM/key lifecycle, measured capacity and backup/restore remain unverified.
- All original **56 mandatory Stage11 test IDs remain `PENDING_SERVER`** until each full original oracle is independently satisfied. Auxiliary smoke, CI and this integration code are **not** a substitute. Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## User-reported Simorgh offline retest — 2026-10-31

On Simorgh, operator fast-forwarded the repository from `f001794` to commit `c8f10ba` and executed these two **offline** suites:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_stage11_protected_worker.py \
  tests/test_stage09_worker.py
```

**Actual operator-reported result:** `36 passed in 0.87s` with no reported skips/failures. The tests confirm local Worker integration/negative-case contracts in the Simorgh Python environment. They do **not** access the real inference server or validate a corporate PostgreSQL connection. The prior CI's 374 passing tests had a separate **isolated ephemeral PostgreSQL + synthetic engine**; do not conflate the two runs. The original 56 enterprise acceptance items remain `PENDING_SERVER`; Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. No inference/production authorization is implied.
