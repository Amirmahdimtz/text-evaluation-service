"""Bounded, redacted Stage11-only vLLM diagnostic observations.

Only captures allowlisted numbers and fixed status categories. Metrics are
shared-service counters and must never be attributed to one request.
"""
from __future__ import annotations

import asyncio
import json
import math
import re

import httpx
from pydantic import ValidationError

from src.infrastructure.providers.llm.local_llm_provider import LlmProviderError, LocalLlmProvider
from src.infrastructure.providers.llm.structured_response import decode_criterion_response

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
    # vLLM 0.10.2 request-phase histogram sums/counts. Global, not per request.
    "vllm:request_queue_time_seconds_count",
    "vllm:request_queue_time_seconds_sum",
    "vllm:request_prefill_time_seconds_count",
    "vllm:request_prefill_time_seconds_sum",
    "vllm:request_inference_time_seconds_count",
    "vllm:request_inference_time_seconds_sum",
    "vllm:e2e_request_latency_seconds_count",
    "vllm:e2e_request_latency_seconds_sum",
    "vllm:time_to_first_token_seconds_count",
    "vllm:time_to_first_token_seconds_sum",
    "vllm:num_requests_running",
    "vllm:num_requests_waiting",
    "vllm:num_requests_swapped",
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



# Fixed taxonomy only. Never expose validation messages, model content, or offsets.
_SAFE_SCHEMA_CATEGORIES = frozenset({
    "CONTRACT_VALID", "RESPONSE_ENVELOPE_INVALID", "MODEL_RESPONSE_MISMATCH",
    "JSON_SYNTAX_INVALID", "JSON_DUPLICATE_KEY", "JSON_NONFINITE_VALUE",
    "JSON_RESPONSE_TOO_LARGE", "SCHEMA_MISSING_OR_INVALID_FIELD",
    "SCHEMA_EVIDENCE_INVALID", "STATUS_EVIDENCE_INCONSISTENT",
    "CRITERION_CODE_MISMATCH", "EVIDENCE_QUOTE_NOT_FOUND",
    "EVIDENCE_OFFSET_INVALID", "UNAVAILABLE",
})


def _classify_criterion_payload(
    response: dict, *, model_id: str, criterion_code: str,
    source_text: str, max_response_bytes: int,
) -> str:
    """Reapply the real decoder only for redacted failure taxonomy, not recovery."""
    if not isinstance(response, dict):
        return "RESPONSE_ENVELOPE_INVALID"
    if response.get("model") != model_id:
        return "MODEL_RESPONSE_MISMATCH"
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        return "RESPONSE_ENVELOPE_INVALID"
    choice = choices[0]
    if not isinstance(choice, dict):
        return "RESPONSE_ENVELOPE_INVALID"
    if choice.get("finish_reason") != "stop":
        return "UNAVAILABLE"
    message = choice.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        return "RESPONSE_ENVELOPE_INVALID"
    try:
        decode_criterion_response(
            message["content"], expected_code=criterion_code,
            source_text=source_text, max_response_bytes=max_response_bytes,
        )
        return "CONTRACT_VALID"
    except json.JSONDecodeError:
        return "JSON_SYNTAX_INVALID"
    except ValidationError as exc:
        try:
            errors = exc.errors(
                include_input=False, include_context=False, include_url=False,
            )
            if not errors:
                return "SCHEMA_MISSING_OR_INVALID_FIELD"
            location = errors[0].get("loc")
            if not location:
                return "STATUS_EVIDENCE_INCONSISTENT"
            if isinstance(location, (tuple, list)) and location[0] == "evidence":
                return "SCHEMA_EVIDENCE_INVALID"
            return "SCHEMA_MISSING_OR_INVALID_FIELD"
        except Exception:
            return "UNAVAILABLE"
    except ValueError as exc:
        # Only exact developer-owned codes; never stringify an unknown error.
        code = exc.args[0] if len(exc.args) == 1 and type(exc.args[0]) is str else None
        return {
            "LLM_WRONG_CRITERION": "CRITERION_CODE_MISMATCH",
            "LLM_QUOTE_NOT_FOUND": "EVIDENCE_QUOTE_NOT_FOUND",
            "LLM_QUOTE_OFFSET_INVALID": "EVIDENCE_OFFSET_INVALID",
            "LLM_DUPLICATE_JSON_KEY": "JSON_DUPLICATE_KEY",
            "LLM_NONFINITE_JSON_NUMBER": "JSON_NONFINITE_VALUE",
            "LLM_RESPONSE_TOO_LARGE": "JSON_RESPONSE_TOO_LARGE",
            "LLM_INVALID_JSON": "JSON_SYNTAX_INVALID",
        }.get(code, "SCHEMA_MISSING_OR_INVALID_FIELD")
    except (TypeError, KeyError, AttributeError, IndexError):
        return "RESPONSE_ENVELOPE_INVALID"


