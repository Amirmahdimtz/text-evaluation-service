"""Offline-only tests for Stage11 Persian rubric evaluation harness."""
from __future__ import annotations

import asyncio
import json

import pytest

from scripts.verification import stage11_persian_domain_smoke as smoke
from src.infrastructure.providers.llm.local_llm_provider import LlmProviderError
from src.infrastructure.providers.llm.structured_response import CriterionInference


class SyntheticProvider:
    def __init__(self):
        self.calls = 0
        self.closed = False

    def declared_configuration(self):
        return {
            "model_id": "synthetic-no-network",
            "model_revision": "synthetic-unverified",
            "revision_verified": False,
            "max_input_characters": 2048,
        }

    async def evaluate_async(self, **kwargs):
        self.calls += 1
        source = kwargs["source_text"]
        quote = source[:6]
        return CriterionInference.model_validate({
            "criterion_code": kwargs["criterion_code"],
            "status": "assessed",
            "score": 4,
            "reason": "Synthetic fixture assessment",
            "strengths": ["Synthetic strength"],
            "weaknesses": ["Synthetic weakness"],
            "recommendations": ["Synthetic improvement"],
            "evidence": [{
                "source_kind": "original_submission",
                "quote": quote,
                "start_offset": 0,
                "end_offset": len(quote),
            }],
        })

    async def aclose(self):
        self.closed = True


@pytest.mark.parametrize("domain,requests", [
    ("speech", 6), ("media", 6), ("research", 5),
])
def test_real_engine_synthetic_samples_have_criterion_and_python_summary(domain, requests):
    fake = SyntheticProvider()
    bounded = smoke.BoundedProvider(fake, pause_seconds=0.0)
    result = asyncio.run(smoke._evaluate(domain, bounded))

    assert result["status"] == "PASS_SYNTHETIC_DOMAIN_EVALUATION"
    assert result["domain"] == domain
    assert len(result["criteria"]) == 6
    assert result["inference_requests_attempted"] == requests
    assert bounded.calls == requests == fake.calls
    assert fake.closed is True
    assert result["summary"]["official_score"] is False
    assert result["summary"]["provisional_score_0_100"] == "80"
    assert result["summary"]["needs_human_review"] is True
    assert result["summary"]["strengths"] == ["Synthetic strength"]
    assert result["summary"]["weaknesses"] == ["Synthetic weakness"]
    assert result["summary"]["recommendations"] == ["Synthetic improvement"]
    for criterion in result["criteria"]:
        if criterion["status"] == "assessed":
            assert criterion["score_0_5"] == 4
            for evidence in criterion["evidence"]:
                assert (result["source_text"][
                    evidence["start_offset"]:evidence["end_offset"]
                ] == evidence["quote"])
    assert "model_id" not in result
    if domain == "research":
        assert next(x for x in result["criteria"]
                    if x["code"] == "research_novelty")["status"] == "not_assessed"


def test_hard_budget_raises_before_seventh_post():
    fake = SyntheticProvider()
    bounded = smoke.BoundedProvider(fake, pause_seconds=0.0)

    async def run():
        source = smoke._EXAMPLES["speech"]
        for _ in range(6):
            await bounded.evaluate_async(
                source_text=source, criterion_code="speech_clarity",
            )
        with pytest.raises(LlmProviderError, match="^STAGE11_REQUEST_BUDGET_EXCEEDED$"):
            await bounded.evaluate_async(source_text=source, criterion_code="speech_clarity")
        await bounded.aclose()

    asyncio.run(run())
    assert bounded.calls == fake.calls == 6
    assert fake.closed


def test_dry_run_never_looks_up_model_or_connects(monkeypatch, capsys):
    def blocked(**kwargs):
        pytest.fail("Dry-run must not query a live endpoint")
    monkeypatch.setattr(smoke, "_query_one_model", blocked)
    assert smoke.main(["--domain", "speech"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "DRY_RUN_NO_NETWORK"
    assert output["max_inference_requests"] == 6
    assert output["max_concurrency"] == 1
    assert output["retries"] == 0


def test_declared_client_profile_is_safe_and_not_persistent(monkeypatch):
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    original = smoke.ConfigReader().settings.llm
    cfg = smoke._local_config("synthetic-model")
    llm = cfg.settings.llm
    assert not original.enabled
    assert llm.enabled
    assert llm.endpoint == "http://127.0.0.1:8000/v1"
    assert llm.max_concurrency == 1
    assert llm.max_attempts == 1
    assert llm.max_output_tokens == 640
    assert llm.model_revision == "unverified-existing-runtime"
    assert smoke.ConfigReader().settings.llm.enabled is False


def test_rejects_non_development_environment_or_invalid_model_id(monkeypatch):
    monkeypatch.setenv("TES_ENVIRONMENT", "production")
    with pytest.raises(ValueError, match="^STAGE11_DEV_ONLY$"):
        smoke._local_config("synthetic-model")
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    with pytest.raises(ValueError, match="^STAGE11_MODEL_ID_INCOMPATIBLE$"):
        smoke._local_config("../bad-model")


@pytest.mark.parametrize("category", [
    "HTTP_429", "HTTP_503", "REQUEST_TIMEOUT", "TRANSPORT_ERROR",
    "private-secret-detail",
])
def test_live_harness_failure_is_categorized_without_exposing_upstream_data(
    monkeypatch, capsys, category,
):
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    monkeypatch.setattr(
        smoke, "_query_one_model",
        lambda *, port: ("synthetic-test-only-model", None),
    )

    class FailingProvider:
        def __init__(self, *_args, **_kwargs):
            self.closed = False

        def declared_configuration(self):
            return {
                "model_id": "synthetic-test-only-model",
                "model_revision": "synthetic-unverified",
                "revision_verified": False,
                "max_input_characters": 2048,
            }

        async def evaluate_async(self, **_kwargs):
            raise LlmProviderError(
                "LLM_CIRCUIT_OPEN", failure_kind=category,
            )

        async def aclose(self):
            self.closed = True

    monkeypatch.setattr(smoke, "LocalLlmProvider", FailingProvider)
    result = smoke.main(["--domain", "speech", "--execute-approved"])
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert result == 1
    assert payload["status"] == "FAIL"
    assert payload["error_code"] == "LLM_CIRCUIT_OPEN"
    assert payload["failure_category"] == (
        category if category in smoke._SAFE_TRANSIENT_KINDS
        else "UNCLASSIFIED"
    )
    assert payload["inference_requests_attempted"] == 1
    assert payload["retries"] == 0
    assert "private-secret-detail" not in output
