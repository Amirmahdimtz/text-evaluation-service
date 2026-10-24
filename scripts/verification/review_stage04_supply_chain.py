"""Offline Stage 04 software supply-chain evidence validator.

This script does not fetch advisory data or claim package publisher authenticity.
All inputs must be independently generated for the SAME reviewed virtualenv.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import re
import ssl
import sysconfig
import zipfile
from datetime import datetime, timezone
from urllib.parse import quote
from pathlib import Path
from typing import Any

from packaging.utils import canonicalize_name, parse_wheel_filename


class EvidenceError(ValueError):
    """Input evidence is incomplete, mismatched, or not fit for a release gate."""


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("EVIDENCE_UNREADABLE") from None
    if not isinstance(value, dict):
        raise EvidenceError("EVIDENCE_NOT_OBJECT")
    return value


def _identities(components: list[dict[str, Any]], *, source: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in components:
        if not isinstance(item, dict):
            raise EvidenceError(f"{source}_COMPONENT_INVALID")
        raw_name, version = item.get("name"), item.get("version")
        if not isinstance(raw_name, str) or not isinstance(version, str) or not version:
            raise EvidenceError(f"{source}_COMPONENT_INVALID")
        name = canonicalize_name(raw_name)
        if name in result and result[name] != version:
            raise EvidenceError(f"{source}_DUPLICATE_VERSION")
        if name in result:
            raise EvidenceError(f"{source}_DUPLICATE_COMPONENT")
        result[name] = version
    return result


def _inventory(data: dict[str, Any]) -> dict[str, str]:
    if data.get("format") != "stage04-installed-dependency-inventory-v1":
        raise EvidenceError("INVENTORY_FORMAT_UNKNOWN")
    if data.get("scope") != "development":
        raise EvidenceError("INVENTORY_SCOPE_MISMATCH")
    comps = data.get("components")
    if not isinstance(comps, list) or not comps:
        raise EvidenceError("INVENTORY_EMPTY")
    for component in comps:
        if not isinstance(component, dict) or not isinstance(component.get("integrity"), dict):
            raise EvidenceError("INVENTORY_INTEGRITY_MISSING")
        if component["integrity"].get("installed_record_sha256_verified", 0) < 1:
            raise EvidenceError("INVENTORY_INTEGRITY_UNVERIFIED")
    return _identities(comps, source="INVENTORY")


def frozen_requirements(inventory: dict[str, Any]) -> str:
    comps = _inventory(inventory)
    return "".join(f"{name}=={version}\n" for name, version in sorted(comps.items()))


def _wheel_identity(path: Path) -> tuple[str, str]:
    try:
        distribution, version, _build, _tags = parse_wheel_filename(path.name)
    except ValueError:
        raise EvidenceError("WHEEL_INVALID_FILENAME") from None
    return canonicalize_name(distribution), str(version)


def verify_wheels(inventory: dict[str, Any], wheelhouse: Path) -> dict[str, Any]:
    expected = _inventory(inventory)
    if not wheelhouse.is_dir():
        raise EvidenceError("WHEELHOUSE_NOT_FOUND")
    wheels = sorted(wheelhouse.iterdir())
    if not wheels or any(not p.is_file() or p.suffix != ".whl" for p in wheels):
        raise EvidenceError("WHEELHOUSE_NONWHEEL_OR_EMPTY")
    found: dict[str, tuple[str, str, str]] = {}
    for path in wheels:
        name, version = _wheel_identity(path)
        if name not in expected or expected[name] != version or name in found:
            raise EvidenceError("WHEELHOUSE_UNEXPECTED_OR_DUPLICATE")
        try:
            with zipfile.ZipFile(path) as wheel:
                # Structural check only; not a cryptographic publisher attestation.
                archive_names = wheel.namelist()
                if not any(p.endswith(".dist-info/WHEEL") for p in archive_names) or not any(p.endswith(".dist-info/METADATA") for p in archive_names):
                    raise EvidenceError("WHEEL_STRUCTURE_INVALID")
                if wheel.testzip() is not None:
                    raise EvidenceError("WHEEL_CORRUPT_ARCHIVE")
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
        except (OSError, zipfile.BadZipFile):
            raise EvidenceError("WHEEL_UNREADABLE") from None
        found[name] = (version, path.name, digest)
    if set(found) != set(expected):
        raise EvidenceError("WHEELHOUSE_INCOMPLETE")
    return {
        "format": "stage04-local-wheel-hashes-v1",
        "hash_scope": "locally_observed_wheel_bytes_not_publisher_attested",
        "components": [
            {"name": name, "version": version, "filename": filename, "sha256": digest}
            for name, (version, filename, digest) in sorted(found.items())
        ],
        "publisher_provenance_verified": False,
    }


def _pypi_release(name: str, version: str) -> dict[str, Any]:
    """Fetch only public package/version metadata from PyPI (opt-in action)."""
    conn = http.client.HTTPSConnection("pypi.org", timeout=20, context=ssl.create_default_context())
    try:
        url = f"/pypi/{quote(name, safe='')}/{quote(version, safe='')}/json"
        conn.request("GET", url, headers={"Accept": "application/json", "User-Agent": "tes-stage04-package-hash-review/1"})
        response = conn.getresponse()
        if response.status != 200:
            raise EvidenceError("PYPI_METADATA_UNAVAILABLE")
        body = response.read(3_000_001)
        if len(body) > 3_000_000:
            raise EvidenceError("PYPI_METADATA_TOO_LARGE")
        result = json.loads(body)
        if not isinstance(result, dict):
            raise EvidenceError("PYPI_METADATA_INVALID")
        return result
    except (OSError, ValueError, json.JSONDecodeError):
        raise EvidenceError("PYPI_METADATA_FAILED") from None
    finally:
        conn.close()


def verify_pypi_digest_metadata(hashes: dict[str, Any], *, fetch=_pypi_release) -> dict[str, Any]:
    """Compare locally observed wheel SHA-256 against public PyPI release JSON.

    HTTPS PyPI metadata is a separate trusted digest source, not a publisher
    signature, a SLSA attestation, or an authorization to use the artifact.
    """
    if hashes.get("format") != "stage04-local-wheel-hashes-v1":
        raise EvidenceError("PYPI_INPUT_INVALID")
    result = []
    for item in hashes.get("components", []):
        name, version, filename, observed = (item.get(k) for k in ("name", "version", "filename", "sha256"))
        if not all(isinstance(v, str) and v for v in (name, version, filename, observed)):
            raise EvidenceError("PYPI_INPUT_INVALID")
        releases = fetch(name, version).get("urls", [])
        if not isinstance(releases, list):
            raise EvidenceError("PYPI_METADATA_INVALID")
        matching = [r for r in releases if isinstance(r, dict) and r.get("filename") == filename]
        if len(matching) != 1:
            raise EvidenceError("PYPI_WHEEL_NOT_FOUND")
        reference = matching[0].get("digests", {}).get("sha256")
        if not isinstance(reference, str) or reference != observed:
            raise EvidenceError("PYPI_WHEEL_SHA256_MISMATCH")
        result.append({"name": name, "version": version, "filename": filename, "sha256": reference})
    if not result:
        raise EvidenceError("PYPI_COMPONENTS_MISSING")
    return {
        "format": "stage04-pypi-release-digest-matches-v1",
        "source": "https://pypi.org/pypi/<normalized-name>/<version>/json",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "components": result,
        "trust_status": "PYPI_TLS_HASH_MATCH_ONLY_NO_PUBLISHER_SIGNATURE_ATTESTATION",
    }


def _validate_pypi_digests(data: dict[str, Any], hashes: dict[str, Any]) -> None:
    if data.get("format") != "stage04-pypi-release-digest-matches-v1" or data.get("trust_status") != "PYPI_TLS_HASH_MATCH_ONLY_NO_PUBLISHER_SIGNATURE_ATTESTATION":
        raise EvidenceError("PYPI_EVIDENCE_INVALID")
    expected = {canonicalize_name(c["name"]): c for c in hashes["components"]}
    records = data.get("components")
    if not isinstance(records, list):
        raise EvidenceError("PYPI_EVIDENCE_INVALID")
    actual = _identities(records, source="PYPI")
    if actual != {key: val["version"] for key, val in expected.items()}:
        raise EvidenceError("PYPI_COVERAGE_MISMATCH")
    for item in records:
        source = expected[canonicalize_name(item["name"])]
        if item.get("filename") != source["filename"] or item.get("sha256") != source["sha256"]:
            raise EvidenceError("PYPI_WHEEL_SHA256_MISMATCH")


def audit_report_status(data: dict[str, Any], expected: dict[str, str]) -> str:
    """Require full named/versioned coverage before calling an advisory result complete."""
    entries = data.get("dependencies")
    if not isinstance(entries, list):
        raise EvidenceError("AUDIT_FORMAT_UNKNOWN")
    actual = _identities(entries, source="AUDIT")
    if any(actual.get(name) != version for name, version in expected.items()):
        raise EvidenceError("AUDIT_COVERAGE_MISMATCH")
    has_findings = False
    for entry in entries:
        vulns = entry.get("vulns")
        if not isinstance(vulns, list):
            raise EvidenceError("AUDIT_MISSING_VULNERABILITY_DATA")
        has_findings = has_findings or bool(vulns)
    return "AUDIT_COMPLETE_WITH_FINDINGS" if has_findings else "AUDIT_COMPLETE_NO_REPORTED_FINDINGS"


def summarize_audit_findings(data: dict[str, Any], inventory: dict[str, Any], *, source: str) -> dict[str, Any]:
    """Render safe package/advisory facts from a complete report; no auto-fixes.

    A successful summary means report parsing succeeded, NOT Stage 04 approval.
    Neither untrusted advisory descriptions nor local paths are included.
    """
    if source not in ("osv", "pypi"):
        raise EvidenceError("AUDIT_SOURCE_UNAPPROVED")
    expected = _inventory(inventory)
    audit_status = audit_report_status(data, expected)
    packages = []
    total = 0
    for entry in data["dependencies"]:
        findings = []
        for vulnerability in entry["vulns"]:
            if not isinstance(vulnerability, dict):
                raise EvidenceError("AUDIT_VULNERABILITY_INVALID")
            advisory_id = vulnerability.get("id")
            fix_versions = vulnerability.get("fix_versions", [])
            aliases = vulnerability.get("aliases", [])
            if (not isinstance(advisory_id, str) or not advisory_id.strip()
                    or len(advisory_id) > 180 or any(ord(c) < 33 for c in advisory_id)
                    or not isinstance(fix_versions, list)
                    or not all(isinstance(v, str) and v.strip() and len(v) < 80 for v in fix_versions)
                    or not isinstance(aliases, list)
                    or not all(isinstance(a, str) and a.strip() and len(a) < 180 for a in aliases)):
                raise EvidenceError("AUDIT_VULNERABILITY_INVALID")
            findings.append({
                "id": advisory_id,
                "aliases": sorted(set(aliases)),
                "fix_versions": sorted(set(fix_versions)),
            })
        if findings:
            packages.append({
                "name": canonicalize_name(entry["name"]),
                "installed_version": entry["version"],
                "in_dependency_closure": canonicalize_name(entry["name"]) in expected,
                "advisories": sorted(findings, key=lambda x: x["id"]),
            })
            total += len(findings)
    packages.sort(key=lambda x: x["name"])
    return {
        "format": "stage04-audit-findings-summary-v1",
        "advisory_source": source,
        "scan_status": audit_status,
        "affected_packages": len(packages),
        "reported_advisories": total,
        "packages": packages,
        "stage04_gate": "OPEN" if packages else "PENDING_LICENSE_AND_EVIDENCE_REVIEW",
        "caveat": "Advisory IDs may alias the same issue. Fix versions are upstream suggestions, not approved upgrades.",
    }


def _validate_audit(data: dict[str, Any], expected: dict[str, str]) -> None:
    if audit_report_status(data, expected) == "AUDIT_COMPLETE_WITH_FINDINGS":
        raise EvidenceError("AUDIT_VULNERABILITIES_REPORTED")


def _validate_sbom(data: dict[str, Any], expected: dict[str, str]) -> None:
    if data.get("bomFormat") != "CycloneDX" or data.get("specVersion") != "1.6":
        raise EvidenceError("SBOM_FORMAT_UNEXPECTED")
    if not isinstance(data.get("metadata"), dict):
        raise EvidenceError("SBOM_MISSING_METADATA")
    comps = data.get("components")
    if not isinstance(comps, list):
        raise EvidenceError("SBOM_COMPONENTS_MISSING")
    actual = _identities(comps, source="SBOM")
    for name, version in expected.items():
        if actual.get(name) != version:
            raise EvidenceError("SBOM_COVERAGE_MISMATCH")
    for component in comps:
        name = canonicalize_name(component["name"])
        if name in expected:
            if component.get("type") != "library":
                raise EvidenceError("SBOM_TYPE_INVALID")
            purl = component.get("purl")
            if not isinstance(purl, str) or not purl.startswith("pkg:pypi/"):
                raise EvidenceError("SBOM_PURL_MISSING")


def _validate_hash_manifest(data: dict[str, Any], expected: dict[str, str], wheelhouse: Path) -> None:
    if data.get("format") != "stage04-local-wheel-hashes-v1" or data.get("publisher_provenance_verified") is not False:
        raise EvidenceError("HASH_MANIFEST_FORMAT_UNKNOWN")
    entries = data.get("components")
    if not isinstance(entries, list):
        raise EvidenceError("HASH_MANIFEST_COMPONENTS_MISSING")
    actual = _identities(entries, source="WHEEL_MANIFEST")
    if actual != expected:
        raise EvidenceError("HASH_MANIFEST_COVERAGE_MISMATCH")
    for item in entries:
        filename, digest = item.get("filename"), item.get("sha256")
        if not isinstance(filename, str) or filename != Path(filename).name or not filename.endswith(".whl"):
            raise EvidenceError("HASH_MANIFEST_FILENAME_INVALID")
        if not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None:
            raise EvidenceError("HASH_MANIFEST_DIGEST_INVALID")
        path = wheelhouse / filename
        if not path.is_file():
            raise EvidenceError("HASH_MANIFEST_WHEEL_MISSING")
        with path.open("rb") as stream:
            actual_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual_digest != digest:
            raise EvidenceError("HASH_MANIFEST_DIGEST_MISMATCH")
        if _wheel_identity(path) != (canonicalize_name(item["name"]), item["version"]):
            raise EvidenceError("HASH_MANIFEST_WHEEL_IDENTITY_MISMATCH")


def _validate_licenses(data: dict[str, Any], inventory: dict[str, Any], expected: dict[str, str]) -> None:
    if data.get("format") != "stage04-license-review-v1":
        raise EvidenceError("LICENSE_REVIEW_FORMAT_UNKNOWN")
    reviewed_by = data.get("reviewed_by")
    if not isinstance(reviewed_by, str) or not reviewed_by.strip():
        raise EvidenceError("LICENSE_REVIEWER_MISSING")
    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        raise EvidenceError("LICENSE_DECISIONS_MISSING")
    actual = _identities(decisions, source="LICENSE")
    if actual != expected:
        raise EvidenceError("LICENSE_COVERAGE_MISMATCH")
    for item in decisions:
        expression = item.get("license_expression")
        if (not isinstance(expression, str) or len(expression) > 160
                or re.fullmatch(r"[A-Za-z0-9+._() -]+", expression) is None
                or expression in ("UNKNOWN", "NOASSERTION")):
            raise EvidenceError("LICENSE_EXPRESSION_UNREVIEWED")
        if item.get("decision") != "APPROVED" or not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            raise EvidenceError("LICENSE_NOT_APPROVED")


def license_review_template(inventory: dict[str, Any]) -> dict[str, Any]:
    _inventory(inventory)
    return {
        "format": "stage04-license-review-v1",
        "reviewed_by": "",
        "decisions": [
            {"name": item["name"], "version": item["version"], "license_metadata": item.get("license_metadata"), "license_expression": "", "decision": "REVIEW_REQUIRED", "evidence": ""}
            for item in inventory["components"]
        ],
    }


def evaluate(*, inventory: dict[str, Any], audit: dict[str, Any], sbom: dict[str, Any], hashes: dict[str, Any], pypi_hashes: dict[str, Any], wheelhouse: Path, licenses: dict[str, Any]) -> dict[str, Any]:
    expected = _inventory(inventory)
    _validate_audit(audit, expected)
    _validate_sbom(sbom, expected)
    _validate_hash_manifest(hashes, expected, wheelhouse)
    _validate_pypi_digests(pypi_hashes, hashes)
    _validate_licenses(licenses, inventory, expected)
    return {
        "result": "PASS_LOCAL_EVIDENCE_ONLY",
        "components": len(expected),
        "vulnerability_audit": "NO_REPORTED_FINDINGS_IN_SUPPLIED_AUDIT",
        "sbom": "CYCLONEDX_1_6_COMPONENT_COVERAGE_VERIFIED",
        "wheel_integrity": "LOCAL_SHA256_AND_PYPI_RELEASE_DIGESTS_MATCH",
        "license_review": "ALL_EXPLICITLY_APPROVED_IN_SUPPLIED_EVIDENCE",
        "publisher_provenance": "NOT_VERIFIED_BY_THIS_TOOL",
        "caveat": "Does not authenticate provenance, audit freshness, scan accuracy, or reviewer authority; final Stage 11 and 12 gates remain separate.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("site-packages", help="Print target interpreter purelib path without shell-embedded Python quotes")
    audit = sub.add_parser("audit-status", help="Validate full JSON CVE audit coverage; distinguish findings from scan failure")
    audit.add_argument("--inventory", type=Path, required=True)
    audit.add_argument("--audit", type=Path, required=True)
    findings = sub.add_parser("audit-findings", help="Summarize complete CVE findings safely without applying fixes")
    findings.add_argument("--inventory", type=Path, required=True)
    findings.add_argument("--audit", type=Path, required=True)
    findings.add_argument("--source", choices=("osv", "pypi"), required=True)
    findings.add_argument("--output", type=Path, required=True)
    req = sub.add_parser("freeze", help="Create exact transitive pins from an installed metadata inventory")
    req.add_argument("--inventory", type=Path, required=True)
    req.add_argument("--output", type=Path, required=True)
    wheel = sub.add_parser("hash-wheels", help="Hash and inventory exact distribution wheels on disk")
    wheel.add_argument("--inventory", type=Path, required=True)
    wheel.add_argument("--wheelhouse", type=Path, required=True)
    wheel.add_argument("--output", type=Path, required=True)
    pypi = sub.add_parser("verify-pypi", help="Opt-in network: match wheel SHA256 to public PyPI release metadata")
    pypi.add_argument("--hashes", type=Path, required=True)
    pypi.add_argument("--output", type=Path, required=True)
    lic = sub.add_parser("license-template", help="Generate blank explicit license review checklist")
    lic.add_argument("--inventory", type=Path, required=True)
    lic.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("evaluate", help="Fail closed on unmatched SBOM, CVE, wheel hashes or license review")
    for field in ("inventory", "audit", "sbom", "hashes", "pypi-hashes", "licenses", "wheelhouse", "output"):
        check.add_argument(f"--{field}", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "site-packages":
        # Native Windows PowerShell can strip quotes passed to `python -c`.
        # Keep the quoted sysconfig key in this Python source file instead.
        target = sysconfig.get_path("purelib")
        if not target or not Path(target).is_dir():
            parser.exit(1, "FAIL: TARGET_SITE_PACKAGES_NOT_FOUND\n")
        print(target)
        return 0
    if args.command == "audit-findings":
        try:
            result = summarize_audit_findings(_read(args.audit), _read(args.inventory), source=args.source)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except (EvidenceError, OSError) as exc:
            parser.exit(1, f"FAIL: {exc}\n")
        print(f"AUDIT_FINDINGS_SUMMARY: {result['affected_packages']} packages, {result['reported_advisories']} advisory records; gate {result['stage04_gate']}")
        return 0
    if args.command == "audit-status":
        try:
            print(audit_report_status(_read(args.audit), _inventory(_read(args.inventory))))
        except (EvidenceError, OSError) as exc:
            parser.exit(1, f"FAIL: {exc}\n")
        return 0
    try:
        inventory = _read(args.inventory) if args.command != "verify-pypi" else None
        if args.command == "freeze":
            output = frozen_requirements(inventory)
        elif args.command == "hash-wheels":
            output = json.dumps(verify_wheels(inventory, args.wheelhouse), indent=2, sort_keys=True) + "\n"
        elif args.command == "verify-pypi":
            output = json.dumps(verify_pypi_digest_metadata(_read(args.hashes)), indent=2, sort_keys=True) + "\n"
        elif args.command == "license-template":
            output = json.dumps(license_review_template(inventory), indent=2, sort_keys=True) + "\n"
        else:
            output = json.dumps(evaluate(inventory=inventory, audit=_read(args.audit), sbom=_read(args.sbom), hashes=_read(args.hashes), pypi_hashes=_read(args.pypi_hashes), licenses=_read(args.licenses), wheelhouse=args.wheelhouse), indent=2, sort_keys=True) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    except (EvidenceError, OSError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    print("PASS_LOCAL_EVIDENCE_GENERATED" if args.command != "evaluate" else "PASS_LOCAL_EVIDENCE_ONLY: independent provenance approval still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
