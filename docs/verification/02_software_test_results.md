# Stage 11 — Software Verification Results

**Status:** `BLOCKED` / real on-premise tests `NOT_RUN`. Date: 2026-10-28. Baseline `9db6025a6a2639928c6536e23c028684caea22f5`.

## Previously executed evidence (not new Stage 11 tests)

| Environment and provenance | Reported observed result | What it proves / does not prove |
|---|---|---|
| GitHub Actions [Stage10 run 40656653349](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40656653349) on source `24ced033c4deac0f117779ed12f4c1875349a98d` | 240 Python tests passed, isolated PostgreSQL 17, migrations/drift, local synthetic API/Worker model stub, 38 Stage03 + 12 Stage02 unittest | Local code and isolated synthetic integration, **not** real vLLM/SSO/KMS/no-egress or organizational DB |
| Operator-reported Simorgh terminal evidence, checkout `dbcf3f2` | 9 focused Auth tests passed (0.87 s); 226 offline pytest tests passed (2.37 s); pinned PyJWT/cryptography installed, pip check clean | Local non-PostgreSQL regressions; nine are included in 226. **14 PostgreSQL tests excluded on Simorgh** |
| Stage 11 enterprise software, security, model, dataset and recovery | `NOT_RUN` | No corporate acceptance claims |

The operator-reported Simorgh tests and CI were already recorded in [Stage10 validation](10_stage10_api_validation.md). No actual Stage 11 test was executed by the assistant.

## Required Stage 11 E2E and software checks (all `PENDING_SERVER`)

1. Approved corporate IdP/JWKS, signed reviewer assignment and revocation; 401/403/404 and tenant/owner IDOR including feedback and rubric operations.
2. Approved staging DB identity/TLS/least privilege, tenancy and encrypted protected-source resolver, KMS/envelope rotation and backup restrictions.
3. Full authenticated HTTP submission → persisted encrypted source+job → worker decrypts under scoped service identity → **real on-premise pinned model** → independently validated criterion evidence/score → scoped report/feedback/audit. No unapproved official score.
4. Lease fencing/crash recovery, idempotency across replicas, queue admission/backpressure and complete/fail atomicity with test-only isolated DB.
5. Schema/Alembic changes only in authorized staging with non-destructive approved change window and backup; no migrations on shared/production DB.
6. Permission failures, retry exhaustion, partial model output, malformed/oversize requests, cancellation, service outages; ensure error/log/trace sanitization.
7. Re-run all local unit/contract suites after any authorized integration code change, recording source SHA and exact commands.

**Important product blocker:** `src/host/evaluation_worker.py` deliberately exits with `WORKER_SECURE_EXECUTOR_NOT_CONFIGURED`; `src/infrastructure/context/sql_db/psql_dbcontext.py` only accepts local `tes_stage05_*` development DBs; `EvaluationApiService` refuses non-development use. These are safety controls, **not** evidence of successful enterprise integration. Do not bypass them by changing runtime flags or shared database settings.

## Execution evidence

- Stage 11 executed Run IDs: **none**.
- Stage 11 software PASS/FAIL measured: **none**.
- Blocking approvals and dependencies: [release blockers](06_release_blockers.md); detailed test IDs: [strategy](01_test_strategy_and_traceability.md).

## Independent Simorgh read-only Stage11 preflight — 2026-10-28

The operator fast-forwarded the local checkout to `e29537b`, ran the new standalone Python preflight safety suite (**13 passed in 0.04s**) and successfully executed the read-only host/GPU inventory command. This is **user-reported host-local test and observation evidence**, **not** completion of an enterprise acceptance test. No live vLLM, corporate DB, IAM, KMS, external egress validation, inference, load, or Recovery test occurred. The source `S11-AI-01` hardware-inventory prerequisite is partially informed, but the pinned runtime/capacity oracle remains unmet and `PENDING_SERVER`. All 56 actual Stage11 gate tests remain `PENDING_SERVER`. [Observed hardware summary](07_stage11_readonly_preflight.md).

## Simorgh Stage11 container metadata observation — 2026-10-28

