"""Inventory installed Stage 04 dependency closure without outbound network calls.

This tool verifies local package metadata and installed wheel RECORD hashes.
It does NOT perform a vulnerability scan, approve licenses or attest provenance.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[2]


def direct_dependencies(*, include_dev: bool = True) -> list[Requirement]:
    files = [ROOT / "requirements.txt"]
    if include_dev:
        files.append(ROOT / "requirements-dev.txt")
    specs: dict[str, Requirement] = {}
    for path in files:
        for source in path.read_text(encoding="utf-8").splitlines():
            line = source.strip()
            if not line or line.startswith("#") or line == "-r requirements.txt":
                continue
            requirement = Requirement(line)
            if requirement.url or requirement.extras or len(requirement.specifier) != 1 or not str(requirement.specifier).startswith("=="):
                raise ValueError("DIRECT_DEPENDENCY_NOT_EXACTLY_PINNED")
            specs[canonicalize_name(requirement.name)] = requirement
    return [specs[k] for k in sorted(specs)]


def _record_integrity(dist: metadata.Distribution) -> dict[str, int]:
    checked = 0
    unhashed = 0
    for entry in dist.files or ():
        if entry.hash is None:
            unhashed += 1
            continue
        if entry.hash.mode != "sha256":
            raise ValueError("DEPENDENCY_UNSUPPORTED_RECORD_HASH")
        actual = hashlib.sha256(dist.locate_file(entry).read_bytes()).digest()
        expected = base64.urlsafe_b64decode(entry.hash.value + "=" * (-len(entry.hash.value) % 4))
        if actual != expected:
            raise ValueError("DEPENDENCY_RECORD_HASH_MISMATCH")
        checked += 1
    return {"installed_record_sha256_verified": checked, "record_entries_unhashed": unhashed}


def build_inventory(*, include_dev: bool = True) -> dict[str, object]:
    roots = direct_dependencies(include_dev=include_dev)
    pending = [str(item) for item in roots]
    seen: dict[str, dict] = {}
    while pending:
        requested = Requirement(pending.pop())
        if requested.marker and not requested.marker.evaluate({"extra": ""}):
            continue
        name = canonicalize_name(requested.name)
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            raise ValueError("DEPENDENCY_MISSING") from None
        version = dist.version
        if version not in requested.specifier:
            raise ValueError("DEPENDENCY_VERSION_CONFLICT")
        if name in seen:
            continue
        details = dist.metadata
        declared_license = details.get("License-Expression") or details.get("License")
        if not declared_license:
            declared_license = "; ".join(x for x in details.get_all("Classifier", ()) if x.startswith("License ::")) or None
        seen[name] = {
            "name": name,
            "version": version,
            "purl": f"pkg:pypi/{name}@{version}",
            "license_metadata": declared_license,
            "license_review": "REVIEW_REQUIRED",
            "integrity": _record_integrity(dist),
        }
        pending.extend(dist.requires or ())
    return {
        "format": "stage04-installed-dependency-inventory-v1",
        "scope": "development" if include_dev else "runtime",
        "components": [seen[key] for key in sorted(seen)],
        "vulnerability_audit": "NOT_RUN_OFFLINE",
        "upstream_wheel_provenance": "NOT_VERIFIED",
        "licenses_approved": False,
        "remarks": "Installed RECORD consistency is not a signed upstream wheel checksum or supply-chain authorization.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-only", action="store_true")
    args = parser.parse_args()
    try:
        inventory = build_inventory(include_dev=not args.runtime_only)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"PASS_INSTALLED_METADATA_ONLY: {len(inventory['components'])} components; license and vulnerability approval STILL_PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
