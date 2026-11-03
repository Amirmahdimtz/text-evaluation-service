"""Bounded, redacted Stage11-only vLLM diagnostic observations.

Only captures allowlisted numbers and fixed status categories. Metrics are
shared-service counters and must never be attributed to one request.
"""
from __future__ import annotations

import asyncio
import json
import math

import httpx

from src.infrastructure.providers.llm.local_llm_provider import LocalLlmProvider

_METRICS_URL = "http://127.0.0.1:8000/metrics"
_MAX_METRICS_BYTES = 2 * 1024 * 1024
_METRIC_NAMES = frozenset({
    "vllm:prompt_tokens_total",
    "vllm:generation_tokens_total",
    "vllm:inter_token_latency_seconds_count",
    "vllm:inter_token_latency_seconds_sum",
    "vllm:request_generation_tokens_count",
    "vllm:request_generation_tokens_sum",
    "vllm:request_success_total",
    "vllm:request_decode_time_seconds_count",
    "vllm:request_decode_time_seconds_sum",
    "vllm:num_preemptions_total",
})
_FINISH_REASONS = frozenset({"stop", "length", "tool_calls", "content_filter"})
_TOKEN_FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")


def _safe_token_count(value: object) -> int | None:
    # bool is a subclass of int; model/server counts must not be booleans.
    return value if type(value) is int and 0 <= value <= 10_000_000 else None


def _response_metadata(data: dict) -> dict:
    """Never retain or emit content, prompts, upstream errors, or extra keys."""
    finish = "UNAVAILABLE"
    syntax = "UNAVAILABLE"
    choices = data.get("choices")
    if isinstance(choices, list) and len(choices) == 1:
        choice = choices[0]
        if isinstance(choice, dict):
            raw_reason = choice.get("finish_reason")
            if isinstance(raw_reason, str) and raw_reason in _FINISH_REASONS:
                finish = raw_reason
            elif raw_reason is not None:
                finish = "OTHER"
            message = choice.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                def reject_nonfinite(_value: str) -> None:
                    raise ValueError("STAGE11_NONFINITE_JSON")

                try:
                    json.loads(message["content"], parse_constant=reject_nonfinite)
                except (ValueError, RecursionError):
                    syntax = "invalid"
                else:
                    syntax = "valid"
    usage = data.get("usage")
    counts = (
        {field: _safe_token_count(usage.get(field)) for field in _TOKEN_FIELDS}
        if isinstance(usage, dict) else None
    )
    return {
        "finish_reason": finish,
        "json_syntax": syntax,
        "reported_usage": counts,
    }


class DiagnosticLocalLlmProvider(LocalLlmProvider):
    """Stage11-only transport observation; uses the production request/validator."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.response_diagnostic: dict | None = None

    async def _send(self, method: str, path: str, payload: dict | None = None) -> dict:
        result = await super()._send(method, path, payload)
        if method == "POST" and path == "/chat/completions":
            self.response_diagnostic = _response_metadata(result)
        return result


def parse_metrics(raw: bytes) -> dict[str, float]:
    """Sum approved Prometheus samples across labels without exposing labels."""
    if len(raw) > _MAX_METRICS_BYTES:
        return {}
    try:
        data = raw.decode("utf-8")
    except UnicodeError:
        return {}
    counters: dict[str, float] = {}
    for line in data.splitlines():
        if not line.startswith("vllm:"):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        name = fields[0].split("{", 1)[0]
        if name not in _METRIC_NAMES:
            continue
        try:
            value = float(fields[1])
        except ValueError:
            continue
        if not math.isfinite(value) or not 0 <= value <= 1e15:
            continue
        counters[name] = counters.get(name, 0.0) + value
    return counters


async def read_metrics() -> dict[str, float] | None:
    """Two read-only localhost GETs per diagnostic run, with hard time/size caps."""
    try:
        async with asyncio.timeout(3):
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(3), trust_env=False, follow_redirects=False,
            ) as client:
                async with client.stream("GET", _METRICS_URL) as response:
                    if response.status_code != 200:
                        return None
                    chunks: list[bytes] = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > _MAX_METRICS_BYTES:
                            return None
                        chunks.append(chunk)
        parsed = parse_metrics(b"".join(chunks))
        return parsed or None
    except (asyncio.TimeoutError, httpx.HTTPError, UnicodeError, ValueError):
        # Never copy upstream exception text, URLs, labels or model content.
        return None


def metrics_delta(
    before: dict[str, float] | None, after: dict[str, float] | None,
) -> tuple[str, dict[str, float] | None]:
    if not before or not after:
        return "UNAVAILABLE", None
    keys = before.keys() & after.keys()
    if not keys:
        return "UNAVAILABLE", None
    deltas: dict[str, float] = {}
    for key in sorted(keys):
        delta = after[key] - before[key]
        if not math.isfinite(delta) or delta < -1e-8:
            return "COUNTER_RESET_OR_INVALID", None
        deltas[key] = round(max(0.0, delta), 6)
    return "AVAILABLE_SHARED_UNATTRIBUTED", deltas
