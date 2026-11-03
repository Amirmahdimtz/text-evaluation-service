"""Offline tests for JSON size and bounded schema/unconstrained comparison.

No vLLM/GPU usage; every provider HTTP call uses an in-memory transport.
"""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest

from scripts.verification import stage11_output_budget as budget
from scripts.verification import stage11_structured_decoding_compare as compare
from scripts.verification import stage11_real_model_criterion_probe as real
from scripts.verification.stage11_vllm_diagnostics import (
    DiagnosticLocalLlmProvider, UnconstrainedDiagnosticLocalLlmProvider,
)
from src.infrastructure.utils.config_reader import ConfigReader


def test_compact_json_has_identical_typed_content_with_all_required_keys():
    result = budget.analyze_offline()
    assert result["status"] == "OFFLINE_STRUCTURAL_ONLY_NOT_MODEL_QUALITY"
    assert result["sample_count"] == 6
    assert result["network_calls"] == 0
    assert result["tokenizer_counts_measured"] is False
    assert result["semantic_quality_verified"] is False
    assert {r["domain"] for r in result["samples"]} == {
        "speech", "media", "research",
    }
    assert {r["sample_status"] for r in result["samples"]} == {
        "assessed", "not_assessed",
    }
    for item in result["samples"]:
        assert item["strict_decoder_valid"] is True
        assert item["required_keys_preserved"] == 8
        assert 0 < item["compact_bytes"] < item["spaced_bytes"]
        assert item["byte_reduction"] == (
            item["spaced_bytes"] - item["compact_bytes"]
        )


def test_budget_cli_does_not_print_synthetic_text(capsys):
    assert budget.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["sample_count"] == 6
    assert "متن ساختگی" not in json.dumps(report, ensure_ascii=False)
    assert "نمونه آزمایشی" not in json.dumps(report, ensure_ascii=False)


def test_comparison_cli_dry_run_never_infers(monkeypatch, capsys):
    async def forbidden():
        pytest.fail("dry run may not call vLLM")
    monkeypatch.setattr(compare, "compare_live", forbidden)
    assert compare.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "DRY_RUN_NO_NETWORK"
    assert result["planned_requests"] == 2
    assert result["order"] == ["json_schema", "unconstrained"]


@pytest.mark.parametrize("args", [
    ["--execute-live"], ["--shared-gpu-approved"],
])
def test_live_comparison_requires_both_explicit_flags(args):
    with pytest.raises(SystemExit) as exc:
        compare.main(args)
    assert exc.value.code == 2


def _stub_report(*, error=None, duration=10000, tokens=256):
    return {
        "results": [{
            "contract": "failed" if error else "valid",
            "duration_ms": duration,
            **({"error_code": error} if error else {"status": "not_assessed"}),
        }],
        "diagnostics": {
            "response": {
                "finish_reason": "length" if error else "stop",
                "json_syntax": "invalid" if error else "valid",
                "reported_usage": {
                    "prompt_tokens": 600, "completion_tokens": tokens,
                    "total_tokens": 600 + tokens,
                } if error != "LLM_CIRCUIT_OPEN" else None,
            },
            "metrics_status": "AVAILABLE_SHARED_UNATTRIBUTED",
        },
    }


def test_pair_is_sequential_and_timing_not_mislabeled_as_causal(monkeypatch):
    observed = []
    async def fake_live(**kwargs):
        observed.append(kwargs)
        return _stub_report(error="LLM_INCOMPLETE_GENERATION")
    monkeypatch.setattr(compare, "_run_live", fake_live)
    report = asyncio.run(compare.compare_live())
    assert report["status"] == "TWO_ARM_TIMING_OBSERVED_NOT_CAUSAL"
    assert len(observed) == 2
    assert [x["comparison_unconstrained"] for x in observed] == [False, True]
    assert all(x["domain"] == "media" for x in observed)
    assert all(x["max_output_tokens"] == 256 for x in observed)
    assert all(x["disable_thinking"] is True for x in observed)
    assert all(x["diagnostics"] is True for x in observed)
    assert all(row["contract"] == "failed" for row in report["results"])
    assert report["structured_decoding_overhead_proven"] is False
    assert report["quality_benchmark"] is False
    assert report["shared_service_unattributed"] is True


