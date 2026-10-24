"""Protect dependency checks against regression to a known-vulnerable Starlette."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "verification"))
import check_stage04_safety as safety


def test_rejects_old_starlette_even_if_exactly_pinned(tmp_path, monkeypatch):
    monkeypatch.setattr(safety, "ROOT", tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("pass\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("fastapi==0.128.2\nstarlette==0.50.0\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("-r requirements.txt\npytest==9.0.3\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n*.key\n*.pem\n*.log\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="known vulnerable Starlette version"):
        safety.main()
    (tmp_path / "requirements.txt").write_text("fastapi==0.148.0\nstarlette==1.9.0\n", encoding="utf-8")
    assert safety.main() == 0


def test_rejects_old_pytest_pin_and_missing_dev_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(safety, "ROOT", tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("pass\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("fastapi==0.148.0\nstarlette==1.9.0\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n*.key\n*.pem\n*.log\n", encoding="utf-8")
    dev = tmp_path / "requirements-dev.txt"
    dev.write_text("-r requirements.txt\npytest==9.0.2\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="known vulnerable pytest version"):
        safety.main()
    dev.write_text("-r requirements.txt\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="patched pytest pin required"):
        safety.main()
    dev.write_text("-r requirements.txt\npytest==9.0.3\n", encoding="utf-8")
    assert safety.main() == 0