The operator pulled commit `095f318`, executed the container-metadata tool's **30 offline tests (30 passed in 0.06 s)**, and ran the opt-in bounded host-local metadata command. Docker container state and installed vLLM package version returned `UNVERIFIED / NOT_OBSERVED`; root cause unknown due to intentional diagnostic suppression. The local `GET /v1/models` metadata endpoint advertised **one** model ID, redacted by the tool as a non-exact match for either known public candidate name. No actual inference, model artifact/revision validation, credential inspection or network isolation proof occurred. The read-only Docker state diagnostic is in [the runbook](08_stage11_container_metadata.md). The 30 passed tests are **not** additional Stage11 acceptance gates; all 56 mandatory enterprise test IDs remain `PENDING_SERVER`.


## Simorgh verified running-container vLLM package observation — 2026-10-28

The operator pulled main commit `86f7d87` and ran the existing bounded metadata script on the named existing Docker container: `container_running=true`, installed `vllm` **Python distribution version `0.10.2`**, proof label `PACKAGE_METADATA_INSIDE_RUNNING_CONTAINER`. The optional loopback request was deliberately skipped in this invocation; earlier metadata indicated one advertised model but not its identity or container binding. No new offline tests were reported for this specific run. This proves **only installed package metadata and the running Boolean**, not live serving process version parity, model weights, Structured Output, model accuracy, security posture or enterprise readiness. `S07-S11-01` and the other **55** enterprise test IDs remain `PENDING_SERVER`; no benchmark, inference or load test was performed. See [bounded runbook](08_stage11_container_metadata.md).

## Authorized one-shot synthetic vLLM structured-output smoke tooling — 2026-10-28

The tool `scripts/verification/stage11_synthetic_inference_smoke.py` and 35 offline synthetic mock-network contract tests were created for the user's scoped permission to make **one** real synthetic completion request. Assistant-host `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_stage11_synthetic_inference_smoke.py` returned **35 passed in 0.11s**; the CLI `--dry-run` returned `DRY_RUN_NO_REQUESTS` with **no network IO**. The assistant has not executed the actual request on Simorgh; its outcome is `PENDING_OPERATOR_EXECUTION`, not `PASSED`. The script sends at most one private-loopback structured-output completion with no source text or credentials and redacts model ID/output/error bodies. A successful simple `{"ack":"ok"}` response would prove **only** a narrow real synthetic structured-output roundtrip. All 56 enterprise acceptance IDs remain `PENDING_SERVER` and Stage11 `BLOCKED`. [Runbook](09_stage11_single_inference_smoke.md).

## First real on-prem synthetic structured-output inference — operator report, 2026-10-28

The Simorgh operator used source SHA `0ba42a29fbbfd9ae2faf1916c593207558cc500d`, ran **35** offline one-shot smoke contract tests (**35 passed in 0.08s**) and verified `--dry-run` returns `DRY_RUN_NO_REQUESTS`. The one user-approved actual fixed-input synthetic inference returned `PASS_SYNTHETIC_STRUCTURED_SMOKE`: HTTP **200**, `finish_reason=stop`, strict tiny JSON schema **valid**, POST elapsed **149ms**, usage **70/10/80** prompt/completion/total tokens. **This is the first reported live model generation observed for Stage11, and is marked `PASS` only as an auxiliary smoke result.** No credentials or source text were passed; the tool only reports sanitized status, not model ID or raw response.

It does **not** execute `CriterionInference` DTO/offset validation, deterministic rubric score calculation, actual Worker encryption/DB integration, model provenance, production SSO/KMS or approved end-to-end tests. The original 56 deferred enterprise IDs remain `PENDING_SERVER` without a passed full oracle, and Stage11 stays `BLOCKED`. The permitted one generation was consumed. [Source evidence/runbook](09_stage11_single_inference_smoke.md).

## Offline full criterion/evidence/offset contract smoke harness — 2026-10-28

A new **opt-in** one-shot probe `scripts/verification/stage11_criterion_contract_smoke.py` prepares the exact Pydantic schema and existing strict `decode_criterion_response` from the real application against **only fixed synthetic Persian text**. A mock-network suite verifies exact quote/offset, score, refusal/tool-call rejection, incomplete generation, model mismatch, oversized/error responses, single GET and at most one POST, no request retries and private data redaction. **35 new synthetic criterion tests passed**, and the prior 35 tests passed in the same assistant execution: **70 passed in 0.14s** on Python 3.13.5. The default dry-run produced `DRY_RUN_NO_NETWORK` and no host inference. The real `structured_response.py` source was byte-for-byte verified against GitHub Git blob `3a1048628755a15f4ce083595d30eaac0b6f17bc`.

