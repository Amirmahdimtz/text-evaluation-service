# Stage 04 — Local Dependency Supply-Chain Evidence and Review

Date: 2026-10-24. Status: `IN_PROGRESS`, **not Production-approved**. Owners: Stage 04 engineering for local controls and test evidence; Security/License reviewer to assess the metadata and policy; organizational infrastructure and publisher-attestation acceptance in Stage 11 (D-017). Business sign-off timing remains Stage 12 (D-015).

## Scope and trust boundaries

The codebase contains only public pinned Python libraries at Stage 04. No private documents, evaluation texts, customer credentials, model weights, or corporate installation endpoints may be submitted to public scanners. The audit below is **opt-in on the user's authorized local development workstation**; it queries a public package advisory service using package names and versions only. Executing the same against the protected internal network requires distinct approval and local/offline feeds. No service runtime outbound capability is added; the audit tools are installed into `.venv-supply-chain`, not the application `.venv-review`.

Existing Stage 04 proof: user-supplied Windows Python 3.12 logs confirmed 37/37 pytest PASS, `pip check` PASS, 27 components in the installed RECORD-integrity/metadata inventory, and live/ready HTTP responses from the upgraded FastAPI/Starlette process on localhost port 50165. This is **not** a CVE, license or trusted upstream wheel audit.

## One-command evidence collection on Windows (PowerShell)

From the cloned repository root on a workstation where downloading public Python package metadata is authorized:

```powershell
# Update only while no incompatible uncommitted changes are present.
git pull --ff-only origin main
$env:TES_ENVIRONMENT = 'development'
$env:PYTHONPATH = '.'

# Existing reviewed Python 3.12 .venv-review environment must still be installed.
# Use a new -EvidencePath on each run. The script NEVER deletes earlier evidence.
.\scripts\verification\run_stage04_supply_chain.ps1 `
  -PythonPath '.\.venv-review\Scripts\python.exe' `
  -EvidencePath '.stage04-evidence-20261024' `
  -VerifyPublicPyPIDigests
```

**Public requests:** Installing `requirements-audit.txt` (pinned `pip-audit` and `cyclonedx-bom` tools), public vulnerability lookups via PyPI, downloading **package wheels**, and optional public release digest lookup **only for package name/version**. It does not transmit application text or submit code content to external LLMs.

The script collects `inventory.json`, `pinned-closure.txt` (exact full dependency closure), `vulnerabilities.json` (`pip-audit`, with exit status), `sbom.cdx.json` (CycloneDX JSON v1.6 from actual target interpreter), `wheelhouse/`, `wheel-hashes.json`, optional `pypi-digests.json`, `license-review.json` (blank *review-required* template), `pip-freeze.txt`, and `run-summary.json`. Data and downloaded wheels are **local-only, outside Git**. The output directory is never overwritten automatically. If any subprocess fails, do **not** infer partial success; inspect its nonzero code and preserve existing artifacts.

### Exact audit commands (when investigating individual failures)

```powershell
.\.venv-review\Scripts\python.exe -m pip check
.\.venv-supply-chain\Scripts\python.exe -m pip_audit --strict --path '.\.venv-review\Lib\site-packages' --vulnerability-service pypi --progress-spinner off --format json --output '.stage04-evidence-20261024\vulnerabilities.json'
.\.venv-supply-chain\Scripts\python.exe -m cyclonedx_py environment '.\.venv-review\Scripts\python.exe' --spec-version 1.6 --output-format JSON --output-file '.stage04-evidence-20261024\sbom.cdx.json'
```

`pip-audit` exit **0** means no vulnerabilities reported by that selected advisory feed as of the run; exit **1** means vulnerabilities were found; failure to contact the service or collect packages must **not** be interpreted as 0. The strict offline review comparator also requires that every installed dependency in `inventory.json` has a name/version-matched audit entry with explicit `vulns` field; missing/partial records fail closed. The generator may include additional environment support tools such as pip; vulnerabilities in any returned entry are not silently ignored.

## Wheel integrity versus publisher authenticity

- `audit_stage04_dependencies.py` checks installed wheel `RECORD` hashes only. These are local package/file consistency checks, not upstream provenance.
- `review_stage04_supply_chain.py hash-wheels` checks that each name/version in the installed dependency inventory has exactly one wheel, validates ZIP/WHEEL/METADATA structure, and computes local SHA-256. No unchecked extra distribution is accepted.
- `review_stage04_supply_chain.py verify-pypi` (opt-in; public network) validates each exact wheel filename and SHA-256 against the `https://pypi.org/pypi/{project}/{version}/json` release file digest returned over TLS. This is independent of the locally observed wheel bytes, **not** a Trusted Publisher attestation or signed SLSA provenance. Formal attestation, organization registry/signatures and artifact-transfer provenance remain Stage 11 requirements.
- Keep the complete wheelhouse and immutable hash manifest in the local evidence vault. Before installing into an isolated internal network, Security/MLOps must approve the transfer and provenance; never install/download straight from the public index in production.

