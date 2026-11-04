"""Offline-only tests for the Stage11 owner-supplied artifact match script."""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.verification import stage11_serving_artifact_match as match


def test_default_never_reads_runtime_paths_or_runs_docker(monkeypatch, capsys):
    monkeypatch.setattr(
        subprocess, "run",
        lambda *_args, **_kwargs: pytest.fail("No subprocess allowed"),
    )
    assert match.main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "OFFLINE_OWNER_ARTIFACT_ATTESTATION_PLAN"
    assert report["model_inference_requests"] == 0
    assert report["network_requests"] == 0
    assert report["docker_commands"] == 0
    assert report["effective_live_backend_verified"] is False


def test_emitted_runtime_is_static_no_model_network_or_secrets(capsys):
    assert match.main(["--emit-runtime-script"]) == 0
    source = capsys.readouterr().out
    assert source == match._RUNTIME
    ast.parse(source)
    assert "ALLOWED_FILES" in source and "tokenizer.json" in source
    assert "read(512 * 1024)" in source
    assert "MAX_TOTAL_BYTES" in source
    assert "socket.socket = _deny" in source
    assert "CUDA_VISIBLE_DEVICES" in source
    assert "resource.RLIMIT_CPU" in source
    for forbidden in ("model.generate", "docker exec", "from_pretrained(",
                      "subprocess.run", "requests.", "httpx.", "os.environ.items"):
        assert forbidden not in source


def _run_compare(
    tmp_path: Path, *, same=False, missing=False,
    mismatch=False, one_sided=False, no_dirs=False,
):
    cached = tmp_path / "cached"
    served = cached if same else tmp_path / "served"
    cached.mkdir()
    if not same:
        served.mkdir()
    for directory in {cached, served}:
        (directory / "config.json").write_bytes(b'{"secret":"do-not-print"}')
        (directory / "tokenizer.json").write_bytes(b"PRIVATE_TOKENIZER_BYTES")
        (directory / "tokenizer_config.json").write_bytes(b"SAFE_LOCAL_TEST")
    if missing:
        (served / "config.json").unlink()
    if mismatch:
        (served / "tokenizer.json").write_bytes(b"DIFFERENT_PRIVATE_BYTES")
    if one_sided:
        (served / "chat_template.jinja").write_bytes(b"SECRET_TEMPLATE_TEXT")
    env = os.environ.copy()
    if no_dirs:
        env.pop("STAGE11_LOCAL_TOKENIZER_DIR", None)
        env.pop("STAGE11_OWNER_SERVED_ARTIFACT_DIR", None)
    else:
        env["STAGE11_LOCAL_TOKENIZER_DIR"] = str(cached)
        env["STAGE11_OWNER_SERVED_ARTIFACT_DIR"] = str(served)
    return subprocess.run(
        [sys.executable, "-B", "-c", match._RUNTIME],
        env=env, cwd=tmp_path, text=True, capture_output=True,
        check=False, timeout=10,
    )


def test_matching_files_not_claimed_live_serving_attestation(tmp_path):
    result = _run_compare(tmp_path)
    assert result.returncode == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "OWNER_SUPPLIED_ARTIFACT_FILES_COMPARED"
    assert report["local_config_files_match"] is True
    assert report["local_tokenizer_files_all_match"] is True
    assert report["matched_core_tokenizer_files_count"] == 1
    assert report["live_served_artifact_provenance_verified"] is False
    assert report["effective_live_backend_verified"] is False
    assert report["model_weights_compared"] is False
    assert report["model_inference_requests"] == 0
    assert report["network_requests"] == 0
    assert "PRIVATE_TOKENIZER_BYTES" not in result.stdout
    assert "do-not-print" not in result.stdout
    assert str(tmp_path) not in result.stdout


@pytest.mark.parametrize("kind", ["mismatch", "one_sided"])
def test_difference_fails_closed_without_disclosing_file_data(tmp_path, kind):
    result = _run_compare(tmp_path, **{kind: True})
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["local_tokenizer_files_all_match"] is False
    assert not (
        report["live_served_artifact_provenance_verified"]
        or report["effective_live_backend_verified"]
    )
    assert "SECRET_TEMPLATE_TEXT" not in result.stdout
    assert "PRIVATE_TOKENIZER_BYTES" not in result.stdout
    assert str(tmp_path) not in result.stdout


def test_same_directory_cannot_be_used_as_independent_proof(tmp_path):
    result = _run_compare(tmp_path, same=True)
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == (
        "SAME_DIRECTORY_NOT_INDEPENDENT_EVIDENCE"
    )


def test_missing_config_fails_closed(tmp_path):
    result = _run_compare(tmp_path, missing=True)
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == "CONFIG_FILE_MISSING"


def test_no_directories_does_not_probe_environment(tmp_path):
    result = _run_compare(tmp_path, no_dirs=True)
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == (
        "OWNER_APPROVED_DIRECTORIES_NOT_CONFIGURED"
    )