This is **local contract/tool verification**, not live enterprise acceptance. A subsequent real criterion request requires a fresh explicitly scoped approval because the prior one-shot permission was consumed; **no actual new server request was sent**. Source Stage 11 IDs `S07-S11-01`, `S07-S11-04`, `S11-AI-06` and `S08-S11-01` remain `PENDING_SERVER` until full original prerequisites and oracles. All 56 Stage11 deferred IDs remain `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. [Criterion smoke runbook](10_stage11_criterion_contract_smoke.md).

## Simorgh operator-reported direct CLI failure and regression fix — 2026-10-28

- Operator fast-forwarded to commit `20233d1`, ran the full offline Stage11 criterion + tiny-schema suites: **70 passed in 0.24s** on Simorgh.
- Immediately thereafter the **direct file-path CLI** dry-run failed during import: `ModuleNotFoundError: No module named 'scripts'`, before any network access. This failure is `FAIL_CLI_IMPORT_PATH`, **not** evidence against inference, vLLM or JSON compatibility.
- The Stage11 CLI script has been corrected with a narrowly scoped direct-entrypoint import-path bootstrap, leaving `src.*` production code unchanged. New subprocess regression tests check direct `python -I -B <script>` and module invocation without ambient PYTHONPATH; CI now executes both. **72 passed in 1.53s locally**, and both dry-run invocation forms return `DRY_RUN_NO_NETWORK`; no server access or GPU load occurred.
- **Fixed CLI on Simorgh remains `PENDING_USER_RETEST`**. No new real inference has been authorized or run; all **56 Stage11 enterprise tests remain `PENDING_SERVER`**, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. [Runbook](10_stage11_criterion_contract_smoke.md).

## Stage11 workflow parsing defect; local regression after fix — 2026-10-28

GitHub Actions on source SHA `5927429e754f48dd228238f93da74a85d1d51859` reported 3 immediate workflow failures with zero jobs: `40696351811` (criterion), `40696353688` (synthetic smoke), and `40696349866` (preflight). The common `--only-binary=:all:` command in a single-line YAML `run:` value failed parsing; local `yaml.safe_load` reproduced the invalid mapping-value exception. **No GitHub runner or inference test started in these workflows.**

All three YAML files now use a `run: |` block with the same pinned pip command; three new YAML validation test instances check parsed jobs, read-only permissions and absence of authorized-generation flags. The local assistant environment ran **75 passed in 2.08s**, and all three workflow files parsed. **GitHub Actions run outcomes after the fix remain pending**; no result is labeled PASS prematurely. Stage11 `BLOCKED`; 56 enterprise tests `PENDING_SERVER`.

## Verified GitHub Actions success after Stage11 YAML/import fixes — 2026-10-28

On main SHA `82595099e3ea67023b61e424542da16748403e75`, the following three workflows **completed successfully**, with actual job-step evidence rather than mere YAML parsing: criterion-contract `40696993930` (including direct isolated and module CLI dry-runs), read-only host/container preflight `40696993921`, and synthetic mock HTTP smoke `40696993968`. The preceding run failures on `5927429` had **zero jobs** and were confirmed invalid YAML, not failing model tests. After correction, local assistant-host suite also returned **75 passed in 1.75s** and both entry points returned `DRY_RUN_NO_NETWORK`.

The user's Simorgh **70 passed** result (on SHA `20233d1`) remains valid for that revision; the direct script import error there was fixed in later commits. A post-fix user-server CLI dry-run has **not** been observed yet: `PENDING_USER_RETEST`. No new inference or protected-data processing was executed by assistant. All **56 mandatory Stage11 enterprise tests remain `PENDING_SERVER`**, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## Simorgh verified final direct-CLI regression retest — 2026-10-31

User-reported Simorgh execution after fast-forwarding to source `f001794`:
- The exact offline Stage11 criterion/synthetic smoke suite returned **75 passed in 0.62s**.
- Direct invocation of `scripts/verification/stage11_criterion_contract_smoke.py` returned status `DRY_RUN_NO_NETWORK` and `stage11_gate=BLOCKED`, plus `http_status=null`, `synthetic_only=true`, `max_inference_requests=1`, `retries=0`, `model_id_logged=false`, `model_output_logged=false`; no traceback or import error was reported.
- This closes the **CLI invocation/import defect** on the target Simorgh host (`PASS_OPERATOR_REPORTED_DIRECT_CLI_REGRESSION`). The dry-run is **strictly network-free**, so there was **no new model inference, criterion-scoring evidence, GPU test or enterprise deployment**.

The prior single tiny-schema real-model completion remains independently recorded as an auxiliary PASS. This **offline** retest does not advance any of the original 56 mandatory enterprise acceptance tests to PASS; all are still `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. [Runbook](10_stage11_criterion_contract_smoke.md).