## License evidence and final local gate validation

`license-review.json` intentionally starts with `REVIEW_REQUIRED` for all packages. Metadata may be incomplete or ambiguous. A qualified reviewer must identify declared SPDX license/actual bundled license texts, assess obligations under organizational policy, record an explicit `license_expression`, reviewer identity/role and evidence for every name/version, and enter `APPROVED` **only when justified**. Formal employer/product sign-off occurs in Stage 12, but it does **not** authorize inventing license clearance here. No blanket allowlist, auto-approval or implied Legal decision is implemented.

After the CVE report, SBOM, downloaded wheelhouse, independent PyPI digests and license decisions have been reviewed and produced, validate the complete evidence bundle **offline**:

```powershell
$e = '.stage04-evidence-20261024'
.\.venv-review\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py evaluate `
  --inventory "$e\inventory.json" `
  --audit "$e\vulnerabilities.json" `
  --sbom "$e\sbom.cdx.json" `
  --hashes "$e\wheel-hashes.json" `
  --pypi-hashes "$e\pypi-digests.json" `
  --wheelhouse "$e\wheelhouse" `
  --licenses "$e\license-review.json" `
  --output "$e\local-gate-evaluation.json"
```

The validator rejects incomplete or nonmatching component/version coverage, vulnerable packages reported by the audit feed, invalid CycloneDX 1.6 structure indicators, missing/different wheel SHA-256, altered PyPI digest records, and unreviewed licenses. Its positive result is deliberately labelled `PASS_LOCAL_EVIDENCE_ONLY`, **not** a cryptographically signed supply-chain attestation or Production approval. Security review of advisory feed freshness, scanner coverage, third-party license terms and authorized publisher provenance is still required. Publisher identity and protected environment No-Egress remain Stage 11 gates under D-017.

**Current evidence status** at authoring: external CVE scan **NOT_RUN**, CycloneDX SBOM for upgraded Windows venv **NOT_RUN**, downloadable wheel SHA-256 comparison **NOT_RUN**, PyPI cross-check **NOT_RUN**, license review **NOT_APPROVED**; the earlier metadata-only inventory of 27 packages **PASS_USER_LOCAL**. The new offline validator unit tests run in the assistant's separate Python 3.13.5 environment using **synthetic package fixtures only**, not the user's Windows venv. Do not change Stage 04 to `DONE` solely because the tooling is committed. Do not begin Stage 05 without explicit user instruction, even after Stage 04 Gate closes.


## Windows PowerShell ExecutionPolicy preflight (2026-10-24)

A user-local PowerShell transcript confirmed **52/52 pytest PASS in 35.24s** on `main` at `684f486` after pulling the new supply-chain test files. Starting `run_stage04_supply_chain.ps1` failed **before script execution** with `PSSecurityException: running scripts is disabled on this system`. Thus **no audit report, SBOM, wheel or license review is claimed produced by that attempt**; the dependency supply-chain Gate is still `NOT_RUN / IN_PROGRESS`.

On a personal/authorized development machine only, first inspect which policy source applies (no modifications):

```powershell
Get-ExecutionPolicy -List
Test-Path '.stage04-evidence-20261024'
```

