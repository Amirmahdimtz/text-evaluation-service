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
    assert "socket.socket = _NetworkDeniedSocket" in source
    assert "socket.getaddrinfo = _deny_network" in source
    assert "GrammarCompiler(" in source
    assert "fill_next_token_bitmask" in source
    assert "accept_token" in source
    assert "MAX_STEPS = 24" in source
    assert "MAX_TRACES = 2" in source
    assert "REASON_SENSITIVITY = False" in source
    assert "MAX_CPU_SECONDS = 25" in source
    assert "MAX_WALL_SECONDS = 45" in source
    assert "return_offsets_mapping=True" in source
    assert "_structural_step_labels(" in source
    assert "_slow_mask_step_indices(fill_ms, 10.0)" in source
    assert "_slow_mask_step_indices(fill_ms, 100.0)" in source
    assert "cpu_synthetic_mask_fill_first_ms" in source
    assert "cpu_synthetic_mask_fill_rest_p95_nearest_rank_ms" in source
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
                   mismatch_version=False, missing_config=False,
                   subclass_import=False, transformers_import_error=False,
                   xgrammar_import_error=False, reason_sensitivity=False):
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
        ("raise RuntimeError('SENSITIVE_XGRAMMAR_IMPORT')\n"
         if xgrammar_import_error else "") +
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
        tokenizer_lines = "__import__('socket').socket().connect(('127.0.0.1', 9))"
    elif tokenizer_leaks:
        tokenizer_lines = "raise RuntimeError('SENSITIVE_TOKENIZER_PATH')"
    else:
        tokenizer_lines = "return type('Tok', (), {'encode': lambda self, s, add_special_tokens: [1] * %d, '__call__': lambda self, s, add_special_tokens, return_offsets_mapping: {'input_ids': [1] * %d, 'offset_mapping': [(min(i, len(s)-1), min(i+1, len(s))) for i in range(%d)]}})()" % (token_count, token_count, token_count)
    (tmp_path / "transformers.py").write_text(
        ("raise RuntimeError('SENSITIVE_TRANSFORMERS_IMPORT')\n"
         if transformers_import_error else "") +
        ("import socket\nclass _ImportSubclass(socket.socket):\n    pass\n"
         if subclass_import else "") +
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
        [sys.executable, "-B", "-c", profile.build_runtime_script(
            reason_sensitivity=reason_sensitivity)],
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
    assert report["cpu_synthetic_mask_fill_rest_steps"] == 23
    assert report["cpu_synthetic_mask_repeat_count"] == 2
    assert report["cpu_synthetic_mask_repeat2_steps"] == 24
    assert report["cpu_synthetic_mask_repeat2_total_ms"] >= 0
    assert report["cpu_synthetic_mask_structural_alignment"] == "ALIGNED"
    assert report["cpu_synthetic_mask_repeat2_structural_alignment"] == "ALIGNED"
    gt10 = report["cpu_synthetic_mask_fill_steps_gt_10ms"]
    gt100 = report["cpu_synthetic_mask_fill_steps_gt_100ms"]
    assert gt10 == sorted(set(gt10))
    assert gt100 == sorted(set(gt100))
    assert all(type(i) is int and 1 <= i <= 24 for i in gt10 + gt100)
    assert set(gt100).issubset(gt10)
    assert report["cpu_synthetic_mask_fill_first_ms"] >= 0
    assert report["cpu_synthetic_mask_fill_rest_mean_ms"] >= 0
    assert report["cpu_synthetic_mask_fill_rest_median_ms"] >= 0
    assert report["cpu_synthetic_mask_fill_rest_p95_nearest_rank_ms"] >= 0
    assert report["cpu_synthetic_mask_fill_rest_max_ms"] >= 0
    assert report["cpu_synthetic_mask_fill_total_ms"] == pytest.approx(
        report["cpu_synthetic_mask_fill_first_ms"]
        + report["cpu_synthetic_mask_fill_rest_total_ms"], abs=0.002,
    )
    assert (report["cpu_synthetic_mask_fill_rest_median_ms"]
            <= report["cpu_synthetic_mask_fill_rest_max_ms"])
    assert (report["cpu_synthetic_mask_fill_rest_p95_nearest_rank_ms"]
            <= report["cpu_synthetic_mask_fill_rest_max_ms"])
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


def test_transformers_import_can_subclass_socket_without_network(tmp_path):
    """Regression: the original socket.socket function shim broke ssl imports."""
    result = _run_generated(tmp_path, subclass_import=True)
    assert result.returncode == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED"
    assert report["network_requests"] == 0


@pytest.mark.parametrize("failure_type,expected", [
    ("xgrammar", "XGRAMMAR_IMPORT_FAILED"),
    ("transformers", "TRANSFORMERS_IMPORT_FAILED"),
])
def test_import_failures_have_distinct_sanitized_status(tmp_path, failure_type, expected):
    result = _run_generated(
        tmp_path,
        xgrammar_import_error=failure_type == "xgrammar",
        transformers_import_error=failure_type == "transformers",
    )
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == expected
    assert "SENSITIVE_" not in result.stdout + result.stderr


def _distribution_from_generated_runtime(name="_mask_fill_distribution"):
    """Isolate pure generated helpers for deterministic data tests."""
    parsed = ast.parse(profile.build_runtime_script())
    function = next(
        node for node in parsed.body
        if isinstance(node, ast.FunctionDef)
        and node.name == name
    )
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 "<synthetic-runtime-helper>", "exec"), namespace)
    return namespace[name]


