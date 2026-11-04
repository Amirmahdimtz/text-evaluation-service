"""No-network Stage11 global phase inventory regression tests."""
from __future__ import annotations

import json

import pytest

from scripts.verification import stage11_vllm_phase_inventory as inventory
from scripts.verification.stage11_vllm_diagnostics import parse_metrics


def test_default_mode_makes_zero_network_calls(monkeypatch, capsys):
    async def forbidden():
        pytest.fail("Default must not fetch local metrics")
    monkeypatch.setattr(inventory, "read_metrics", forbidden)
    assert inventory.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "OFFLINE_PHASE_METRICS_PLAN"
    assert result["network_requests"] == 0
    assert result["historical_media_request_phase_breakdown"] == "UNAVAILABLE"


def test_phase_histograms_are_allowlisted_and_scrub_all_labels():
    raw = (
        '# HELP vllm:request_queue_time_seconds private description\n'
        'vllm:request_queue_time_seconds_count{model_name="PRIVATE_ID"} 1\n'
        'vllm:request_queue_time_seconds_count{model_name="OTHER_ID"} 2\n'
        'vllm:request_queue_time_seconds_sum{model_name="PRIVATE_ID"} 0.2\n'
        'vllm:request_queue_time_seconds_sum{model_name="OTHER_ID"} 0.4\n'
        'vllm:request_prefill_time_seconds_count 3\n'
        'vllm:request_prefill_time_seconds_sum 1.5\n'
        'vllm:request_decode_time_seconds_count 0\n'
        'vllm:request_decode_time_seconds_sum 0\n'
        'vllm:num_requests_waiting{tenant="PRIVATE_USER"} 2\n'
        'vllm:private_request_trace{source="SECRET"} 300\n'
    ).encode()
    parsed = parse_metrics(raw)
    result = inventory.inventory(parsed)
    assert result["phase_metrics"]["queue"] == {
        "status": "SHARED_LIFETIME_AGGREGATE",
        "sample_count": 3, "sum_seconds": 0.6, "mean_seconds": 0.2,
    }
    assert result["phase_metrics"]["prefill"]["sample_count"] == 3
    assert result["phase_metrics"]["prefill"]["mean_seconds"] == 0.5
    assert result["phase_metrics"]["decode"]["status"] == (
        "ZERO_RECORDED_SAMPLES"
    )
    assert result["phase_metrics"]["inference"]["status"] == (
        "NOT_PRESENT_IN_SNAPSHOT"
    )
    assert result["current_shared_queue"]["waiting"] == 2.0
    assert result["historical_media_request_phase_breakdown"] == "UNAVAILABLE"
    assert result["per_request_attribution"] is False
    public = json.dumps(result)
    for private in ("PRIVATE_ID", "OTHER_ID", "PRIVATE_USER", "SECRET"):
        assert private not in public


@pytest.mark.parametrize("metrics,status", [
    ({}, "LOCAL_METRICS_UNAVAILABLE"),
    (None, "LOCAL_METRICS_UNAVAILABLE"),
    ({"vllm:request_queue_time_seconds_count": 1},
     "READ_ONLY_SHARED_PHASE_INVENTORY"),
])
def test_missing_metrics_never_claim_recovered_historical_trace(metrics, status):
    report = inventory.inventory(metrics)
    assert report["status"] == status
    assert report["historical_media_request_phase_breakdown"] == "UNAVAILABLE"
    assert report["effective_guided_backend_verified"] is False
    if metrics:
        assert report["phase_metrics"]["queue"]["status"] == "INCOMPLETE_METRIC"


@pytest.mark.parametrize("values,expected", [
    ({"vllm:request_queue_time_seconds_count": 0.0,
      "vllm:request_queue_time_seconds_sum": 3.0}, "INVALID_AGGREGATE"),
    ({"vllm:request_queue_time_seconds_count": 1.25,
      "vllm:request_queue_time_seconds_sum": 2.0}, "INVALID_AGGREGATE"),
    ({"vllm:request_queue_time_seconds_count": -3.0,
      "vllm:request_queue_time_seconds_sum": 2.0}, "INCOMPLETE_METRIC"),
    ({"vllm:request_queue_time_seconds_count": 0.0,
      "vllm:request_queue_time_seconds_sum": 0.0}, "ZERO_RECORDED_SAMPLES"),
])
def test_phase_invalid_or_zero_samples_fail_closed(values, expected):
    assert inventory.inventory(values)["phase_metrics"]["queue"]["status"] == (
        expected
    )


def test_explicit_opt_in_only_reads_single_approved_source(monkeypatch, capsys):
    calls = []
    async def read_once():
        calls.append("GET")
        return {
            "vllm:request_decode_time_seconds_count": 4.0,
            "vllm:request_decode_time_seconds_sum": 8.0,
        }
    monkeypatch.setattr(inventory, "read_metrics", read_once)
    assert inventory.main(["--inspect-local-metrics"]) == 0
    assert calls == ["GET"]
    report = json.loads(capsys.readouterr().out)
    assert report["network_requests"] == 1
    assert report["model_inference_requests"] == 0
    assert report["gpu_model_execution"] is False
    assert report["phase_metrics"]["decode"]["mean_seconds"] == 2
    assert report["historical_media_request_phase_breakdown"] == "UNAVAILABLE"


def test_unavailable_opt_in_fails_without_private_exception(monkeypatch, capsys):
    async def inaccessible():
        raise RuntimeError("PRIVATE_HOSTNAME_OR_SECRET")
    monkeypatch.setattr(inventory, "read_metrics", inaccessible)
    assert inventory.main(["--inspect-local-metrics"]) == 2
    report = capsys.readouterr().out
    assert "PRIVATE_HOSTNAME_OR_SECRET" not in report
    assert json.loads(report)["status"] == "LOCAL_METRICS_UNAVAILABLE"
    assert json.loads(report)["network_requests"] == 1