def test_pair_stops_after_first_timeout(monkeypatch):
    calls = []
    async def fake_live(**kwargs):
        calls.append(kwargs)
        return _stub_report(error="LLM_CIRCUIT_OPEN")
    monkeypatch.setattr(compare, "_run_live", fake_live)
    report = asyncio.run(compare.compare_live())
    assert report["status"] == "INCONCLUSIVE_OR_ABORTED"
    assert report["attempted_requests"] == 1
    assert report["stopped_early"] is True
    assert len(calls) == 1


def test_comparator_report_is_redacted_and_does_not_claim_quality():
    raw = _stub_report(error="LLM_SCHEMA_REJECTED")
    raw["results"][0]["sensitive_exception"] = "PRIVATE_TEST_TEXT"
    raw["diagnostics"]["response"]["raw_content"] = "PRIVATE_MODEL_OUTPUT"
    row = compare._redacted_row("unconstrained", raw)
    assert row["mode"] == "unconstrained"
    assert "PRIVATE" not in json.dumps(row)


def test_unconstrained_provider_wire_payload_differs_by_only_response_format():
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        output = {
            "criterion_code": "media_message_clarity",
            "status": "not_assessed",
            "score": None,
            "reason": "Synthetic evidence insufficient",
            "strengths": [], "weaknesses": [],
            "recommendations": [], "evidence": [],
        }
        return httpx.Response(200, json={
            "model": "shared-llm",
            "choices": [{"finish_reason": "stop", "message": {
                "content": json.dumps(output),
            }}],
            "usage": {
                "prompt_tokens": 600, "completion_tokens": 52, "total_tokens": 652,
            },
        })

    llm = ConfigReader().settings.llm.__class__.model_validate({
        "enabled": True, "endpoint": "http://127.0.0.1:8000/v1",
        "model_id": "shared-llm", "model_revision": "unverified",
        "max_input_characters": 2048, "max_context_tokens": 8192,
        "max_output_tokens": 256, "timeout_seconds": 45,
        "max_concurrency": 1, "max_attempts": 1,
        "retry_backoff_seconds": 0, "circuit_failures": 1,
        "circuit_reset_seconds": 10, "temperature": 0,
        "thinking_mode": "disabled",
    })
    config = SimpleNamespace(
        environment="development", settings=SimpleNamespace(llm=llm),
    )
    secret_resolver = SimpleNamespace(resolve_reference=lambda _: None)

    async def run_pair():
        for cls in (
            DiagnosticLocalLlmProvider,
            UnconstrainedDiagnosticLocalLlmProvider,
        ):
            provider = cls(
                config, secret_resolver,
                transport=httpx.MockTransport(handler),
            )
            try:
                assessed = await provider.evaluate_async(
                    source_text="متن کاملا ساختگی برای بررسی قرارداد پاسخ و شواهد.",
                    criterion_code="media_message_clarity",
                    instructions="Rubric-only synthetic instructions",
                    rubric_checksum="a" * 64,
                )
                assert assessed.status == "not_assessed"
            finally:
                await provider.aclose()
    asyncio.run(run_pair())
    assert len(requests) == 2
    schema, unbounded = requests
    assert schema["response_format"]["type"] == "json_schema"
    assert "response_format" not in unbounded
    assert schema["max_tokens"] == unbounded["max_tokens"] == 256
    assert schema["chat_template_kwargs"] == unbounded["chat_template_kwargs"]
    assert schema["chat_template_kwargs"] == {"enable_thinking": False}
    schema_without_constraint = dict(schema)
    del schema_without_constraint["response_format"]
    assert schema_without_constraint == unbounded
    assert "PRIVATE" not in json.dumps(requests)


@pytest.mark.parametrize("bad", [
    {"comparison_unconstrained": True},
    {"comparison_unconstrained": True, "diagnostics": True, "domain": "speech"},
    {"comparison_unconstrained": True, "diagnostics": True, "domain": "media",
     "max_output_tokens": 512, "disable_thinking": True},
])
def test_direct_unconstrained_mode_cannot_bypass_safety_guards(bad):
    with pytest.raises(ValueError, match="STAGE11_DIAGNOSTICS_SCOPE_INVALID"):
        asyncio.run(real._run_live(**bad))
