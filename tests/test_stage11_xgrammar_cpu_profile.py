"""Offline tests for the bounded, safe Stage11 XGrammar conversion diagnostic."""
from __future__ import annotations

import ast
import json
import subprocess
import sys

import pytest

from scripts.verification import stage11_xgrammar_cpu_profile as profile


def test_schema_report_recognizes_combined_pattern_and_length():
    report = profile.offline_report()
    assert report["status"] == "OFFLINE_GRAMMAR_CONVERSION_PREFLIGHT"
    assert report["pattern_with_length_or_format_count"] == 1
    assert len(report["schema_sha256"]) == 64
    assert report["cpu_conversion_measured"] is False
    assert report["tokenizer_aware_compilation_measured"] is False
    assert report["per_token_masking_measured"] is False
    assert report["model_inference_requests"] == 0
    assert report["docker_commands"] == 0


@pytest.mark.parametrize("node, expected", [
    ({"type": "string", "pattern": "^[a-z]+$", "maxLength": 100}, 1),
    ({"type": "string", "pattern": "^[a-z]+$"}, 0),
    ({"type": "string", "minLength": 1, "maxLength": 20}, 0),
    ({"type": "array", "items": [{"type": "string", "pattern": "x", "format": "date"}]}, 1),
    ({"type": "object", "properties": {"a": {"type": "string", "pattern": "x", "minLength": 1}}}, 1),
])
def test_pattern_overlap_is_recursive(node, expected):
    assert profile._conflict_count(node) == expected


def test_default_mode_cannot_attempt_container_or_network(monkeypatch, capsys):
    def fail(*_args, **_kwargs):
        raise AssertionError("Default CLI must not launch a process")
    monkeypatch.setattr(subprocess, "run", fail)
    assert profile.main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["network_requests"] == 0
    assert report["model_inference_requests"] == 0


def test_generated_runtime_script_is_static_auditable_and_schema_pinned():
    payload = profile.build_runtime_script()
    ast.parse(payload)
    assert "Grammar.from_json_schema(SCHEMA)" in payload
    assert "model_inference_requests" in payload
    assert "GrammarCompiler(" not in payload
    assert "torch.cuda" not in payload
    assert "subprocess" not in payload
    assert "httpx" not in payload
    assert "docker" not in payload
    assert "source_text" not in payload
    assert profile.offline_report()["schema_sha256"] in payload


def test_generated_probe_success_with_synthetic_xgrammar_stub(tmp_path):
    (tmp_path / "xgrammar.py").write_text(
        "class Grammar:\n"
        "    @staticmethod\n"
        "    def from_json_schema(schema):\n"
        "        assert len(schema['properties']) == 8\n"
        "        return object()\n",
        encoding="utf-8",
    )
    # Launch from temp working directory with a synthetic xgrammar module.
    result = subprocess.run(
        [sys.executable, "-B", "-c", profile.build_runtime_script()],
        cwd=tmp_path, capture_output=True, text=True, timeout=8, check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "CPU_GRAMMAR_CONVERSION_OBSERVED"
    assert report["runs"] == 2
    assert isinstance(report["versions"]["xgrammar"], str)
    assert report["conversion_ms_first"] >= 0
    assert report["request_latency_measured"] is False
    assert report["per_token_masking_measured"] is False


def test_generated_probe_compile_error_is_sanitized(tmp_path):
    (tmp_path / "xgrammar.py").write_text(
        "class Grammar:\n"
        "    @staticmethod\n"
        "    def from_json_schema(schema):\n"
        "        raise RuntimeError('SECRET_MODEL_DATA')\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", profile.build_runtime_script()],
        cwd=tmp_path, capture_output=True, text=True, timeout=8, check=False,
    )
    assert result.returncode == 2
    assert "SECRET_MODEL_DATA" not in result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "XGRAMMAR_CONVERSION_FAILED"


def test_generated_probe_import_error_is_sanitized(tmp_path):
    (tmp_path / "xgrammar.py").write_text(
        "raise RuntimeError('SECRET_IMPORT_DATA')\n", encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", profile.build_runtime_script()],
        cwd=tmp_path, capture_output=True, text=True, timeout=8, check=False,
    )
    assert result.returncode == 3
    assert "SECRET_IMPORT_DATA" not in result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "XGRAMMAR_IMPORT_UNAVAILABLE"


def test_emit_runtime_script_is_full_and_no_execution(capsys):
    assert profile.main(["--emit-runtime-script"]) == 0
    payload = capsys.readouterr().out
    assert payload.startswith('"""Generated Stage11')
    assert "SCHEMA_SHA256" in payload
    ast.parse(payload)
