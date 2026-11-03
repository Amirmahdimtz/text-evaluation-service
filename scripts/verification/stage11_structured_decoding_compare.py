"""Stage11 synthetic structured-vs-unconstrained A/B diagnostic.

Default is a zero-network plan. Live mode requires explicit two-flag
consent and independently approved access to the shared vLLM GPU.
This is ONE ordered pair maximum, NOT a throughput benchmark or quality gate.
"""
from __future__ import annotations

import argparse
import asyncio
import json

from scripts.verification.stage11_real_model_criterion_probe import _run_live

_MODES = ("json_schema", "unconstrained")
_ALLOWED_FOLLOWUP_FAILURES = frozenset({
    "LLM_INCOMPLETE_GENERATION", "LLM_SCHEMA_REJECTED",
})


def _redacted_row(mode: str, report: dict) -> dict:
    rows = report.get("results", [])
    outcome = rows[0] if len(rows) == 1 else {}
    diag = report.get("diagnostics", {})
    response = diag.get("response", {})
    return {
        "mode": mode,
        "contract": outcome.get("contract", "failed"),
        "status": outcome.get("status", "UNAVAILABLE"),
        "duration_ms": outcome.get("duration_ms"),
        "error_code": outcome.get("error_code"),
        "failure_kind": outcome.get("failure_kind"),
        "finish_reason": response.get("finish_reason", "UNAVAILABLE"),
        "json_syntax": response.get("json_syntax", "UNAVAILABLE"),
        "reported_usage": response.get("reported_usage"),
        "shared_metrics_status": diag.get("metrics_status", "UNAVAILABLE"),
    }


async def compare_live() -> dict:
    rows = []
    stopped = False
    for mode in _MODES:
        report = await _run_live(
            domain="media", disable_thinking=True, diagnostics=True,
            max_output_tokens=256,
            comparison_unconstrained=(mode == "unconstrained"),
        )
        row = _redacted_row(mode, report)
        rows.append(row)
        # Fail fast on timeout, transport/HTTP failures, circuit break or
        # other unknown errors. A length/schema-rejected complete response
        # can still be useful for the bounded speed comparison.
        if row["contract"] != "valid" and (
            row["error_code"] not in _ALLOWED_FOLLOWUP_FAILURES
        ):
            stopped = True
            break

    measured = len(rows) == 2 and all(
        isinstance(row["reported_usage"], dict)
        and type(row["reported_usage"].get("completion_tokens")) is int
        and row["reported_usage"]["completion_tokens"] > 0
        and type(row["duration_ms"]) is int and row["duration_ms"] > 0
        for row in rows
    )
    return {
        "status": (
            "TWO_ARM_TIMING_OBSERVED_NOT_CAUSAL"
            if measured else "INCONCLUSIVE_OR_ABORTED"
        ),
        "planned_requests": 2,
        "attempted_requests": len(rows),
        "stopped_early": stopped,
        "order": list(_MODES),
        "max_concurrent_requests": 1,
        "retries": 0,
        "synthetic_only": True,
        "max_output_tokens_each": 256,
        "timeout_seconds_each": 45,
        "thinking_mode_requested": "disabled",
        "shared_service_unattributed": True,
        "equal_prompts_and_sampling_except_response_format": True,
        "quality_benchmark": False,
        "structured_decoding_overhead_proven": False,
        "results": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true",
                        help="Run at most two sequential synthetic model calls.")
    parser.add_argument("--shared-gpu-approved", action="store_true",
                        help="Confirm separate operational approval for shared GPU use.")
    args = parser.parse_args(argv)
    if args.execute_live != args.shared_gpu_approved:
        parser.error("--execute-live requires --shared-gpu-approved and vice versa")
    if not args.execute_live:
        print(json.dumps({
            "status": "DRY_RUN_NO_NETWORK",
            "planned_requests": 2,
            "order": list(_MODES),
            "max_concurrent_requests": 1,
            "max_output_tokens_each": 256,
            "timeout_seconds_each": 45,
            "retries": 0,
            "requires": "--execute-live --shared-gpu-approved",
            "caveat": "Ordered pair; no attribution/causal or quality conclusion",
        }, sort_keys=True))
        return 0
    try:
        report = asyncio.run(compare_live())
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if report["status"] == "TWO_ARM_TIMING_OBSERVED_NOT_CAUSAL" else 2
    except Exception:
        print(json.dumps({"status": "STAGE11_DECODING_COMPARISON_ABORTED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
