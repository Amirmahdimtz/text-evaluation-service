"""No-network Stage11 vLLM backend inspection regression tests."""
from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from scripts.verification import stage11_guided_backend_inspect as inspect


def test_real_criterion_schema_static_report_has_no_unsupported_known_features():
    summary = inspect.schema_report()
    assert summary["schema_top_level_fields"] == 8
    assert summary["schema_definitions"] == 1
    assert summary["array_max_items"] == [32, 32, 32, 32]
    assert summary["any_of_nodes"] == 1
    assert summary["ref_nodes"] == 1
    assert summary["additional_properties_false_count"] == 2
    assert summary["xgrammar_v0102_static_unsupported_keywords"] == []
    assert summary["xgrammar_v0102_compiler_validation"] == "NOT_RUN"
    assert summary["pydantic_cross_field_validation_in_json_schema"] is False


@pytest.mark.parametrize("schema,expected", [
    ({"type": "number", "multipleOf": 2}, ["multipleOf"]),
    ({"type": "array", "contains": {"type": "string"}}, ["contains"]),
    ({"type": "string", "format": "date"}, ["format"]),
    ({"type": "object", "patternProperties": {"x": {"type": "string"}}},
     ["patternProperties"]),
    ({"type": "object", "properties": {"x": {
        "type": "array", "uniqueItems": True}}}, ["uniqueItems"]),
])
def test_v0102_known_xgrammar_keywords_checked_recursively(schema, expected):
    assert inspect._unsupported_xgrammar_keywords(schema) == expected


def test_default_cli_never_calls_docker(monkeypatch, capsys):
    monkeypatch.setattr(
        inspect.subprocess, "run",
        lambda *a, **k: pytest.fail("Docker must not run on default CLI"),
    )
    assert inspect.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "READ_ONLY_BACKEND_PREFLIGHT"
    assert result["gpu_inference_requests"] == 0
    assert result["container"]["launch_metadata_status"] == "NOT_REQUESTED"
    assert result["schema"]["xgrammar_v0102_compiler_validation"] == "NOT_RUN"


@pytest.mark.parametrize("args", [
    ["--container", "../invalid"],
    ["--container", "a/b"],
    ["--container", ""],
])
def test_bad_container_names_cannot_reach_docker(monkeypatch, args):
    monkeypatch.setattr(
        inspect.subprocess, "run",
        lambda *a, **k: pytest.fail("Invalid container name may not reach Docker"),
    )
    with pytest.raises(ValueError, match="INVALID_CONTAINER_NAME"):
        inspect.main(args)


def test_sudo_without_container_fails_before_docker(monkeypatch):
    monkeypatch.setattr(
        inspect.subprocess, "run",
        lambda *a, **k: pytest.fail("No Docker invocation"),
    )
    with pytest.raises(SystemExit) as exc:
        inspect.main(["--sudo-docker"])
    assert exc.value.code == 2


def test_backend_and_whitespace_only_inspected_with_secrets_redacted(
    monkeypatch, capsys,
):
    calls = []
    # Sensitive strings are present in the mocked Docker arrays, but must
    # NEVER be emitted in the diagnostic report.
    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        raw = (
            '["vllm", "serve"]'
            if len(calls) == 1 else
            '["SECRET_MODEL_ID", "--api-key", "SECRET_CREDENTIAL", '
            '"--guided-decoding-backend", "xgrammar", '
            '"--guided-decoding-disable-any-whitespace"]'
        )
        return SimpleNamespace(returncode=0, stdout=raw)
    monkeypatch.setattr(inspect.subprocess, "run", fake_run)
    assert inspect.main(["--container", "synthetic-vllm"]) == 0
    output = capsys.readouterr().out
    report = json.loads(output)
    assert "SECRET" not in output
    assert "synthetic-vllm" not in output
    assert report["container"]["declared_backend"] == "xgrammar"
    assert report["container"]["disable_any_whitespace_flag"] == "ENABLED"
    assert report["container"]["effective_request_backend"] == "UNVERIFIED"
    assert len(calls) == 2
    for argv, kwargs in calls:
        assert argv[:4] == ["docker", "inspect", "--type", "container"]
        assert argv[-1] == "synthetic-vllm"
        assert kwargs["stderr"] == subprocess.DEVNULL
        assert kwargs["timeout"] == 6
        assert kwargs["check"] is False


def test_no_flag_is_default_intent_not_verified_runtime():
    report = inspect.parse_launch_arguments(["vllm", "serve"], ["model"])
    assert report["declared_backend"] == "NOT_DECLARED_DOCUMENTED_DEFAULT_AUTO"
    assert report["effective_request_backend"] == "UNVERIFIED"


def test_shell_wrapper_is_not_interpreted_or_disclosed():
    report = inspect.parse_launch_arguments(
        ["sh", "-c"],
        ["vllm serve PRIVATE_MODEL --guided-decoding-backend guidance"],
    )
    assert report["launch_metadata_status"] == "SHELL_WRAPPED_UNVERIFIED"
    assert report["declared_backend"] == "UNVERIFIED"
    assert "PRIVATE_MODEL" not in json.dumps(report)


@pytest.mark.parametrize("flag", [
    ["--guided-decoding-backend", "bogus"],
    ["--guided-decoding-backend"],
    ["--guided-decoding-backend=xgrammar", "--guided-decoding-backend=guidance"],
])
def test_invalid_or_conflicting_flags_fail_closed(flag):
    report = inspect.parse_launch_arguments([], flag)
    assert report["declared_backend"] == "INVALID_OR_AMBIGUOUS"
    assert report["effective_request_backend"] == "UNVERIFIED"


def test_docker_failure_and_timeout_do_not_leak_metadata(monkeypatch, capsys):
    def no_access(*args, **kwargs):
        raise subprocess.TimeoutExpired("PRIVATE_ARGS", 6)
    monkeypatch.setattr(inspect.subprocess, "run", no_access)
    assert inspect.main(["--container", "synthetic-vllm"]) == 0
    output = capsys.readouterr().out
    assert "PRIVATE_ARGS" not in output
    assert json.loads(output)["container"]["launch_metadata_status"] == (
        "DOCKER_INSPECT_UNAVAILABLE"
    )


def test_sudo_opt_in_is_non_interactive_only(monkeypatch):
    argv_seen = []
    def fake_run(argv, **kwargs):
        argv_seen.append(argv)
        return SimpleNamespace(returncode=0, stdout='[]')
    monkeypatch.setattr(inspect.subprocess, "run", fake_run)
    report = inspect.inspect_container_launch("synthetic-vllm", sudo=True)
    assert report["declared_backend"] == "NOT_DECLARED_DOCUMENTED_DEFAULT_AUTO"
    assert all(a[:3] == ["sudo", "-n", "docker"] for a in argv_seen)