def test_mask_fill_distribution_first_vs_rest_with_fixed_values():
    summary = _distribution_from_generated_runtime()(
        [12.0, 1.0, 3.0, 2.0, 4.0]
    )
    assert summary == {
        "cpu_synthetic_mask_fill_first_ms": 12.0,
        "cpu_synthetic_mask_fill_first_share_percent": 54.55,
        "cpu_synthetic_mask_fill_rest_steps": 4,
        "cpu_synthetic_mask_fill_rest_total_ms": 10.0,
        "cpu_synthetic_mask_fill_rest_mean_ms": 2.5,
        "cpu_synthetic_mask_fill_rest_median_ms": 2.5,
        "cpu_synthetic_mask_fill_rest_p95_nearest_rank_ms": 4.0,
        "cpu_synthetic_mask_fill_rest_max_ms": 4.0,
    }


def test_mask_fill_distribution_fails_closed_with_fewer_than_two_steps():
    summary = _distribution_from_generated_runtime()
    assert summary([]) is None
    assert summary([0.5]) is None


def test_single_token_trace_refuses_misleading_distribution(tmp_path):
    result = _run_generated(tmp_path, token_count=1)
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["status"] == "SYNTHETIC_MASK_STEPS_INSUFFICIENT"
    assert report["model_inference_requests"] == 0
    assert "cpu_synthetic_mask_fill_rest_p95_nearest_rank_ms" not in report


def test_mask_fill_distribution_zero_duration_has_no_invalid_ratio():
    summary = _distribution_from_generated_runtime()([0.0, 0.0])
    assert summary["cpu_synthetic_mask_fill_first_share_percent"] is None
    assert summary["cpu_synthetic_mask_fill_rest_steps"] == 1
    assert summary["cpu_synthetic_mask_fill_rest_p95_nearest_rank_ms"] == 0.0


def test_slow_step_indices_use_strict_thresholds_and_one_based_positions():
    """Threshold equality is excluded; only synthetic positions are returned."""
    classify = _distribution_from_generated_runtime("_slow_mask_step_indices")
    timings = [0.094, 10.0, 10.001, 100.0, 100.001, 247.760]
    assert classify(timings, 10.0) == [3, 4, 5, 6]
    assert classify(timings, 100.0) == [5, 6]