If `MachinePolicy` and `UserPolicy` are both `Undefined` and local security policy permits running this reviewed project script, use a **separate one-time PowerShell process** with `RemoteSigned` (which does not persistently change ExecutionPolicy and remains stricter than `Bypass`):

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\\scripts\\verification\\run_stage04_supply_chain.ps1" -PythonPath ".\\.venv-review\\Scripts\\python.exe" -EvidencePath ".stage04-evidence-20261024" -VerifyPublicPyPIDigests
```

Execute it from the repository root and only if public **dependency package metadata** lookups and wheel downloads are authorized on that workstation. This mechanism does **not** override Group Policy-enforced MachinePolicy/UserPolicy. If an organizational policy disallows scripts, do not disable or bypass it: consult the local administrator/security team for an approved procedure. If the evidence directory already exists, choose an unused new name; the script deliberately fails closed instead of overwriting evidence. The command's return value and generated evidence must be independently checked; PowerShell launch alone is **not** supply-chain Gate approval. Do not run the script in an isolated company production network without separate authorization.


## Windows PowerShell native quoting regression and fix — 2026-10-24

User-local evidence from `main` at `9c6cb03`: all `Get-ExecutionPolicy -List` scopes were `Undefined` and the one-off `-ExecutionPolicy RemoteSigned` script invocation **started successfully**. `pip check` reported `No broken requirements found`, then the original inline `python -c '...["purelib"]...'` lost nested string quotes in Windows PowerShell native argument passing, raising `NameError: name 'purelib' is not defined`. **Collector stopped before dependency inventory, CVE scan, SBOM, wheel checks, public digest review, or license decisions.** This was a script/quoting defect; do not mark Stage 04 gate PASS.

The collector now invokes `review_stage04_supply_chain.py site-packages` via the **reviewed target Python**; this CLI resolves `sysconfig.get_path("purelib")` in a real source file without any embedded command-line quotes, ensures the directory exists and prints only its path. The output directory is now created after this preflight. The relevant Stage 04 synthetic regression tests and an isolated CLI invocation passed in the assistant's Linux/Python 3.13 environment (**17/17 supply-chain test module PASSED**); the corrected Windows PowerShell collector itself remains **PENDING_USER_LOCAL**.

The initial failed collector created `.stage04-evidence-20261024` before exiting. **Do not delete or overwrite it**; after pulling the fix, use a new, unused evidence path, e.g.:

```powershell
git pull --ff-only origin main
.\.venv-review\Scripts\python.exe -m pytest -q tests
.\.venv-review\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py site-packages
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\scripts\verification\run_stage04_supply_chain.ps1" -PythonPath ".\.venv-review\Scripts\python.exe" -EvidencePath ".stage04-evidence-20261024-02" -VerifyPublicPyPIDigests
```

Use this one-off command **only** on a workstation where executing reviewed scripts and public package metadata lookups are authorized. No persistent ExecutionPolicy changes or deletion required. If the new path exists, choose another unused name. The corrected script still fails closed on any incomplete tool/evidence step. An audit run may report vulnerabilities or unsupported wheel availability; those outcomes must be evaluated rather than bypassed. The Stage 04 Gate remains `IN_PROGRESS` until real scan/license/wheel/SBOM evidence is reviewed.


## Windows dependency download timeout (2026-10-24)

The user installed the latest Stage 04 fix (`359e6ea`), successfully printed the target `site-packages` path using the new CLI and ran the **entire 54-test suite: 54 passed in 12.40s**. The authorized one-off PowerShell collector then passed `pip check`, installed-RECORD metadata inventory (**27 packages**) and generated the exact frozen dependency closure and blank license-review template. It proceeded to `pip install -r requirements-audit.txt` in the separate audit virtualenv, but `files.pythonhosted.org` timed out during the `chardet` wheel download (pip default 15-second socket timeout). The collector correctly **failed closed with exit code 2**; vulnerability scanning, CycloneDX generation, wheelhouse digest verification, PyPI digest comparison and license approvals have **not run** on this Windows attempt.

The collector now uses **bounded per-command** pip networking options (`--timeout 120 --retries 6`) for both audit-tool installation and exact-wheel download. Neither system proxy/firewall nor persistent pip configuration is modified, and failures still stop the run. The already created `.stage04-evidence-20261024-02` is incomplete historical evidence; **do not delete, overwrite or present it as approved**. The existing `.venv-supply-chain` may be reused; pip resolves/install missing dependencies on retry without dropping evidence.

From repository root on an authorized workstation, use a **fresh evidence directory name**:

```powershell
git pull --ff-only origin main
.\.venv-review\Scripts\python.exe -m pytest -q tests
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\scripts\verification\run_stage04_supply_chain.ps1" -PythonPath ".\.venv-review\Scripts\python.exe" -EvidencePath ".stage04-evidence-20261024-03" -VerifyPublicPyPIDigests
```

If public package downloads continue to time out, report the failed host and step. Do not disable SSL verification, skip vulnerability scans, change corporate network controls, or artificially mark the local Gate as passed. An authorized package mirror or existing verified wheel cache can be evaluated as an explicit follow-up; **do not silently substitute an unknown index**. New network-resilience regression and an isolated Python compile test passed in the assistant container; the corrected Windows collector and external audit remain **PENDING_USER_LOCAL**.


## Advisory scan timeout and reuse of verified local evidence — 2026-10-24

User-local evidence: **55/55 tests PASS**, tools successfully installed, 27 wheel files downloaded, and wheel manifest plus PyPI digest checks returned success. However, the `pip-audit` vulnerability query timed out against `pypi.org` with its own `--timeout` default of **15 seconds**; previous `pip install --timeout 120` does not govern this command. The scanner returned exit 1 on network error with **no verified complete JSON**. Consequently `vulnerabilities.json` must not be marked PASS, and the local license review is still unapproved. The collected `.stage04-evidence-20261024-03` directory is **partial evidence to preserve**, not to overwrite or delete.

The collector now uses **`pip-audit --timeout 120`** and validates the full report with `review_stage04_supply_chain.py audit-status` (exact package/version coverage, explicit vulnerability lists). The CLI distinguishes `AUDIT_COMPLETE_NO_REPORTED_FINDINGS` from `AUDIT_COMPLETE_WITH_FINDINGS`; it returns nonzero on missing/partial/unreadable scan evidence. Public service failures abort the collector fail-closed; a complete report with known vulnerabilities is retained for remediation but does not approve the Gate. Four focused synthetic/CLI/static regression tests added; **22/22 isolated tests PASS**, Windows scanner not yet rerun.

### Targeted Windows audit retry (avoids redownloading 27 wheels)

After pulling the fix, from the repository root run the commands below on an authorized development workstation; they send **only public package names/versions** to the advisory service. Use a *new report filename* to preserve the failed attempt's history:

```powershell
git pull --ff-only origin main
.\.venv-review\Scripts\python.exe -m pytest -q tests

