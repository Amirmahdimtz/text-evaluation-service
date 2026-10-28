"""Offline safety/contract tests for the Stage11 host-local preflight."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from scripts.verification.stage11_readonly_preflight import (
    GPU_QUERY, collect_inventory, main, parse_gpu_csv, probe_gpu,
    read_memory_summary,
)


def test_valid_gpu_csv_two_records():
    rows = parse_gpu_csv("0, NVIDIA RTX 3090, 24576, 18532, 550.10\n1, NVIDIA A10, 22528, 0, 550.10\n")
    assert len(rows) == 2
    assert rows[0]["vram_total_mib"] == 24576
    assert rows[1]["vram_used_mib_at_probe"] == 0
    assert "uuid" not in rows[0]


@pytest.mark.parametrize("raw", ["", "0, Model, 10, 11, 555", "0, Model, 10, -1, 555", "0, X, 10, 1", "0, X, 10, 1, 555\n0, Y, 10, 1, 555"])
def test_anomalous_gpu_output_fails_closed(raw):
    with pytest.raises(ValueError):
        parse_gpu_csv(raw)


def test_probe_gpu_only_bounded_readonly_nvidia_query():
    completed = Mock(returncode=0, stdout="0, NVIDIA RTX 3090, 24576, 18000, 555.11")
    with patch("shutil.which", return_value="/usr/bin/nvidia-smi"), patch("subprocess.run", return_value=completed) as run:
        result = probe_gpu()
    assert result["status"] == "OBSERVED_READ_ONLY"
    call = run.call_args
    assert call.args == (GPU_QUERY,)
    assert call.kwargs["timeout"] == 8
    assert call.kwargs["stderr"] == subprocess.DEVNULL
    assert call.kwargs["check"] is False
    assert "shell" not in call.kwargs


def test_missing_gpu_tool_never_spawns_process():
    with patch("shutil.which", return_value=None), patch("subprocess.run") as run:
        assert probe_gpu()["status"] == "TOOL_NOT_FOUND"
        run.assert_not_called()


def test_gpu_probe_timeout_is_unverified():
    with patch("shutil.which", return_value="/usr/bin/nvidia-smi"), patch("subprocess.run", side_effect=subprocess.TimeoutExpired(GPU_QUERY, 8)):
        assert probe_gpu() == {"status": "TIMEOUT", "gpus": []}


def test_failed_gpu_output_not_exposed():
    with patch("shutil.which", return_value="/usr/bin/nvidia-smi"), patch("subprocess.run", return_value=Mock(returncode=1, stdout="secret text")):
        assert probe_gpu() == {"status": "QUERY_FAILED", "gpus": []}


def test_memory_summary_without_private_metadata(tmp_path):
    f = tmp_path / "meminfo"
    f.write_text("MemTotal:       1048576 kB\nMemAvailable:    524288 kB\n", encoding="ascii")
    assert read_memory_summary(f) == {"status": "OBSERVED_READ_ONLY", "total_mib": 1024, "available_mib": 512}
    f.write_text("MemTotal: 123 bytes\nMemAvailable: 20 kB\n", encoding="ascii")
    assert read_memory_summary(f)["status"] == "UNVERIFIED"


def test_collect_and_main_skip_gpu_without_network_or_daemon(capsys):
    with patch("shutil.which", return_value=None), patch("subprocess.run") as run:
        assert main(["--no-gpu"]) == 0
        run.assert_not_called()
    payload = json.loads(capsys.readouterr().out)
    assert payload["stage11_acceptance"] == "BLOCKED_PENDING_APPROVALS_AND_REAL_TESTS"
    assert payload["gpu"]["status"] == "SKIPPED_BY_OPERATOR"
    assert "network_egress_or_tls" in payload["not_examined"]
    assert "hostname" not in str(payload).lower()


def test_disallow_output_path_and_unknown_side_effect_options():
    with pytest.raises(SystemExit) as err:
        main(["--output", "/tmp/preflight.txt"])
    assert err.value.code == 2
