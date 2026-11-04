"""No-GPU Stage11 CPU tokenizer diagnostic contract and fail-closed tests."""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys

import pytest

from scripts.verification import stage11_xgrammar_tokenizer_profile as profile


def test_default_plan_never_executes_inference_or_docker(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_kw: pytest.fail("must not execute"))
    assert profile.main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "OFFLINE_TOKENIZER_PROFILE_PLAN"
    assert report["schema_sha256"] == (
        "da781d766a47140e7ba844d501fc35c7ae65ae5506a3975440118c77d0e2c584"
    )
    assert report["container_execution_requires_owner_approval"] is True
    assert report["live_backend_verified"] is False
    assert report["tokenizer_aware_compilation_measured"] is False
    assert report["model_inference_requests"] == 0
    assert report["network_requests"] == 0
    assert report["docker_commands"] == 0


def test_generated_script_is_static_pinned_and_no_network_or_gpu(capsys):
    assert profile.main(["--emit-runtime-script"]) == 0
    source = capsys.readouterr().out
    ast.parse(source)
    assert source == profile.build_runtime_script()
    assert profile._SCHEMA_SHA256 in source
    assert "HF_HUB_OFFLINE" in source and "local_files_only=True" in source
    assert "trust_remote_code=False" in source
    assert "CUDA_VISIBLE_DEVICES" in source
    assert "socket.socket = _deny_network" in source
    assert "GrammarCompiler(" in source
    assert "fill_next_token_bitmask" in source
    assert "accept_token" in source
    assert "MAX_STEPS = 24" in source
    assert "max_threads=1" in source
    assert "resource.RLIMIT_CPU" in source
    assert "os.path.isfile(os.path.join(tokenizer_dir, \"config.json\"))" in source
    for forbidden in ("docker exec", "httpx", "requests.post", "from_pretrained(\n            model", "model.generate", "subprocess.run", "torch.cuda"):
        assert forbidden not in source
    assert "source_text" not in source
    assert "Bearer " not in source


