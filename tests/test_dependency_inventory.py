"""No-network audit parser and evidence-status regressions."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "verification"))
import audit_stage04_dependencies as audit


def test_direct_pins_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    (tmp_path / "requirements.txt").write_text("fastapi==0.148.0\nstarlette==1.9.0\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("-r requirements.txt\npytest==9.0.2\n", encoding="utf-8")
    assert len(audit.direct_dependencies()) == 3
    (tmp_path / "requirements.txt").write_text("fastapi>=0.148.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="DIRECT_DEPENDENCY_NOT_EXACTLY_PINNED"):
        audit.direct_dependencies()


def test_manifest_does_not_pretend_to_be_cve_or_license_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    (tmp_path / "requirements.txt").write_text("pytest==9.0.2\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("-r requirements.txt\n", encoding="utf-8")
    result = audit.build_inventory()
    assert result["vulnerability_audit"] == "NOT_RUN_OFFLINE"
    assert result["upstream_wheel_provenance"] == "NOT_VERIFIED"
    assert result["licenses_approved"] is False
    assert all(c["license_review"] == "REVIEW_REQUIRED" for c in result["components"])
    assert "pytest" in {c["name"] for c in result["components"]}


def test_installed_record_tampering_is_rejected(tmp_path, monkeypatch):
    class FakeEntry:
        hash = type("Hash", (), {"mode": "sha256", "value": "AAAAAAAAAA"})()
    class FakeDist:
        files = [FakeEntry()]
        def locate_file(self, entry):
            return tmp_path / "record.txt"
    (tmp_path / "record.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ValueError, match="DEPENDENCY_RECORD_HASH_MISMATCH"):
        audit._record_integrity(FakeDist())