def test_slow_step_indices_empty_and_bounded_trace():
    classify = _distribution_from_generated_runtime("_slow_mask_step_indices")
    assert classify([], 10.0) == []
    timings = [0.0] * 24
    timings[0] = 10.01
    timings[23] = 100.01
    assert classify(timings, 10.0) == [1, 24]
    assert classify(timings, 100.0) == [24]


def test_generated_success_report_exposes_no_synthetic_tokens(tmp_path):
    result = _run_generated(tmp_path, token_count=300)
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert isinstance(report["cpu_synthetic_mask_fill_steps_gt_10ms"], list)
    assert isinstance(report["cpu_synthetic_mask_fill_steps_gt_100ms"], list)
    assert "synthetic_output" not in result.stdout.lower()
    assert "sample_code" not in result.stdout
    assert "synthetic diagnostic only" not in result.stdout.lower()
    assert "local-tokenizer" not in result.stdout


def _generated_pure_function(name, dependencies=()):
    """Extract pure functions from the exact emitted runtime script."""
    ast_tree = ast.parse(profile.build_runtime_script())
    selected = [node for node in ast_tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name in (name, *dependencies)]
    namespace = {"json": json, "MAX_STEPS": 24}
    exec(compile(ast.Module(body=selected, type_ignores=[]),
                 "<safe-synthetic-helper>", "exec"), namespace)
    return namespace[name]


def test_json_region_mapping_only_returns_structure_and_field_ordinals():
    regions = _generated_pure_function("_json_structure")(
        '{"a":"v","b":[]}')
    assert regions is not None
    assert regions[0] == ("SYNTAX", None)
    assert regions[1:4] == [("KEY", 1)] * 3
    assert regions[5:8] == [("VALUE", 1)] * 3
    assert regions[9:12] == [("KEY", 2)] * 3
    assert regions[13:15] == [("VALUE", 2)] * 2
    assert _generated_pure_function("_json_structure")(
        '{"a":"v"}trailing') is None


def test_structural_alignment_with_fixed_synthetic_offsets():
    classify = _generated_pure_function(
        "_structural_step_labels", ("_json_structure",))
    text = '{"a":"v","b":[]}'
    class Stub:
        def __call__(self, *_args, **_kwargs):
            return {
                "input_ids": [1, 2, 3, 4],
                "offset_mapping": [(1, 4), (5, 8), (8, 12), (13, 15)],
            }
    status, labels = classify(Stub(), text, [1, 2, 3, 4], [1, 2, 3, 4])
    assert status == "ALIGNED"
    assert labels == [
        {"step": 1, "json_region": "KEY", "field_ordinal": 1},
        {"step": 2, "json_region": "VALUE", "field_ordinal": 1},
        {"step": 3, "json_region": "CROSS_REGION", "field_ordinal": None},
        {"step": 4, "json_region": "VALUE", "field_ordinal": 2},
    ]


@pytest.mark.parametrize("offsets,token_ids", [
    ([(-1, 99)], [1]),
    ([(0, 0)], [1]),
    ([(1, 4)], [2]),
])
def test_structural_alignment_invalid_offsets_are_unverified(offsets, token_ids):
    classify = _generated_pure_function(
        "_structural_step_labels", ("_json_structure",))
    class Stub:
        def __call__(self, *_args, **_kwargs):
            return {"input_ids": token_ids, "offset_mapping": offsets}
    assert classify(Stub(), '{"a":"v"}', [1], [1]) == ("UNVERIFIED", [])


def test_two_synthetic_traces_are_bounded_and_redacted(tmp_path):
    result = _run_generated(tmp_path, token_count=300)
    assert result.returncode == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["cpu_synthetic_mask_repeat_count"] == 2
    assert data["cpu_synthetic_mask_repeat2_steps"] == 24
    for key in (
        "cpu_synthetic_mask_fill_steps_gt_100ms",
        "cpu_synthetic_mask_repeat2_steps_gt_100ms",
    ):
        assert all(type(i) is int and 1 <= i <= 24 for i in data[key])
    for key in (
        "cpu_synthetic_mask_slow_step_regions",
        "cpu_synthetic_mask_repeat2_slow_step_regions",
    ):
        assert all(
            set(item) == {"step", "json_region", "field_ordinal"}
            and item["json_region"] in
            {"SYNTAX", "KEY", "VALUE", "CROSS_REGION"}
            for item in data[key]
        )
    assert "sample_code" not in result.stdout
    assert "Synthetic diagnostic only." not in result.stdout
    assert "local-tokenizer" not in result.stdout