def _run_generated(tmp_path, *, configured=True, xgrammar_broken=False,
                   tokenizer_leaks=False, token_count=30,
                   mask_rejects=False, tokenizer_network=False,
                   mismatch_version=False, missing_config=False):
    """Execute synthetic modules; no real tokenizer, GPU or network."""
    for name, version in [("vllm", "0.10.2"),
                          ("xgrammar", "0.1.22" if mismatch_version else "0.1.23")]:
        dist = tmp_path / f"{name}-{version}.dist-info"
        dist.mkdir()
        (dist / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")

    if xgrammar_broken:
        compile_lines = "raise RuntimeError('SENSITIVE_COMPILE_PATH')"
    else:
        compile_lines = "return object()"
    (tmp_path / "xgrammar.py").write_text(
        "class TokenizerInfo:\n"
        "    @staticmethod\n"
        "    def from_huggingface(tokenizer, vocab_size):\n"
        "        assert vocab_size == 1024\n"
        "        return object()\n"
        "class GrammarCompiler:\n"
        "    def __init__(self, info, *, max_threads, cache_enabled, cache_limit_bytes):\n"
        "        assert max_threads == 1 and cache_limit_bytes == 32 * 1024 * 1024\n"
        "    def compile_json_schema(self, schema, *, any_whitespace):\n"
        "        assert any_whitespace and len(__import__('json').loads(schema)['properties']) == 8\n"
        f"        {compile_lines}\n"
        "class GrammarMatcher:\n"
        "    def __init__(self, compiled): pass\n"
        "    def fill_next_token_bitmask(self, bitmask, idx): assert idx == 0\n"
        f"    def accept_token(self, token): return {not mask_rejects}\n"
        "def allocate_token_bitmask(n, vocab_size):\n"
        "    assert n == 1 and vocab_size == 1024\n"
        "    return object()\n",
        encoding="utf-8",
    )
    if tokenizer_network:
        tokenizer_lines = "__import__('socket').socket()"
    elif tokenizer_leaks:
        tokenizer_lines = "raise RuntimeError('SENSITIVE_TOKENIZER_PATH')"
    else:
        tokenizer_lines = "return type('Tok', (), {'encode': lambda self, s, add_special_tokens: [1] * %d})()" % token_count
    (tmp_path / "transformers.py").write_text(
        "class AutoConfig:\n"
        "    @staticmethod\n"
        "    def from_pretrained(path, *, local_files_only, trust_remote_code):\n"
        "        assert local_files_only and not trust_remote_code\n"
        "        return type('Cfg', (), {'vocab_size': 1024})()\n"
        "class AutoTokenizer:\n"
        "    @staticmethod\n"
        "    def from_pretrained(path, *, local_files_only, trust_remote_code, use_fast):\n"
        "        assert local_files_only and not trust_remote_code and use_fast\n"
        f"        {tokenizer_lines}\n",
        encoding="utf-8",
    )
    tokenizer_dir = tmp_path / "local-tokenizer"
    tokenizer_dir.mkdir()
    if not missing_config:
        (tokenizer_dir / "config.json").write_text("{}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    if configured:
        env["STAGE11_LOCAL_TOKENIZER_DIR"] = str(tokenizer_dir)
    else:
        env.pop("STAGE11_LOCAL_TOKENIZER_DIR", None)
    return subprocess.run(
        [sys.executable, "-B", "-c", profile.build_runtime_script()],
        env=env, cwd=tmp_path, capture_output=True, text=True, timeout=12,
        check=False,
    )


def test_missing_tokenizer_directory_aborts_before_import(tmp_path):
    result = _run_generated(tmp_path, configured=False)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["status"] == "LOCAL_TOKENIZER_DIRECTORY_NOT_CONFIGURED"
    assert report["model_inference_requests"] == 0
    assert "local-tokenizer" not in result.stdout


def test_synthetic_tokenizer_compiler_and_mask_success(tmp_path):
    result = _run_generated(tmp_path, token_count=300)
    assert result.returncode == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED"
    assert report["versions"] == {"vllm": "0.10.2", "xgrammar": "0.1.23"}
    assert report["tokenizer_aware_compilation_measured"] is True
    assert report["cpu_synthetic_mask_fill_steps"] == 24
    assert report["gpu_token_mask_application_measured"] is False
    assert report["real_request_latency_measured"] is False
    assert report["effective_live_backend_verified"] is False
    assert report["network_requests"] == 0
    assert report["model_inference_requests"] == 0
    assert "local-tokenizer" not in result.stdout


@pytest.mark.parametrize("failure_type,expected", [
    ("xgrammar", "TOKENIZER_GRAMMAR_COMPILE_FAILED"),
    ("tokenizer", "LOCAL_TOKENIZER_LOAD_FAILED"),
])
def test_exception_from_runtime_is_redacted(tmp_path, failure_type, expected):
    result = _run_generated(
        tmp_path, xgrammar_broken=failure_type == "xgrammar",
        tokenizer_leaks=failure_type == "tokenizer",
    )
    assert result.returncode in (2, 3), result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == expected
    assert "SENSITIVE" not in result.stdout + result.stderr
    assert "local-tokenizer" not in result.stdout + result.stderr
    assert report["model_inference_requests"] == 0


def test_package_version_mismatch_fails_closed(tmp_path):
    result = _run_generated(tmp_path, mismatch_version=True)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["status"] == "UNVERIFIED_RUNTIME_VERSION"
    assert report["model_inference_requests"] == 0


def test_absent_local_model_config_fails_closed(tmp_path):
    result = _run_generated(tmp_path, missing_config=True)
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == "LOCAL_TOKENIZER_DIRECTORY_NOT_CONFIGURED"


def test_network_access_attempt_is_rejected_and_hidden(tmp_path):
    result = _run_generated(tmp_path, tokenizer_network=True)
    assert result.returncode == 3
    report = json.loads(result.stdout)
    assert report["status"] == "LOCAL_TOKENIZER_LOAD_FAILED"
    assert report["network_requests"] == 0


def test_synthetic_bad_token_is_rejected(tmp_path):
    result = _run_generated(tmp_path, mask_rejects=True)
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "SYNTHETIC_GRAMMAR_TOKEN_REJECTED"
