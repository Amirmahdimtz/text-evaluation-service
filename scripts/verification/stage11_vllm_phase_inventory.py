"""Stage11 read-only vLLM 0.10.2 phase-metric inventory; no model POST.

The historic 45-second failed request CANNOT be decomposed by sampling
current, shared Prometheus counters. This tool reports only the availability
of allowlisted GLOBAL queue/prefill/decode histograms and current queue gauges.
Default mode never contacts the server. The opt-in mode makes one bounded,
read-only localhost /metrics GET using the existing Stage11 safe diagnostics.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math

from scripts.verification.stage11_vllm_diagnostics import read_metrics

_PHASES = (
    ("queue", "vllm:request_queue_time_seconds"),
    ("prefill", "vllm:request_prefill_time_seconds"),
    ("decode", "vllm:request_decode_time_seconds"),
    ("inference", "vllm:request_inference_time_seconds"),
    ("end_to_end", "vllm:e2e_request_latency_seconds"),
    ("time_to_first_token", "vllm:time_to_first_token_seconds"),
)
_CURRENT_GAUGES = (
    ("running", "vllm:num_requests_running"),
    ("waiting", "vllm:num_requests_waiting"),
    ("swapped", "vllm:num_requests_swapped"),
)


def _safe_metric(value: object) -> float | None:
    if (type(value) not in (float, int) or value < 0 or value > 1e15
            or not math.isfinite(value)):
        return None
    return float(value)


def _phase_entry(values: dict[str, float], root: str) -> dict[str, object]:
    count = _safe_metric(values.get(root + "_count"))
    total = _safe_metric(values.get(root + "_sum"))
    if count is None and total is None:
        return {"status": "NOT_PRESENT_IN_SNAPSHOT", "sample_count": None,
                "sum_seconds": None, "mean_seconds": None}
    if count is None or total is None:
        return {"status": "INCOMPLETE_METRIC", "sample_count": None,
                "sum_seconds": None, "mean_seconds": None}
    if not count.is_integer() or (count == 0 and total != 0):
        return {"status": "INVALID_AGGREGATE", "sample_count": None,
                "sum_seconds": None, "mean_seconds": None}
    if count == 0:
        return {"status": "ZERO_RECORDED_SAMPLES", "sample_count": 0,
                "sum_seconds": 0.0, "mean_seconds": None}
    return {
        "status": "SHARED_LIFETIME_AGGREGATE",
        "sample_count": int(count),
        "sum_seconds": round(total, 6),
        "mean_seconds": round(total / count, 6),
    }


def inventory(metrics: dict[str, float] | None) -> dict[str, object]:
    """Analyze redacted allowlisted samples, never a request-specific timeline."""
    result: dict[str, object] = {
        "status": ("READ_ONLY_SHARED_PHASE_INVENTORY"
                   if metrics else "LOCAL_METRICS_UNAVAILABLE"),
        "scope": "ONE_CURRENT_SHARED_SNAPSHOT_NOT_HISTORICAL_TRACE",
        "historical_media_request_phase_breakdown": "UNAVAILABLE",
        "per_request_attribution": False,
        "effective_guided_backend_verified": False,
        "model_revision_verified": False,
        "no_new_inference": True,
        "gpu_model_execution": False,
        "model_inference_requests": 0,
        "raw_metric_labels_or_model_ids_emitted": False,
        "phase_metrics": {},
        "current_shared_queue": {},
    }
    if not metrics:
        return result
    result["phase_metrics"] = {
        name: _phase_entry(metrics, root) for name, root in _PHASES
    }
    result["current_shared_queue"] = {
        name: _safe_metric(metrics.get(metric))
        for name, metric in _CURRENT_GAUGES
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inspect-local-metrics", action="store_true",
        help="One owner-approved read-only GET to 127.0.0.1:8000/metrics.",
    )
    args = parser.parse_args(argv)
    if not args.inspect_local_metrics:
        print(json.dumps({
            "status": "OFFLINE_PHASE_METRICS_PLAN",
            "network_requests": 0,
            "model_inference_requests": 0,
            "gpu_model_execution": False,
            "read_only_metrics_get_requires_owner_approval": True,
            "historical_media_request_phase_breakdown": "UNAVAILABLE",
        }, sort_keys=True))
        return 0
    try:
        # Existing helper enforces exactly one loopback URL, no redirects,
        # trust_env=False, 2MiB maximum body and 3s overall timeout.
        result = inventory(asyncio.run(read_metrics()))
    except Exception:
        # No exception text, URL, payload or source path in terminal output.
        result = inventory(None)
    result["network_requests"] = 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "READ_ONLY_SHARED_PHASE_INVENTORY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