$e = '.stage04-evidence-20261024-03'
$installed = & .\.venv-review\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py site-packages
& .\.venv-supply-chain\Scripts\python.exe -m pip_audit --strict --path $installed --vulnerability-service pypi --timeout 120 --progress-spinner off --format json --output "$e\vulnerabilities-retry.json"
$auditExit = $LASTEXITCODE
Write-Host "pip-audit exit: $auditExit"

if (Test-Path -LiteralPath "$e\vulnerabilities-retry.json" -PathType Leaf) {
    & .\.venv-review\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py audit-status --inventory "$e\inventory.json" --audit "$e\vulnerabilities-retry.json"
    Write-Host "report verification exit: $LASTEXITCODE"
} else {
    Write-Warning 'No complete audit report produced; Stage 04 remains OPEN'
}
```

Do not interpret the `pip-audit` exit code alone as a vulnerability count; **valid JSON and full inventory coverage are mandatory**. If the audit report is complete and identifies vulnerabilities, address or explicitly risk-review them; do not ignore findings or run `--fix` automatically. If no vulnerabilities are reported, this only closes the advisory-scan subgate for the selected PyPI feed/date; license decisions, independent evidence review, and full Stage 04 acceptance are still required. The offline `evaluate` command in this runbook accepts `--audit "$e\vulnerabilities-retry.json"` while reusing all other `-03` artifacts once all 27 license reviews have been legitimately completed and recorded. Do **not** invent a reviewer name, license expression, signed attestation or APPROVED decision.

For a later complete collector run, use a *new* unused EvidencePath such as `.stage04-evidence-20261024-04`; the original `-03` remains immutable historical evidence. No further corporate network/secret/production changes are authorized.


## Alternative advisory service after PyPI connection resets — 2026-10-24

User verified latest `main` at `229df23` on Windows Python 3.12: **59/59 tests PASS (26.88s)**. The targeted `pip-audit --timeout 120 --vulnerability-service pypi` attempt raised `requests.exceptions.ConnectionError` / `RemoteDisconnected` when connecting to the PyPI service and returned exit 1 **without creating `vulnerabilities-retry.json`**. This is a **network/service failure**, not a vulnerability finding or advisory clearance. The already preserved `.stage04-evidence-20261024-03` records 27 installed packages, SBOM/wheel hashes and public PyPI wheel digest checks according to earlier user logs; full artifacts have not been independently read by the assistant. License review remains OPEN.

`pip-audit==2.10.1` supports the **OSV** vulnerability service through `--vulnerability-service osv` (upstream pip-audit CLI, https://github.com/pypa/pip-audit). OSV is an **alternate public advisory feed**, not a proven replacement for complete PyPI advisory coverage and not a bypass of a corporate network policy. The collector now accepts only explicit `-VulnerabilityService pypi` (default) or `-VulnerabilityService osv`, persists the selected service and the provider-specific JSON report filename in `run-summary.json`, and **never automatically switches providers**. Its full-coverage `audit-status` check still fails closed for missing/partial JSON; a report with findings cannot approve Stage 04.

### Targeted OSV retry using existing evidence (no redownload)

On a workstation with approval to send **public package names and versions** to `api.osv.dev`, from the repository root:

```powershell

