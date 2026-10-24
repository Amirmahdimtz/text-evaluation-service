# Stage 04 — Independent Security and Architecture Review

Date: 2026-10-24. Repository: `Amirmahdimtz/text-evaluation-service`, branch `main`. Review is scoped exclusively to Stage 04; no Stage 05 database/schema/migration feature was started.

## Gate verdict: NO_GO_STAGE_05 — Stage 04 IN_PROGRESS

The local development application, DI/bootstrap, static policy checks and real Windows health endpoints have previously passed. The implementation nevertheless cannot yet be declared Stage 04 DONE or production approved: direct dependency pins were resolving a known-vulnerable Starlette 0.50.0, the tenant-scoped administrative permission primitive admitted an unscoped path, and a preinstalled logging handler could bypass the redacting formatter.

## Remediation included in this review

| Finding | Severity / reasoning | Fix | Evidence |
|---|---|---|---|
| `fastapi==0.128.2` constrains Starlette to `<0.51`; installed `starlette==0.50.0` is affected by CVE-2026-54283 | HIGH upstream advisory, CVSS 7.5. The current health-only service does not expose a form route, so current exploitability is narrower than the CVE affected-version statement; future API expansion makes this unacceptable as baseline. | Pin `fastapi==0.148.0` plus `starlette==1.9.0` explicitly; `httpx2==2.16.0` is dev-only for modern Starlette TestClient. Guard rejects a Starlette pin below 1.3.1. | PyPI metadata for FastAPI 0.148.0 permits `starlette>=0.46.0`; Starlette release notes confirm 1.3.1 fixes FormParser limits. **New resolved environment install/test is NOT_RUN** in isolated assistant runtime (package index inaccessible). |
| `is_allowed` allowed `rubric:manage` / `metrics:read` without a resource/tenant scope | Incomplete default-deny for future tenant-isolated operations. | Require a verified `ResourceScope` with matching nonempty organization; still require explicit permission and authenticated identity. | New positive and negative local policy regression tests PASS. Final SSO binding/organization-level authorization requires Stage 10/11. |
| `configure_logging` did not replace unsafe formatter on existing handler | Raw message / exception could be emitted if an application logger handler was registered before setup. | Enforce `SafeFormatter` on every existing handler as well as newly created handlers. | New synthetic secret/exception leak regression PASS. Third-party/server/gateway log redaction remains Stage 11. |
| `urlsplit` strips some controls before address validation | Ambiguous internal endpoint strings could reach future service clients unmodified. | Reject control characters, whitespace and backslash before parsing. | Five negative endpoint regressions PASS. Real outbound firewall remains Stage 11. |
| No reproducible local dependency closure/license/RECORD metadata evidence | A manifest pin and `pip check` do not equal supply-chain approval. | Added offline-only `audit_stage04_dependencies.py` for exact-direct-pin checking, complete installed closure metadata and installed RECORD SHA-256 verification; inventory explicitly marks vulnerability/licensing/provenance unfinished. | Three focused auditor tests PASS. **Updated dependency inventory cannot execute to completion on this assistant's old installed FastAPI/Starlette environment.** |

Public advisory sources (retrieved 2026-10-24):
- https://nvd.nist.gov/vuln/detail/CVE-2026-54283
- https://starlette.dev/release-notes/
- https://pypi.org/pypi/fastapi/0.148.0/json
- https://pypi.org/project/pip-audit/

## Tests and evidence boundary

| Execution | Result | What was actually tested |
|---|---|---|
| Existing Stage 04 26 tests on user-local Windows Python 3.12, pre-review dependencies | 26/26 PASS (previous user-provided evidence) | Original baseline including Uvicorn 18080 and real HTTP live/ready; **not new pinned dependencies** |
| New `tests/test_security_review.py` + `tests/test_dependency_inventory.py` + `tests/test_safety_guard.py` | **11/11 PASS_ASSISTANT_LOCAL** | Security fixes, pin guard, offline-audit parser/status controls, using assistant's original shared Python 3.13.5 installed packages |
| `compileall -q src tests scripts` and updated Stage 04 static guard, **reviewed subset** | PASS_ASSISTANT_LOCAL | Locally recreated modified source and new scripts, not a complete GitHub checkout; reports 2 runtime files in subset |
| Full original 26 tests on upgraded FastAPI 0.148.0/Starlette 1.9.0 | **NOT_RUN** | Requires a clean installation and execution on user's Windows / approved CI |
| Complete Stage 02/03 regressions on new dependency pins | **NOT_RUN** | Previously passed before this review, no new claims |
| Vulnerability scan on resolved package graph (`pip-audit`) | **NOT_RUN** | Requires an up-to-date approved advisory DB; not an upstream security proof |
| Wheel hashes, full CycloneDX SBOM, license approval and provenance | **NOT_RUN/PARTIAL_LOCAL_TOOLING** | Offline installed RECORD digest comparison is not upstream wheel integrity / approval |
| Corporate SSO/Vault/No-Egress/firewall/GPU/model/DR/load/E2E | **DEFERRED_TO_STAGE_11** | D-017; no organizational infrastructure/data contacted |

### Clean Windows re-verification (repository root)