## Stage11 B11-06 encrypted-source Worker integration code and actual CI — 2026-10-31

Source `e63b2ca42688ff5a3629579b6e5e586555ad5f62` adds an injectable, scoped `ProtectedEvaluationExecutor` for existing `EvaluationWorkerService` and minimal encrypted-source/Rubric read path. It validates existing authentication/worker/LLM/egress settings, exact key ID, Rubric integrity, grounded Unicode evidence offsets, encrypts per-criterion details and leaves the official overall score **NULL**. The actual provider instance's client lifecycle now closes correctly. No schema migration, new external service, real model download or shared Simorgh setting change.

**Tests executed in GitHub Actions:** [Stage10 isolated PostgreSQL E2E run 41178699423](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41178699423) completed **SUCCESS**, including full suite **374 passed in 4.89s**; new protected Worker E2E used real PostgreSQL migration, signed synthetic HTTP, actual AES-GCM encryption/decryption, fenced Worker result persistence, authorized report and cross-org denial, with a **synthetic engine in place of an LLM**. [Stage08 run 41178699459](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41178699459) **SUCCESS**, 359 passed/8 skipped in 2.64s. Stage05 `41178699356`, Stage06 `41178699330`, Stage09 `41178699354` all **SUCCESS**. No real on-prem inference was performed by this change.

**Classification:** `PASS_CODE_AND_ISOLATED_SYNTHETIC_E2E`; `PENDING_SERVER_REAL_AI_AND_ENTERPRISE_IDENTITY`. Staging/Production Host and DB guard still reject direct use without approved wiring. The original 56 mandatory enterprise acceptance test IDs remain `PENDING_SERVER`, Stage11 `BLOCKED`. See [full evidence and commands](12_stage11_protected_worker_integration.md).

## Simorgh — protected Worker suites passed in server Python runtime — 2026-10-31

The operator provided terminal evidence of a fast-forward to `c8f10bac82b00d8e124502cd5b111f453b0f2913`. In the actual Simorgh checkout, `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_protected_worker.py tests/test_stage09_worker.py` completed **36 passed in 0.87s** (no failures shown). This is a user-reported real test run on the host and confirms the new encrypted-source Worker **offline synthetic/negative tests can run there**. It does not contact vLLM or require a PostgreSQL E2E database fixture.

**Distinct evidence:** public GitHub CI previously passed real ephemeral-PostgreSQL E2E with a synthetic engine (374 tests), which is not a test on Simorgh's enterprise database. The present 36 host-side passes are not 36 of the 56 mandatory enterprise acceptance IDs. No new vLLM inference, No-Egress audit or secure Staging/Production deployment has occurred. [Runbook](12_stage11_protected_worker_integration.md). Gate remains `Stage11=BLOCKED`, 56 `PENDING_SERVER`, `Stage12=NOT_STARTED`.

## Live on-prem full CriterionInference one-shot result — 2026-10-31

User-provided Simorgh transcript: exactly one approved active invocation of `scripts/verification/stage11_criterion_contract_smoke.py --port 8000 --execute-approved`; reported HTTP **200**, elapsed **6047 ms**, and `CRITERION_CONTRACT_UNVERIFIED` (client summary with no model ID or generated source/output logged). This is **FAIL / UNVERIFIED on auxiliary full-criterion smoke**, not a passing AI contract. The exact root cause is **undetermined** because the old script discarded individual parser/format/offset/abstention failure categories. The previously passed **simple one-field structured smoke** is not contradicted, but it is strictly narrower.