class DiagnosticLocalLlmProvider(LocalLlmProvider):
    """Stage11-only transport observation; uses the production request/validator."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.response_diagnostic: dict | None = None
        self._classification_context: tuple[str, str] | None = None
        self._schema_failure_category = "UNAVAILABLE"

    async def evaluate_async(
        self, *, source_text: str, criterion_code: str,
        instructions: str, rubric_checksum: str,
    ):
        self._classification_context = (source_text, criterion_code)
        self._schema_failure_category = "UNAVAILABLE"
        try:
            return await super().evaluate_async(
                source_text=source_text, criterion_code=criterion_code,
                instructions=instructions, rubric_checksum=rubric_checksum,
            )
        except LlmProviderError as exc:
            if str(exc) == "LLM_SCHEMA_REJECTED":
                # An allowlisted category only; no exception message is exposed.
                exc.failure_kind = self._schema_failure_category
            raise
        finally:
            self._classification_context = None

    async def _send(self, method: str, path: str, payload: dict | None = None) -> dict:
        result = await super()._send(method, path, payload)
        if method == "POST" and path == "/chat/completions":
            self.response_diagnostic = _response_metadata(result)
            context = self._classification_context
            if context is not None:
                try:
                    self._schema_failure_category = _classify_criterion_payload(
                        result, model_id=self._config.model_id,
                        criterion_code=context[1], source_text=context[0],
                        max_response_bytes=max(
                            65536, self._config.max_output_tokens * 48,
                        ),
                    )
                except Exception:
                    # Diagnostics must never change the production decoder outcome.
                    self._schema_failure_category = "UNAVAILABLE"
        return result



# Experimental prompt-only variant; never registered in production DI.
_COMPACT_RESPONSE_GUIDANCE = (
    "Stage11 synthetic diagnostic only. Keep every required JSON field and comply "
    "with all rubric score anchors and evidence requirements. Prefer a single short "
    "Persian reason sentence (target 120 characters), and at most one brief, "
    "supported item per strengths, weaknesses and recommendations list where "
    "the rubric permits; otherwise use empty lists for unsupported items. "
    "Provide all necessary exact original-source evidence quotes and offsets, "
    "without normalization, omission or invention. Do not change score, status "
    "or abstention rules. Emit compact JSON without optional whitespace."
)


def compact_criterion_instructions(instructions: str) -> str:
    """Change only output brevity guidance, never the rubric or evidence rules."""
    if not isinstance(instructions, str) or len(instructions) > 10000:
        raise LlmProviderError("LLM_INPUT_REJECTED")

    def unique_pairs(pairs):
        values = {}
        for key, value in pairs:
            if key in values:
                raise ValueError("DUPLICATE_KEY")
            values[key] = value
        return values

    try:
        payload = json.loads(instructions, object_pairs_hook=unique_pairs)
    except (ValueError, TypeError, RecursionError):
        raise LlmProviderError("LLM_INPUT_REJECTED") from None
    if (not isinstance(payload, dict)
            or not all(key in payload for key in (
                "criterion_code", "operational_definition",
                "evaluation_instructions", "evidence_requirements",
                "applicability_rules", "score_anchors", "response_guidance",
            ))
            or not isinstance(payload["response_guidance"], str)
            or not payload["response_guidance"].strip()):
        raise LlmProviderError("LLM_INPUT_REJECTED")
    modified = dict(payload)
    modified["response_guidance"] = (
        payload["response_guidance"] + " " + _COMPACT_RESPONSE_GUIDANCE
    )
    output = json.dumps(
        modified, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    if len(output) > 10000:
        raise LlmProviderError("LLM_INPUT_REJECTED")
    return output


class CompactResponseDiagnosticLocalLlmProvider(DiagnosticLocalLlmProvider):
    """Opt-in prompt-brevity test; production schema and decoder are unchanged."""

    async def evaluate_async(
        self, *, source_text: str, criterion_code: str,
        instructions: str, rubric_checksum: str,
    ):
        return await super().evaluate_async(
            source_text=source_text,
            criterion_code=criterion_code,
            instructions=compact_criterion_instructions(instructions),
            rubric_checksum=rubric_checksum,
        )


# Diagnostic-only indexed excerpts. Derive spans from the exact original source.
# This never adjusts model offsets after generation or relaxes the strict decoder.
def indexed_evidence_instructions(instructions: str, source_text: str) -> str:
    """Give the synthetic model short, exact Unicode-indexed evidence options."""
    if (not isinstance(source_text, str)
            or not 32 <= len(source_text) <= 2048
            or not source_text.isprintable()):
        raise LlmProviderError("LLM_INPUT_REJECTED")
    base = compact_criterion_instructions(instructions)

    anchors: list[dict[str, object]] = []
    for match in re.finditer(r"[^.!؟\\n]+[.!؟]?", source_text):
        fragment = match.group(0)
        leading = len(fragment) - len(fragment.lstrip())
        start = match.start() + leading
        phrase = fragment[leading:].rstrip()
        if len(phrase) < 16:
            continue
        if len(phrase) > 56:
            boundary = phrase.rfind(" ", 24, 57)
            if boundary <= 24:
                raise LlmProviderError("LLM_INPUT_REJECTED")
            phrase = phrase[:boundary]
        end = start + len(phrase)
        if not (source_text[start:end] == phrase and start < end):
            raise LlmProviderError("LLM_INPUT_REJECTED")
        anchors.append({
            "quote": phrase, "start_offset": start, "end_offset": end,
        })
        if len(anchors) > 8:
            raise LlmProviderError("LLM_INPUT_REJECTED")
    if not anchors:
        raise LlmProviderError("LLM_INPUT_REJECTED")

    try:
        payload = json.loads(base)
    except ValueError:
        raise LlmProviderError("LLM_INPUT_REJECTED") from None
    guidance = (
        "Stage11 synthetic-only offset diagnostic: choose only semantically "
        "relevant evidence from the following exact source substrings, copying "
        "quote, start_offset and end_offset together WITHOUT modification. "
        "The offsets are Python Unicode codepoint indices in the untouched "
        "original source (start inclusive, end exclusive). Do not calculate "
        "offsets yourself, normalize the quote or add any other output fields. "
        "If none of these snippets adequately supports a rubric assessment, "
        "return not_assessed with null score and empty evidence; never invent "
        "a score or evidence. Pre-indexed evidence choices: "
    )
    payload["response_guidance"] += (
        " " + guidance
        + json.dumps(anchors, ensure_ascii=False, separators=(",", ":"))
    )
    output = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    if len(output) > 10000:
        raise LlmProviderError("LLM_INPUT_REJECTED")
    return output


class IndexedEvidenceDiagnosticLocalLlmProvider(DiagnosticLocalLlmProvider):
    """Opt-in test; leave production schema, scoring and quote checking intact."""

    async def evaluate_async(
        self, *, source_text: str, criterion_code: str,
        instructions: str, rubric_checksum: str,
    ):
        return await super().evaluate_async(
            source_text=source_text,
            criterion_code=criterion_code,
            instructions=indexed_evidence_instructions(instructions, source_text),
            rubric_checksum=rubric_checksum,
        )


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
    """One bounded read-only localhost GET; callers may invoke twice explicitly."""
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


class UnconstrainedDiagnosticLocalLlmProvider(DiagnosticLocalLlmProvider):
    """Stage11-only comparison: same messages, omit JSON Schema constraint.

    This MUST NOT be registered in DI or substituted for the production
    LocalLlmProvider. Its response is still checked by the strict decoder.
    """

    async def _send(
        self, method: str, path: str, payload: dict | None = None,
    ) -> dict:
        if method == "POST" and path == "/chat/completions":
            if not isinstance(payload, dict) or "response_format" not in payload:
                raise ValueError("STAGE11_COMPARISON_REQUEST_INVALID")
            # Do not mutate the production Provider request. All other
            # settings and both prompt messages remain byte-equivalent.
            unconstrained = dict(payload)
            del unconstrained["response_format"]
            return await super()._send(method, path, unconstrained)
        return await super()._send(method, path, payload)
