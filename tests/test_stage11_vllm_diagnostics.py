"""No-network tests for safe Stage11 vLLM request/metrics diagnostics."""
from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from scripts.verification import stage11_vllm_diagnostics as diag
from scripts.verification import stage11_real_model_criterion_probe as probe


def _model_reply(*, finish="stop", content=None, usage=None):
    result = {
        "criterion_code": "media_message_clarity",
        "status": "not_assessed",
        "score": None,
        "reason": "Synthetic data is insufficient",
        "strengths": [],
        "weaknesses": [],
        "recommendations": [],
        "evidence": [],
    }
    return {
        "model": "shared-llm",
        "choices": [{
            "finish_reason": finish,
            "message": {"content": content if content is not None else json.dumps(result)},
        }],
        "usage": usage if usage is not None else {
            "prompt_tokens": 225, "completion_tokens": 55, "total_tokens": 280,
        },
    }


@pytest.mark.parametrize("reason,expected", [
    ("stop", "stop"), ("length", "length"),
    ("private-remote-text", "OTHER"), (["private-content"], "OTHER"),
    (None, "UNAVAILABLE"),
])
def test_response_metadata_only_reports_safe_categories(reason, expected):
    response = _model_reply(finish=reason)
    response["choices"][0]["message"]["content"] = '{"x": "private-user-input"}'
    result = diag._response_metadata(response)
    assert result["finish_reason"] == expected
    assert result["json_syntax"] == "valid"
    assert result["reported_usage"]["completion_tokens"] == 55
    assert "private" not in json.dumps(result)
    assert "choices" not in json.dumps(result)


@pytest.mark.parametrize("content,expected", [
    ('{"criterion_code": "safe"}', "valid"),
    ("{broken-json", "invalid"),
    ("NaN", "invalid"),  # Nonfinite constants are not valid standard JSON.
    ("", "invalid"),
])
def test_json_syntax_does_not_expose_output_text(content, expected):
    result = diag._response_metadata(_model_reply(content=content))
    assert result["json_syntax"] == expected
    if content:
        assert content not in json.dumps(result)


def test_usage_counts_reject_untrusted_types_and_bounds():
    response = _model_reply(usage={
        "prompt_tokens": True,
        "completion_tokens": -5,
        "total_tokens": 10000001,
        "private_token": "very_sensitive",
    })
    result = diag._response_metadata(response)
    assert result["reported_usage"] == {
        "prompt_tokens": None, "completion_tokens": None, "total_tokens": None,
    }
    assert "very_sensitive" not in json.dumps(result)


def test_metrics_allowlisted_parsing_sums_labels_but_drops_them():
    raw = (
        '# HELP vllm:generation_tokens_total private-internal-description\n'
        'vllm:generation_tokens_total{model_name="PRIVATE-TENANT"} 101\n'
        'vllm:generation_tokens_total{model_name="another"} 22\n'
        'vllm:request_success_total{finished_reason="stop"} 2\n'
        'vllm:request_success_total{finished_reason="abort"} 1\n'
        'vllm:inter_token_latency_seconds_sum 12.5\n'
        'vllm:unknown_metric{secret="SHOULD-NOT-LEAK"} 200\n'
        'vllm:prompt_tokens_total NaN\n'
        'vllm:request_generation_tokens_sum -9\n'
    ).encode()
    result = diag.parse_metrics(raw)
    assert result == {
        "vllm:generation_tokens_total": 123.0,
        "vllm:request_success_total": 3.0,
        "vllm:inter_token_latency_seconds_sum": 12.5,
    }
    assert "PRIVATE-TENANT" not in json.dumps(result)
    assert "SHOULD-NOT-LEAK" not in json.dumps(result)


@pytest.mark.parametrize("raw", [
    b"\xff", b"vllm:generation_tokens_total bogus\n",
    b"vllm:generation_tokens_total inf\n",
    b"vllm:private_metric 3\n",
])
def test_invalid_metrics_are_ignored(raw):
    assert diag.parse_metrics(raw) == {}


def test_large_metrics_payload_is_rejected():
    assert diag.parse_metrics(b"x" * (diag._MAX_METRICS_BYTES + 1)) == {}


def test_delta_is_shared_and_never_negative():
    before = {"vllm:generation_tokens_total": 200.0, "vllm:request_success_total": 2.0}
    after = {"vllm:generation_tokens_total": 235.0, "vllm:request_success_total": 2.0}
    status, delta = diag.metrics_delta(before, after)
    assert status == "AVAILABLE_SHARED_UNATTRIBUTED"
    assert delta == {
        "vllm:generation_tokens_total": 35.0,
        "vllm:request_success_total": 0.0,
    }
    assert diag.metrics_delta(before, {
        "vllm:generation_tokens_total": 1.0, "vllm:request_success_total": 2.0,
    }) == ("COUNTER_RESET_OR_INVALID", None)
    assert diag.metrics_delta(None, after) == ("UNAVAILABLE", None)