git pull --ff-only origin main
.\.venv-review\Scripts\python.exe -m pytest -q tests

$e = '.stage04-evidence-20261024-03'
$installed = & .\.venv-review\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py site-packages
& .\.venv-supply-chain\Scripts\python.exe -m pip_audit --strict --path $installed --vulnerability-service osv --timeout 120 --progress-spinner off --format json --output "$e\vulnerabilities-osv.json"
$auditExit = $LASTEXITCODE
Write-Host "OSV pip-audit exit: $auditExit"
if (Test-Path -LiteralPath "$e\vulnerabilities-osv.json" -PathType Leaf) {
    & .\.venv-review\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py audit-status --inventory "$e\inventory.json" --audit "$e\vulnerabilities-osv.json"
    Write-Host "OSV coverage validation exit: $LASTEXITCODE"
} else {
    Write-Warning 'No complete OSV report; Stage 04 remains OPEN'
}
```

A subsequent **full** collector run may explicitly select OSV with `-VulnerabilityService osv` and **must use a new unused EvidencePath**, e.g. `.stage04-evidence-20261024-04`; do not delete/overwrite `-03`. The targeted OSV output is not a full collector run and does not automatically create a `run-summary.json` binding that report to the existing wheelhouse. If OSV also fails due to approved-network restrictions, use an authorized mirror/feed or a different allowed workstation, preserving original evidence and without disabling TLS validation. If OSV returns known vulnerabilities, assess/fix them; do not ignore records or misreport the feed as PyPI. Internal-server/inference artifacts remain Stage 11 under D-017; Stage 04 Gate remains **IN_PROGRESS** until package findings, license decisions and local evidence have been reviewed.


## Real OSV security findings and offline findings summary — 2026-10-24

**User-executed Windows Python 3.12 evidence:** after pulling `main` at `9ea0083`, all **61/61 project tests passed in 30.29 seconds**. `pip-audit==2.10.1`, pointed at the reviewed `.venv-review` environment and `--vulnerability-service osv`, **completed its public advisory scan** and reported `Found 14 known vulnerabilities in 2 packages`. The scanner exited **1** due to identified findings, **not** due to network failure. The project's existing `audit-status` output was `AUDIT_COMPLETE_WITH_FINDINGS`, validation exit **0**, meaning the entire inventory was represented in a parseable report. **This is not a successful security Gate.** Do not infer package identities, severities, or fixed versions from the count alone; full advisory JSON remains on the user's workstation and has not been inspected in this repo review.

A dedicated **offline and fail-closed** `audit-findings` command now generates a narrow public-metadata-only summary from the already completed scan and its matching original installed-inventory manifest. It records only package name/installed version, advisory ID/aliases and scanner-reported `fix_versions`, package-closure membership, advisory source, finding counts and `stage04_gate: OPEN`; it never copies descriptions, secrets, host paths or private service text, and performs **zero network I/O or package changes**. Advisory aliases can describe the same underlying issue; do not assume 14 independent exploit paths. 

Run **from the repository root**, retaining the original complete `vulnerabilities-osv.json`, `inventory.json` and Wheel/SBOM evidence unchanged:

```powershell
git pull --ff-only origin main
.\.venv-review\Scripts\python.exe -m pytest -q tests
$e = '.stage04-evidence-20261024-03'
.\.venv-review\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py audit-findings --inventory "$e\inventory.json" --audit "$e\vulnerabilities-osv.json" --source osv --output "$e\findings-summary-osv.json"
Get-Content "$e\findings-summary-osv.json"
```

The command prints `AUDIT_FINDINGS_SUMMARY: 2 packages, 14 advisory records; gate OPEN` if the supplied files contain precisely the previously reported results and their fields pass validation; counts are **not guaranteed until actually run**. The generated summary contains only **public package and advisory metadata**, not private business text. Share this summary (not any confidential environment settings or raw application data) for a package-by-package decision on whether each issue is in runtime or dev-only closure, availability of a supported patched version, exploitability, direct/transitive constraints and precise retesting. **Never blindly upgrade or run `pip-audit --fix`.**

Upstream fix versions returned in JSON are *candidates*, not approvals. If the package is a shared tool (for example `pip`) beyond the 27-package source closure, it is still included in this report and marked `in_dependency_closure: false`; the reviewer must determine whether it affects runtime/deployment. After approved package remediation, reinstall into a clean disposable test environment, rerun the entire test suite, regenerate all evidence in a **fresh immutable directory**, rerun OSV/PyPI or authorized advisory check and separately complete qualified license review. The 27 wheels and hashes from the old environment are **not** proof for changed versions. Corporate-only security remains `DEFERRED_TO_STAGE_11`, Stage 05 remains `NOT_STARTED`.

New summary CLI and its adversarial regression tests: **28/28 supply-chain tests PASS_ASSISTANT_LOCAL (Python 3.13.5)**; compilation PASS. Combined Windows suite including this new change **PENDING_USER_LOCAL**. Stage 04 remains **IN_PROGRESS / NO_GO_STAGE_05**.


## Remediation of confirmed OSV findings in pip and pytest — 2026-10-24

The user-supplied `findings-summary-osv.json` from Python 3.12 Windows on `114c659` is **complete** and corresponds to **65/65 passing tests (37.46 seconds)**. OSV reported **14 records, seven unique PYSEC IDs / CVE groups**: six issues in the **bootstrap installer `pip==25.0.1`** (12 duplicate advisory records, **not a direct project dependency**) and one in **dev-only `pytest==9.0.2`** (two duplicate advisory records, **in the 27-package dependency closure**). Affected package data is public metadata, not confidential evaluation text.

**Version selection and independently verified sources:**
- `pytest==9.0.3`: patch for CVE-2025-71176, which is specifically about insecure temporary directories on Unix. Source: https://www.pytest.org/en/latest/changelog.html and https://github.com/advisories/GHSA-6w46-j5rx-g56g ; Python >=3.10 is supported.
- `pip==26.2.2`: fixes all six reported pip advisory version ranges, including CVE-2026-13346 (patched in 26.2.0). Released October 20, 2026; official Python and PyPI sources: https://pypi.org/project/pip/26.2.2/ and https://www.python.org/downloads/release/python-3149/ . The official pip wheel SHA256 is `fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70`. This pin targets **only disposable development/audit virtualenv installers**; do not introduce `pip` as a production runtime dependency or upgrade system Python.

**Changes to Stage 04 only:** `requirements-dev.txt` pins pytest 9.0.3; static safety guard rejects older/missing pytest pin; the offline supply-chain verifier now has `bootstrap-check` requiring `pip>=26.2.2`, rejects unverifiable/prerelease versions, and the PowerShell collector runs it on **both** reviewed target Python and dedicated audit Python **before** installing or downloading packages. Neither pip nor pytest is upgraded automatically by a scanner. Minimal isolated code/test subset in assistant Python 3.13.5: **37/37 tests PASSED** (32 supply-chain, two static safety, three installed-inventory regressions); `compileall` PASSED. Assistant's sandbox still has an **older pip and pytest** and could not install the patched public versions, so *upgraded-target Windows installation, complete integration suite and repeat OSV audit are PENDING_USER_LOCAL*.

### Exact Windows remediation on authorized development workstation

**Preserve `.stage04-evidence-20261024-03` and the OSV finding report.** Use the official hashed pip wheel direct link below, as published by PyPI/Python.org, only if outbound public package downloads are permitted. This is a change **only inside the existing `.venv-review` and `.venv-supply-chain` environments**, with no system-wide pip/Secret/Production changes:

```powershell
git pull --ff-only origin main
$pipWheel = 'https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70'
& .\.venv-review\Scripts\python.exe -m pip install --disable-pip-version-check --timeout 120 --retries 6 --no-deps $pipWheel
& .\.venv-supply-chain\Scripts\python.exe -m pip install --disable-pip-version-check --timeout 120 --retries 6 --no-deps $pipWheel
& .\.venv-review\Scripts\python.exe -m pip install --disable-pip-version-check --timeout 120 --retries 6 -r requirements-dev.txt

