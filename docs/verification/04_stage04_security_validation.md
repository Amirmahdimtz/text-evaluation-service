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