Use only synthetic data, and ensure installing from approved public index is acceptable on this **local development machine** (never on isolated production infrastructure). Recreate the disposable environment to avoid a stale dependency resolution:

```powershell
git pull --ff-only origin main
py -3.12 -m venv .venv-review
.\.venv-review\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements-dev.txt
.\.venv-review\Scripts\python.exe -m pip check
.\.venv-review\Scripts\python.exe -m pytest -q tests/test_foundation.py tests/test_security_review.py tests/test_dependency_inventory.py tests/test_safety_guard.py
.\.venv-review\Scripts\python.exe -m compileall -q src tests scripts
.\.venv-review\Scripts\python.exe scripts/verification/check_stage04_safety.py
.\.venv-review\Scripts\python.exe scripts/verification/check_stage02_docs.py
.\.venv-review\Scripts\python.exe scripts/verification/test_check_stage02_docs.py
.\.venv-review\Scripts\python.exe scripts/benchmark/test_validate_stage03_outputs.py
.\.venv-review\Scripts\python.exe scripts/verification/audit_stage04_dependencies.py --output "$env:TEMP\stage04-dependency-inventory.json"
.\.venv-review\Scripts\python.exe -m pip freeze > "$env:TEMP\stage04-freeze.txt"
```

For a public advisory-service audit from an approved local development machine, install a vetted exact-version `pip-audit` in a **separate audit environment** and scan the reviewed venv (`--path` or equivalent according to the installed pip-audit version). Do not send business text, credentials or any confidential data to external scanners. Save date, database/service, exit status, reviewed components and findings. Validate upstream wheel SHA-256 from an approved package repository, review licenses with Security/Legal, and generate a standard CycloneDX SBOM before closing Stage 04.

After updated dependencies pass, check HTTP on configured development port 18080 exactly as in the Stage 04 validation report. Existing `appsettings.yaml` for staging/production was not modified and deployment remains unapproved.

**Stage 05 entry criteria:** all relevant local tests on the updated complete dependency graph PASS, zero unresolved unaccepted local High/Critical findings, and transitive inventory/license/vulnerability/integrity evidence reviewed. Because these conditions are currently **not met**, **entry approval is withheld**. Under D-017, real corporate-environment security testing belongs to Stage 11 and is not incorrectly marked PASS.

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


## Review update: upgraded full-suite regression fixed (2026-10-24)

The user ran the new `main` commit `e16c5d6` in the already installed Python 3.12 Windows `.venv-review`: **37/37 pytest PASS (10.21s)**, `pip check` PASS. This supersedes the pre-fix 35 PASS / 2 FAIL run and closes that compatibility issue with observed user-local evidence. Port `18080` is occupied by Python PID 8896; a separate Uvicorn instance launched successfully with `--port 0` and announced `127.0.0.1:50165` (PID 13500). **No `/health/live` or `/health/ready` requests to port 50165 have been submitted yet**; do not conflate with historical health checks on 18080.

The **Gate verdict remains NO_GO_STAGE_05 / IN_PROGRESS** solely because full dependency supply-chain review is still outstanding: historical offline installed metadata/RECORD inventory of 27 packages is not an independently approved CVE scan, standardized SBOM, license decision or provenance/integrity attestation. Corporate-only tests remain `DEFERRED_TO_STAGE_11`. See [security validation](04_stage04_security_validation.md).


## Upgraded Windows HTTP health confirmation — 2026-10-24

User-run PowerShell `Invoke-RestMethod` calls to both `/health/live` and `/health/ready` at `127.0.0.1:50165` returned `alive` and `ready`. This supersedes the preceding `NOT_RUN` statement for health GETs on the upgraded local environment; **HTTP bootstrap smoke PASS_USER_LOCAL**, in addition to the verified **37/37 full test suite** and `pip check` PASS. It does not verify business subsystems or corporate networking. **NO_GO_STAGE_05** remains in effect only because the standalone Stage 04 supply-chain security acceptance gates (current CVE scan, standardized SBOM, licensing/provenance/integrity) have not been closed. See [security validation](04_stage04_security_validation.md).


## Supply-chain remediation tooling (2026-10-24)

The remaining local Stage 04 supply-chain controls now have dedicated code/tests and a [self-contained Windows runbook](04_stage04_supply_chain_runbook.md). The pinned tool environment is separate from runtime. The offline comparator uses the installed RECORD-tested closure, strict CVE-result coverage, CycloneDX JSON 1.6 package coverage, wheelhouse ZIP/sha256 validation, optional public PyPI digest cross-check and **explicit** per-package license decisions (no auto-approval). **15/15 new isolated synthetic tests PASS** under Python 3.13.5. Direct vulnerability feed, approved license evidence, wheel-to-PyPI provenance hash checks and environment-specific full-suite retest remain unexecuted due to access restrictions, and are not mislabeled PASS. NVD desk review of CVE-2026-54283 establishes only that the pinned Starlette 1.9.0 is newer than its 1.3.1 fix threshold, not closure-wide safety. Gate: `NO_GO_STAGE_05` / `IN_PROGRESS` until supply-chain evidence is genuinely reviewed.