def test_reason_sensitivity_requires_emitting_script(capsys):
    with pytest.raises(SystemExit) as error:
        profile.main(["--reason-sensitivity"])
    assert error.value.code == 2
    assert "requires --emit-runtime-script" in capsys.readouterr().err


def test_reason_sensitivity_generated_script_is_fixed_and_cpu_only(capsys):
    assert profile.main([
        "--emit-runtime-script", "--reason-sensitivity",
    ]) == 0
    emitted = capsys.readouterr().out
    ast.parse(emitted)
    assert emitted == profile.build_runtime_script(reason_sensitivity=True)
    assert "REASON_SENSITIVITY = True" in emitted
    assert "MAX_STEPS = 24" in emitted
    assert "MAX_TRACES = 2" in emitted
    assert "MAX_CPU_SECONDS = 25" in emitted
    assert "CUDA_VISIBLE_DEVICES" in emitted
    assert "HF_HUB_OFFLINE" in emitted
    assert "socket.socket = _NetworkDeniedSocket" in emitted
    assert "model.generate" not in emitted
    assert "docker exec" not in emitted


def test_fixed_reason_variants_preserve_validated_contract():
    original = profile._fixed_synthetic_json(profile._SYNTHETIC_OUTPUT)
    parsed = json.loads(original)
    assert list(parsed) == sorted(parsed)
    assert parsed["reason"] == "Synthetic diagnostic only."
    with pytest.raises(Exception):
        profile._fixed_synthetic_json({
            **profile._SYNTHETIC_OUTPUT, "reason": "",
        })


def test_reason_sensitivity_runs_exactly_two_bounded_redacted_variants(tmp_path):
    result = _run_generated(tmp_path, token_count=300, reason_sensitivity=True)
    assert result.returncode == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED"
    assert report["cpu_synthetic_reason_sensitivity_enabled"] is True
    assert report["cpu_synthetic_mask_repeat_count"] == 2
    rows = report["cpu_synthetic_reason_sensitivity_rows"]
    assert [row["fixture"] for row in rows] == [
        "REASON_SHORT", "REASON_SAME_LENGTH",
    ]
    assert all(row["mask_fill_steps"] == 24 for row in rows)
    assert all(row["mask_fill_total_ms"] >= 0 for row in rows)
    assert all(
        row["reason_value_alignment"] in ("ALIGNED", "UNVERIFIED")
        and row["slow_step_structural_alignment"] in ("ALIGNED", "UNVERIFIED")
        for row in rows
    )
    assert all(
        1 <= step <= 24
        for row in rows for step in row["mask_fill_steps_gt_100ms"]
    )
    assert report["cpu_synthetic_baseline_reason_value_alignment"] == "ALIGNED"
    assert report["cpu_synthetic_repeat2_reason_value_alignment"] == "ALIGNED"
    assert report["model_inference_requests"] == 0
    assert report["gpu_model_execution"] is False
    assert report["network_requests"] == 0
    for forbidden in ("sample_code", "Synthetic diagnostic only.",
                      "local-tokenizer", "REASON_SAME_LENGTH_TEXT"):
        assert forbidden not in result.stdout


def test_default_runtime_does_not_execute_sensitivity_variants(tmp_path):
    result = _run_generated(tmp_path, token_count=300)
    assert result.returncode == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["cpu_synthetic_reason_sensitivity_enabled"] is False
    assert report["cpu_synthetic_reason_sensitivity_rows"] == []
