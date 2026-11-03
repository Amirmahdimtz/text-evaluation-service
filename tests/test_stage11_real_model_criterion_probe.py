"""Offline safety and reporting tests; never contact the shared GPU."""
from __future__ import annotations

import asyncio
import json

import pytest

from src.core.services.text_evaluation.criterion_evaluation_service import (
    CriterionAssessment,
)
from src.infrastructure.providers.llm.local_llm_provider import LlmProviderError
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
        assert "ساختگی" in case.original_text or "فرضی" in case.original_text


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


def test_legitimate_abstention_is_not_an invented_score():
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
    async def simulate():
        return {"status": "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS"}
    monkeypatch.setattr(probe, "_run_live", simulate)
    assert probe.main(["--execute-live"]) == 0
    assert "REAL_MODEL_THREE_DOMAIN_CONTRACT_PASS" in capsys.readouterr().out
