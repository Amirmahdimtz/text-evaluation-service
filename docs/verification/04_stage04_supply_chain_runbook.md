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
