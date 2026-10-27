# Stage 04 — Local Security Validation and Acceptance Evidence

Date: 2026-10-24. GitHub baseline: `4e14c2db36dcd7ac771c3ee554367fd9e3a34b88`, `main`, public repository, verified using GitHub connector. Environment: isolated Python 3.13.5 sandbox, no access to corporate network, no real data or credentials. Direct package versions: FastAPI 0.128.2, Pydantic 2.13.5, PyYAML 6.0.3, Uvicorn 0.48.0; test: pytest 9.0.2, httpx 0.28.1. Python >=3.10 should be verified in supported corporate environment; actual interpreter target not organization-approved (`OD-13 OPEN`).

## Implemented local controls

- Real FastAPI startup/application factory; default only static liveness and readiness; discovery/wiring for future controllers, no real business route or DB/model/worker. Router is convention-discovered and DI scans `infrastructure`, `core`, `application`, except excluded directories, with fail-closed import errors and a bootstrap guard. DI singleton locking and cycle detection.
- Fail-closed YAML configuration, development/staging/production separation, strict schema, no external-allowed flag or non-loopback bind; env-only fake secret references. Actual Vault service is **not invented** while `OD-08 OPEN`.
- Metadata-only log formatter (untrusted free-text and exception ignored), correlation IDs, error status normalization, disabled docs and programmatic access logs (`python -m src.host.app` only); clean lifespan shutdown.
- Local role/scope/assignment authorization primitive, private-literal endpoint validation, no runtime HTTP/LLM client or model auto-download.

## Executed checks (observed)

| Check | Command | Result | Scope |
|---|---|---|---|
| Stage 04 unit/security/integration smoke | `PYTHONPATH=. python -m pytest -q tests/test_foundation.py` | `26 PASSED, 0 FAILED, 0 SKIPPED` | local synthetic only |
| Real Uvicorn loopback smoke | `PYTHONPATH=. python -m src.host.app`, local Python urllib GET `/health/live` and `/health/ready`, then SIGTERM | PASS: both HTTP 200; APP_START/APP_STOP observed | isolated local only |
| Python syntax | `PYTHONPATH=. python -m compileall -q src tests scripts` | `PASS` | local Python 3.13.5 |
| Static safety/source constraints | `python scripts/verification/check_stage04_safety.py` | `PASS: 9 runtime source files; dependency pins; credential patterns; ignored secrets` | AST/runtime source; not whole-repo DLP |
| Installed pinned versions | `importlib.metadata.version(...)` | `MATCH direct pins` | current sandbox, not clean dependency resolution |
| Environment-wide dependency check | `python -m pip check` | `FAIL (unrelated environment package moviepy requires pillow<12; installed pillow 12.3)` | shared host packages; no Stage04 package shown at fault |
| Original Stage 02/03 regression scripts | `NOT_RUN` | `NOT_RUN: GitHub files were inspected remotely but not present in sandbox runtime` | repeat in a real full clone; not PASS |
| Full transitive SBOM, vulnerability and license approval | `NOT_RUN` | `NOT_RUN: offline vulnerability database, approved wheelhouse and lock/hash manifest unavailable` | **local supply-chain gate outstanding** |
| Corporate SSO/Vault/mTLS/firewall/no-egress/model/restore/load | `DEFERRED_TO_STAGE_11` | not run | see ledger |

The earlier DI test initially failed due to inherited `object.__init__(*args, **kwargs)` being treated as injection parameters. The resolver now skips variadic arguments; tests rerun 26/26 PASS. A local cyclic self-annotation issue was fixed by supplying the decorated class to localns; rerun PASS. No tests are claimed successful before rerun.

## Gate evaluation

| Acceptance item | Local verdict | Evidence / remaining risk |
|---|---|---|
| Threat modeling and trust boundaries | PASS_DOCUMENTED | `docs/security/01_threat_model.md` |
| Candidate access matrix + local denial policy | PASS_LOCAL / ORG_APPROVAL_OPEN | Policy tests in 26-test suite, `OD-07` not decided |
| Config, DI, bootstrap, discoverable WebService | PASS_LOCAL | Discovery, singleton, config and startup tests; **only synthetic discovery fixture; no actual product controller** until Stage 10 |
| Import/startup/shutdown/health/error sanitization | PASS_LOCAL | TestClient smoke, static liveness/readiness and all sanitized errors |
| Sensitive logging/secret handling local | PASS_LOCAL | Synthetic marker and redacted config/exception tests; external gateway logs unverified |
| Network/topology/secrets deployment design | PASS_DOCUMENTED / NOT_DEPLOYED | proposed topology and port matrix, OD-08/13 OPEN |
| Outbound endpoint and auto-download prevention | PASS_LOCAL_STATIC | no external runtime client; future Stage 07 re-evaluation; real firewall `DEFERRED_TO_STAGE_11` |
| Dependency and supply-chain review | **PARTIAL / NOT_RUN full SCA** | versions pinned and source scanned; no complete SBOM/license/vulnerability scan or offline wheelhouse |
| Original regression verification | **NOT_RUN** | complete checkout unavailable in runner; must rerun |
| Real internal-server-only tests | `DEFERRED_TO_STAGE_11` | detailed test ledger |
| No unmitigated Critical/High local security defect | NOT_PROVEN_AS_ABSOLUTE | No evident local exploit, but full dependency security check outstanding |

**Stage status until missing local gates are closed: `IN_PROGRESS`**, not `DONE`. The absence of organizational server alone is *not* a blocker (D-017); unresolved **local** regression and supply-chain checks are not misclassified as server-dependent. Never treat this foundation as a production deployment approval. Stage 05 is not authorized by this document.


## Independent user-local Windows verification — 2026-10-24

**Evidence source:** user-provided PowerShell console transcript, not commands executed by the assistant. Working copy was fast-forwarded from `e9d6f1e` to `ce2d389` on `main`. A fresh Python **3.12** virtual environment installed `requirements-dev.txt` successfully, including all exact direct pins. Some transient PyPI read-timeout retries resolved without aborting installation.

| Verification | User-local command | Observed result |
|---|---|---|
| Stage 04 tests | `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_foundation.py` | **26 passed, 0 failed, 1 DeprecationWarning** (Starlette TestClient imports deprecated AnyIO alias) |
| Syntax | `.\\.venv\\Scripts\\python.exe -m compileall -q src tests scripts` | **PASS** (zero exit/errors printed) |
| Safety/static | `.\\.venv\\Scripts\\python.exe scripts/verification/check_stage04_safety.py` | **PASS**; 9 runtime files, dependency pins, credential patterns, ignored secrets |
| Dependency consistency | `.\\.venv\\Scripts\\python.exe -m pip check` | **PASS:** `No broken requirements found.` (consistency only, **not** a CVE/license audit) |
| Stage 02 documentation checks | `.\\.venv\\Scripts\\python.exe scripts/verification/check_stage02_docs.py` | **19/19 PASS**, complete Git tree showed 40 entries |
| Stage 02 regression suite | `.\\.venv\\Scripts\\python.exe scripts/verification/test_check_stage02_docs.py` | **12/12 PASS** |
| Stage 03 regression suite | `.\\.venv\\Scripts\\python.exe scripts/benchmark/test_validate_stage03_outputs.py` | **38/38 PASS** |
| Windows Uvicorn bound to configured port | `.\\.venv\\Scripts\\python.exe -m src.host.app` | **FAIL to bind** at `127.0.0.1:8000`, `WinError 10048`; `APP_START`, then `APP_STOP` logged; port already in use by an unidentified local process. **No Windows HTTP health endpoint check was performed**. |
| Clean working-tree check | `git status --short` | **NOT_RUN/NOT_PROVIDED** in this transcript |

The port binding error is an environment resource collision, not evidence of a DI import/startup failure. On this checkout, `src/host/res/appsettings.development.yaml` configures port `8000`. Safe non-destructive alternate smoke command:

```powershell
.\\.venv\\Scripts\\python.exe -m uvicorn src.host.app:app --host 127.0.0.1 --port 8001 --no-access-log
# In a separate PowerShell:
Invoke-RestMethod http://127.0.0.1:8001/health/live
Invoke-RestMethod http://127.0.0.1:8001/health/ready
```

**Updated gate classification:** previous assistant-isolated `pip check` conflict and original Stage 02/03 `NOT_RUN` statements above remain accurate *for that earlier sandbox*; these checks have now **PASSED_USER_LOCAL** in an independent Windows Python 3.12 environment. The **full transitive vulnerability/SBOM/license/artifact provenance audit remains NOT_RUN**; no absence-of-vulnerabilities claim is made. Windows-specific standalone bind/HTTP smoke is `BLOCKED_PORT_IN_USE`, while the separate earlier assistant sandbox did verify both routes over HTTP 200. Stage 04 overall **IN_PROGRESS** until required local supply-chain gate evidence is available; real company-network controls remain `DEFERRED_TO_STAGE_11` per D-017.


## Development-only port collision correction — 2026-10-24

A second user-supplied Windows PowerShell transcript verified that `127.0.0.1:8000` was actively LISTENING in `com.docker.backend` (PID 5552). Direct `uvicorn --host 127.0.0.1 --port 8001 --no-access-log` also **failed** at bind with `WinError 10048`; no owning process for 8001 was identified. Both attempts reached ASGI startup and clean shutdown, but **neither Windows bind / HTTP request succeeded**. Do not stop Docker or infer the second port's owner without additional evidence.

**Scoped code correction:** development YAML (`src/host/res/appsettings.development.yaml`) now configures `server.port=18080`; the separate `appsettings.yaml` for staging/production remains **unchanged at 8000** pending platform approval. The existing development ConfigReader test includes an assertion for `18080`, and development topology documentation was aligned. This is a proposed local conflict avoidance, **not proof that 18080 is available on the user's Windows machine**. No live corporate environment, firewall, port forwarding or Docker configuration was changed.

Recommended verification from the repository root on updated `main`:

```powershell
Get-NetTCPConnection -LocalPort 18080 -State Listen -ErrorAction SilentlyContinue
.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_foundation.py
$env:TES_ENVIRONMENT = "development"
.\\.venv\\Scripts\\python.exe -m src.host.app
# In a second PowerShell after successful listening:
Invoke-RestMethod http://127.0.0.1:18080/health/live
Invoke-RestMethod http://127.0.0.1:18080/health/ready
```

**Verification status:** user-local port 18080 bind/HTTP **NOT_RUN** at time of change; regression after this YAML/assertion change **NOT_RUN** in the user's updated checkout; prior user-local 26/26 PASS refers to the old 8000 configuration. Existing Stage 04 overall **IN_PROGRESS** with supply-chain audit outstanding. If 18080 is also occupied or excluded, test OS-selected ephemeral port with `uvicorn src.host.app:app --host 127.0.0.1 --port 0 --no-access-log` and use the actually announced port before selecting another fixed default.


## Windows confirmation after development port adjustment — 2026-10-24

User-supplied PowerShell output, on a working copy fast-forwarded to `f391461` (`main`), with `TES_ENVIRONMENT=development` and `PYTHONPATH=.`:

- `Get-NetTCPConnection -LocalPort 18080 -State Listen -ErrorAction SilentlyContinue` returned **no listening entry before startup** (not itself a proof of port availability).
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_foundation.py` returned **26 passed, 0 failed, 1 non-fatal AnyIO/Starlette deprecation warning**, in **6.58s**, **after** changing development port and asserting `server.port == 18080`.
- `.\\.venv\\Scripts\\python.exe -m src.host.app` logged `APP_START`, `Application startup complete`, followed by `Uvicorn running on http://127.0.0.1:18080` (server process **8896**). No bind error was reported; local development **port bind/startup PASS_USER_LOCAL**.
- The user has **not yet supplied actual GET responses** for `/health/live` and `/health/ready` on port 18080; Windows HTTP health check remains **NOT_RUN / EVIDENCE_PENDING**. An earlier independent assistant sandbox did execute HTTP 200 on both routes but does not replace platform-specific Windows evidence.
- No clean working-tree command after pull was included. Corporate network, Vault, SSO, model, DB, firewall and Production still not tested/touched. Dependency/SBOM/vulnerability/license/provenance audit remains **NOT_RUN**.

**Gate conclusion: Stage 04 `IN_PROGRESS`.** The development port collision is resolved for actual Uvicorn startup on the user's machine, but network HTTP response verification and the outstanding local dependency supply-chain review cannot be marked PASS on this evidence alone. Stage 05 not started.

## User-local Windows live HTTP health verification — 2026-10-24

The user supplied actual PowerShell responses from the running development FastAPI/Uvicorn instance (previously verified bound on `127.0.0.1:18080`):

