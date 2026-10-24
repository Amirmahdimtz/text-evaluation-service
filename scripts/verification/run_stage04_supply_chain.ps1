# Run only on an approved development workstation with public package metadata.
# No text-evaluation input, corporate secret, or model artifact is accessed.
# A clean results directory is required so stale evidence cannot be reused.
[CmdletBinding()]
param(
    [string]$PythonPath = '.\.venv-review\Scripts\python.exe',
    [string]$AuditPythonPath = '.\.venv-supply-chain\Scripts\python.exe',
    [string]$EvidencePath = '.stage04-evidence',
    [ValidateSet('pypi', 'osv')]
    [string]$VulnerabilityService = 'pypi',
    [switch]$VerifyPublicPyPIDigests
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $repository
try {
    if (-not (Test-Path $PythonPath -PathType Leaf)) {
        throw "Reviewed target Python not found: $PythonPath"
    }
    if (Test-Path $EvidencePath) {
        throw 'Evidence directory already exists. Preserve previous evidence and choose a fresh -EvidencePath. Do not delete prior evidence automatically.'
    }
    function Assert-Exit([string]$Step) {
        if ($LASTEXITCODE -ne 0) {
            throw "$Step failed with exit code $LASTEXITCODE; do not accept Stage 04 gate."
        }
    }

    & $PythonPath -m pip check
    Assert-Exit 'Target environment pip check'

    # Avoid `python -c` with quoted dictionary keys: Windows PowerShell 5.1
    # strips embedded native argument quotes, causing NameError: purelib.
    $installedPath = & $PythonPath scripts/verification/review_stage04_supply_chain.py site-packages
    Assert-Exit 'Target site-packages resolution'
    if (-not $installedPath -or -not (Test-Path -LiteralPath $installedPath -PathType Container)) {
        throw 'Target Python site-packages directory not found'
    }

    # Create an immutable evidence directory only after local preflight passes.
    # A failed run leaves its evidence intact and must use a fresh path.
    New-Item -ItemType Directory -Path $EvidencePath -ErrorAction Stop | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $EvidencePath 'wheelhouse') -ErrorAction Stop | Out-Null

    & $PythonPath scripts/verification/audit_stage04_dependencies.py --output (Join-Path $EvidencePath 'inventory.json')
    Assert-Exit 'Installed dependency RECORD and license metadata inventory'

    & $PythonPath scripts/verification/review_stage04_supply_chain.py freeze --inventory (Join-Path $EvidencePath 'inventory.json') --output (Join-Path $EvidencePath 'pinned-closure.txt')
    Assert-Exit 'Exact dependency closure export'
    & $PythonPath scripts/verification/review_stage04_supply_chain.py license-template --inventory (Join-Path $EvidencePath 'inventory.json') --output (Join-Path $EvidencePath 'license-review.json')
    Assert-Exit 'License review checklist'

    # The separate audit venv keeps audit-tool dependencies out of the service closure.
    if (-not (Test-Path $AuditPythonPath -PathType Leaf)) {
        py -3.12 -m venv .venv-supply-chain
        Assert-Exit 'Create dedicated audit environment'
    }
    # Public package CDN downloads can be slow; use a bounded longer read timeout.
    # Do not suppress failed installs or change global pip / network policy.
    & $AuditPythonPath -m pip install --disable-pip-version-check --timeout 120 --retries 6 -r requirements-audit.txt
    Assert-Exit 'Install pinned audit tools (approved development workstation only)'

    # pip-audit has a separate socket timeout (default 15s), independent from pip install.
    # Exit code 1 can mean real findings OR an advisory-service failure: validate the JSON.
    # An explicitly chosen service is mandatory for reproducible advisory evidence.
    # Never silently fall back to another provider after a network failure.
    $auditReport = Join-Path $EvidencePath ("vulnerabilities.{0}.json" -f $VulnerabilityService)
    Write-Host "Auditing public package names/versions via $VulnerabilityService"
    & $AuditPythonPath -m pip_audit --strict --path $installedPath --vulnerability-service $VulnerabilityService --timeout 120 --progress-spinner off --format json --output $auditReport
    $auditExitCode = $LASTEXITCODE
    if (-not (Test-Path -LiteralPath $auditReport -PathType Leaf)) {
        throw "Vulnerability audit produced no report (exit $auditExitCode); preserve partial evidence. Stage 04 gate remains OPEN."
    }
    $auditStatus = & $PythonPath scripts/verification/review_stage04_supply_chain.py audit-status --inventory (Join-Path $EvidencePath 'inventory.json') --audit $auditReport
    Assert-Exit 'Vulnerability audit report completeness'
    if ($auditStatus -eq 'AUDIT_COMPLETE_WITH_FINDINGS') {
        if ($auditExitCode -ne 1) {
            throw "Vulnerability audit reported findings with unexpected exit code $auditExitCode"
        }
        Write-Warning 'Verified vulnerability findings in complete audit JSON. Stage 04 gate is NOT approved.'
    } elseif ($auditStatus -eq 'AUDIT_COMPLETE_NO_REPORTED_FINDINGS') {
        if ($auditExitCode -ne 0) {
            throw "Vulnerability audit returned exit code $auditExitCode despite clean JSON; gate remains OPEN."
        }
    } else {
        throw 'Vulnerability audit returned an unknown status; gate remains OPEN.'
    }

    & $AuditPythonPath -m cyclonedx_py environment $PythonPath --spec-version 1.6 --output-format JSON --output-file (Join-Path $EvidencePath 'sbom.cdx.json')
    Assert-Exit 'Generate CycloneDX 1.6 SBOM for reviewed interpreter'

    # --no-deps is safe ONLY because pinned-closure.txt lists all installed transitive deps.
    & $PythonPath -m pip download --disable-pip-version-check --timeout 120 --retries 6 --only-binary=:all: --no-deps -r (Join-Path $EvidencePath 'pinned-closure.txt') -d (Join-Path $EvidencePath 'wheelhouse')
    Assert-Exit 'Download exact installed wheel versions for observed target platform'

    & $PythonPath scripts/verification/review_stage04_supply_chain.py hash-wheels --inventory (Join-Path $EvidencePath 'inventory.json') --wheelhouse (Join-Path $EvidencePath 'wheelhouse') --output (Join-Path $EvidencePath 'wheel-hashes.json')
    Assert-Exit 'Verify wheel coverage, archive format and local digests'

    if ($VerifyPublicPyPIDigests) {
        # Explicit opt-in: sends ONLY public PyPI package names and versions; no application data.
        & $PythonPath scripts/verification/review_stage04_supply_chain.py verify-pypi --hashes (Join-Path $EvidencePath 'wheel-hashes.json') --output (Join-Path $EvidencePath 'pypi-digests.json')
        Assert-Exit 'Verify wheel hashes against public PyPI release metadata'
    }

    & $PythonPath -m pip freeze > (Join-Path $EvidencePath 'pip-freeze.txt')
    Assert-Exit 'Capture installed distribution versions'

    $summary = @{
        reviewed_python = $PythonPath
        vulnerability_audit_exit = $auditExitCode
        vulnerability_audit_status = $auditStatus
        vulnerability_service = $VulnerabilityService
        vulnerability_report = (Split-Path -Leaf $auditReport)
        wheel_manifest = 'wheel-hashes.json'
        sbom = 'sbom.cdx.json'
        license_review = 'REVIEW_REQUIRED (license-review.json is an unapproved template)'
        public_pypi_sha256_checked = [bool]$VerifyPublicPyPIDigests
        gate = 'IN_PROGRESS - no automatic legal approval, publisher provenance or Stage 05 entry'
    }
    $summary | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $EvidencePath 'run-summary.json') -Encoding UTF8
    Write-Host "Evidence collected in $EvidencePath. Local Stage 04 gate remains OPEN until reviewed evidence is accepted."
}
finally {
    Pop-Location
}
