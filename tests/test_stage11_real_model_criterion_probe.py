"""Offline safety and reporting tests; never contact the shared GPU."""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest

from src.core.services.text_evaluation.criterion_evaluation_service import (
    CriterionAssessment,
)
from src.infrastructure.providers.llm.local_llm_provider import (
    LlmProviderError, LocalLlmProvider,
)
from src.core.services.text_evaluation.criterion_evaluation_service import (
    CriterionEvaluationService,
)
from src.infrastructure.utils.config_reader import ConfigReader
from scripts.verification import stage11_real_model_criterion_probe as probe


def test_default_dry_run_never_infers(monkeypatch, capsys):
    async def forbidden():
        pytest.fail("dry run must not invoke real vLLM")
    monkeypatch.setattr(probe, "_run_live", forbidden)
    assert probe.main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "DRY_RUN_NO_NETWORK"
    assert report["requests_planned"] == 3
    assert report["criteria"] == [
        "speech_clarity", "media_message_clarity", "research_academic_writing"
    ]


def test_synthetic_cases_bind_to_actual_candidate_rubric():
    selected = probe._load_selected_rubrics()
    assert len(selected) == 3
    assert len({case.domain for case, _, _ in selected}) == 3
    for case, criterion, checksum in selected:
        assert criterion.criterion_code == case.criterion_code
        assert criterion.evaluation_instructions
        assert len(checksum) == 64
        assert isinstance(case.original_text, str)
        assert 32 <= len(case.original_text) <= 2048


@pytest.mark.parametrize("key,value", [
    ("TES_ENVIRONMENT", "production"),
    ("TES_STAGE11_SETTINGS_FILE", "/tmp/occupied-private.yaml"),
    ("TES_STAGE05_DATABASE_URL", "postgresql+asyncpg://fake"),
    ("TES_STAGE11_PROCESS_E2E", "1"),
])
def test_real_probing_refuses_private_runtime_and_other_environments(
    monkeypatch, key, value,
):
    for protected in (
        "TES_STAGE11_SETTINGS_FILE", "TES_STAGE05_DATABASE_URL",
        "TES_STAGE11_PROCESS_E2E",
    ):
        monkeypatch.delenv(protected, raising=False)
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match="STAGE11_PROBE_ENVIRONMENT_REFUSED"):
        probe._require_safe_environment()


def test_one_candidate_criterion_per_domain_without_leaking_evidence(capsys):
    class FakeEvaluator:
        async def evaluate_criterion_async(self, *, criterion, original_text,
                                           rubric_checksum):
            return CriterionAssessment(
                criterion_code=criterion.criterion_code,
                status="assessed", score=4, reason="synthetic secret not in output",
                reason_code=None, evidence=((original_text[:4], 0, 4),),
            )
    report = asyncio.run(probe._run_cases(FakeEvaluator()))
    assert report["status"] == "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS"
    assert report["requests_attempted"] == 3
    assert report["max_concurrent_requests"] == 1
    assert all(item["evidence_count"] == 1 for item in report["results"])
    safe = json.dumps(report, ensure_ascii=False)
    assert "secret" not in safe
    assert "ساختگی" not in safe
    assert all("reason" not in item for item in report["results"])


def test_legitimate_abstention_is_not_an_invented_score():
    class FakeEvaluator:
        async def evaluate_criterion_async(self, *, criterion, **kwargs):
            return CriterionAssessment(
                criterion_code=criterion.criterion_code,
                status="not_assessed", score=None, reason="No evidence",
                reason_code="MODEL_ABSTAINED",
            )
    report = asyncio.run(probe._run_cases(FakeEvaluator()))
    assert report["status"] == "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS"
    assert all(row["score"] is None and row["evidence_count"] == 0
               for row in report["results"])


def test_error_in_provider_is_redacted():
    class BrokenEvaluator:
        async def evaluate_criterion_async(self, **kwargs):
            raise RuntimeError("private-text-sensitive")
    report = asyncio.run(probe._run_cases(BrokenEvaluator()))
    assert report["status"] == "REAL_MODEL_THREE_DOMAIN_CONTRACT_PARTIAL_FAILURE"
    assert all(row["error_code"] == "STAGE11_MODEL_PROBE_FAILED"
               for row in report["results"])
    assert "private-text-sensitive" not in json.dumps(report)


def test_allowlisted_provider_errors():
    class BrokenEvaluator:
        async def evaluate_criterion_async(self, **kwargs):
            raise LlmProviderError("LLM_SCHEMA_REJECTED")
    report = asyncio.run(probe._run_cases(BrokenEvaluator()))
    assert all(row["error_code"] == "LLM_SCHEMA_REJECTED"
               for row in report["results"])


