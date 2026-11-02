"""Offline-only controls for the opt-in Stage11 isolated process runner."""
import json
import os

import pytest

from scripts.verification import stage11_isolated_process_runner as runner


def test_default_is_noop(monkeypatch, capsys):
    monkeypatch.setattr(
        runner, "execute_isolated",
        lambda: pytest.fail("dry run must never call Docker"),
    )
    assert runner.main([]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == (
        "DRY_RUN_NO_DOCKER_NO_NETWORK"
    )


@pytest.mark.parametrize("name", [
    "TES_STAGE05_DATABASE_URL",
    "TES_STAGE11_SETTINGS_FILE",
    "TES_STAGE11_DB_PASSWORD",
    "TES_STAGE11_DB_PORT",
])
def test_existing_db_or_private_runtime_rejected(monkeypatch, name):
    for key in (
        "TES_STAGE05_DATABASE_URL", "TES_STAGE11_SETTINGS_FILE",
        "TES_STAGE11_DB_PASSWORD", "TES_STAGE11_DB_PORT",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    monkeypatch.setenv(name, "synthetic-occupied-test-scope")
    with pytest.raises(RuntimeError, match="STAGE11_EXISTING_ENVIRONMENT_REFUSED"):
        runner.execute_isolated()


def test_non_dev_runner_rejected_before_docker(monkeypatch):
    for key in (
        "TES_STAGE05_DATABASE_URL", "TES_STAGE11_SETTINGS_FILE",
        "TES_STAGE11_DB_PASSWORD", "TES_STAGE11_DB_PORT",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TES_ENVIRONMENT", "staging")
    with pytest.raises(RuntimeError, match="STAGE11_EXISTING_ENVIRONMENT_REFUSED"):
        runner.execute_isolated()


def test_image_absent_or_docker_error_fails_closed_without_leak(
    monkeypatch, capsys,
):
    for key in (
        "TES_STAGE05_DATABASE_URL", "TES_STAGE11_SETTINGS_FILE",
        "TES_STAGE11_DB_PASSWORD", "TES_STAGE11_DB_PORT",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TES_ENVIRONMENT", "development")

    def docker_unavailable(*args, **kwargs):
        raise FileNotFoundError("synthetic-sensitive-error-message")

    monkeypatch.setattr(runner, "_invoke", docker_unavailable)
    assert runner.main(["--execute-isolated"]) == 2
    output = capsys.readouterr().out
    assert "synthetic-sensitive-error-message" not in output
    assert "STAGE11_ISOLATED_RUN_ABORTED" in output

@pytest.mark.parametrize("failure_phase", [
    "compose_up", "postgres_readiness", "schema_migration", "api_worker_e2e",
])
def test_failure_phase_redacted_and_unique_container_stop_attempted(
    monkeypatch, capsys, failure_phase
):
    for key in (
        "TES_STAGE05_DATABASE_URL", "TES_STAGE11_SETTINGS_FILE",
        "TES_STAGE11_DB_PASSWORD", "TES_STAGE11_DB_PORT",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    calls = []

    async def ready(_env):
        if failure_phase == "postgres_readiness":
            raise RuntimeError("synthetic-sensitive-password")

    def invoke(args, *, env, suppress_output=False):
        calls.append(args)
        if ((failure_phase == "compose_up" and "up" in args)
                or (failure_phase == "schema_migration" and "upgrade" in args)
                or (failure_phase == "api_worker_e2e" and "pytest" in args)):
            raise RuntimeError("synthetic-sensitive-password")

    monkeypatch.setattr(runner, "_invoke", invoke)
    monkeypatch.setattr(runner, "_wait_for_database", ready)
    assert runner.main(["--execute-isolated"]) == 2
    printed = capsys.readouterr().out
    result = json.loads(printed.splitlines()[-1])
    assert result["failure_phase"] == failure_phase
    assert result["status"] == "ISOLATED_PROCESS_E2E_FAILED"
    assert "synthetic-sensitive-password" not in printed
    assert any("stop" in args for args in calls)
    assert all("down" not in args for args in calls)


def test_runner_succeeds_with_mocked_isolated_operations(monkeypatch, capsys):
    for key in (
        "TES_STAGE05_DATABASE_URL", "TES_STAGE11_SETTINGS_FILE",
        "TES_STAGE11_DB_PASSWORD", "TES_STAGE11_DB_PORT",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    calls = []

    async def ready(_env):
        pass

    def invoke(args, *, env, suppress_output=False):
        calls.append(args)
        assert suppress_output is True
        assert "down" not in args

    monkeypatch.setattr(runner, "_invoke", invoke)
    monkeypatch.setattr(runner, "_wait_for_database", ready)
    assert runner.main(["--execute-isolated"]) == 0
    printed = capsys.readouterr().out
    assert '"status": "ISOLATED_PROCESS_E2E_PASS"' in printed
    assert any("upgrade" in args for args in calls)
    assert any("pytest" in args for args in calls)
    assert any("stop" in args for args in calls)