A targeted offline instrumentation patch in `1758390` now emits only static `failure_class` plus safe token counts for any **later authorized** error. [Criterion-contract CI 41181109595](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41181109595) **SUCCESS: 90 passed in 0.61s**, with mocked HTTP tests and network-free CLI checks. Neither code revision nor the passing mocks constitute an additional real model call. **The current one-shot authorization is consumed.** No 56 enterprise acceptance IDs have passed; all stay `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## Simorgh diagnostic tool pull and offline regressions — 2026-10-31

**User-reported real host commands:** GitHub `git pull --ff-only origin main` first failed with `Could not resolve host: github.com`; offline tests on old code still passed (75) and default CLI produced `DRY_RUN_NO_NETWORK`. A later retry **succeeded** with fast-forward `c8f10ba..63fb8e3`; `git rev-parse --short HEAD` output `63fb8e3`. On this updated checkout, `tests/test_stage11_criterion_contract_smoke.py` + `tests/test_stage11_synthetic_inference_smoke.py` completed **90 passed in 0.67s**. Thus the fixed diagnostic code is deployed to the actual Simorgh Python environment and its tests run successfully there.

The earlier diagnostic-less *live* `CRITERION_CONTRACT_UNVERIFIED` at HTTP 200/6047 ms remains **UNVERIFIED**, not retroactively classified or made PASS. No live inference was run in the latest transcript. The `git status --short` output preceding the pull showed unknown untracked nested `text-evaluation-service/`; **no deletion, forced reset or cleaning is authorized**. Stage11's original 56 mandatory items remain `PENDING_SERVER`; Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.

## Second live criterion request revealed strict quote/offset mismatch — 2026-10-31

User-reported Simorgh result: one synthetic `CriterionInference` request, HTTP **200**, `6010 ms`, `prompt_tokens=166`, `completion_tokens=113`, `total_tokens=279`, `retries=0`, `failure_class=QUOTE_OFFSET_MISMATCH`. This confirms response schema/expected-code parsing reached original source quote/offset matching and **failed** the exact-match oracle. The redacted summary cannot tell whether the quote was fabricated/not verbatim or simply assigned incorrect offsets. It does not evidence a 320-token completion truncation, model quality or actual enterprise E2E.

Targeted parser/prompt correction `fd072f1e18c866479c6462b0a026d1dbe660969e` retains exact matching, distinguishes `QUOTE_NOT_FOUND_IN_SOURCE` from `QUOTE_OFFSET_INCORRECT` for any future specifically authorized test, and describes half-open Unicode codepoint boundaries in both synthetic and actual internal Provider prompts. `PROMPT_VERSION` now `stage08-prompt-candidate-0.2`. No silent evidence relocation or score publication. GitHub CI success: criterion offline `41182886694` **91 passed**, Stage07 `41182886707` **53 passed**, Stage08 `41182886739` **37 passed** and full non-DB **376 passed/8 skipped**, Stage10 PostgreSQL `41182886734` full suite **391 passed**, plus Stage05/06/09 jobs successful. No extra inference or secret modification was done by the assistant.

**Classification:** `CODE_FIX_OFFLINE_PASSED / SECOND_REAL_CRITERION_SMOKE_FAILED`. All 56 original real Stage11 gate IDs remain `PENDING_SERVER`; Stage11 `BLOCKED`, Stage12 `NOT_STARTED`. [Evidence and exact offline test commands](10_stage11_criterion_contract_smoke.md).

## Simorgh post-correction runtime verification — 2026-10-31

After a successful fast-forward pull from `63fb8e3` to `a5fd771`, the operator reported **144 passed in 1.47s** from the three offline Stage11 criterion/smoke and Stage07 local LLM provider test modules. The default criterion script returned `DRY_RUN_NO_NETWORK`, `http_status=null`, `retries=0` and `stage11_gate=BLOCKED` on Simorgh. This host evidence confirms that updated quote/offset diagnostics and prompts are installed and tested with mocks/fixtures; it **does not** prove that real model inference now produces matching evidence. The last actual model result remains `QUOTE_OFFSET_MISMATCH`; re-inference requires a new narrowly scoped operational approval. The 56 original enterprise acceptance test IDs remain `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.