def test_mismatched_quote_is_rejected():
    class FakeEvaluator:
        async def evaluate_criterion_async(self, *, criterion, **kwargs):
            return CriterionAssessment(
                criterion_code=criterion.criterion_code, status="assessed",
                score=3, reason="synthetic", reason_code=None,
                evidence=(("text-not-present", 0, 16),),
            )
    report = asyncio.run(probe._run_cases(FakeEvaluator()))
    assert all(row["contract"] == "failed" for row in report["results"])


def test_main_live_simulation_has_no_real_io(monkeypatch, capsys):
    async def simulate(*, domain=None, disable_thinking=False,
                       diagnostics=False, max_output_tokens=512):
        return {"status": "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS"}
    monkeypatch.setattr(probe, "_run_live", simulate)
    assert probe.main(["--execute-live"]) == 0
    assert "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS" in capsys.readouterr().out


@pytest.mark.parametrize("kind", [
    "REQUEST_TIMEOUT", "TRANSPORT_ERROR", "HTTP_429", "HTTP_500",
    "HTTP_502", "HTTP_503", "HTTP_504",
])
def test_circuit_breaker_reports_allowed_kind_and_stops(kind):
    requests = []

    class FailingEvaluator:
        async def evaluate_criterion_async(self, *, criterion, **kwargs):
            requests.append(criterion.criterion_code)
            raise LlmProviderError("LLM_CIRCUIT_OPEN", failure_kind=kind)

    result = asyncio.run(probe._run_cases(FailingEvaluator()))
    assert requests == ["speech_clarity"]
    assert result["status"] == "REAL_MODEL_THREE_DOMAIN_CONTRACT_PARTIAL_FAILURE"
    assert (result["requests_planned"], result["requests_attempted"],
            result["requests_not_attempted"]) == (3, 1, 2)
    assert result["stopped_after_circuit_open"] is True
    assert len(result["results"]) == 1
    assert result["results"][0]["failure_kind"] == kind


@pytest.mark.parametrize("kind", [
    None, "UNTRUSTED_MARKER", "HTTP_418", "HTTP_503-private",
])
def test_unexpected_diagnostic_is_redacted(kind):
    class FailingEvaluator:
        async def evaluate_criterion_async(self, **kwargs):
            raise LlmProviderError("LLM_CIRCUIT_OPEN", failure_kind=kind)

    result = asyncio.run(probe._run_cases(FailingEvaluator()))
    assert result["results"][0]["failure_kind"] == "UNAVAILABLE"
    assert "UNTRUSTED_MARKER" not in json.dumps(result)


def test_other_provider_failures_dont_incorrectly_open_circuit():
    called = []

    class FailingEvaluator:
        async def evaluate_criterion_async(self, *, criterion, **kwargs):
            called.append(criterion.criterion_code)
            raise LlmProviderError("LLM_SCHEMA_REJECTED")

    result = asyncio.run(probe._run_cases(FailingEvaluator()))
    assert len(called) == 3
    assert result["requests_not_attempted"] == 0
    assert result["stopped_after_circuit_open"] is False
    assert all("failure_kind" not in item for item in result["results"])


@pytest.mark.parametrize("upstream,expected", [
    (429, "HTTP_429"), (503, "HTTP_503"),
    ("timeout", "REQUEST_TIMEOUT"),
    ("transport", "TRANSPORT_ERROR"),
])
def test_provider_mock_transport_failure_is_reported_without_extra_requests(
    upstream, expected,
):
    calls = []

    async def handler(request):
        calls.append(request)
        if upstream == "timeout":
            raise httpx.ReadTimeout("fake-transport-detail")
        if upstream == "transport":
            raise httpx.ConnectError("fake-transport-detail")
        return httpx.Response(upstream, text="fake-upstream-body")

    settings = ConfigReader().settings.llm.__class__.model_validate({
        "enabled": True,
        "endpoint": "http://127.0.0.1:8000/v1",
        "model_id": "shared-llm",
        "model_revision": "unverified",
        "max_input_characters": 2048,
        "max_context_tokens": 8192,
        "max_output_tokens": 512,
        "timeout_seconds": 1,
        "max_concurrency": 1,
        "max_attempts": 1,
        "retry_backoff_seconds": 0,
        "circuit_failures": 1,
        "circuit_reset_seconds": 10,
        "temperature": 0,
        "thinking_mode": "runtime_default",
    })
    config = SimpleNamespace(
        environment="development",
        settings=SimpleNamespace(llm=settings),
    )
    provider = LocalLlmProvider(
        config, SimpleNamespace(resolve_reference=lambda ref: None),
        transport=httpx.MockTransport(handler),
    )
    evaluator = CriterionEvaluationService(provider)

    async def run():
        try:
            return await probe._run_cases(evaluator)
        finally:
            await provider.aclose()

    result = asyncio.run(run())
    assert len(calls) == 1
    assert calls[0].url.path == "/v1/chat/completions"
    assert result["requests_attempted"] == 1
    assert result["requests_not_attempted"] == 2
    assert result["stopped_after_circuit_open"] is True
    assert result["results"][0]["error_code"] == "LLM_CIRCUIT_OPEN"
    assert result["results"][0]["failure_kind"] == expected
    summary = json.dumps(result)
    assert "fake-upstream-body" not in summary
    assert "fake-transport-detail" not in summary