& .\.venv-review\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py bootstrap-check
& .\.venv-supply-chain\Scripts\python.exe scripts/verification/review_stage04_supply_chain.py bootstrap-check
& .\.venv-review\Scripts\python.exe -m pip check
& .\.venv-review\Scripts\python.exe -m pytest -q tests
& .\.venv-review\Scripts\python.exe -m compileall -q src tests scripts
& .\.venv-review\Scripts\python.exe scripts/verification/check_stage04_safety.py

# The old 27-package closure changed (pytest): new immutable evidence is mandatory.
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\scripts\verification\run_stage04_supply_chain.ps1" -PythonPath ".\.venv-review\Scripts\python.exe" -AuditPythonPath ".\.venv-supply-chain\Scripts\python.exe" -EvidencePath ".stage04-evidence-20261024-04" -VulnerabilityService osv -VerifyPublicPyPIDigests
```

Stop and report the first failed command; do not treat partial results as Gate PASS. If `.stage04-evidence-20261024-04` already exists, choose a new unique name. The new OSV scan **must** confirm complete coverage and no new unaccepted vulnerabilities; the collector must regenerate all Wheel hashes, public PyPI release-digest matches and CycloneDX SBOM from the **new** installed dependency closure. Its `license-review.json` is an **unapproved template**; license obligations must be evaluated by the responsible reviewer for all installed packages. Package hashes matched over TLS are not a signed upstream publisher attestation. Local Stage 04 stays **IN_PROGRESS / NO_GO_STAGE_05**, while corporate No-Egress/SSO/Vault and organization artifact provenance remain Stage 11 under D-017.

**Note:** An observed Windows-only exploitability limitation of the pytest CVE does not waive patching; this project is intended for Unix/Linux server deployment. The new static guard is a pin-floor regression check, not a current vulnerability database scan.

## Starlette wheel index discovery failure and verified local-source recovery — 2026-10-24

**User-local Windows Python 3.12 evidence on HEAD `5be8039`:** GitHub access restored, `pytest==9.0.3` installed, both isolated environments have `pip==26.2.2` and `bootstrap-check` PASS, `pip check` PASS, full test suite **70/70 PASS in 57.29s**. The fresh `.stage04-evidence-20261024-05` collector passed 27-package metadata inventory, complete OSV audit **`No known vulnerabilities found`**, and CycloneDX SBOM generation. However, `pip download` aborted with `No matching distribution found for starlette==1.9.0` and `from versions: none`. The collector correctly failed closed; this fresh run produced **no complete 27-wheel integrity/PyPI-digest report or final run-summary**. The prior immutable `-05` evidence must be preserved. No known vulnerabilities in this one OSV scan does not prove permanent/complete immunity or satisfy the license Gate.

**PyPI verification, Oct 24, 2026:** official [starlette 1.9.0 release](https://pypi.org/project/starlette/1.9.0/) provides `starlette-1.9.0-py3-none-any.whl` for **Python >=3.11**, uploaded Oct 18, 2026. Its published SHA-256 is `fd3f159936e882d06c1108f84688f7cda2cf85fc6a592a50edbd175e882c2ddc`. This means the transient package-index candidate failure **does not support a package/Python incompatibility conclusion**. The previous `-04` wheelhouse contains that wheel according to user-local download log and can be considered **only if the actual local file matches this independent public checksum**. Official [pip download docs](https://pip.pypa.io/en/stable/cli/pip_download/) confirm use of a local directory through `--find-links`; `PIP_FIND_LINKS` is the process-scoped environment equivalent. This source is *not* a signed builder provenance guarantee; independent official publisher attestations can be reviewed separately.

### Non-destructive recovery with an explicitly verified historical wheelhouse

On the authorized Windows development workstation, **after confirming the patched repository and Python environment still match**, run from the repository root:

```powershell
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw 'Cannot verify current checkout' }

