"""Offline synthetic assurance: no secrets/registry/commands and no inference."""
from __future__ import annotations

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from scripts.verification.stage11_container_metadata import (
    _docker_argv, collect, inspect_runtime, main, parse_model_metadata,
    probe_loopback_models,
)


def test_running_version_uses_strict_inspect_and_package_metadata():
    with patch("subprocess.run", side_effect=[
        Mock(returncode=0, stdout="true\n"), Mock(returncode=0, stdout="0.11.2\n")
    ]) as run:
        result = inspect_runtime("local-vllm")
    assert result == {
        "container_running": True,
        "installed_vllm_version": "0.11.2",
        "version_evidence": "PACKAGE_METADATA_INSIDE_RUNNING_CONTAINER",
    }
    state, version = run.call_args_list
    assert state.args[0] == ["docker", "inspect", "--type", "container", "--format", "{{.State.Running}}", "local-vllm"]
    assert version.args[0][:3] == ["docker", "exec", "--env"]
    assert "PYTHONDONTWRITEBYTECODE=1" in version.args[0]
    assert "python3" in version.args[0]
    assert "vllm" in version.args[0][-1]
    for call in (state, version):
        assert call.kwargs["stderr"] == subprocess.DEVNULL
        assert call.kwargs["timeout"] == 8
        assert "shell" not in call.kwargs
        assert "Config.Env" not in " ".join(call.args[0])
        assert "Config.Cmd" not in " ".join(call.args[0])


def test_sudo_explicit_noninteractive_only():
    assert _docker_argv("vllm.1", sudo=True) == ["sudo", "-n", "docker"]
    assert _docker_argv("vllm.1", sudo=False) == ["docker"]


@pytest.mark.parametrize("bad", ["", "../../name", "x;id", "vllm name", "--help", "x\nE=secret", "x"*140])
def test_invalid_container_cannot_reach_docker(bad):
    with pytest.raises(ValueError):
        _docker_argv(bad, sudo=False)


def test_missing_docker_or_sudo_skips_process():
    with patch("shutil.which", return_value=None), patch("subprocess.run") as run:
        result = collect(container="vllm.1", port=None, sudo=False)
    assert result["container"]["version_evidence"] == "NOT_OBSERVED"
    run.assert_not_called()


def test_stopped_container_does_not_exec():
    with patch("subprocess.run", return_value=Mock(returncode=0, stdout="false\n")) as run:
        result = inspect_runtime("vllm.1")
    assert result["container_running"] is False
    assert result["installed_vllm_version"] == "UNVERIFIED"
    assert run.call_count == 1


@pytest.mark.parametrize("state,version", [("true", "secret.example.com/token"), ("true", ""), ("wat", "0.0.0")])
def test_invalid_version_or_state_fails_closed(state, version):
    with patch("subprocess.run", side_effect=[
        Mock(returncode=0, stdout=state), Mock(returncode=0, stdout=version),
    ]):
        result = inspect_runtime("local-vllm")
    assert result["installed_vllm_version"] == "UNVERIFIED"


def test_public_ids_exact_match_only_and_private_ids_redacted():
    raw = json.dumps({"data": [
        {"id": "Qwen/Qwen3-14B", "root": "/secrets/internal-model-dir"},
        {"id": "/private/vllm/model?token=SECRET"},
    ]}).encode()
    result = parse_model_metadata(raw)
    assert result["known_public_candidate_ids"] == ["Qwen/Qwen3-14B"]
    assert result["other_model_ids_redacted_count"] == 1
    assert "SECRET" not in json.dumps(result)
    assert "/secrets/" not in json.dumps(result)


@pytest.mark.parametrize("raw", [b"", b"not json", b"{}", b'{"data": "bad"}', b'{"data":[{}]}', b"x"*65537])
def test_malformed_or_large_model_metadata_rejected(raw):
    with pytest.raises(ValueError):
        parse_model_metadata(raw)


def test_loopback_only_get_models_and_no_raw_token_leaks():
    raw = b'{"data":[{"id":"private-model-path-secret"}]}'
    response = Mock(status=200)
    response.read.return_value = raw
    connection = Mock()
    connection.getresponse.return_value = response
    with patch("http.client.HTTPConnection", return_value=connection) as ctor:
        result = probe_loopback_models(8000)
    assert ctor.call_args.args == ("127.0.0.1",)
    assert ctor.call_args.kwargs == {"port": 8000, "timeout": 4}
    assert connection.request.call_args.args[:2] == ("GET", "/v1/models")
    assert "secret" not in json.dumps(result)
    assert result["status"] == "OBSERVED_LOOPBACK_METADATA"
    connection.close.assert_called_once()


def test_unauthorized_http_never_reports_models():
    response = Mock(status=401)
    connection = Mock()
    connection.getresponse.return_value = response
    with patch("http.client.HTTPConnection", return_value=connection):
        result = probe_loopback_models(8000)
    assert result["status"] == "HTTP_NOT_200"
    assert result["model_metadata"] == "UNVERIFIED"
    response.read.assert_not_called()


@pytest.mark.parametrize("bad", [-1, 0, 65536, True, "8080"])
def test_refuse_out_of_range_ports(bad):
    with pytest.raises(ValueError):
        probe_loopback_models(bad)


def test_main_is_sanitized_and_no_shell(capsys):
    with patch("shutil.which", return_value=None), patch("http.client.HTTPConnection") as connect:
        assert main(["--container", "local-vllm"]) == 0
        connect.assert_not_called()
    result = json.loads(capsys.readouterr().out)
    assert "local-vllm" not in json.dumps(result)
    assert result["stage11_acceptance"] == "BLOCKED_PENDING_APPROVALS_AND_REAL_TESTS"
    assert "environment_variables_or_secrets" in result["not_examined"]


def test_invalid_cli_port_fails_before_docker_process():
    with patch("shutil.which", return_value="/usr/bin/docker"), patch("subprocess.run") as run:
        with pytest.raises(SystemExit) as err:
            main(["--container", "local-vllm", "--port", "65536"])
    assert err.value.code == 2
    run.assert_not_called()