@pytest.mark.parametrize("mode", ["stop", "length", "invalid_json", "timeout"])
def test_real_provider_mock_transport_diagnostic_is_redacted_and_fail_closed(
    monkeypatch, mode,
):
    calls = []

    async def handler(request):
        calls.append(request)
        assert request.url.path == "/v1/chat/completions"
        request_payload = json.loads(request.content)
        assert request_payload["max_tokens"] == 256
        assert request_payload["chat_template_kwargs"] == {"enable_thinking": False}
        if mode == "timeout":
            raise httpx.ReadTimeout("PRIVATE_FAILURE_REQUEST")
        finish = "length" if mode == "length" else "stop"
        content = "{private-secret" if mode == "invalid_json" else None
        return httpx.Response(200, json=_model_reply(finish=finish, content=content))

    monkeypatch.setattr(
        probe, "DiagnosticLocalLlmProvider",
        lambda config, secrets: diag.DiagnosticLocalLlmProvider(
            config, secrets, transport=httpx.MockTransport(handler),
        ),
    )
    snapshots = iter([
        {"vllm:generation_tokens_total": 100.0, "vllm:request_success_total": 2.0},
        {"vllm:generation_tokens_total": 135.0, "vllm:request_success_total": 3.0},
    ])

    async def sampled_metrics():
        return next(snapshots)

    monkeypatch.setattr(probe, "read_metrics", sampled_metrics)
    result = asyncio.run(probe._run_live(
        domain="media", disable_thinking=True,
        diagnostics=True, max_output_tokens=256,
    ))
    assert len(calls) == 1
    assert result["requests_attempted"] == result["requests_planned"] == 1
    assert result["diagnostics"]["max_output_tokens"] == 256
    assert result["diagnostics"]["metrics_attribution"] == "SHARED_SERVICE_UNATTRIBUTED"
    assert result["diagnostics"]["shared_metrics_delta"][
        "vllm:generation_tokens_total"
    ] == 35.0
    response = result["diagnostics"]["response"]
    if mode == "stop":
        assert result["results"][0]["contract"] == "valid"
        assert response["finish_reason"] == "stop"
        assert response["json_syntax"] == "valid"
        assert response["reported_usage"]["completion_tokens"] == 55
    elif mode == "length":
        assert result["results"][0]["error_code"] == "LLM_INCOMPLETE_GENERATION"
        assert response["finish_reason"] == "length"
        assert result["results"][0]["contract"] == "failed"
    elif mode == "invalid_json":
        assert result["results"][0]["error_code"] == "LLM_SCHEMA_REJECTED"
        assert response["json_syntax"] == "invalid"
    else:
        assert result["results"][0]["failure_kind"] == "REQUEST_TIMEOUT"
        assert response["finish_reason"] == "UNAVAILABLE"
        assert response["reported_usage"] is None
    public = json.dumps(result)
    assert "PRIVATE_FAILURE_REQUEST" not in public
    assert "private-secret" not in public


def test_metrics_failure_cannot_turn_provider_success_into_false_failure(monkeypatch):
    async def no_metrics():
        return None

    monkeypatch.setattr(probe, "read_metrics", no_metrics)
    monkeypatch.setattr(
        probe, "DiagnosticLocalLlmProvider",
        lambda config, secrets: diag.DiagnosticLocalLlmProvider(
            config, secrets,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json=_model_reply()),
            ),
        ),
    )
    report = asyncio.run(probe._run_live(domain="media", diagnostics=True))
    assert report["results"][0]["contract"] == "valid"
    assert report["diagnostics"]["metrics_status"] == "UNAVAILABLE"
    assert report["diagnostics"]["shared_metrics_delta"] is None



