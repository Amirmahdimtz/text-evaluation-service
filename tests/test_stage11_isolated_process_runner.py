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