def test_dry_run_single_domain_never_uses_network(capsys):
    assert probe.main(["--domain", "media"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "DRY_RUN_NO_NETWORK"
    assert report["requests_planned"] == 1
    assert report["criteria"] == ["media_message_clarity"]


def test_only_selected_domain_is_invoked():
    seen = []

    class Evaluator:
        async def evaluate_criterion_async(self, *, criterion, **kwargs):
            seen.append(criterion.criterion_code)
            raise LlmProviderError("LLM_CIRCUIT_OPEN", failure_kind="HTTP_503")

    report = asyncio.run(probe._run_cases(Evaluator(), domain="media"))
    assert seen == ["media_message_clarity"]
    assert report["requests_planned"] == report["requests_attempted"] == 1
    assert report["requests_not_attempted"] == 0
    assert report["results"][0]["failure_kind"] == "HTTP_503"



def test_no_thinking_dry_run_selects_single_media_domain(capsys):
    assert probe.main(["--disable-thinking", "--domain", "media"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "DRY_RUN_NO_NETWORK"
    assert report["requests_planned"] == 1
    assert report["thinking_mode_requested"] == "disabled"


def test_no_thinking_requires_single_domain_to_avoid_multiple_live_calls(capsys):
    with pytest.raises(SystemExit) as err:
        probe.main(["--execute-live", "--disable-thinking"])
    assert err.value.code == 2
    assert "requires --domain" in capsys.readouterr().err


def test_no_thinking_opt_in_is_forwarded_without_network(monkeypatch, capsys):
    observed = []

    async def simulate(*, domain=None, disable_thinking=False,
                       diagnostics=False, max_output_tokens=512):
        observed.append((domain, disable_thinking))
        return {
            "status": "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS",
            "thinking_mode_requested": "disabled",
        }

    monkeypatch.setattr(probe, "_run_live", simulate)
    assert probe.main([
        "--execute-live", "--domain", "media", "--disable-thinking",
    ]) == 0
    assert observed == [("media", True)]
    assert "disabled" in capsys.readouterr().out



def test_diagnostics_dry_run_selects_one_domain_and_no_network(capsys, monkeypatch):
    async def forbidden():
        pytest.fail("dry-run must not scrape metrics or send inference")
    monkeypatch.setattr(probe, "read_metrics", forbidden)
    report_code = probe.main([
        "--domain", "media", "--disable-thinking", "--diagnostics",
        "--max-output-tokens", "256",
    ])
    report = json.loads(capsys.readouterr().out)
    assert report_code == 0
    assert report["status"] == "DRY_RUN_NO_NETWORK"
    assert report["requests_planned"] == 1
    assert report["max_output_tokens"] == 256
    assert report["diagnostics_requested"] is True


@pytest.mark.parametrize("args,expected", [
    (["--diagnostics"], "--diagnostics requires --domain"),
    (["--max-output-tokens", "256", "--domain", "media"],
     "reduced --max-output-tokens requires --diagnostics"),
    (["--max-output-tokens", "4096", "--diagnostics", "--domain", "media"],
     "invalid choice"),
])
def test_diagnostic_scope_guards_are_fail_closed(capsys, args, expected):
    with pytest.raises(SystemExit) as err:
        probe.main(["--execute-live", *args])
    assert err.value.code == 2
    assert expected in capsys.readouterr().err


def test_direct_live_call_cannot_bypass_single_domain_guard():
    with pytest.raises(ValueError, match="STAGE11_DIAGNOSTICS_SCOPE_INVALID"):
        asyncio.run(probe._run_live(diagnostics=True))
    with pytest.raises(ValueError, match="STAGE11_DIAGNOSTICS_SCOPE_INVALID"):
        asyncio.run(probe._run_live(domain="media", max_output_tokens=256))