@pytest.mark.parametrize("mode", [
    "success", "redirect", "http_error", "transport_error", "oversized",
])
def test_read_metrics_is_bounded_local_and_does_not_follow_redirects(
    monkeypatch, mode,
):
    observed = []
    original_client = httpx.AsyncClient

    async def handler(request):
        observed.append(str(request.url))
        assert str(request.url) == "http://127.0.0.1:8000/metrics"
        if mode == "redirect":
            return httpx.Response(
                302, headers={"location": "https://untrusted.example/private"},
            )
        if mode == "http_error":
            return httpx.Response(503, text="private-error")
        if mode == "transport_error":
            raise httpx.ConnectError("private-transport-error")
        if mode == "oversized":
            return httpx.Response(200, content=b"x" * (diag._MAX_METRICS_BYTES + 1))
        return httpx.Response(
            200,
            text='vllm:generation_tokens_total{model_name="PRIVATE-OWNER"} 25\n',
        )

    def fake_client(**kwargs):
        assert kwargs["trust_env"] is False
        assert kwargs["follow_redirects"] is False
        return original_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(diag.httpx, "AsyncClient", fake_client)
    result = asyncio.run(diag.read_metrics())
    assert observed == ["http://127.0.0.1:8000/metrics"]
    if mode == "success":
        assert result == {"vllm:generation_tokens_total": 25.0}
    else:
        assert result is None
    assert "PRIVATE-OWNER" not in json.dumps(result)


@pytest.mark.parametrize("mode,expected", [
    ("quote_not_found", "EVIDENCE_QUOTE_NOT_FOUND"),
    ("offset_invalid", "EVIDENCE_OFFSET_INVALID"),
    ("missing_reason", "SCHEMA_MISSING_OR_INVALID_FIELD"),
    ("status_evidence", "STATUS_EVIDENCE_INCONSISTENT"),
    ("wrong_code", "CRITERION_CODE_MISMATCH"),
    ("duplicate_json_key", "JSON_DUPLICATE_KEY"),
    ("invalid_json", "JSON_SYNTAX_INVALID"),
])
def test_schema_failure_diagnostic_categories_use_real_provider_and_decoder(
    monkeypatch, mode, expected,
):
    from scripts.verification.stage11_vllm_diagnostics import (
        CompactResponseDiagnosticLocalLlmProvider,
    )
    from src.infrastructure.providers.llm.local_llm_provider import LlmProviderError

    case, _, _ = probe._load_selected_rubrics()[1]
    base = {
        "criterion_code": "media_message_clarity", "status": "not_assessed",
        "score": None, "reason": "Synthetic test value",
        "strengths": [], "weaknesses": [], "recommendations": [],
        "evidence": [],
    }
    if mode in ("quote_not_found", "offset_invalid"):
        base.update(status="assessed", score=3)
        base["evidence"] = [{
            "source_kind": "original_submission",
            "quote": "not-in-synthetic-source" if mode == "quote_not_found" else "امروز",
            "start_offset": 1, "end_offset": 24 if mode == "quote_not_found" else 6,
        }]
    elif mode == "missing_reason":
        del base["reason"]
    elif mode == "status_evidence":
        base["score"] = 3
    elif mode == "wrong_code":
        base["criterion_code"] = "speech_clarity"

    content = json.dumps(base, ensure_ascii=False)
    if mode == "duplicate_json_key":
        content = '{"criterion_code":"media_message_clarity","criterion_code":"speech_clarity"}'
    elif mode == "invalid_json":
        content = "{not-valid-private-model-json"

    async def handler(request):
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json=_model_reply(content=content))

    monkeypatch.setattr(
        probe, "CompactResponseDiagnosticLocalLlmProvider",
        lambda config, secrets: CompactResponseDiagnosticLocalLlmProvider(
            config, secrets, transport=httpx.MockTransport(handler),
        ),
    )
    async def no_metrics():
        return None
    monkeypatch.setattr(probe, "read_metrics", no_metrics)
    report = asyncio.run(probe._run_live(
        domain="media", disable_thinking=True, diagnostics=True,
        compact_response=True, max_output_tokens=512,
    ))
    row = report["results"][0]
    assert row["contract"] == "failed"
    assert row["error_code"] == "LLM_SCHEMA_REJECTED"
    assert row["schema_failure_category"] == expected
    safe = json.dumps(report, ensure_ascii=False)
    assert "not-in-synthetic-source" not in safe
    assert "not-valid-private-model-json" not in safe
    assert "Synthetic test value" not in safe
    assert case.original_text not in safe


def test_unknown_schema_error_category_never_leaks_arbitrary_failure_kind():
    from src.infrastructure.providers.llm.local_llm_provider import LlmProviderError
    class FakeEvaluator:
        async def evaluate_criterion_async(self, **kwargs):
            raise LlmProviderError(
                "LLM_SCHEMA_REJECTED",
                failure_kind="private-free-text-untrusted",
            )
    result = asyncio.run(probe._run_cases(FakeEvaluator(), domain="media"))
    assert result["results"][0]["schema_failure_category"] == "UNAVAILABLE"
    assert "private-free-text-untrusted" not in json.dumps(result)
