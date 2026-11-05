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


def test_compact_guidance_preserves_actual_criterion_rubric_fields():
    from scripts.verification.stage11_vllm_diagnostics import (
        compact_criterion_instructions,
    )
    from src.infrastructure.providers.llm.structured_response import CriterionInference

    class CapturingProvider:
        instructions = None

        async def evaluate_async(self, **kwargs):
            self.instructions = kwargs["instructions"]
            return CriterionInference(
                criterion_code=kwargs["criterion_code"],
                status="not_assessed", score=None,
                reason="Insufficient evidence", strengths=[],
                weaknesses=[], recommendations=[], evidence=[],
            )

    case, rubric, checksum = probe._load_selected_rubrics()[1]
    provider = CapturingProvider()
    asyncio.run(CriterionEvaluationService(provider).evaluate_criterion_async(
        criterion=rubric, original_text=case.original_text,
        rubric_checksum=checksum,
    ))
    original = json.loads(provider.instructions)
    variant = json.loads(compact_criterion_instructions(provider.instructions))
    assert set(original) == set(variant)
    assert {
        key: value for key, value in original.items() if key != "response_guidance"
    } == {
        key: value for key, value in variant.items() if key != "response_guidance"
    }
    assert "required JSON field" in variant["response_guidance"]
    assert "evidence quotes and offsets" in variant["response_guidance"]
    assert "Do not change score, status" in variant["response_guidance"]
    assert len(compact_criterion_instructions(provider.instructions)) <= 10000
    assert len(CriterionInference.model_fields) == 8


@pytest.mark.parametrize("invalid", [
    "not json", "[]", "{}", '{"response_guidance":"hi"}',
    '{"response_guidance":"first","response_guidance":"second"}',
    "x" * 10001,
])
def test_compact_guidance_rejects_untrusted_or_missing_contract(invalid):
    from scripts.verification.stage11_vllm_diagnostics import (
        compact_criterion_instructions,
    )
    with pytest.raises(LlmProviderError, match="LLM_INPUT_REJECTED"):
        compact_criterion_instructions(invalid)


def test_compact_provider_only_rewrites_instruction_field(monkeypatch):
    from scripts.verification.stage11_vllm_diagnostics import (
        CompactResponseDiagnosticLocalLlmProvider,
    )

    captured = {}

    async def fake_provider_evaluate(self, **kwargs):
        captured.update(kwargs)
        return "synthetic-ok"

    monkeypatch.setattr(LocalLlmProvider, "evaluate_async", fake_provider_evaluate)
    case, rubric, checksum = probe._load_selected_rubrics()[1]
    raw = json.dumps({
        "criterion_code": rubric.criterion_code,
        "operational_definition": rubric.operational_definition,
        "evaluation_instructions": rubric.evaluation_instructions,
        "evidence_requirements": rubric.evidence_requirements,
        "applicability_rules": rubric.applicability_rules,
        "score_anchors": rubric.scoring_anchors,
        "response_guidance": "Preserve source evidence",
    }, ensure_ascii=False)
    provider = object.__new__(CompactResponseDiagnosticLocalLlmProvider)
    output = asyncio.run(provider.evaluate_async(
        source_text=case.original_text, criterion_code=rubric.criterion_code,
        instructions=raw, rubric_checksum=checksum,
    ))
    assert output == "synthetic-ok"
    assert captured["source_text"] == case.original_text
    assert captured["criterion_code"] == rubric.criterion_code
    assert captured["rubric_checksum"] == checksum
    assert json.loads(captured["instructions"])["score_anchors"] == rubric.scoring_anchors
    assert json.loads(captured["instructions"])["response_guidance"] != "Preserve source evidence"


