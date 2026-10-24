"""Offline acceptance-oracle tests. No actual CVE scan or release approval."""

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verification" / "review_stage04_supply_chain.py"
spec = importlib.util.spec_from_file_location("stage04_supply_chain_review", SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def fixture(tmp_path):
    entries = [{"name": "example-pkg", "version": "1.2.3", "license_metadata": "MIT", "integrity": {"installed_record_sha256_verified": 2}}]
    inventory = {"format": "stage04-installed-dependency-inventory-v1", "scope": "development", "components": entries}
    audit = {"dependencies": [{"name": "example_pkg", "version": "1.2.3", "vulns": []}]}
    sbom = {"bomFormat": "CycloneDX", "specVersion": "1.6", "metadata": {"tools": {}}, "components": [{"type": "library", "name": "example-pkg", "version": "1.2.3", "purl": "pkg:pypi/example-pkg@1.2.3"}]}
    licensed = {"format": "stage04-license-review-v1", "reviewed_by": "synthetic-test-reviewer", "decisions": [{"name": "example-pkg", "version": "1.2.3", "decision": "APPROVED", "license_expression": "MIT", "evidence": "synthetic-test-only-license-policy"}]}
    wheelhouse = tmp_path / "wheels"
    wheelhouse.mkdir()
    wheel = wheelhouse / "example_pkg-1.2.3-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as f:
        f.writestr("example_pkg-1.2.3.dist-info/WHEEL", "Wheel-Version: 1.0\n")
        f.writestr("example_pkg-1.2.3.dist-info/METADATA", "Name: example-pkg\nVersion: 1.2.3\n")
    hashes = review.verify_wheels(inventory, wheelhouse)
    pypi = review.verify_pypi_digest_metadata(hashes, fetch=lambda n,v: {"urls": [{"filename": hashes["components"][0]["filename"], "digests": {"sha256": hashes["components"][0]["sha256"]}}]})
    return inventory, audit, sbom, hashes, pypi, wheelhouse, licensed


def test_wheel_and_sbom_gate_passes_only_with_complete_synthetic_evidence(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    result = review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)
    assert result["result"] == "PASS_LOCAL_EVIDENCE_ONLY"
    assert result["publisher_provenance"] == "NOT_VERIFIED_BY_THIS_TOOL"
    assert hashes["components"][0]["sha256"] == hashlib.sha256((wh / hashes["components"][0]["filename"]).read_bytes()).hexdigest()


def test_vulnerability_findings_fail_closed(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    audit["dependencies"][0]["vulns"] = [{"id": "SYNTHETIC-CVE-0000"}]
    with pytest.raises(review.EvidenceError, match="AUDIT_VULNERABILITIES_REPORTED"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_partial_audit_not_pass(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    audit["dependencies"] = []
    with pytest.raises(review.EvidenceError, match="AUDIT_COVERAGE_MISMATCH"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_sbom_wrong_version_and_missing_component(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    sbom["specVersion"] = "1.5"
    with pytest.raises(review.EvidenceError, match="SBOM_FORMAT_UNEXPECTED"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)
    sbom["specVersion"] = "1.6"
    sbom["components"] = []
    with pytest.raises(review.EvidenceError, match="SBOM_COVERAGE_MISMATCH"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_unreviewed_license_rejected(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    licenses["decisions"][0]["decision"] = "REVIEW_REQUIRED"
    with pytest.raises(review.EvidenceError, match="LICENSE_NOT_APPROVED"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)
    templ = review.license_review_template(inv)
    assert templ["reviewed_by"] == ""
    assert templ["decisions"][0]["decision"] == "REVIEW_REQUIRED"


def test_wheel_modified_after_manifest_rejected(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    with (wh / hashes["components"][0]["filename"]).open("ab") as stream:
        stream.write(b"tampers wheel but still valid zip")
    with pytest.raises(review.EvidenceError, match="HASH_MANIFEST_DIGEST_MISMATCH"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_missing_wheel_rejected(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    (wh / hashes["components"][0]["filename"]).unlink()
    with pytest.raises(review.EvidenceError, match="HASH_MANIFEST_WHEEL_MISSING"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_duplicate_wheel_rejected(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    original = wh / hashes["components"][0]["filename"]
    another = wh / "example_pkg-1.2.3-py2-none-any.whl"
    another.write_bytes(original.read_bytes())
    with pytest.raises(review.EvidenceError, match="WHEELHOUSE_UNEXPECTED_OR_DUPLICATE"):
        review.verify_wheels(inv, wh)


def test_freeze_matches_inventory_not_environment(tmp_path):
    inv, *_ = fixture(tmp_path)
    assert review.frozen_requirements(inv) == "example-pkg==1.2.3\n"
    inv["components"][0]["integrity"]["installed_record_sha256_verified"] = 0
    with pytest.raises(review.EvidenceError, match="INVENTORY_INTEGRITY_UNVERIFIED"):
        review.frozen_requirements(inv)


def test_cli_does_not_emit_success_on_failure(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    inv_path = tmp_path / "input-inventory.json"
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    import subprocess
    import sys
    target = tmp_path / "pins.txt"
    done = subprocess.run([sys.executable, str(SCRIPT), "freeze", "--inventory", str(inv_path), "--output", str(target)], capture_output=True, text=True)
    assert done.returncode == 0
    assert target.read_text(encoding="utf-8") == "example-pkg==1.2.3\n"
    inv["components"] = []
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    failed = subprocess.run([sys.executable, str(SCRIPT), "freeze", "--inventory", str(inv_path), "--output", str(target)], capture_output=True, text=True)
    assert failed.returncode != 0
    assert "PASS_" not in failed.stdout


def test_pypi_digest_mismatch_fails_closed(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    with pytest.raises(review.EvidenceError, match="PYPI_WHEEL_SHA256_MISMATCH"):
        review.verify_pypi_digest_metadata(hashes, fetch=lambda n, v: {"urls": [{"filename": hashes["components"][0]["filename"], "digests": {"sha256": "0" * 64}}]})
    pypi["components"][0]["sha256"] = "f" * 64
    with pytest.raises(review.EvidenceError, match="PYPI_WHEEL_SHA256_MISMATCH"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_offline_validator_rejects_missing_pypi_evidence(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    pypi["components"] = []
    with pytest.raises(review.EvidenceError, match="PYPI_COVERAGE_MISMATCH"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_public_pypi_metadata_verifier_is_opt_in_only_and_never_called_in_freeze(tmp_path, monkeypatch):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    monkeypatch.setattr(review, "_pypi_release", lambda *_: (_ for _ in ()).throw(AssertionError("unexpected network")))
    assert review.frozen_requirements(inv) == "example-pkg==1.2.3\n"
    assert review.verify_wheels(inv, wh)["components"][0]["name"] == "example-pkg"


def test_audit_may_include_extra_installed_environment_tools(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    audit["dependencies"].append({"name": "pip", "version": "25.1.1", "vulns": []})
    assert review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)["result"] == "PASS_LOCAL_EVIDENCE_ONLY"
    audit["dependencies"][1]["vulns"].append({"id": "SYNTHETIC-TOOLS-EXPOSURE"})
    with pytest.raises(review.EvidenceError, match="AUDIT_VULNERABILITIES_REPORTED"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_license_expression_must_be_explicit_and_auditable(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    licenses["decisions"][0]["license_expression"] = ""
    with pytest.raises(review.EvidenceError, match="LICENSE_EXPRESSION_UNREVIEWED"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_site_packages_cli_outputs_actual_python_path_without_inline_code_quotes():
    import subprocess
    import sys
    import sysconfig

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "site-packages"],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert "PASS_" not in completed.stdout
    assert Path(completed.stdout.strip()).resolve() == Path(sysconfig.get_path("purelib")).resolve()
    assert Path(completed.stdout.strip()).is_dir()


def test_powershell_collector_uses_python_cli_without_fragile_inline_quoted_expression():
    content = (SCRIPT.parent / "run_stage04_supply_chain.ps1").read_text(encoding="utf-8")
    assert "review_stage04_supply_chain.py site-packages" in content
    assert "-c 'import sysconfig" not in content
    assert content.index("Assert-Exit 'Target site-packages resolution'") < content.index("New-Item -ItemType Directory -Path $EvidencePath")


def test_collector_uses_bounded_pip_timeouts_and_retries():
    content = (SCRIPT.parent / "run_stage04_supply_chain.ps1").read_text(encoding="utf-8")
    assert "-m pip install --disable-pip-version-check --timeout 120 --retries 6 -r requirements-audit.txt" in content
    assert "-m pip download --disable-pip-version-check --timeout 120 --retries 6 --only-binary=:all: --no-deps" in content
    assert "Assert-Exit 'Install pinned audit tools" in content
    assert "Assert-Exit 'Download exact installed wheel versions" in content


def test_audit_status_distinguishes_complete_clean_and_findings(tmp_path):
    inv, audit, sbom, hashes, pypi, wh, licenses = fixture(tmp_path)
    expected = review._inventory(inv)
    assert review.audit_report_status(audit, expected) == "AUDIT_COMPLETE_NO_REPORTED_FINDINGS"
    audit["dependencies"][0]["vulns"] = [{"id": "SYNTHETIC-CVE"}]
    assert review.audit_report_status(audit, expected) == "AUDIT_COMPLETE_WITH_FINDINGS"
    with pytest.raises(review.EvidenceError, match="AUDIT_VULNERABILITIES_REPORTED"):
        review.evaluate(inventory=inv, audit=audit, sbom=sbom, hashes=hashes, pypi_hashes=pypi, wheelhouse=wh, licenses=licenses)


def test_audit_status_rejects_incomplete_and_unknown_advisory_results(tmp_path):
    inv, audit, *_ = fixture(tmp_path)
    expected = review._inventory(inv)
    del audit["dependencies"][0]["vulns"]
    with pytest.raises(review.EvidenceError, match="AUDIT_MISSING_VULNERABILITY_DATA"):
        review.audit_report_status(audit, expected)
    audit["dependencies"] = []
    with pytest.raises(review.EvidenceError, match="AUDIT_COVERAGE_MISMATCH"):
        review.audit_report_status(audit, expected)


def test_audit_status_cli_fails_without_report_and_accepts_complete_synthetic(tmp_path):
    import subprocess
    import sys
    inv, audit, *_ = fixture(tmp_path)
    inv_path = tmp_path / "inventory.json"
    audit_path = tmp_path / "scan.json"
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    cmd = [sys.executable, str(SCRIPT), "audit-status", "--inventory", str(inv_path), "--audit", str(audit_path)]
    missing = subprocess.run(cmd, capture_output=True, text=True)
    assert missing.returncode != 0
    assert "AUDIT_COMPLETE" not in missing.stdout
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    done = subprocess.run(cmd, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "AUDIT_COMPLETE_NO_REPORTED_FINDINGS"


def test_collector_uses_independent_pip_audit_timeout_and_requires_complete_report():
    content = (SCRIPT.parent / "run_stage04_supply_chain.ps1").read_text(encoding="utf-8")
    assert "-m pip_audit --strict --path $installedPath --vulnerability-service $VulnerabilityService --timeout 120" in content
    assert "review_stage04_supply_chain.py audit-status --inventory" in content
    assert "Vulnerability audit report completeness" in content
    assert "Vulnerability audit produced no report" in content
    assert "AUDIT_COMPLETE_WITH_FINDINGS" in content
    assert "AUDIT_COMPLETE_NO_REPORTED_FINDINGS" in content


def test_findings_summary_is_offline_with_package_ids_and_fixes(tmp_path, monkeypatch):
    inv, audit, *_ = fixture(tmp_path)
    audit["dependencies"][0]["vulns"] = [
        {"id": "GHSA-SYNTHETIC-ONE", "aliases": ["CVE-SYNTHETIC-ONE"],
         "fix_versions": ["1.2.4"], "description": "PRIVATE-TEXT-MUST-NOT-COPY"},
        {"id": "GHSA-SYNTHETIC-TWO", "fix_versions": [], "aliases": []},
    ]
    result = review.summarize_audit_findings(audit, inv, source="osv")
    assert result["affected_packages"] == 1
    assert result["reported_advisories"] == 2
    assert result["packages"][0]["in_dependency_closure"] is True
    assert result["packages"][0]["advisories"][0]["fix_versions"] == ["1.2.4"]
    assert "PRIVATE-TEXT-MUST-NOT-COPY" not in json.dumps(result)
    assert result["stage04_gate"] == "OPEN"


def test_findings_summary_rejects_missing_coverage_and_invalid_vulnerability(tmp_path):
    inv, audit, *_ = fixture(tmp_path)
    with pytest.raises(review.EvidenceError, match="AUDIT_SOURCE_UNAPPROVED"):
        review.summarize_audit_findings(audit, inv, source="unknown")
    audit["dependencies"] = []
    with pytest.raises(review.EvidenceError, match="AUDIT_COVERAGE_MISMATCH"):
        review.summarize_audit_findings(audit, inv, source="osv")
    audit["dependencies"] = [{"name": "example-pkg", "version": "1.2.3", "vulns": [{"id": "bad", "fix_versions": "1.2.4"}]}]
    with pytest.raises(review.EvidenceError, match="AUDIT_VULNERABILITY_INVALID"):
        review.summarize_audit_findings(audit, inv, source="osv")


def test_audit_findings_cli_reports_known_findings_without_false_pass(tmp_path):
    import subprocess
    import sys
    inv, audit, *_ = fixture(tmp_path)
    audit["dependencies"][0]["vulns"] = [{"id": "GHSA-SYNTHETIC", "fix_versions": ["1.3.0"]}]
    inv_path = tmp_path / "inv.json"
    audit_path = tmp_path / "audit.json"
    output = tmp_path / "findings.json"
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    command = [sys.executable, str(SCRIPT), "audit-findings", "--inventory", str(inv_path),
               "--audit", str(audit_path), "--source", "osv", "--output", str(output)]
    completed = subprocess.run(command, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    assert "gate OPEN" in completed.stdout
    assert "PASS_" not in completed.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["packages"][0]["name"] == "example-pkg"
    audit_path.write_text("{}", encoding="utf-8")
    denied = subprocess.run(command, capture_output=True, text=True)
    assert denied.returncode != 0
    assert "PASS_" not in denied.stdout
    assert "AUDIT_FINDINGS_SUMMARY" not in denied.stdout


def test_findings_summary_keeps_extra_installed_tool_advisories(tmp_path):
    inv, audit, *_ = fixture(tmp_path)
    audit["dependencies"].append({"name": "pip", "version": "25.0.1", "vulns": [
        {"id": "PYSEC-SYNTHETIC", "fix_versions": ["25.1.2"]}]})
    result = review.summarize_audit_findings(audit, inv, source="osv")
    assert result["packages"][0]["name"] == "pip"
    assert result["packages"][0]["in_dependency_closure"] is False
    assert result["reported_advisories"] == 1


def test_collector_supports_explicit_allowlisted_advisory_services_without_silent_fallback():
    content = (SCRIPT.parent / 'run_stage04_supply_chain.ps1').read_text(encoding='utf-8')
    assert "[ValidateSet('pypi', 'osv')]" in content
    assert "[string]$VulnerabilityService = 'pypi'" in content
    assert '("vulnerabilities.{0}.json" -f $VulnerabilityService)' in content
    assert "vulnerability_service = $VulnerabilityService" in content
    assert "vulnerability_report = (Split-Path -Leaf $auditReport)" in content
    assert "Never silently fall back to another provider" in content


def test_advisory_source_is_passed_as_single_explicit_pip_audit_argument():
    content = (SCRIPT.parent / 'run_stage04_supply_chain.ps1').read_text(encoding='utf-8')
    assert content.count('--vulnerability-service $VulnerabilityService') == 1
    assert '--vulnerability-service pypi --timeout' not in content
    assert '--vulnerability-service osv --timeout' not in content
    assert "Assert-Exit 'Vulnerability audit report completeness'" in content
    assert "Vulnerability audit produced no report" in content