$source = '.stage04-evidence-20261024-04\wheelhouse'
$wheel = Join-Path $source 'starlette-1.9.0-py3-none-any.whl'
$sha256 = 'fd3f159936e882d06c1108f84688f7cda2cf85fc6a592a50edbd175e882c2ddc'
if (-not (Test-Path -LiteralPath $wheel -PathType Leaf)) {
    throw 'Trusted prior Starlette wheel missing; cannot recover offline'
}
if ((Get-FileHash -LiteralPath $wheel -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha256) {
    throw 'Starlette wheel differs from official PyPI digest'
}
if (Test-Path -LiteralPath '.stage04-evidence-20261024-06') {
    throw 'Evidence output already exists; choose a new unique directory'
}

$previousLinks = [Environment]::GetEnvironmentVariable('PIP_FIND_LINKS', 'Process')
try {
    # Local source is allowed only after byte-for-byte comparison to the official SHA256.
    $env:PIP_FIND_LINKS = (Resolve-Path -LiteralPath $source).Path
    powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ".\scripts\verification\run_stage04_supply_chain.ps1" -PythonPath ".\.venv-review\Scripts\python.exe" -AuditPythonPath ".\.venv-supply-chain\Scripts\python.exe" -EvidencePath ".stage04-evidence-20261024-06" -VulnerabilityService osv -VerifyPublicPyPIDigests
    if ($LASTEXITCODE -ne 0) { throw 'Stage 04 collector failed; preserve all evidence' }
} finally {
    if ($null -eq $previousLinks) {
        Remove-Item Env:PIP_FIND_LINKS -ErrorAction SilentlyContinue
    } else {
        $env:PIP_FIND_LINKS = $previousLinks
    }
}
```

The process-local links apply to the child PowerShell invocation and `pip download` without overwriting any old wheelhouse. The new pinned closure still requires `pytest==9.0.3`; the older `pytest==9.0.2` wheel from `-04` **must not** enter the resulting manifest. The existing offline `hash-wheels` validator rejects wrong/duplicate/missing wheel identities; the opt-in public PyPI release metadata comparison checks every actual SHA-256. If the verified `-04` source is unusable or PyPI remains unavailable for other wheels, stop with an explicit failure, **do not skip Hash/CVE/License checks, change Starlette versions, or disable TLS**.

Once successful, independently check `-06` output for `pytest==9.0.3`, `AUDIT_COMPLETE_NO_REPORTED_FINDINGS`, 27 wheel SHA matches and CycloneDX coverage. The `license-review.json` in the collector output is still a **blank human-review template** and cannot be declared legal-approved without qualified evidence/reviewer sign-off. **Stage 04 IN_PROGRESS, Stage 05 NOT_STARTED.** No product source, runtime dependencies or secrets were changed by this recovery documentation.