def test_compact_dry_run_has_zero_network_calls_and_fixed_scope(capsys, monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail("compact dry-run must not touch the model")
    monkeypatch.setattr(probe, "_run_live", forbidden)
    assert probe.main([
        "--compact-response", "--domain", "media", "--disable-thinking",
        "--diagnostics", "--max-output-tokens", "512",
    ]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "DRY_RUN_NO_NETWORK"
    assert output["requests_planned"] == 1
    assert output["prompt_variant"] == "compact_response_candidate_v1"


@pytest.mark.parametrize("args", [
    ["--compact-response"],
    ["--compact-response", "--domain", "media"],
    ["--compact-response", "--domain", "media", "--diagnostics"],
    ["--compact-response", "--diagnostics", "--disable-thinking"],
])
def test_compact_live_and_offline_modes_require_safe_scope(capsys, args):
    with pytest.raises(SystemExit) as exc:
        probe.main(["--execute-live", *args])
    assert exc.value.code == 2
    assert "requires --domain --diagnostics --disable-thinking" in capsys.readouterr().err


def test_compact_live_mode_selects_diagnostic_provider_without_network(monkeypatch):
    from scripts.verification.stage11_vllm_diagnostics import (
        CompactResponseDiagnosticLocalLlmProvider,
    )

    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    for key in (
        "TES_STAGE11_SETTINGS_FILE", "TES_STAGE05_DATABASE_URL",
        "TES_STAGE11_PROCESS_E2E",
    ):
        monkeypatch.delenv(key, raising=False)

    async def no_metrics():
        return None

    async def fake_cases(evaluator, *, domain):
        assert domain == "media"
        assert isinstance(
            evaluator._provider, CompactResponseDiagnosticLocalLlmProvider,
        )
        return {"status": "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS"}

    monkeypatch.setattr(probe, "read_metrics", no_metrics)
    monkeypatch.setattr(probe, "_run_cases", fake_cases)
    report = asyncio.run(probe._run_live(
        domain="media", disable_thinking=True, diagnostics=True,
        max_output_tokens=512, compact_response=True,
    ))
    assert report["prompt_variant"] == "compact_response_candidate_v1"
    assert report["diagnostics"]["max_output_tokens"] == 512


def test_compact_direct_api_call_rejects_unsafely_broad_run():
    with pytest.raises(ValueError, match="STAGE11_DIAGNOSTICS_SCOPE_INVALID"):
        asyncio.run(probe._run_live(compact_response=True))


def test_indexed_evidence_anchors_match_exact_original_unicode_offsets():
    from scripts.verification.stage11_vllm_diagnostics import (
        indexed_evidence_instructions,
    )

    case, rubric, checksum = probe._load_selected_rubrics()[1]
    class Capture:
        instructions = ""
        async def evaluate_async(self, **kwargs):
            self.instructions = kwargs["instructions"]
            from src.infrastructure.providers.llm.structured_response import (
                CriterionInference,
            )
            return CriterionInference(
                criterion_code=kwargs["criterion_code"],
                status="not_assessed", score=None, reason="No evidence",
                strengths=[], weaknesses=[], recommendations=[], evidence=[],
            )

    from src.core.services.text_evaluation.criterion_evaluation_service import (
        CriterionEvaluationService,
    )
    capture = Capture()
    asyncio.run(CriterionEvaluationService(capture).evaluate_criterion_async(
        criterion=rubric, original_text=case.original_text,
        rubric_checksum=checksum,
    ))
    raw = json.loads(capture.instructions)
    guided = json.loads(indexed_evidence_instructions(
        capture.instructions, case.original_text,
    ))
    assert {
        k: v for k, v in guided.items() if k != "response_guidance"
    } == {
        k: v for k, v in raw.items() if k != "response_guidance"
    }
    import re
    items = re.search(
        r"Pre-indexed evidence choices: (\[.*\])$",
        guided["response_guidance"],
    )
    assert items is not None
    anchors = json.loads(items.group(1))
    assert len(anchors) == 3
    assert all(
        case.original_text[row["start_offset"]:row["end_offset"]] == row["quote"]
        for row in anchors
    )
    assert any(row["start_offset"] > 0 for row in anchors)
    assert any("\u200c" in row["quote"] for row in anchors)
    assert all(16 <= len(row["quote"]) <= 56 for row in anchors)
    assert set(anchors[0]) == {"quote", "start_offset", "end_offset"}
    assert len(indexed_evidence_instructions(
        capture.instructions, case.original_text,
    )) <= 10000


@pytest.mark.parametrize("source", [
    "", "short", "x" * 2049, "x" * 40, "a" * 30 + "\\n" + "b" * 30,
])
def test_indexed_evidence_rejects_unbounded_or_unsupported_source(source):
    from scripts.verification.stage11_vllm_diagnostics import (
        indexed_evidence_instructions,
    )
    with pytest.raises(LlmProviderError, match="LLM_INPUT_REJECTED"):
        indexed_evidence_instructions(
            json.dumps({
                "criterion_code": "media_message_clarity",
                "operational_definition": "Synthetic",
                "evaluation_instructions": "Synthetic",
                "evidence_requirements": "Synthetic",
                "applicability_rules": "Synthetic",
                "score_anchors": {},
                "response_guidance": "Preserve evidence",
            }),
            source,
        )


def test_indexed_evidence_dry_run_requires_no_network(monkeypatch, capsys):
    async def forbidden(**kwargs):
        pytest.fail("No model request permitted during dry-run")

    monkeypatch.setattr(probe, "_run_live", forbidden)
    args = [
        "--domain", "media", "--compact-response", "--indexed-evidence",
        "--disable-thinking", "--diagnostics", "--max-output-tokens", "512",
    ]
    assert probe.main(args) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "DRY_RUN_NO_NETWORK"
    assert output["prompt_variant"] == "indexed_evidence_candidate_v1"
    assert output["requests_planned"] == 1


@pytest.mark.parametrize("args", [
    ["--indexed-evidence"],
    ["--indexed-evidence", "--domain", "media", "--diagnostics", "--disable-thinking"],
    ["--indexed-evidence", "--compact-response", "--domain", "speech", "--diagnostics", "--disable-thinking"],
])
def test_indexed_evidence_flag_rejects_broader_or_unsafe_scope(args, capsys):
    with pytest.raises(SystemExit) as e:
        probe.main(["--execute-live", *args])
    assert e.value.code == 2
    assert "--indexed-evidence requires" in capsys.readouterr().err


def test_indexed_evidence_provider_selection_and_no_network(monkeypatch):
    from scripts.verification.stage11_vllm_diagnostics import (
        IndexedEvidenceDiagnosticLocalLlmProvider,
    )
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    for key in (
        "TES_STAGE11_SETTINGS_FILE", "TES_STAGE05_DATABASE_URL",
        "TES_STAGE11_PROCESS_E2E",
    ):
        monkeypatch.delenv(key, raising=False)

    async def no_metrics():
        return None

    async def fake_run_cases(evaluator, *, domain):
        assert domain == "media"
        assert isinstance(
            evaluator._provider, IndexedEvidenceDiagnosticLocalLlmProvider
        )
        return {"status": "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS"}

    monkeypatch.setattr(probe, "read_metrics", no_metrics)
    monkeypatch.setattr(probe, "_run_cases", fake_run_cases)
    outcome = asyncio.run(probe._run_live(
        domain="media", compact_response=True, indexed_evidence=True,
        disable_thinking=True, diagnostics=True, max_output_tokens=512,
    ))
    assert outcome["prompt_variant"] == "indexed_evidence_candidate_v1"
    assert outcome["diagnostics"]["response"]["finish_reason"] == "UNAVAILABLE"


@pytest.mark.parametrize("domain", ["speech", "media", "research"])
def test_single_domain_contract_success_does_not_claim_three_domain(domain):
    class FakeEvaluator:
        async def evaluate_criterion_async(self, *, criterion, **kwargs):
            return CriterionAssessment(
                criterion_code=criterion.criterion_code,
                status="assessed", score=3, reason="Synthetic",
                reason_code=None,
                evidence=((kwargs["original_text"][:7], 0, 7),),
            )

    result = asyncio.run(probe._run_cases(FakeEvaluator(), domain=domain))
    assert result["status"] == "REAL_MODEL_SINGLE_DOMAIN_CONTRACT_PASS"
    assert result["scope"] == "single_domain"
    assert result["requests_planned"] == result["requests_attempted"] == 1
    assert result["results"][0]["domain"] == domain


def test_single_domain_contract_failure_does_not_claim_three_domain():
    class FakeEvaluator:
        async def evaluate_criterion_async(self, **kwargs):
            raise LlmProviderError("LLM_SCHEMA_REJECTED")

    result = asyncio.run(probe._run_cases(FakeEvaluator(), domain="media"))
    assert result["status"] == "REAL_MODEL_SINGLE_DOMAIN_CONTRACT_FAILURE"
    assert result["scope"] == "single_domain"
    assert result["requests_attempted"] == 1


def test_single_domain_success_cli_exit_zero(monkeypatch, capsys):
    async def fake(*, domain, disable_thinking, diagnostics, max_output_tokens):
        assert domain == "speech"
        return {"status": "REAL_MODEL_SINGLE_DOMAIN_CONTRACT_PASS"}

    monkeypatch.setattr(probe, "_run_live", fake)
    assert probe.main(["--execute-live", "--domain", "speech"]) == 0
    assert "REAL_MODEL_SINGLE_DOMAIN_CONTRACT_PASS" in capsys.readouterr().out


@pytest.mark.parametrize("domain", ["speech", "media", "research"])
def test_quote_only_dry_run_accepts_one_selected_domain_without_gpu(domain, monkeypatch, capsys):
    async def forbidden(**kwargs):
        pytest.fail("No GPU access in dry-run")

    monkeypatch.setattr(probe, "_run_live", forbidden)
    assert probe.main([
        "--quote-only-evidence", "--compact-response",
        "--domain", domain, "--disable-thinking",
        "--diagnostics", "--max-output-tokens", "512",
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "DRY_RUN_NO_NETWORK"
    assert result["requests_planned"] == 1
    assert result["criteria"] == [
        {"speech": "speech_clarity",
         "media": "media_message_clarity",
         "research": "research_academic_writing"}[domain]
    ]
    assert result["prompt_variant"] == "quote_only_evidence_candidate_v1"