| Request (executed on user's Windows host) | Observed response | Result |
|---|---|---|
| `Invoke-RestMethod http://127.0.0.1:18080/health/live` | `status: alive` | **PASS_USER_LOCAL** |
| `Invoke-RestMethod http://127.0.0.1:18080/health/ready` | `status: ready` | **PASS_USER_LOCAL** |

The PowerShell commands completed without HTTP errors; their formatted output did not explicitly display numeric HTTP codes. The implemented routes use FastAPI's default successful response behavior, but numeric codes were not captured in the user's transcript. This evidence supplements the already reported **26/26 foundation pytest PASS after the port change** and **actual Windows Uvicorn bind/startup PASS**. Earlier `NOT_RUN` statements above remain historically accurate for the earlier snapshots and are now superseded **for these two Windows health requests** by this evidence.

**Meaning of readiness at Stage 04:** health checks assert ASGI application lifespan/bootstrap only. Database, inference model, worker, corporate identity/network dependencies are not implemented or exercised and are not implied to be healthy.

**Remaining acceptance work:** full transitive SBOM, artifact hash/provenance, license and vulnerability review **NOT_RUN**; internal organization network/security/inference tests **DEFERRED_TO_STAGE_11**. **Stage 04 = IN_PROGRESS** and **Stage 05 = NOT_STARTED**. Neither confidential data nor production systems were accessed.


## 2026-10-24 independent readiness review — NO_GO for Stage 05

The reviewed sources and architecture were cross-checked against both mandatory Project Source documents. The initial Stage 04 delivery is not sufficient for gate closure due to a **High-severity upstream Starlette issue** (CVE-2026-54283 in resolved Starlette 0.50.0, CVSS 7.5), default-deny permission scoping and unsafe preinstalled logging-handler configuration. Code and dependency pins were corrected in a targeted change. Added 11 new tests: **11 PASSED in assistant isolated Python 3.13 environment**; compile and updated static safety guard PASS on the revised subset. Unlike the earlier 26/26 Windows results, the **updated FastAPI 0.148.0 + Starlette 1.9.0 + httpx2 2.16.0 combination was NOT installed or exercised** in this offline assistant container. No new full-suite PASS claim is made. A local-only dependency inventory/installed RECORD digest verifier now exists, but vulnerability database audit, CycloneDX SBOM, signed provenance, upstream wheel checksum and organizational license clearance are STILL OPEN. Stage 11's infrastructure-dependent security tests are deferred under D-017, not passed. Stage 04 remains IN_PROGRESS; Stage 05 entry is NOT APPROVED. See [review report](04_stage04_independent_review.md) for findings, revised commands and acceptance criteria.

## Windows regression on updated dependency graph — 2026-10-24

User-provided PowerShell evidence from full repository, commit `34b8720`, Python 3.12 fresh `.venv-review`:

| Check | Observed | Verdict |
|---|---|---|
| `pip install -r requirements-dev.txt` | FastAPI 0.148.0, Starlette 1.9.0, httpx2 2.16.0 installed successfully | **PASS_USER_LOCAL** |
| `pip check` | No broken requirements found | **PASS_USER_LOCAL** |
| `python -m pytest -q tests` | **35 passed, 2 failed**, 11.83s | **FAIL_USER_LOCAL** before test fix |
| Failed tests | `test_app_does_not_initialize_external_resources` and `test_controller_auto_discovery_with_synthetic_fixture` crashed while directly reading `route.path` on FastAPI `_IncludedRouter` | **CAUSE_IDENTIFIED** |
| `compileall -q src tests scripts` | no errors | **PASS_USER_LOCAL** |
| Stage 04 static safety | `PASS: 9 runtime source files; dependency pins; patched Starlette baseline; credential patterns; ignored secrets` | **PASS_USER_LOCAL** |
| Stage 02 documentation check | **19/19 PASS** | **PASS_USER_LOCAL** |
| Stage 02 regression unittest | **12/12 PASS** | **PASS_USER_LOCAL** |
| Stage 03 benchmark validator tests | **38/38 PASS** | **PASS_USER_LOCAL** |
| Offline dependency metadata/RECORD inventory | **`PASS_INSTALLED_METADATA_ONLY: 27 components`** | **PASS_METADATA_ONLY**, vulnerability/license approval remains OPEN |
| Windows Uvicorn startup on 18080 | `WinError 10048`: port already in use by unidentified listener in this run | **BLOCKED_PORT_IN_USE**, not a runtime import/ASGI startup failure |

**Fix committed in this follow-up:** only two Stage 04 foundation tests now validate the public ASGI HTTP contract with FastAPI `TestClient`, avoiding dependency on a flat `app.routes` list. The first test checks the absent feature route (404) under a blocked outbound socket monkeypatch; the second verifies that a synthetic discovered feature controller responds on `/api/v1/fixture/probe` with HTTP 200 and expected JSON, including router prefixes. This is strictly a test compatibility fix; no production router, security policy, dependency pin, or application configuration changed.

**Post-fix verification boundary:** a representative nested-router `TestClient` smoke was executed in the assistant's isolated **older FastAPI** environment and passed, but **the complete 37-test suite on FastAPI 0.148.0/Starlette 1.9.0 has not been rerun since the change**; mark it `PENDING_USER_LOCAL`, **not PASS**. The earlier 35/37 results remain genuine pre-fix evidence. The independent source change was reviewed for scope, but user-local regression is required before Gate approval. To diagnose port occupation, inspect `Get-NetTCPConnection -LocalPort 18080 -State Listen` with process identity; stop only a known, user-controlled prior Uvicorn process, not Docker or arbitrary services. Otherwise use an OS-selected ephemeral port for smoke testing. No production operations authorized.

**Stage status `IN_PROGRESS`; Stage 05 entry remains `NOT_APPROVED`.** Full transitive vulnerability scanning, license clearance, trusted wheel hash/provenance and standard SBOM are still outstanding; company-network No-Egress/SSO/Vault tests remain deferred to Stage 11 per D-017.


## Post-fix user-local acceptance evidence — 2026-10-24

**User-supplied PowerShell transcript, complete project after commit `e16c5d6`, Windows Python 3.12 `.venv-review` with the upgraded dependency graph:**

| Check | Command / observation | Result |
|---|---|---|
| Latest checked-out main | `git pull --ff-only origin main` → `Already up to date` | **PASS_USER_LOCAL** |
| Complete foundation + security review tests | `.\\.venv-review\\Scripts\\python.exe -m pytest -q tests` → **37 passed in 10.21s** | **37/37 PASS_USER_LOCAL**, no failures; resolves prior 35/37 pre-fix run |
| Installed dependency consistency | `.\\.venv-review\\Scripts\\python.exe -m pip check` → `No broken requirements found` | **PASS_USER_LOCAL** (not SCA/CVE clearance) |
| Existing port owner | `Get-NetTCPConnection -LocalPort 18080 -State Listen`, PID 8896 `python` | **IDENTIFIED_PROCESS**, not terminated; exact command line not verified |
| Alternate port development ASGI smoke | `.\\.venv-review\\Scripts\\python.exe -m uvicorn src.host.app:app --host 127.0.0.1 --port 0 --no-access-log` | **PASS_USER_LOCAL** startup/listening on `127.0.0.1:50165`, process 13500, `APP_START` event present |
| GET `/health/live` + `/health/ready` on new temporary port | Not provided | **NOT_RUN_ON_50165**; prior port 18080 HTTP responses passed on older process |
| Vulnerability scan / standardized SBOM / approved licenses / upstream artifact wheel hash & provenance | Not provided | **NOT_RUN / GATE OPEN** (27 packages inventoried earlier as metadata only) |

The _two_ previous `_IncludedRouter` compatibility test failures are now verified fixed on the **new** FastAPI/Starlette version in the user-controlled local Windows environment. New temporary-port binding does not replace real HTTP smoke evidence on the same new interpreter. No data confidentiality, on-premise No-Egress or production readiness is implied by `ready` without DB/Worker/AI.

**Current Stage 04: `IN_PROGRESS`; Stage 05 entry `NOT_APPROVED`.** Only unverified supply-chain checks (and new-interpreter temporary-port endpoint smoke as a requested supplementary confirmation) remain on the local review ledger. All organization-specific server security cases remain deferred to Stage 11 under D-017. The transcript is evidence supplied by the user; the assistant did not execute Windows commands or access the user's machine.


## Final user-local upgraded-runtime health evidence — 2026-10-24

PowerShell on the user's Windows machine successfully executed `Invoke-RestMethod http://127.0.0.1:50165/health/live` → `status: alive` and `Invoke-RestMethod http://127.0.0.1:50165/health/ready` → `status: ready`, on the same ephemeral port previously confirmed running the new `.venv-review` FastAPI 0.148.0 / Starlette 1.9.0 Uvicorn instance. **Both HTTP endpoint smoke tests now PASS_USER_LOCAL** after the dependency upgrades. The previous `NOT_RUN_ON_50165` statement is historical and superseded. The separately observed `37/37 pytest PASS` and `pip check` PASS stand; these are user-executed results. This only verifies the application startup/health contract; DB, worker, model and approved security controls are not implemented/tested at this point. Supply-chain CVE/license/standard SBOM/upstream artifact provenance remains `NOT_RUN` and Stage 04 remains `IN_PROGRESS` / Stage 05 `NOT_APPROVED`.


## Stage 04 reproducible supply-chain evidence framework — 2026-10-24

Added [local supply-chain runbook](04_stage04_supply_chain_runbook.md), a Windows collector and offline fail-closed evidence comparison utility, with exact pinned separate audit-tool dependencies. Assistant isolated Python 3.13.5: **15/15 new synthetic tests PASS**, Python compile PASS; adversarial tests cover CVE data gaps/findings, CycloneDX 1.6 coverage and version, wheel hashing and ZIP structure, tamper detection, PyPI SHA mismatch, license reviews and missing evidence. **This is implementation/testing of the evidence mechanism, not a real security clearance.** The user-local Windows 3.12 37/37 and Uvicorn health evidence preceded these newly added tests and remains separate, not yet rerun on latest files. Container cannot contact PyPI, so `pip-audit`, wheel downloads/public wheel digests, generated Windows SBOM and human licensing checks **NOT_RUN**. Reverify Stage 04 only when these independent artifacts exist and pass explicit security review. No organization data/server/Secrets used. Stage 04 `IN_PROGRESS`; Stage 05 `NOT_STARTED`.


## Windows 52-test verification and audit script blocked by ExecutionPolicy — 2026-10-24

User-executed PowerShell evidence after fast-forward from `e16c5d6` to `684f486`: fresh Stage 04 supply-chain validator tests included in complete `.venv-review` run `python -m pytest -q tests` **52 PASSED, 0 FAILED, in 35.24s**. `run_stage04_supply_chain.ps1` was blocked by Windows PowerShell's `PSSecurityException` (scripts disabled) before execution. Therefore **actual CVE audit, CycloneDX, wheelhouse, public digests and license review remain NOT_RUN**, not failed Python tests or successful scans. The [runbook](04_stage04_supply_chain_runbook.md#windows-powershell-executionpolicy-preflight-2026-10-24) now includes a one-shot process-scoped `RemoteSigned` launch on authorized developer machines; no persistent policy changes, secrets or production resources touched. **Stage 04 remains IN_PROGRESS; Stage 05 NOT_STARTED / NOT_APPROVED.**


## 2026-10-24 — PowerShell native quote handling correction

User ran `Get-ExecutionPolicy -List` (all scopes `Undefined`) and a one-off `-ExecutionPolicy RemoteSigned` process. The collector actually began and `pip check` **PASS_USER_LOCAL**, but PowerShell quote handling stripped `"purelib"` inside `python -c` and Python raised `NameError: name 'purelib' is not defined`. Script terminated with **Target site-packages resolution FAILED** before CVE scanning/SBOM/wheel integrity/license review. The prior results directory `.stage04-evidence-20261024` was created before the error and must not be silently overwritten/deleted.

Stage 04 fix: Python evidence verifier offers a read-only `site-packages` CLI derived from `sysconfig.get_path("purelib")` of the actual target interpreter; PowerShell calls it without embedded quote escaping, validates the returned directory, and defers evidence-dir creation until preflight succeeds. **17/17 isolated synthetic/local CLI tests PASS_ASSISTANT_LOCAL**, plus compile PASS; full upgraded Windows test suite/collector on this fix **PENDING_USER_LOCAL**. No confidential text, network credential, or production configuration changed. Local supply-chain acceptance remains **NOT_RUN / IN_PROGRESS**, Stage 05 **NOT_APPROVED**.


## Windows Stage 04 supply-chain collector — package CDN timeout (2026-10-24)

User-local latest `main` after fast-forward to `359e6ea`: `review_stage04_supply_chain.py site-packages` **PASS_USER_LOCAL** (target interpreter correctly resolved); `pytest -q tests` **54/54 PASS in 12.40s**. One-off `RemoteSigned` evidence collector with `-VerifyPublicPyPIDigests` passed target `pip check`, printed `PASS_INSTALLED_METADATA_ONLY: 27 components`, and generated pinned closure/license template before attempting to install the separate audit tools. **Audit-tool installation FAILED due to HTTPS read timeout** downloading `chardet` from `files.pythonhosted.org` (pip default `read timeout=15`). No vulnerability scan, CycloneDX SBOM, downloaded closure wheel-hash/PyPI-digest verification or reviewed license decisions were produced. The evidence directory `.stage04-evidence-20261024-02` must be preserved and is explicitly incomplete.

Engineering mitigation: apply bounded `pip install/download --timeout 120 --retries 6` **within the Stage 04 collector only**; no global OS/network/pip changes and never ignore installer failures. New isolated supply-chain test module after applying the static regression (**18/18 PASS_ASSISTANT_LOCAL**); compile PASS. Full Windows suite and public scanner with this latest script **PENDING_USER_LOCAL**. Current Stage 04 = `IN_PROGRESS`; Stage 05 = `NOT_STARTED / NOT_APPROVED`; corporate server security checks = `DEFERRED_TO_STAGE_11`. See [runbook](04_stage04_supply_chain_runbook.md#windows-dependency-download-timeout-2026-10-24).


## Windows partial supply-chain evidence with advisory timeout — 2026-10-24

User ran current main `ff150cb` on Windows Python 3.12. **55/55 complete pytest PASS (22.71s)**, local `pip check` PASS and installed RECORD/license metadata inventory for **27 packages** PASS. Dedicated `pip-audit==2.10.1` and `cyclonedx-bom==7.5.0` tools installed successfully. `pip-audit` attempted public PyPI vulnerability queries but failed with a `requests.exceptions.ReadTimeout` after its separate default 15-second socket timeout. Its exit code 1 is **SCAN_ERROR / NO COMPLETE ADVISORY RESULT**, *not evidence of zero vulnerabilities and not a confirmed CVE finding*. The previous collector ambiguously logged the exit and continued.

Evidence collector continued independently: CycloneDX generation had no reported error; downloaded all **27 exact-version wheels**; `hash-wheels` and opt-in public PyPI SHA-256 comparisons each returned `PASS_LOCAL_EVIDENCE_GENERATED`. The run finished with a warning that Stage 04 remained OPEN; the actual JSON files were not attached to this user transcript and their full contents have not been independently inspected. `license-review.json` remains a **REVIEW_REQUIRED** template with no authorization; formal license review is OPEN. The local directory `.stage04-evidence-20261024-03` must be preserved.

Engineering fix: apply separate `pip-audit --timeout 120`, and require **complete name/version/vulnerability-data JSON coverage** via a new `audit-status` CLI before any collector may claim a completed scan; treat findings distinctly from a missing or incomplete report. Do not ignore failed scanner calls. **22/22 new isolated supply-chain tests PASS_ASSISTANT_LOCAL** plus Python compile, but the Windows suite and actual advisory re-query after this fix remain `PENDING_USER_LOCAL`. Reuse existing `-03` artifacts and rerun **only** advisory scan to a distinct `vulnerabilities-retry.json` without downloading wheels again; see [supply-chain runbook](04_stage04_supply_chain_runbook.md#advisory-scan-timeout-and-reuse-of-verified-local-evidence-2026-10-24).

**Stage 04 = IN_PROGRESS; Stage 05 = NOT_STARTED / NOT_APPROVED.** Independent CVE proof and reviewer-authorized licenses are missing. Corporate network/SSO/Vault/model tests remain `DEFERRED_TO_STAGE_11` under D-017; no company data was transmitted.


## User-local 59-test proof and alternate advisory route (2026-10-24)

User-supplied Windows Python 3.12 transcript after fast-forward to `229df23`: `pytest -q tests` **59/59 PASS in 26.88s**. `pip-audit --vulnerability-service pypi --timeout 120` failed with `requests.exceptions.ConnectionError` / `RemoteDisconnected` contacting the external PyPI advisory API; `pip-audit` exited 1 **without writing `vulnerabilities-retry.json`**. This is **FAILED_NETWORK (no complete CVE scan)**, not a zero-findings report. The earlier 27-package installed metadata, CycloneDX and wheel/official PyPI digest steps were user-reported successful, but the evidence JSON files themselves were not attached for inspection; License Review still `REVIEW_REQUIRED`. To avoid repeated failure against the same remote service, the Stage 04 collector explicitly accepts `pypi` or `osv` as a selected vulnerability advisory feed, records the chosen source and distinct filename, and prohibits silent fallback. Targeted OSV instructions preserve existing `-03` evidence without repeating the 27 wheel downloads. New Python regression tests are focused on the explicit choice, no silent automatic fallback, and report-source recording; **OSV network scan and updated Windows full suite remain PENDING_USER_LOCAL**. This is not a credential/network change or company-data transmission by the assistant. **Stage 04 IN_PROGRESS, Stage 05 NOT_APPROVED.**


## Verified OSV findings in Windows local venv — 2026-10-24

User PowerShell after fast-forward to `9ea0083`: `python -m pytest -q tests` **61/61 PASS in 30.29 seconds**. Targeted `pip-audit --vulnerability-service osv --timeout 120 --format json` completed and reported **14 known vulnerability advisory records in 2 packages**, exit **1**. The `review_stage04_supply_chain.py audit-status` returned **`AUDIT_COMPLETE_WITH_FINDINGS`**, process exit **0** for *report validation only*. This is a **complete positive vulnerability finding scan**: **SECURITY_GATE_FAILED_FINDINGS**, not a failed connection and not successful clearance. The JSON report contents and vulnerable package identifiers have not been provided. No dependency upgrades or CVE suppressions were made.

Added a no-network `audit-findings` report command to extract package/version/advisory IDs/aliases/fix versions safely, with exact installed-inventory matching; no secrets, descriptions, paths, remote network or unreviewed auto-upgrades. Assistant isolated Python 3.13.5: **28/28 relevant tests PASS**, compile PASS; new Windows full test suite and extraction PENDING_USER_LOCAL. Preserve OSV evidence at `.stage04-evidence-20261024-03`. Once the finding identities and actual supported fix releases are reviewed, change only approved Stage 04 dependencies, rerun and reconstruct all version-bound wheel/SBOM/scan evidence. Reviewed license decisions still `REVIEW_REQUIRED`. **Stage 04 = IN_PROGRESS, Stage 05 = NOT_STARTED / NOT_APPROVED**, server-only security checks `DEFERRED_TO_STAGE_11`.


## OSV 14-record / 7-unique remediation proposal and guard — 2026-10-24

User-local Python 3.12 `pytest -q tests` completed **65/65 PASS in 37.46s** at `114c659`. User-provided offline findings report validated `AUDIT_COMPLETE_WITH_FINDINGS` and identified **pip 25.0.1** (six distinct PYSEC advisories, duplicated 12 times; in bootstrap tool environment, **outside 27-package closure**) and **pytest 9.0.2** (one distinct PYSEC advisory, repeated twice; **development dependency in closure**). Latest fixed versions independently checked from the official PyPI and pytest release sources: `pytest==9.0.3` fixes CVE-2025-71176; `pip==26.2.2` is newer than every fix version reported for the six pip issues including CVE-2026-13346 (patched from 26.2.0).

Stage 04-only code remediation: new exact pytest 9.0.3 dev pin, static pin regression guard, `bootstrap-check` minimum patched pip version on both target reviewed venv and dedicated audit venv, and focused positive/negative regressions. The scanner **does not auto-modify either interpreter**. Assistant isolated Python 3.13.5 subset **37/37 new and related tests PASS** and `compileall` PASS; **NOT** a complete cloned-repository full suite, real Python 3.12 patched package resolution, or OSV reassessment. The previously saved 27 wheels and SBOM are stale once pytest is upgraded; the user must reinstall exact reviewed packages and regenerate the full advisory, CycloneDX, upstream-wheel-hash and license evidence under a fresh immutable directory before closure. [Exact commands](04_stage04_supply_chain_runbook.md#remediation-of-confirmed-osv-findings-in-pip-and-pytest--2026-10-24).

**Current Stage 04 `IN_PROGRESS`, OSV findings `REMEDIATION_COMMITTED_AWAITING_RESCAN`, patched-vEnv Windows tests `PENDING_USER_LOCAL`, license decisions `REVIEW_REQUIRED`, Stage 05 `NOT_APPROVED`.** Corporate security and artifact provenance remain `DEFERRED_TO_STAGE_11` per D-017.


## Stage 04 user-local post-fix attempt blocked by GitHub network (2026-10-24)

User execution log: `git pull --ff-only origin main` failed with connection error to `github.com:443`, so the local checkout remained **older than published fix commit `6f1c43b`**. Both disposable project/auditor virtualenv `pip` instances successfully upgraded **25.0.1 → 26.2.2**, while old `requirements-dev.txt` still requested `pytest==9.0.2` and therefore `pip install -r` left pytest vulnerable. CLI `bootstrap-check` was not present in stale local source, giving `invalid choice` twice. `pip check` PASS and **65/65 existing source tests PASS**; static guard PASS on old version, **not** verification of new Stage 04 remediation.

Collector with old code and `-VulnerabilityService osv` generated `.stage04-evidence-20261024-04` with **2 known vulnerability records across 1 package**, warning `Verified vulnerability findings`, so **OSV SECURITY_GATE_FAILED_FINDINGS**. The specific package in the newer scan is not shown directly in transcript; prior findings and unpatched pytest 9.0.2 suggest it. Wheel count 27 and generated SHA evidence are for the **old closure** and must not be presented as patched-version evidence. User should preserve `-04` and wait for successful GitHub pull, then install `pytest==9.0.3` from new pin, test both `bootstrap-check`s and rerun full OSV/SBOM/Wheel validation under a fresh unused `-05`. Unreviewed package licenses remain OPEN. **Stage 04 stays IN_PROGRESS, Stage 05 NOT_STARTED, no real service/environment security Gate passed.**


## Latest verified 70/70 and OSV-clean scan, interrupted wheelhouse acquisition — 2026-10-24

User-local Windows after `main` updated to `5be8039`: `pytest==9.0.3` installed replacing 9.0.2, `pip==26.2.2` in both venvs; `bootstrap-check` PASS in both, `pip check` PASS, **70/70 suite PASS in 57.29s**. The user's `.stage04-evidence-20261024-05` collector reported `No known vulnerabilities found` from OSV and generated a CycloneDX SBOM, after verifying 27 installed distribution RECORD entries. **OSV scan = USER_LOCAL_NO_REPORTED_FINDINGS**; this is only the selected feed/snapshot, not complete security clearance. `pip download` then failed for `starlette==1.9.0` with **INDEX_NO_CANDIDATE / NO_MATCHING_DISTRIBUTION**, before complete wheel checksum and public PyPI digest reporting. Independent PyPI page establishes Starlette 1.9.0 supports Python >=3.11 and its universal Wheel SHA256 is `fd3f159936e882d06c1108f84688f7cda2cf85fc6a592a50edbd175e882c2ddc`. Actual file in earlier `-04` wheelhouse must be SHA256 matched before reuse. Runbook has a process-scoped `PIP_FIND_LINKS` + fresh `-06` evidence procedure preserving incomplete `-05` and historic `-04`. **No modified product code and no repeated assistant execution of Windows scanner**. Current Stage04 `IN_PROGRESS`: final package-hash/PyPI digest and qualified License Review `NOT_APPROVED`; Stage05 `NOT_STARTED`. Corporate tests remain `DEFERRED_TO_STAGE_11`.


## 2026-10-24 — Complete 27-wheel collector succeeded on patched Python 3.12 Windows

User's submitted PowerShell transcript confirms `git pull` to `b3f1e63` succeeded; original `-04` Starlette wheel SHA256 matched externally referenced official PyPI SHA256 `fd3f159936e882d06c1108f84688f7cda2cf85fc6a592a50edbd175e882c2ddc`; prior immutable evidence was preserved and only process-local `PIP_FIND_LINKS` used. New `.stage04-evidence-20261024-06` collector ran through all steps without error: both patched-pip `bootstrap-check` PASS; `pip check` PASS; installed dependency inventory 27 components with installed RECORD integrity; `pip-audit==2.10.1` against OSV reported `No known vulnerabilities found` (scan exit 0); CycloneDX 1.6 SBOM generation completed; all **27 pinned Wheel downloads** including `pytest==9.0.3` succeeded; both local Wheel hashes and public PyPI release metadata digests returned `PASS_LOCAL_EVIDENCE_GENERATED`; final `run-summary.json` generated and user-supplied `audit-status` returned `AUDIT_COMPLETE_NO_REPORTED_FINDINGS` (exit 0). Earlier **70/70 pytest PASS** was run on patched local package closure and remains valid user-local evidence; tests were not rerun in this latest collector invocation.

**Precision of proof:** the user supplied complete tool output and run-summary text, but **not the underlying JSON evidence or Wheel bytes**; label these **PASS_USER_LOCAL_REPORTED**, not independent assistant artifact verification. The public OSV feed can miss undisclosed/unindexed vulnerabilities, and TLS SHA256 matching does not authenticate a publisher's signature or enterprise artifact provenance. The generated `license-review.json` is still `REVIEW_REQUIRED` for all 27 components; qualified per-component SPDX expression, license text/obligation review, evidence reference and reviewer approval are **NOT_DONE**. See [runbook](04_stage04_supply_chain_runbook.md#license-metadata-triage-after-successful-06-collector--2026-10-24). Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED`; real corporate security checks `DEFERRED_TO_STAGE_11` per D-017.


## 27-license metadata triage evidence — 2026-10-25

User local Windows PowerShell format/count check on `-06/license-review.json`: **27 entries** and `stage04-license-review-v1` valid; public-only projection supplied to assistant. Metadata distribution: MIT=13, BSD-3-Clause=8, BSD generic classifier=1, BSD-2-Clause=1, Apache-2.0=1, Apache-2.0 OR BSD-2-Clause=1, MPL-2.0=1, PSF-2.0=1. No license metadata blank. Independent web review corroborated **five targeted version-specific declared licenses/descriptions** (certifi, packaging, colorama, typing-extensions, opentelemetry-api), but **none of the 27 exact wheel LICENSE/NOTICE texts or company license approvals was supplied**. Generic colorama classifier is not itself a valid specific SPDX choice until exact release license checked. No `APPROVED`, `reviewed_by` or legal sign-off was manufactured. [Matrix](04_stage04_license_triage.md). License review gate **OPEN**; Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED`.


## 2026-10-25 — Verified license-file presence from 27 exact Wheels

User provided the successful ZipArchive path listing for all **27/27** downloaded `-06/wheelhouse` Wheels; **29 paths** match LICENSE (three in `packaging 26.3`), and each Wheel has an explicit `.dist-info/licenses/LICENSE*` record, including certifi, colorama and typing-extensions. **PASS_USER_LOCAL_REPORTED only for entry presence**. No actual contents, bytes/entry SHA, Notice wording, policy decision, independent ZIP inspection or qualified legal reviewer approval were provided; all remain `REVIEW_REQUIRED`. This does **not** close Stage04 or approve Stage05. [Triaged details](04_stage04_license_triage.md#exact-27-wheel-license-entry-presence-inspection--2026-10-25).


## 2026-10-25 — Pasted full texts of 29 wheel license files

User supplied the actual displayed text and SHA256/byte-length metadata for 29 LICENSE entries belonging to all 27 `-06` versioned Wheels. Preliminary human-readable inspection found **no apparent inconsistency with asserted license families**, including colorama's 3-clause BSD text, packaging's explicitly dual `OR` permission, Apache-2.0 full terms, MIT/BSD notices, MPL notice in certifi and PSF 2 plus older Python license history for typing-extensions. A syntax/count validation of all **29 claimed SHA-256 strings** was performed, but the original Wheel/ZIP bytes remain on the user's machine and were **NOT inspected or independently compared**. Full license/notice distribution/compliance and qualified signoff still `REVIEW_REQUIRED`; the local text review is `TEXT_TO_METADATA_PRELIMINARY_CONSISTENT_27_OF_27`, not a legal approval. [SHA ledger](04_stage04_license_triage.md#full-text-license-analysis-from-user-supplied-evidence--2026-10-25). Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED`.


## 2026-10-26 — Ubuntu isolated venv dependency bootstrap BLOCKED by public package DNS

**Evidence source:** user-submitted SSH shell log on the shared Ubuntu 24.04 host. The checked-out Git tree was clean on `main` commit `07f47f1` before execution. A `bash` sequence with `set -Eeuo pipefail` entered `/srv/projects/text-evaluation-service`, created `.venv-review` using `python3 -m venv`, and attempted `.venv-review/bin/python -m pip install --disable-pip-version-check "pip==26.2.2"`. The installer repeatedly reported `[Errno -3] Temporary failure in name resolution` for `files.pythonhosted.org` and terminated with a nonzero download error. The output shows `pip` did execute inside the new venv, but the requested upgrade did **not** complete.

**Test states:** `VENv_CREATION=USER_LOCAL_REPORTED`; `PIP_26_2_2_INSTALL=FAILED_DNS`; `REQUIREMENTS_DEV_INSTALL=NOT_RUN`; `BOOTSTRAP_SECURITY_CHECK=NOT_RUN`; `PIP_CHECK=NOT_RUN`; `PYTEST_UBUNTU=NOT_RUN_BLOCKED_BY_DEPENDENCY_SETUP`. The earlier `70/70` result remains solely Windows user-local evidence; **no Ubuntu regression PASS** is claimed. The visually mangled pasted shell text also merits using short commands, inspecting exit statuses and not assuming unseen commands executed.

**Security boundary:** An observed public-package DNS failure is **not** proof of an intentional firewall No-Egress rule, corporate Air-Gap certification or model egress control. Do **not** replace the configured resolver with a public DNS, edit network/firewall/proxy, disable TLS checking, join the privileged docker group, restart shared services or treat old Windows binary Wheels (`win_amd64`) as Linux install media. Obtain operator clarity whether package internet egress is authorized. If not, procure **version-pinned, scanned and hash-verified Linux/Python 3.12-compatible wheels** using an approved external staging machine or authorized package mirror and transfer under an approved offline import procedure. Preserve prior `-06` Windows evidence unchanged; do not reuse its Wheel hashes as Linux artifact hashes.

**Next non-mutating diagnostics on server:** show `python --version`/`pip --version` from existing `.venv-review`, `git status --short`, resolver target/config with secrets redacted, and only the **presence** (not values) of proxy/PIP index environment variables. DNS resolution to an external public domain should occur only if external network tests are approved. Stage 04 `IN_PROGRESS`; Stage 05 `NOT_STARTED`; all company-specific Stage 11 acceptance tests retain `DEFERRED_TO_STAGE_11`.


## 2026-10-26 — Read-only diagnosis of Ubuntu Python venv and resolver stub

User-submitted read-only commands confirmed `/srv/projects/text-evaluation-service/.venv-review/bin/python` reports **Python 3.12.3** and its installed `pip` reports **24.0** (the pinned `pip==26.2.2` bootstrap still **FAILED_DNS**). `git status --short` was empty. `/etc/resolv.conf` resolves to `/run/systemd/resolve/stub-resolv.conf` with **nameserver `127.0.0.53`**, which is a normal local systemd-resolved DNS stub. This **does not prove that systemd-resolved is active, that upstream DNS servers are configured or reachable, that the public PyPI host resolves, or that Internet egress is permitted or blocked by policy**. No `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, corresponding lowercase variants, `PIP_INDEX_URL` or `PIP_EXTRA_INDEX_URL` values were set in the displayed environment; **only presence**, not proxy/index values or secrets, was inspected.

**Next authorized-safe diagnosis:** read-only `systemctl is-active systemd-resolved`, `resolvectl status --no-pager`, `ip route`, with host DNS/internal network addresses redacted before external sharing. Only if the server owner explicitly allows public DNS/network lookups, perform `resolvectl query files.pythonhosted.org` and then any approved index connectivity test. **No resolver edits, public DNS substitution, TLS-disabling, firewall changes, restart, shared-project changes or unsafe pip retries**. Linux dependency installation and pytest remain **NOT_RUN/BLOCKED**; Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED`, Stage11 real network acceptance `DEFERRED_TO_STAGE_11`.


## 2026-10-26 — Resolved DNS upstream inventory from shared Ubuntu host (read-only)

User submitted read-only `systemctl is-active systemd-resolved`, `resolvectl status --no-pager` and `ip route show default` outputs. `systemd-resolved` reported **active**; `/etc/resolv.conf` remained the standard stub setup; physical interface `ens33` had DNS scope and an upstream DNS list containing **public resolver 8.8.8.8 as the current selection** plus **two private RFC1918 resolver addresses**. A **private IPv4 default gateway** via `ens33` was present. These are **configuration inventory observations**, not proof that any configured resolver is reachable, that `files.pythonhosted.org` resolves, or that outbound DNS/TCP/HTTPS to PyPI is allowed. A default route and running resolver alone cannot explain the exact reason for the observed earlier `[Errno -3]` name resolution failure. The selected public resolver could be unreachable or disallowed on a private multi-project host; this is a hypothesis, **not a verified finding**.

**Operator-safe next steps:** first determine whether external DNS and package HTTPS checks are permitted by the host/network owner. **Only if allowed**, run bounded `resolvectl query files.pythonhosted.org` and `resolvectl query pypi.org`, recording their exit statuses, then a separate bounded approved HTTPS connectivity test if DNS succeeds. If public package access is prohibited, obtain an approved offline Linux/Python 3.12 Wheelhouse instead. **No** changes to DNS priority/server addresses, `/etc/resolv.conf`, netplan, firewall, proxies, public-network access rules, Docker networks or shared containers without explicit operator approval. Do not disable TLS verification to install packages. Existing venv pip remains 24.0; pinned pip download `FAILED_DNS`; dependency setup and Linux regression tests `NOT_RUN/BLOCKED`. This observation is **not** a No-Egress security verification. Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED` and D-017 real company server tests `DEFERRED_TO_STAGE_11`.


## 2026-10-26 — Public package DNS lookup differential on Ubuntu (user-observed)

On the same shared Ubuntu 24.04 host where pip bootstrap had failed to resolve `files.pythonhosted.org`, the user ran direct read-only `resolvectl query` checks:
- `resolvectl query files.pythonhosted.org` returned **`resolve call failed: Connection timed out`**, with no DNS address result.
- `resolvectl query pypi.org` succeeded, returning **both IPv4 and IPv6 results** via `ens33` from network DNS, in approximately **5.2987 seconds**. The query result was not cryptographically authenticated (`Data is authenticated: no`).

**Conclusion and scope:** DNS failure is **hostname-specific in these observations**, not proof that all name resolution is down. This provides a plausible immediate reason that pip cannot retrieve downloads from the public `files.pythonhosted.org` CDN. It **does NOT demonstrate** HTTPS egress reachability, establish an intentional No-Egress control, certify any dependency, or prove DNS poisoning/filtering; alternate causes include transient upstream latency or broken record-family resolution. There is no evidence here that the administrator has approved public package downloads. The configured upstream list (currently selected public resolver and two private resolvers) is evidence of configuration, not of specific resolver responsibility for each answer.

**Next bounded and non-mutating DNS-only diagnostic, conditional on the host policy allowing public lookups:** run `timeout 15s resolvectl query --type=A files.pythonhosted.org` and independently `timeout 15s resolvectl query --type=AAAA files.pythonhosted.org`, recording the exit statuses. If DNS succeeds, request explicit approval before attempting public HTTPS/package downloads. If package internet access is disallowed or the CDN remains unresolved, use a policy-approved offline Linux x86_64/Python 3.12 pinned and hash-verified Wheelhouse instead. **Do not** edit the shared host DNS resolver, route, firewall, network, proxy, Docker or shared services and do not disable TLS or blindly retry pip.

**Execution state:** pip upgrade to `26.2.2` remains `FAILED_DNS`; current venv pip `24.0` from earlier read-only inspection; Ubuntu requirements installation and pytest remain `NOT_RUN/BLOCKED`. No new tests executed beyond the two reported DNS lookups. Stage 04 `IN_PROGRESS`, Stage 05 `NOT_STARTED / NOT_APPROVED`, corporate D-017 validation `DEFERRED_TO_STAGE_11`.


## 2026-10-26 — Bounded A/AAAA DNS probes exhausted without response

User performed two independent **15-second read-only DNS-only** probes, from the pre-existing Ubuntu project shell:
- `timeout 15s resolvectl query --type=A files.pythonhosted.org` -> `IPv4_LOOKUP_EXIT=124`;
- `timeout 15s resolvectl query --type=AAAA files.pythonhosted.org` -> `IPv6_LOOKUP_EXIT=124`.

GNU `timeout` exit 124 means that the invoked command **did not complete before the 15-second deadline** and was stopped. It is **not** the DNS protocol's `NXDOMAIN` code, and neither lookup furnished an IP address. By contrast, the earlier `pypi.org` query succeeded and furnished A and AAAA records. Repeated failure for both types rules out a *simple record-family-only explanation in these observations*, but it does **not prove a persistent DNS block, deliberate censorship, or firewall No-Egress**; the tested resolver/upstream, network conditions and access policy remain unverified.

**Operational decision needed from authorized server/network owner:** Is outbound PyPI/CDN DNS+HTTPS explicitly allowed on this multi-project machine? If **yes**, the owner should investigate the upstream DNS response path and authorized reachability to `files.pythonhosted.org` under a controlled diagnostic/change process; no additional repeated public pip installation commands until an approved resolution path exists. If **no/unknown**, avoid network modifications and stage a license-reviewed, hash-verified, pinned **Python 3.12 Linux x86_64-compatible** Wheelhouse through the approved package acquisition/import channel, preserving exact version requirements. The user's historical Windows Wheelhouse is NOT sufficient for Linux native packages, and the Windows hashes cannot serve as Linux wheel artifact digests. **Never** set arbitrary public resolvers, disable TLS, alter global `systemd-resolved`/netplan/firewall, or restart/modify shared vLLM/Postgres as an unapproved workaround.

**Status:** `DNS_A_LOOKUP=TIMED_OUT_15S`; `DNS_AAAA_LOOKUP=TIMED_OUT_15S`; `PIP_BOOTSTRAP=FAILED_DNS`; `UBUNTU_DEPENDENCIES=NOT_INSTALLED`; `UBUNTU_PYTEST=NOT_RUN/BLOCKED`. No app regression tests executed in this event and no Linux test `PASS` is claimed; earlier Windows `70/70` remains separate user-reported evidence. Stage 04 `IN_PROGRESS`, Stage 05 `NOT_STARTED`; organizational No-Egress and live inference remain `DEFERRED_TO_STAGE_11`. The two DNS commands themselves are not Stage 11 security tests.


## 2026-10-26 — Host HTTPS endpoint differential: GitHub/PyPI succeeded, Wheel CDN name timed out

User executed read-only HEAD probes via `curl -I --connect-timeout 5 --max-time 10` from the **existing shared Ubuntu host**, with no pip install attempt. `https://github.com` returned **HTTP/2 200**. `https://pypi.org` returned **HTTP/2 200**. `https://files.pythonhosted.org` failed **before an HTTP response** with `curl: (28) Resolving timed out after 5002 milliseconds`. This is **consistent with earlier direct A/AAAA DNS query timeouts for the Wheel-file CDN** and establishes that **some HTTPS Internet destinations are reachable**, not that all destinations are reachable or that the public package download path is usable. No exact root cause (policy/filter, broken upstream DNS response, or transient failure) has been proved.

**Security handling:** The `curl -I` GitHub response included **Set-Cookie headers**, which are **not evidence needed for troubleshooting** and must not be copied into Git, test artifacts, or support diagnostics. This record stores status codes and the error string only, without raw headers/cookies or environment data. For future host-only checks, use `curl --silent --show-error --output /dev/null --write-out 'HTTP %{http_code}\\n' ...` rather than sharing headers; still require operator permission before external requests.

**Operational outcome:** There is **no basis for declaring the whole machine offline**; it has selective working HTTPS reachability. Prefer operator-approved diagnosis of DNS resolution/access to `files.pythonhosted.org` without editing global DNS, DHCP/netplan, firewall, or shared containers. If fixing authorized access would disturb other projects or is disallowed, use a **version-pinned, hash-reviewed, license-reviewed Python 3.12 Linux x86_64 offline Wheelhouse** from an approved source. Do not use the Windows `win_amd64` binary Wheels as Linux artifacts; no TLS verification bypass, arbitrary static CDN IP mapping or global DNS workaround is approved.

**Truthful stage evidence:** Ubuntu `.venv-review` exists with pip 24.0, pin upgrade `FAILED_DNS`, `requirements-dev.txt` `NOT_RUN`, Ubuntu `pip check` and `pytest` `NOT_RUN/BLOCKED`; previous user-local Windows `70/70` is separate. These HTTPS header probes **do not satisfy** D-017 Stage11 No-Egress/Network Security gates. Stage 04 `IN_PROGRESS`, Stage 05 `NOT_STARTED / NOT_APPROVED`.


## 2026-10-27 — Docker-isolated external PyPI mirror connectivity (user-observed)

The user executed a transient **Docker** Python 3.12.12-slim container with a single public synthetic HTTP probe to `https://pypi.tuna.tsinghua.edu.cn/simple/setuptools/`. The only reported program output was **`Mirror HTTP status: 200`**. This means the tested **setuptools simple-index route was reachable from that container** in this invocation; it does **not** establish that pip downloads, wheel file URLs, dependency versions, TLS verification of downloaded package signatures/hashes, arbitrary PyPI URLs, or an actual Dockerfile build succeeded. In particular, the old `files.pythonhosted.org` failure is *not* fixed or disproven. The externally operated mirror is a new software supply-chain dependency and is **not** an independently approved, signed or authoritative package source.

Real Repo inspection on the then-current main: **no Dockerfile, Compose, pyproject.toml, setup.py or setup.cfg**; pinned runtime pip requirements in `requirements.txt` and dev/test extras in `requirements-dev.txt`, plus separated audit tool requirements. Next proposed non-production experiment: create an ephemeral **allowlisted Git archive** containing only tracked `requirements.txt` and `src/`, generate a temporary Dockerfile outside the repository, use `python:3.12.12-slim` already pulled for the probe, install pinned pip + runtime requirements from the tested mirror using wheels only, check `pip check`, import `src.host.app`, and build/tag a **Stage04 candidate only**. Do not use a repository-root build context that might leak private `.env`/keys; do not create or run application containers, publish ports, modify shared networks, touch Postgres/vLLM, or infer legal approval. An actual image build has **not** yet been executed or reported; `DOCKER_MIRROR_INDEX_SETUPOOLS_HTTP_200=PASS_USER_SERVER_REPORTED`; `DOCKER_IMAGE_BUILD=NOT_RUN`; `PYTEST_UBUNTU=NOT_RUN/BLOCKED`; `HOST_VENV_PIP_UPGRADE=FAILED_DNS`.

**Production and supply-chain boundaries:** A third-party mirror returning 200 is not a verified artifact source; for approval, independently match each actual Linux Wheel's SHA-256 against trustworthy release metadata/manifest, scan SBOM and vulnerabilities, resolve 27 OSS legal reviews plus platform-specific components, and enforce approved build isolation and authenticated artifact promotion. Network No-Egress and service integrity remain `DEFERRED_TO_STAGE_11` under D-017. Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED`.


## 2026-10-27 — Ubuntu Docker Stage 04 candidate image built via mirror (user-reported)

**Execution provenance:** The user supplied the full `sudo docker build --pull=false --network default --progress plain` terminal log from shared Ubuntu Simorgh. The exploratory Dockerfile and context were **ephemeral and outside Git**, assembled with `git archive HEAD requirements.txt src` from the user's checked-out Git HEAD **`07f47f10fc0c`**. The temporary context copied only 12 tracked runtime paths (one `requirements.txt` plus 11 tracked `src/` files). GitHub blob SHA comparisons independently confirmed that **all these 12 runtime input files are identical** between the build's checked-out commit `07f47f10fc0ce89f62dd3253ea1ab43aff980346` and latest pre-recording `main` `6b8ae40fada22a3bee8779654955051d25d7dea6`. This check covers only tracked/runtime file identity; **it is not an inspection of the user's local Build Context bytes or image filesystem**. No Dockerfile/Compose exists in the Repository or was committed by this build.

**Reported Docker log:**
- Base: `python:3.12.12-slim`, locally resolved by Docker to `sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c`, **not independently validated for signature/attestation or CVEs**.
- Installer: `pip==26.2.2` successfully downloaded and installed through `https://pypi.tuna.tsinghua.edu.cn/simple` (15 pinned runtime + transitive packages reported; 5 top-level runtime pins in `requirements.txt`). In this build, the mirror successfully hosted `pip` and all requested runtime Linux distributions; this result does not repair host DNS resolution for `files.pythonhosted.org`.
- Explicit `pip check`: `No broken requirements found.` => `PASS_USER_SERVER_REPORTED`.
- `RUN python -c 'from src.host.app import app; assert app.title == "text-evaluation-service"; print("APP_IMPORT_PASS")'` emitted `APP_IMPORT_PASS` => import/composition-root smoke `PASS_USER_SERVER_REPORTED`, **not HTTP/E2E, synthetic data processing or pytest**.
- Docker exported and tagged `text-evaluation-service:stage04-mirror-07f47f10fc0c`, architecture `amd64`, reported virtual image Size `221542151` bytes, image index ID `sha256:ca7fd9f851bda6e3dbcb116ec256c21ec7356d6d283b76a0bb9bc05c4fc9948c`. User's final echoed `STAGE04_IMAGE_BUILD_PASS`. Image identity/metadata has **not** been freshly inspected from the actual Docker daemon by the assistant.
- Docker build did not execute or deploy the application container, publish a port, attach to `simorgh-db-net` or `ai-inference_default`, run migrations, start a DB or model, or modify existing shared service settings. This is **build-only evidence**, not independent proof of all possible side effects.

**Constraints, security and open gates:** A custom third-party PyPI Mirror is a provisional transport, **not** trusted publisher provenance. The log does not show independent `sha256` equality of every Linux Wheel to PyPI canonical records, a Linux SBOM, OSV/pip-audit results, CVE risk disposition, qualified 27-package OSS license signoff, verified image digest/attestation, reproducible build of all transitive versions or a secure image runtime test. Importing `app` and `pip check` are *not* equivalent to full tests. The `root` pip warning was in the Docker build layer, not a runtime privilege test; the candidate image Dockerfile sets `USER 65532:65532` but has not been launched. App configuration enforces a loopback bind (`127.0.0.1`); do not publish this Image as a functioning production API without an approved stage-specific network/app plan. **No prompts, proprietary customer text, DB secrets, server credentials or .env were intentionally included in the allowlisted context**, yet full runtime image contents require independent inspection. The `host .venv-review` pip upgrade is still `FAILED_DNS` and host Ubuntu requirements/test suite remain `NOT_RUN/BLOCKED`. The historical Windows `70/70` result remains separately reported.

**Verdict:** `DOCKER_STAGE04_CANDIDATE_BUILD=PASS_USER_SERVER_REPORTED`, `LINUX_RUNTIME_PIP_CHECK=PASS_USER_SERVER_REPORTED_DOCKER_BUILD`, `DOCKER_IMPORT_SMOKE=PASS_USER_SERVER_REPORTED`, `IMAGE_SUPPLY_CHAIN_APPROVAL=OPEN`, `UBUNTU_PYTEST=NOT_RUN`, `STAGE04=IN_PROGRESS`, `STAGE05=NOT_STARTED`, company No-Egress/model/GPU/load tests `DEFERRED_TO_STAGE_11`. This supports Stage 04 exploratory artifact build only, not Production or Stage 11 promotion.


## 2026-10-27 — Candidate image config and shared-service continuity check (user-reported, read-only)

After the documented successful candidate Docker Build, the user ran `sudo docker image inspect` on `text-evaluation-service:stage04-mirror-07f47f10fc0c` and supplied its actual terminal output: `ID=sha256:ca7fd9f851bda6e3dbcb116ec256c21ec7356d6d283b76a0bb9bc05c4fc9948c`, `Architecture=amd64`, `User=65532:65532`, `Cmd=["python","-m","src.host.app"]`. This is **PASS_USER_SERVER_REPORTED** for candidate identity/architecture/configured non-root user/command metadata, **not** an execution test of effective privileges or real API health. The user also ran `sudo docker ps`: existing `shared-postgres-postgres-1` was `Up 41 hours (healthy)` with no host-published DB port, and `ai-inference-vllm-1` was `Up 41 hours`, published on `127.0.0.1:8000`. Additional unrelated project containers were present (sum-service staging, imagegen-dev and an unclassified `adoring_satoshi` container): their ownership, settings and lifecycle **were not inspected or changed**. The separate `git status --short` command produced **no output**, consistent with a clean checkout.

**Correct inference:** Two previously identified shared services remained up after the candidate build. Read-only Docker listing alone cannot prove every other container was unaffected or that the candidate's build changed no global cache layers. No container named for this text-evaluation-service image was reported running, but no full image-ID-to-container inventory has been audited. No connection to Postgres/vLLM or network isolation test has been performed.

**Open acceptance gates:** Runtime-configured loopback host `127.0.0.1` binds *inside* a container and cannot be treated as an approved externally routable HTTP endpoint. Do not adjust the application's strict bind policy or publish network ports in Stage04 as a workaround. The third-party mirror's Linux wheels and Base Image still need an approved license/CVE/SBOM/hash/provenance review, along with qualified legal signoff. Host Ubuntu venv/test suite remains `NOT_RUN/BLOCKED` by CDN DNS, while Docker image build `PASS_USER_SERVER_REPORTED`. The user did not execute additional pytest, API, model or Stage11 tests in this step. **Stage04=IN_PROGRESS**, **Stage05=NOT_STARTED**, D-017 organizational tests `DEFERRED_TO_STAGE_11`.


## 2026-10-27 — Non-root offline image import smoke FAILED (user-reported)

User executed the previously supplied exploratory `sudo docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 256m --cpus 0.5 --entrypoint python text-evaluation-service:stage04-mirror-07f47f10fc0c -c ...` against the **existing** Stage04 candidate. It terminated at the top-level `from src.host.app import app` with `ModuleNotFoundError: No module named 'src.host.app'` (Traceback at `<string>`, line 6). Therefore **`STAGE04_OFFLINE_CONTAINER_SMOKE=FAIL_USER_SERVER_REPORTED`**; the subsequent `os.getuid()` assertion, `pip check` and success sentinel were **NOT_RUN** in that container invocation. **Do not extrapolate the prior BuildKit root-user `APP_IMPORT_PASS` into a non-root runtime PASS.** The image identity and non-root `Config.User` metadata had previously been inspected, but effective execution still fails this import.

**Diagnosis still pending:** Check container cwd, `sys.path`, exact file presence, directory/file modes, UID and package resolution using a **read-only non-root container** on `--network none`. A private Build Context was created under a restrictive umask; this suggests permission issues but is **not proven** by the traceback alone (GNU tar extraction may restore archive modes). Do not change global permissions, launch exposed application, attach DB/LLM networks, delete the candidate, or change production configuration before diagnosis. No files, volumes or secrets were mounted in the reported failure. Existing Docker candidate Build remains `PASS_USER_SERVER_REPORTED`, but runtime smoke is a **distinct FAIL**. Host Python `.venv-review` tests remain `NOT_RUN/BLOCKED`; Stage04 `IN_PROGRESS`; Stage05 `NOT_STARTED`; D-017 enterprise gates `DEFERRED_TO_STAGE_11`.


## 2026-10-27 — Non-root import failure root cause confirmed by file modes (user-reported)

A subsequent **read-only, offline, ephemeral** Docker probe ran the existing candidate with `--network none --read-only --cap-drop ALL --security-opt no-new-privileges` and `--entrypoint /bin/sh`, then displayed `id; pwd; ls -ld /app /app/src /app/src/host /app/src/host/app.py`. The provided terminal result was:

```text
uid=65532 gid=65532 groups=65532
/app
ls: cannot access '/app/src/host/app.py': Permission denied
drwxr-xr-x 1 root root 4096 ... /app
drwxr-xr-x 5 root root 4096 ... /app/src
drwx------ 3 root root 4096 ... /app/src/host
```

**Confirmed root cause:** `/app/src/host` is owned by UID 0 / GID 0 with mode **0700**, so the configured unprivileged UID **65532** cannot traverse it and cannot read `src.host.app`. The earlier root-user BuildKit import `APP_IMPORT_PASS` was therefore an insufficient runtime-privilege gate; later runtime failure `ModuleNotFoundError: No module named 'src.host.app'` is consistent with this permission denial. Other source subdirectories could share restrictive modes; correcting only the `host` directory is not a complete remedy. Earlier temp-build context extraction under `umask 077` is consistent with these permissions but the precise file creation sequence was not independently witnessed.

**Proposed, NOT YET RUN FIX:** In an isolated temporary allowlisted Git build context, derive a distinct candidate tag from the prior local Stage04 image, `COPY --chown=65532:65532 src/ ./src/`, and add `RUN python -m pip check` and `RUN python -c 'import os; from src.host.app import app; assert os.getuid()==65532; ...'` after `USER 65532:65532`. Use `docker build --network none --pull=false` with the original image as the sole local base, avoiding new downloads and no existing-image overwrite. Follow with the same offline/read-only/non-root runtime smoke check to confirm. No `chmod 777`, no modification of tracked repository source, project networks, global DNS or other shared services. **Do not change stage acceptance based on the proposed fix**: corrected build and corrected runtime smoke `NOT_RUN`; original candidate runtime smoke `FAIL_USER_SERVER_REPORTED`; Stage04 `IN_PROGRESS`; Stage05 `NOT_STARTED`; D-017 `DEFERRED_TO_STAGE_11`.


## 2026-10-27 — Offline Stage04 non-root permission fix image: build and runtime smoke PASS (user-reported)

**Input:** The same previously built and locally verified Stage04 image `text-evaluation-service:stage04-mirror-07f47f10fc0c` (Docker index digest `sha256:ca7fd9f851bda6e3dbcb116ec256c21ec7356d6d283b76a0bb9bc05c4fc9948c`). A Dockerfile **generated in temporary `/tmp/tes-nonrootfix.*` context, not committed to Git**, used `FROM text-evaluation-service:stage04-mirror-07f47f10fc0c`, `USER root`, and the following specific group-only repair:
```dockerfile
RUN chgrp -R 65532 /app/src \
    && chmod -R g-w,o-rwx /app/src \
    && chmod -R g+rX /app/src
USER 65532:65532
RUN python -m pip check \
    && python -c 'import os; from src.host.app import app; assert os.getuid() == 65532; assert app.title == "text-evaluation-service"; print("NON_ROOT_BUILD_SMOKE_PASS")'
```
This **supersedes the earlier proposed `COPY --chown` approach**; it kept the existing root-owned source files and granted runtime group 65532 read/traverse permission without group write or public access. `docker build --network none --pull=false --no-cache` rebuilt solely from the local image, without fetching fresh Python packages. It did not rebuild / change the original image tag. Docker BuildKit emitted `No broken requirements found.`, `NON_ROOT_BUILD_SMOKE_PASS`, and successfully tagged **`text-evaluation-service:stage04-nonrootfix-07f47f10fc0c`**.

**Offline runtime test:** A disposable `sudo docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 256m --cpus 0.5 --entrypoint python` container from the corrected image ran `from src.host.app import app`, asserted `os.getuid() == 65532` and application title, and printed **`NON_ROOT_RUNTIME_SMOKE_PASS`**. It was not the full application server or HTTP test. Image inspect in the user's terminal gave `ID=sha256:f0ba5ac4e7321cc6d1999e1a97de460e18815ab5ac7aa8e400cbedd770f2505a`, `User=65532:65532`, `Architecture=amd64`. The script then printed `STAGE04_NONROOT_IMAGE_PASS`.

**Results and scope:**
- `CORRECTED_IMAGE_BUILD=PASS_USER_SERVER_REPORTED`.
- `NONROOT_BUILD_PIP_CHECK=PASS_USER_SERVER_REPORTED`.
- `NONROOT_BUILD_APP_IMPORT=PASS_USER_SERVER_REPORTED`.
- `NONROOT_RUNTIME_OFFLINE_READONLY_APP_IMPORT=PASS_USER_SERVER_REPORTED`.
- `IMAGE_INSPECT_NONROOT_AMD64=PASS_USER_SERVER_REPORTED`.
- **`pip check` inside the corrected runtime container was NOT_RUN**: the check was performed during non-root Docker Build, not during `docker run`.
- The output included `WARNING: The directory '/.cache/pip' ... is not owned or is not writable ... cache has been disabled`; that is a pip cache permission warning, **not** a dependency validation failure. No password/secret has been recorded in this evidence.
- Prior broken candidate still exists separately, and its prior non-root smoke remains **FAIL** as a historical fact. No old Image cleanup or replacement occurred. No source tracked in Git was changed, no global DNS/network policies changed, no app service was launched, and no explicit connections to other project networks or services were made. This does not independently prove all unrelated containers unchanged; the shared services' status was separately recorded in the preceding inspection.

**Open gates remain:** Full 70-test suite **NOT_RUN on Ubuntu** (historically 70/70 on user-local Windows only); host venv pip upgrade **FAILED_DNS**; approved per-Linux-wheel SHA256/provenance, frozen transitive dependency closure, image-base CVE review, SBOM/pip-audit, and qualified OSS license approval still pending. `--network none` in this *smoke* is not a Stage11 proof of actual production No-Egress. **Stage04=IN_PROGRESS**, **Stage05=NOT_STARTED**; real internal model, organizational isolation and server security gates **DEFERRED_TO_STAGE_11** under D-017. This remains a candidate image, **not approved for Production deployment**.


## 2026-10-27 — Scoped Linux Docker test-runner committed, execution pending

User explicitly requested completing Stage 04. Reviewed both mandatory Project Sources, Stage04-specific checklist/Gates and GitHub runtime/test source. Added **`scripts/verification/run_stage04_linux_container_tests.sh`** as a **read-only-to-repository, manually triggered** test runner only. The runner:
- Requires clean `main`, unchanged `requirements.txt`/`src/` relative to source commit `07f47f10fc0c`, and existing corrected Image `text-evaluation-service:stage04-nonrootfix-07f47f10fc0c`. **Never** overwrites a previously created test image tag.
- Creates an ephemeral context through `git archive HEAD requirements.txt requirements-dev.txt scripts tests`, **excluding all untracked files**, project-specific `.env`, credentials, staging volumes, unrelated projects and even the tracked `src/` (already in the local base Image). Temporary context is cleaned by a scoped exit trap.
- Builds a **distinct development/test Image** using only the already inspected local base and the same third-party Tsinghua PyPI mirror for **public development dependencies** (`requirements-dev.txt`), with wheels only and explicit pip timeout/retries; no new runtime deployment and no model/DB connectors.
- Runs **full project `pytest tests`, Stage03 benchmark-validator tests, Stage02 checker regressions, Stage04 static source safety guard, `pip check` and non-root FastAPI import** in a disposable **`--network none --read-only`** container, with read/write `/tmp` tmpfs, UID 65532, no capabilities, no published ports or volume mounts and bounded resources.
- Emits `STAGE04_LINUX_CONTAINER_TESTS_PASS` **only after every check returns success**. Fails closed otherwise. No Docker Compose, shared DNS/firewall/network/service alteration or permanent tracked project change is performed by running the script.

**Actual current test evidence (assistant's local sandbox):** `bash -n` on the authored runner **PASS**; 13 targeted static safety assertions against its network, scope, read-only, non-root, staging and network/deploy safety semantics **PASS**. These are **not equivalent to executing the runner's actual Docker Build/pytest**. Assistant has **no remote SSH execution capability**; the user must pull the commit and run `bash scripts/verification/run_stage04_linux_container_tests.sh` on Simorgh from the clean repo, after authorization for the third-party public mirror/download and Docker test build. The default branch of the server was previously `07f47f...` but its current `git status` after any later activity must be verified by the operator. The exact `sudo docker build` of this **test-only** image and Ubuntu project tests remain **`NOT_RUN / PENDING_USER_SERVER_EXECUTION`** until logs are supplied. This is a **new local-test gate attempt**, not an E2E company infrastructure test deferred to Stage11.

**Gate status remains OPEN:** independently inspect the Linux-wheel SHA256 versus official release manifest, base image CVE/SBOM and provenance, and complete authorized OSS license reviews (`REVIEW_REQUIRED` for all 27 Windows snapshot packages, with Linux closure requiring its own inventory). Third-party mirror package hashes are not independently authenticated by a successful pip install, and top-level pins do not lock transitives. No Stage 04 `DONE` nor Stage 05 permission is claimed; company-specific gates remain D-017 `DEFERRED_TO_STAGE_11`.


## 2026-10-27 — Runner fail-closed tests executed in assistant's sandbox

The **identical Git blob `12aabb950b7bc896136a1d9a1aabb6131edb99ef`** was checked by the assistant under Bash. Results:
- `bash -n scripts/verification/run_stage04_linux_container_tests.sh` => **PASS**.
- **13/13 targeted source safety invariants PASS** (scope-limited tracked `git archive`, offline/read-only and UID65532 runtime, no privileged/Compose/other-project actions).
- Three **isolated synthetic Git checkout** negative execution cases were run against the actual authored script; each rejected the input before Docker: `FRESH_BUT_MISMATCHED_SOURCE=PASS_FAIL_CLOSED`, `DIRTY_CHECKOUT=PASS_FAIL_CLOSED`, `NON_MAIN_BRANCH=PASS_FAIL_CLOSED`. **3/3 PASS** on preflight rejection.
- These are genuine local **runner behavior tests**, **not** actual server-side Docker Build/Ubuntu `pytest`. The user must execute the real Linux test command. Stage 04 remains `IN_PROGRESS`, Stage 05 `NOT_STARTED`. The remaining artifact/legal reviews are unchanged.


## 2026-10-27 — Ubuntu Linux suites PASS; Docker safety checker blocked by a test-only permission defect

**User-server observed evidence:** Clean checkout `git pull --ff-only origin main` fast-forwarded `07f47f1..53072ff`. `bash scripts/verification/run_stage04_linux_container_tests.sh` successfully built disposable test Image `text-evaluation-service:stage04-pytest-53072ff3246e`, Docker-reported manifest digest `sha256:cb12dfa955f2b47a185758e01d6fd46d2f5b5a6453e319f0ef6b7f4e2209e914`, installed pinned public dev dependencies via the Tsinghua mirror (brief `Errno 101 Network is unreachable` followed by successful retry) and executed Build-time `pip check`: **`No broken requirements found.`** This does not prove stable CDN/network behavior or independently verified package provenance.

**Linux tests executed:** `python -m pytest -q -p no:cacheprovider tests` => **70 passed / 0 failed (4.52s)**; `python -m unittest discover -s scripts/benchmark -p 'test_*.py' -q` => **38/38 OK (0.170s)**; `python -m unittest discover -s scripts/verification -p 'test_check_stage02_docs.py' -q` => **12/12 OK (0.001s)**. The three distinct suites have passed and are recorded separately.

**Full runner FAIL, not PASS:** `python scripts/verification/check_stage04_safety.py` then crashed while reading `/app/requirements.txt`: `PermissionError: [Errno 13] Permission denied`. This reflects a **test Image read-permission defect**, rather than a failed static safety rule. The original runner copied runtime/development manifests with restrictive root-owned file modes under `umask 077`, but made only `/app/tests` and `/app/scripts` readable by runtime GID 65532. Source checker additionally reads `.gitignore`, **omitted from the original test Build Context**; subsequent offline runtime `pip check`, non-root import and terminal `STAGE04_LINUX_CONTAINER_TESTS_PASS` were **NOT_RUN**. Record `RUNNER_SAFETY_CHECK=ERROR_PERMISSION`, `RUNNER_OVERALL=FAIL`; preserve original test Image for evidence.

**Minimal remediation (committed, actual Ubuntu re-execution PENDING):** add only tracked `.gitignore` to the allowlisted Git archive and Docker COPY; set `chgrp 65532` and `chmod 0640` on root-owned `/app/.gitignore`, `/app/requirements.txt`, `/app/requirements-dev.txt` **inside the temporary test Image**, prior to non-root `USER 65532:65532`; no public readability, write permission, source modification, global file permission change, service deployment, external DB/LLM network/volume or DNS edits. Add `tests/test_linux_runner_permissions.py` (one focused regression) to prevent recurrence. Assistant sandbox ran **`bash -n` PASS**, **9/9 scoped source safety assertions PASS**, and **targeted regression 1/1 pytest PASS**. Re-running the full updated script on Ubuntu is still **`PENDING_USER_SERVER_RETEST`** (expected pytest count now at least 71 due new test). The runner's tag derives from new HEAD, so the old `stage04-pytest-53072ff3246e` tag is not overwritten. Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED`; Linux Wheel hashes/SBOM/CVE/license acceptance remains OPEN, D-017 on-prem organizational gates `DEFERRED_TO_STAGE_11`.


## 2026-10-27 — Stage04 full Linux Docker test runner SUCCESS (user-server log)

**Operator evidence:** user ran `git status --short` (empty), `git pull --ff-only origin main` (fast-forward `53072ff..d39e5f2`), `bash -n scripts/verification/run_stage04_linux_container_tests.sh` (no syntax errors), and `bash scripts/verification/run_stage04_linux_container_tests.sh` on shared Ubuntu Simorgh. The tool created a separate **test-only Docker image** from the previously verified local fixed runtime image, adding only tracked `.gitignore`, `requirements.txt`, `requirements-dev.txt`, `tests/`, and `scripts/` through temporary Git archive. No new runtime source or permanent Dockerfile was introduced. Package installation from the previously accepted external Tsinghua mirror and `pip check` succeeded during Build.

**Docker test artifact:** `text-evaluation-service:stage04-pytest-d39e5f21c3c3`, Image index `sha256:7b3c7532a3e31f002ec1f8211c28d22148602b74ff1bfc51dd8edb4df5239785`, `User=65532:65532`, `Architecture=amd64` (user terminal). New image is distinct from both the older test image and repaired runtime image. Build created a local image only, not an app deployment.

**Verified from user transcript — all checks in the fail-fast pipeline completed:**
- Linux Python 3.12 `pytest -q -p no:cacheprovider tests` → **`71 passed in 4.97s`**, including the new runner permission regression (reported count, not individually enumerated).
- Stage03 `unittest discover -s scripts/benchmark -p 'test_*.py' -q` → **`Ran 38 tests ... OK`**.
- Stage02 checker regression `unittest discover -s scripts/verification -p 'test_check_stage02_docs.py' -q` → **`Ran 12 tests ... OK`**.
- Stage04 static safety source guard → **`PASS: 9 runtime source files; dependency pins; patched Starlette baseline; credential patterns; ignored secrets`**.
- Non-root offline runtime `python -m pip check` → **`No broken requirements found.`**.
- Non-root application import → **`NON_ROOT_IMPORT_PASS`**.
- Final scripted success marker → **`STAGE04_LINUX_CONTAINER_TESTS_PASS image=text-evaluation-service:stage04-pytest-d39e5f21c3c3`**.

**Execution conditions** (from reviewed committed runner): disposable runtime container launched `--rm --network none --read-only --tmpfs /tmp`, `--cap-drop ALL --security-opt no-new-privileges --user 65532:65532` with bounded PIDs/memory/CPU and no volume mounts or published ports. This is **local no-network smoke/test evidence, not organizational Network No-Egress certification**. Prior test attempt at HEAD `53072ff` passed 70+38+12 tests but failed checker manifest permissions; **that failure has been corrected and the entire revised runner passed**. Preserve both historical facts.

**Final local-test gate statement:** `FULL_LINUX_PYTEST=PASS_USER_SERVER_REPORTED_71_OF_71`, `STAGE03_LINUX_REGRESSION=PASS_38_OF_38`, `STAGE02_LINUX_REGRESSION=PASS_12_OF_12`, `STAGE04_STATIC_SAFETY=PASS`, `RUNTIME_NONROOT_IMPORT=PASS`, `RUNTIME_PIP_CHECK=PASS`, `STAGE04_LINUX_CONTAINER_TESTS_PASS=CONFIRMED_USER_LOG`. Existing Windows `70/70` is separate pre-new-test evidence. **Not executed:** CI promotion/Production image test, real model/DB end-to-end, on-prem network policies (D-017 `DEFERRED_TO_STAGE_11`), actual Linux Wheel official digest comparison, Linux SBOM + advisories scoped to final image/base layers, qualified license approvals (existing 27 Windows evidence decisions `REVIEW_REQUIRED`). Successful import/tests alone do not authorize unsafe third-party mirror packages or Stage 05. **Stage04 remains `IN_PROGRESS`; Stage05 `NOT_STARTED / NOT_APPROVED`.**


## 2026-10-27 — Simorgh Linux installed package-version inventory (user-observed, NOT a provenance audit)

The operator ran a **read-only, no-network, non-root** `importlib.metadata.distributions()` listing inside the previously passing Stage 04 Docker **development test Image** `text-evaluation-service:stage04-pytest-d39e5f21c3c3`. The user reported 27 installed distributions (names normalized for comparison below; package values and versions otherwise unchanged):

```text
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
certifi==2026.10.23
click==8.5.0
fastapi==0.148.0
h11==0.16.0
httpcore==1.0.9
httpcore2==2.16.0
httpx==0.28.1
httpx2==2.16.0
idna==3.20
iniconfig==2.3.1
opentelemetry-api==1.45.1
packaging==26.3
pip==26.2.2
pluggy==1.7.0
pydantic==2.13.5
pydantic_core==2.46.5
pygments==2.21.0
pytest==9.0.3
pyyaml==6.0.3
starlette==1.9.0
truststore==0.10.5
typing-inspection==0.4.4
typing_extensions==4.16.0
uvicorn==0.48.0
TOTAL_PACKAGES=27
```

**Independent cross-check against the Git-reviewed Windows license-triage metadata:** all **26 Linux application + development dependency closure names/versions** match corresponding entries in the Windows 27-package list exactly after standardizing separator spelling (`pydantic_core` ↔ `pydantic-core`; `typing_extensions` ↔ `typing-extensions`). The different 27th entry is `pip==26.2.2` in Linux **as a separately installed packaging/bootstrap tool** versus `colorama==0.4.6` in the Windows closure (not installed in this Linux Image). Therefore **Linux `TOTAL_PACKAGES=27` is not equivalent to a new all-dependencies/all-wheels license approval**, and the existing Windows 27-component license review metadata does not cover Linux's installed pip distribution. Actual **runtime-only** image closure is smaller than this development test Image; no app runtime SBOM can be inferred from the dev Image count.

**What this proves:** the precise installed package/version list, as emitted by the user-observed package metadata API, and that 26 overlap with the previously recorded Windows snapshot. It does **not** itself verify installed-wheel RECORD hashes, Wheel contents or their independent official PyPI digests, approved exact transitive lockfile, CycloneDX SBOM, OSV vulnerability scan, Linux base-image CVEs, actual license obligations, or provenance from the third-party Tsinghua mirror. The user did **not** run `audit_stage04_dependencies.py` in this interaction: `LINUX_INSTALLED_RECORD_VALIDATION=NOT_RUN`. `LINUX_SBOM=NOT_RUN`; `LINUX_INDEPENDENT_WHEEL_SHA256=NOT_RUN`; `LINUX_CVE=NOT_RUN`; `LEGAL_LICENSE_APPROVAL=OPEN`, including an explicit review of `pip` where included in shipped images and OS layer license obligations. Do not confuse previously reported Windows Wheel 27/27 / OSV-clean with a Linux Wheel + base-image review.

**Status:** local Stage04 Linux Python/regression/safety test runner remains `PASS_USER_SERVER_REPORTED` from previous evidence. Stage04 `IN_PROGRESS` for remaining accessible-artifact Supply Chain and qualified OSS legal review; Stage05 `NOT_STARTED`; on-prem internal-network/model/Credential acceptance remains `DEFERRED_TO_STAGE_11` under D-017.


## 2026-10-27 — Offline installed RECORD integrity and exact Linux dependency closure (user-reported)

**Input provenance:** The user ran a `sudo docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 768m --cpus 1 --user 65532:65532 --entrypoint python` probe against the existing **development/test** image `text-evaluation-service:stage04-pytest-d39e5f21c3c3`. Despite partially duplicated/garbled *echoed* terminal paste, the final Python output included all expected sentinel markers and the full 26-line exact dependency closure, with no Python exception. The actual executed command exact bytes were not independently audited, so evidence is `USER_SERVER_REPORTED`, not assistant-executed.

The probe imported the existing repository's `scripts.verification.audit_stage04_dependencies.build_inventory(include_dev=True)`, `bootstrap_pip_status`, and `frozen_requirements`. User output:

```text
DEPENDENCY_CLOSURE_COUNT= 26
INSTALLED_RECORD_SHA256_VERIFIED= 1147
LICENSE_REVIEW_REQUIRED= 26
PASS_BOOTSTRAP_PIP_VERSION: 26.2.2 (version floor only; CVE scan still required)
FROZEN_REQUIREMENTS_BEGIN
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
certifi==2026.10.23
click==8.5.0
fastapi==0.148.0
h11==0.16.0
httpcore==1.0.9
httpcore2==2.16.0
httpx==0.28.1
httpx2==2.16.0
idna==3.20
iniconfig==2.3.1
opentelemetry-api==1.45.1
packaging==26.3
pluggy==1.7.0
pydantic==2.13.5
pydantic-core==2.46.5
pygments==2.21.0
pytest==9.0.3
pyyaml==6.0.3
starlette==1.9.0
truststore==0.10.5
typing-extensions==4.16.0
typing-inspection==0.4.4
uvicorn==0.48.0
FROZEN_REQUIREMENTS_END
```

**Evidence interpretation:** `26` is the installed **runtime+development dependency closure** resolved from pinned top-level `requirements.txt` and `requirements-dev.txt`, not all installed Python distributions. The preceding image enumeration gave `27`, whose additional `pip==26.2.2` is a bootstrap tool rather than a declared app dependency; the existing Windows 27-Wheel evidence included `colorama` instead of pip. The `build_inventory` verifier recomputed **1,147 installed file SHA-256 digests against their local wheel `RECORD` entries** across the 26 dependencies and found no mismatch reported. `RECORD` is installation-local; a matching `RECORD` is **NOT evidence of authenticity or unmodified publisher original**, and the tool does not scan files not listed in `RECORD`. The 26 `REVIEW_REQUIRED` entries affirm **zero approved license decisions** in this invocation. The pip bootstrap version floor check is **not an OSV scan**. The printed lock list is a **snapshot of exact installed versions**, not a hash-locked dependency resolution, and was **not written into a committed lockfile**.

**Actual outcome:** `LINUX_DEVELOPMENT_CLOSURE=26_USER_SERVER_REPORTED`, `INSTALLED_RECORD_SHA256=PASS_USER_SERVER_REPORTED_1147`, `PIP_BOOTSTRAP_VERSION=PASS_USER_SERVER_REPORTED_26_2_2`, `LICENSE_26_OF_26=REVIEW_REQUIRED`. No new Docker Build, code changes, network calls, container service deployment or shared DB/LLM interaction occurred. Actual Linux distribution wheel-byte SHA256 versus official PyPI, frozen/hash-bound reproducible build, live Linux OSV audit, CycloneDX SBOM and base-image vulnerability/license review remain `NOT_RUN/OPEN`; the previously obtained Windows OSV/Wheel/license information remains evidence scoped to Windows only. Continue to treat the installation as **Stage04 candidate, not certified Production**. Stage04 `IN_PROGRESS`, Stage05 `NOT_STARTED`, D-017 organization-only gates `DEFERRED_TO_STAGE_11`.


## 2026-10-27 — Linux Stage04 supply-chain collection runner added, execution pending

- Previous Simorgh user-supplied Linux verification is unchanged: **71/71 pytest**, **38/38 Stage03**, **12/12 Stage02**, non-root import and pip check PASS; dependency closure 26 and **1,147 installed local RECORD SHA256** checks PASS. This evidence refers to the already fixed test image, NOT PyPI publisher attestation.
- A dedicated Linux Stage04 collector was added at [run_stage04_linux_supply_chain.sh](../../scripts/verification/run_stage04_linux_supply_chain.sh), along with [synthetic preflight tests](../../tests/test_linux_supply_chain_runner.py). Local assistant execution on authored files: shell syntax **PASS** and **3/3 scoped pytest PASS** including clean-branch/dirtiness fail-closed checks. This is not an execution of Docker, OSV or CycloneDX on Simorgh. Repository read-back and SHA/pin preflight guard were reviewed.
- Collector uses an exact existing non-root Docker test image; auditor tools are separately isolated, installs happen only in a disposable derivative image from a previously accessed public PyPI mirror, and evidence is written under a new unique UID65532-owned Git-ignored directory. No source DB, vLLM, shared network or running-service operation is in its path; optional public package/advisory network traffic requires prior network-owner authorization.
- Actual Ubuntu wheelhouse, official PyPI digest match, Linux OSV scan, CycloneDX 1.6 and trustworthy base image/OS scan/attestation remain **NOT_RUN / GATE OPEN** pending authorized user host execution. A completed Linux collector does NOT approve any of the 26 component licenses; separately review bootstrap pip and OS packages.
- **Stage04 IN_PROGRESS**; Stage05 **NOT_STARTED / NOT_APPROVED**. Enterprise-only inference, internal IAM, real No-Egress remain **DEFERRED_TO_STAGE_11**, not passed.


## 2026-10-27 — Simorgh Stage04 Git-in-container and BuildKit bridge-network failures

User-supplied Simorgh evidence at HEAD c7235db8237bfe00ed3027aee5b6130a5578b43a: Stage04 Linux test image build and build-time pip check PASS. Full pytest ran 74 tests: **73 PASS / 1 FAIL**. The only failure was test_linux_supply_chain_runner_rejects_dirty_or_wrong_branch_without_docker, where the slim test image lacked an installed Git executable (FileNotFoundError). Because pytest exited non-zero, Stage02/03 regressions and subsequent runtime checks in this attempt were NOT_RUN.

The separate Linux supply-chain collector stopped at Docker build before creating evidence because this host BuildKit driver rejects docker build --network bridge. No OSV, CycloneDX, Linux wheel or PyPI SHA results were generated.

**Targeted remediation:** the negative-case test uses a temporary Git stub to exercise dirty checkout, wrong branch and missing baseline commit without requiring an OS package inside the test image. The real collector still runs actual Git on the host. Auditor image build uses docker build --network default, which previously worked for the Linux test runner; explicit docker run --network bridge remains limited to its public advisory/wheel phase and docker run --network none is retained for installed metadata inventory. No app/DB/model image changes and no shared service operation.

**Assistant local execution:** bash -n PASS, targeted synthetic pytest 3/3 PASS, compileall PASS and 6 focused safety assertions PASS. Real Docker retest for these changes and full collector remains PENDING_USER_SERVER_RETEST. This is not a supply-chain approval or a legal signoff. Stage04 IN_PROGRESS; Stage05 NOT_STARTED / NOT_APPROVED; corporate controls DEFERRED_TO_STAGE_11.

## 2026-10-27 — Simorgh Linux package collector completed; hardened noexec regression still open

Evidence source: user-supplied terminal output for repository HEAD 186b041e4cedc079c8c12d1fe02e255983a8d80d.

- The test image built and its pip check passed. Python pytest: **73 PASS, 1 FAIL of 74**. The sole failing test was test_linux_supply_chain_runner_rejects_dirty_or_wrong_branch_without_docker: executing a temporary Git stub under /tmp returned **Permission denied (exit 126)**. The previous missing-Git regression was changed into an executable-stub permissions issue; do not infer an exact kernel mount-policy cause without host inspection. Subsequent Stage02/03 checks and import/static runner steps were NOT_RUN in this attempt.
- The separately built auditor image completed successfully with isolated patched pip, pip-audit 2.10.1 and cyclonedx-bom 7.5.0; auditor pip check PASS. No production service was started.
- Installed metadata inventory PASS: **26 Linux app+dev dependency distributions**, exact frozen closure, unapproved license template. A previous standalone command verified **1,147 installed RECORD SHA256 files**; the current console excerpt does not recount those hashes.
- **OSV executed, zero reported findings:** pip-audit printed 'No known vulnerabilities found'; the collector accepted its complete-report status. This concerns the selected installed Python package environment at scan time, not all OS/base-image packages or publisher provenance.
- **CycloneDX 1.6 SBOM GENERATED**, not yet independently accepted against inventory by the final offline evaluator. **26 Linux wheels downloaded** matching the pinned closure. Local manifest/archive hash validation PASS and independent official PyPI release SHA256 metadata comparison PASS (two PASS_LOCAL_EVIDENCE_GENERATED messages); the runner ended with LINUX_PACKAGE_EVIDENCE_COLLECTED_NOT_LEGALLY_APPROVED.
- Evidence folder reported by operator: .stage04-evidence-linux-20261027-02, owner UID 65532, not uploaded. Contents were not read byte-for-byte by the assistant; the claims above are limited to log evidence.
- New targeted fix: load an in-process synthetic Bash Git function from a readable but non-executable BASH_ENV file (0400), avoiding invocation of executables from /tmp. Assistant synthetic local Bash preflight and 3/3 negative-case smoke scenarios PASS. Complete hardened Docker test suite after this fix **PENDING_USER_RETEST**.
- Still OPEN: complete local Linux test gate, evidence validation, authorized license reviews for 26 closure packages and separately shipped pip, base-image OS vulnerability scan/attestation and trusted provenance. No unperformed check is marked PASS.
- Stage04 IN_PROGRESS; Stage05 NOT_STARTED/NOT_APPROVED; genuine organization-only runtime and No-Egress DEFERRED_TO_STAGE_11.

## 2026-10-27 — Simorgh hardened Stage04 Linux regression fully passed (user-reported)

**Observed repository HEAD:** `e90d8d4550296152a6cb0085fe3639190a40ffe2` (clean main before fast-forward; user explicitly showed Git update and commit ID). A new isolated Docker test image was built and ran under non-root UID/GID 65532:65532, architecture amd64.

| Gate evidence from the exact user-supplied terminal stdout | Status |
|---|---|
| Full Python pytest suite | **PASS 74/74**, 4.67s; no failures |
| Stage03 benchmark validator regressions | **PASS 38/38**, 0.172s |
| Stage02 documentation contract regressions | **PASS 12/12**, 0.001s |
| Stage04 static security guard | **PASS**, checks 9 runtime source files, pins, Starlette baseline, credentials and secret ignores |
| Docker build-time and runtime `pip check` | **PASS**, 'No broken requirements found' |
| Non-root import smoke | **PASS**, `NON_ROOT_IMPORT_PASS` |
| Runner completion marker | **PASS**, `STAGE04_LINUX_CONTAINER_TESTS_PASS` |

- Immutable test image reference: `text-evaluation-service:stage04-pytest-e90d8d455029`; Docker-reported image ID `sha256:e8e55a716888d85cc5e91ad629059657868cb44de7614f61eeb6679b2cd1599c`. This is a locally generated development test image, **not** a signed upstream/Production provenance attestation.
- The formerly failing noexec-sensitive synthetic Git preflight test now passes within the full suite. Stage04 **local code/test regression gate PASS_USER_SERVER_REPORTED**; the assistant did not independently log into Simorgh or execute this Docker suite.
- Preserve the separately completed Linux supply-chain artifacts in `.stage04-evidence-linux-20261027-02` (user-reported earlier): OSV returned no reported Python-package vulnerabilities, 26 exact-version Linux Wheels and official PyPI release SHA256 matches collected, CycloneDX 1.6 SBOM generated. **Do not rerun/download merely to clear a passed code test.** Those files have not been byte-reviewed by the assistant, and the final offline cross-artifact consistency check remains **PENDING**.
- Legal and security reservations are unchanged: 26 version-exact Linux package license decisions plus separately installed pip remain `REVIEW_REQUIRED`; base image/OS vulnerability scan and artifact provenance are unverified. Corporate server-only controls are `DEFERRED_TO_STAGE_11` under D-017. Do not infer a production release or network No-Egress PASS from Docker `--network none`.
- **Stage04 remains IN_PROGRESS**, local regression gate PASSED, independent evidence/License/Base-OS gates OPEN; **Stage05 NOT_STARTED / NOT_APPROVED**.

## 2026-10-27 — Read-only Simorgh technical evidence verification marker (paste partially truncated)

- User reports running a `sudo docker run --network none --read-only` Python validator against the preserved `.stage04-evidence-linux-20261027-02` directory with a `:ro` mount and the existing `stage04-linux-audit-186b041e4ced` image. The terminal printed **`STAGE04_TECHNICAL_EVIDENCE_CONSISTENT_26; LICENSE_REVIEW_PENDING`** with no traceback or Docker failure reported.
- The visible copied command includes the 26-component inventory/closure comparison, complete OSV report validation, CycloneDX coverage check and Wheel SHA256 validation call. **However, the pasted terminal command is visibly truncated/malformed after the wheel-hash validator** (ending near `'rint(...)`); the exact executed Python program and whether the PyPI manifest and license-template assertions ran cannot be reconstructed from this paste. Therefore this marker is recorded as **USER_REPORTED_SUCCESS_WITH_TRUNCATED_COMMAND**, *not* assistant-independent full artifact verification.
- The independent public PyPI comparison previously completed successfully during evidence collection; it remains true that the final separately re-executed cross-artifact check for PyPI and the unapproved license template has **not been conclusively documented by this new paste**. The runbook provides a narrow **offline, read-only, zero-network** follow-up to verify only those remaining pieces without rerunning the already passed tests, advisory scan or Wheel downloads.
- The full Simorgh Linux test suite remains **PASS_USER_SERVER_REPORTED: 74/74 pytest + 38/38 Stage03 + 12/12 Stage02** at e90d8d4. The status of Stage04 is still `IN_PROGRESS`, with authorized OSS license approvals (26 Linux closure components plus separately shipped pip) and approved OS/base-image CVE/provenance review OPEN. Stage05 remains NOT_STARTED and organizational tests stay DEFERRED_TO_STAGE_11.

## 2026-10-27 — Simorgh offline PyPI digest/license-template cross-check independently rerun and passed

**User-observed execution:** From `/srv/projects/text-evaluation-service`, `sudo docker run --rm --network none --read-only` ran the existing `text-evaluation-service:stage04-linux-audit-186b041e4ced` container as UID/GID 65532 with a **read-only bind mount** of `.stage04-evidence-linux-20261027-02`. `--cap-drop ALL`, `--security-opt no-new-privileges`, bounded memory/CPU/pids and isolated temp space were present. No host service changes or external network were requested.

- Executed Python logic loaded `inventory.json`, verified the expected dependency closure size **26**, loaded `wheel-hashes.json` and `pypi-digests.json`, and successfully ran `_validate_pypi_digests(...)`, confirming local manifest identities, Wheel names, versions and SHA256 values are consistent with the **previously captured** official-PyPI digest metadata. This was offline revalidation of recorded PyPI evidence, **not a fresh live PyPI request or a signature/installation provenance attestation**.
- It loaded `license-review.json`, checked the expected review-template format, matched the full 26-component/version license decision identity set, and verified **every decision was `REVIEW_REQUIRED`**. This is correct template completeness, **not license compliance approval**.
- The terminal ended without an error with exact output **`STAGE04_PYPI_LICENSE_TEMPLATE_MATCH_26; LEGAL_APPROVAL_PENDING`**. Mark this narrow cross-artifact gate **PASS_USER_SERVER_REPORTED**, replacing the previous pending status caused by the incomplete earlier pasted command.
- Earlier operator evidence: same artifact collection included a complete Python OSV scan with zero reported findings, CycloneDX 1.6 output, 26 exact Linux Wheels and local Wheel SHA256 verification. The earlier separate comprehensive offline verification printed `STAGE04_TECHNICAL_EVIDENCE_CONSISTENT_26; LICENSE_REVIEW_PENDING`, but its pasted command was truncated; the narrow check above conclusively covers the **previously unconfirmed final PyPI/template assertions**. Raw evidence bytes have **not been transferred to the assistant** for separate external re-verification.
- Hardened Linux tests remain **74/74 pytest**, **38/38 Stage03**, **12/12 Stage02**, static guard, pip check and non-root smoke PASS per earlier terminal logs.
- **Stage04 remains `IN_PROGRESS`** pending a qualified human license/redistribution determination for 26 Linux-closure packages plus separately installed `pip`, approved base-image/OS vulnerability scan and upstream origin/installed-bytes provenance review. Organizational model/no-egress/IAM tests stay `DEFERRED_TO_STAGE_11`; **Stage05 NOT_STARTED / NOT_APPROVED**.


## 2026-10-27 — Debian OS-layer inventory reported from Simorgh

Read-only operator output for the previously reviewed image ID ending `5239785` showed Debian 13 (trixie), release 13.3, linux/amd64, runtime user 65532:65532 and 87 installed dpkg packages. No OS CVE scan was executed. Official Debian 13.7 was published on 2026-09-12, so the point-release string merits package-version review but does not alone prove any vulnerability. Existing Python OSV zero-findings do not assess Debian system packages. No image provenance, license signoff, rebuild or package upgrades were performed. Stage04 IN_PROGRESS; Stage05 NOT_STARTED.

## 2026-10-27 — Simorgh OS scanner absence and non-authoritative local RepoDigests

Operator ran read-only `command -v` checks and inspected the exact existing Docker image `text-evaluation-service:stage04-pytest-d39e5f21c3c3`: `trivy=NOT_INSTALLED`, `grype=NOT_INSTALLED`, `syft=NOT_INSTALLED`. Local ID remains `sha256:7b3c7532a3e31f002ec1f8211c28d22148602b74ff1bfc51dd8edb4df5239785`. Docker returned `RepoDigests=["text-evaluation-service@sha256:7b3c7532a3e31f002ec1f8211c28d22148602b74ff1bfc51dd8edb4df5239785"]`.

- `RepoDigests` here refers to the project's **local image name**. Matching a local digest or image ID does **not** independently authenticate the original Docker Hub/Python/Debian upstream base image, a registry signature, builder provenance, or installer inputs.
- Consequently **OS_IMAGE_VULNERABILITY_SCAN = NOT_RUN / PENDING_APPROVED_SCANNER_AND_CURRENT_DATABASE**. The 87 Debian 13/trixie OS packages observed previously were counted, but their individual name/version/architecture manifest is still not in the operator-shared evidence. No Debian CVE status may be inferred from Python OSV zero-finding results, current trixie release naming or the lack of scanner.
- The next permitted low-impact step is exact `dpkg-query` name/version/architecture inventory via a `--pull never --network none --read-only` non-root container with the exact already verified image. Then choose a qualified image scanner, approved source/digest/signature, a sufficiently fresh Debian advisory DB and isolated non-production execution path, with documented image identifier, findings and timestamp. **No host scanner installation, unreviewed `curl | sh`, new Docker socket mount, image pull, OS upgrade, or change to shared services is authorized by inventory alone.**
- The 26 Linux Python package digests/license-template cross-check, previous 74/74 local tests and OSV Python scope results remain separately USER_SERVER_REPORTED PASS. Qualified OSS license signoff for those packages plus separately installed pip and base-image/source/installed-byte provenance remain OPEN. Stage04 IN_PROGRESS; Stage05 NOT_STARTED; corporation-only real environment tests DEFERRED_TO_STAGE_11.

## 2026-10-27 — Complete Debian package inventory and initial official source-package desk comparison

Operator supplied the exact `dpkg-query -W` name/version/architecture output from the unchanged non-root read-only Docker image `text-evaluation-service:stage04-pytest-d39e5f21c3c3` (ID `sha256:7b3c7532a3e31f002ec1f8211c28d22148602b74ff1bfc51dd8edb4df5239785`). Full source-preserving tab-separated inventory: [`04_stage04_debian_os_package_inventory.tsv`](04_stage04_debian_os_package_inventory.tsv). Repository read-back validates **87 unique installed binary package names/versions** with **74 `amd64`** and **13 `all`** entries. Debian package epoch, architecture-qualified binary name, Debian revision, and `+deb13u`/`~deb13u` suffixes were retained. This is **user-provided inventory**, not a new assistant-run Docker query or external auditor signature.

**Initial source-package checks against official Debian Security Tracker pages** (a narrow desk comparison, not a full 87-package CVE scan):

| Installed Debian binary package(s) | Installed version | Debian tracker release versions seen | Interpretation |
|---|---|---|---|
| `openssl`, `libssl3t64`, `openssl-provider-legacy` | `3.5.4-1~deb13u2` | source `openssl`, trixie `3.5.7-1~deb13u2`, trixie-security `3.5.7-1~deb13u3` | Older installed revision; owner should assess applicable Debian security/point-release updates; **not an asserted CVE match** |
| `libc6`, `libc-bin` | `2.41-12+deb13u1` | source `glibc`, trixie `2.41-12+deb13u4` | Older installed revision; assess relevant source-package advisories and approved upgrade path; **not an asserted CVE match** |

Official desk-review references: `https://security-tracker.debian.org/tracker/source-package/openssl` and `https://security-tracker.debian.org/tracker/source-package/glibc` (consulted 2026-10-27 in assistant web source). Security Tracker data may change after this observation. Neither comparison establishes exploitability, CVE severity, backport patch coverage, image trust or update authorization, and only **two Debian source packages** received this cursory release-version comparison.

**Gate classification:** `OS_PACKAGE_INVENTORY = PASS_USER_SUPPLIED_87`, `OFFICIAL_SOURCE_VERSION_DESK_COMPARISON = PARTIAL_2_SOURCE_PACKAGES`, `DEBIAN_OS_LAYER_CVE_SCAN = NOT_RUN`, `UPSTREAM_IMAGE_PROVENANCE = UNVERIFIED`. The separate Python OSV result (26-package closure, no reported findings), downloaded Wheel/PyPI hashes and local 74/74 test result do not certify the Debian OS layer. Approved, dated, complete Debian trixie vulnerability DB, scanner binary provenance, exact whole-image input and safe isolated scan are still required; previous scanner discovery found `trivy`, `grype`, `syft` not installed on Simorgh. No changes to shared host, packages, containers, running services, images or secrets were made.

**Stage04 IN_PROGRESS** pending authorized Debian image/package vulnerability clearance, official image/installed-byte origin checks and qualified software license approval for the 26 Python dependencies plus separately shipped pip; Stage05 NOT_STARTED/NOT_APPROVED and internal-server gates DEFERRED_TO_STAGE_11.

## 2026-10-27 — No locally discoverable scanner Docker tags on Simorgh

The operator ran only a read-only `sudo docker image ls --format '{{.Repository}}:{{.Tag}}' | grep -Ei '(^|/)(trivy|grype|syft):' || echo 'NO_LOCAL_SCANNER_IMAGE_FOUND'` against the shared Simorgh Docker daemon. Output: **`NO_LOCAL_SCANNER_IMAGE_FOUND`**. This confirms no *matching named/tagged local image* was discovered; it cannot exclude an untagged or differently named image. Earlier `command -v` checks likewise found no `trivy`, `grype` or `syft` executable in PATH.

- **OS_IMAGE_SCANNER_AVAILABLE = NO_APPROVED_SCANNER_IDENTIFIED**. **OS_LAYER_CVE_SCAN = NOT_RUN**: no Debian 13/trixie advisory database was loaded and no CVE results for the 87 dpkg packages or image layers have been produced. A version inventory and desk comparison of 2 Debian source packages do not substitute for a full scan.
- **Blocked dependency:** Security/Infrastructure authorization for a known-version, source/hash-verified scanner plus sufficiently recent Debian vulnerability DB and an isolated scan environment. Prefer an approved, non-shared scanning workstation with reviewed artifact transfer or a separately authorized isolated scanner runner. Do not install onto the shared host, run untrusted remote install scripts, automatically pull images, change Docker configuration/network, export private images externally or mount shared Docker socket to untrusted tools.
- **Required eventual evidence:** exact target image identity; scanner binary/container and database digests, data freshness and Debian 13 support; complete OS package and Python scope distinction; structured CVE report including source-package mapping, fixed versions, unknown/ignored items and remediation or qualified risk signoff. Image provenance and human software-license compliance remain separately OPEN.
- **Stage04 `IN_PROGRESS` / blocker `PENDING_APPROVED_OS_SCANNER_AND_DB`**, Stage05 NOT_STARTED/NOT_APPROVED; the Stage11 enterprise-only ledger remains as defined in D-017, with no implied new approval to defer otherwise locally executable tests.

## 2026-10-27 — Final Stage04 local foundation gate verdict: DONE (D-017 scoped)

**Authoritative current status:** [04_stage04_closure_report.md](04_stage04_closure_report.md) records five normative Stage04 *local* acceptance gates, their implementation references, operator-executed tests and exact unresolved prerequisites. All five local gates are now **PASS in their documented scopes**: trust-boundary/port/secret security design; DI/config/bootstrap/policy/health and safe-log fixture/smoke tests; runtime static prohibitions on unapproved external clients and auto-download; environment/approval/rollback plan; and ten explicitly deferred corporate verification cases. This closure is based on the 2026-10-27 operator-run full Linux suite and offline package evidence together with GitHub source structural review.

**Concrete independently submitted test transcript:** pytest **74/74 PASS**; Stage03 validators **38/38 PASS**; Stage02 regressions **12/12 PASS**; static safety checker **PASS on 9 runtime source files**; Docker/non-root import, runtime pip check and test-runner completion **PASS**. Prior Python supply-chain auditor output reported 26 exact installed distributions, a completed OSV scan with zero findings in the Python package scope, CycloneDX 1.6 output, 26 Linux Wheels matching official PyPI public digest manifests and an offline 26-license-row `REVIEW_REQUIRED` consistency check. The assistant did not re-execute Docker or inspect every original raw artifact byte on Simorgh.

**Critical scope distinction:** Stage04 is a development/security-foundation **DONE**, not legal permission, OS CVE clearance, a hardened deployable artifact or Production-Ready status. The development candidate Debian 13 OS manifest lists 87 installed dpkg packages; full OS package/image vulnerability scan is **NOT_RUN**, no approved scanner/DB exists there, original base image provenance **UNVERIFIED**, and the 26 Linux dependency license decisions plus pip remain `REVIEW_REQUIRED`. These are retained explicitly in S04-S11-06 as **mandatory security/artifact gates before authorized Stage11 promotion and Stage12 release**. User-confirmed D-017 makes actual organizational security testing Stage11, and D-015 final formal acceptance Stage12. No unperformed gate is relabeled PASSED.

**Change scope:** this latest closeout changed documentation and progress classification only. No code/DB/migration/secret/model/network/Production operation was performed. Stage05 stays `NOT_STARTED`; moving to Stage05 requires an explicit follow-up user request.
