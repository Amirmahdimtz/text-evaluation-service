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
