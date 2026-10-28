"""All Stage07 transport contracts use in-process HTTPX MockTransport and synthetic data."""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from pydantic import ValidationError

from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.di.inject import resolve
from src.infrastructure.providers.llm.local_llm_provider import (
    LocalLlmProvider, LlmProviderError,
)
from src.infrastructure.providers.llm.structured_response import decode_criterion_response
from src.infrastructure.utils.config_reader import ConfigReader

SOURCE = "متن ساختگی با نشانه\u200cگذاری"
CODE = "speech_clarity"
FIXED = "a" * 64


def test_settings_and_di_disabled_by_default():
    bootstrap_di()
    instance = resolve(LocalLlmProvider)
    assert isinstance(instance, LocalLlmProvider)
    async def exercise():
        with pytest.raises(LlmProviderError, match="^LLM_NOT_CONFIGURED$"):
            await instance.evaluate_async(
                source_text=SOURCE, criterion_code=CODE, instructions="synthetic-only",
                rubric_checksum=FIXED,
            )
    asyncio.run(exercise())


def make_provider(handler, *, endpoint="http://127.0.0.1:18090/v1",
                  environment="development", overrides=None, secrets=None):
    settings = {
        "enabled": True, "endpoint": endpoint, "model_id": "approved-local-model",
        "model_revision": "synthetic-rev-sha256",
        "max_input_characters": 2048, "max_context_tokens": 8192,
        "max_output_tokens": 1024, "timeout_seconds": 0.5,
        "max_concurrency": 2, "max_attempts": 2,
        "retry_backoff_seconds": 0, "circuit_failures": 5,
        "circuit_reset_seconds": 0.01, "temperature": 0,
        "thinking_mode": "runtime_default",
    }
    settings.update(overrides or {})
    llm = ConfigReader().settings.llm.__class__.model_validate(settings)
    fake_config = SimpleNamespace(environment=environment, settings=SimpleNamespace(llm=llm))
    fake_secrets = SimpleNamespace(resolve_reference=lambda ref: secrets[ref])
    return LocalLlmProvider(fake_config, fake_secrets, transport=httpx.MockTransport(handler))


def expected_result(*, assessed=True):
    evidence = [{
        "source_kind": "original_submission",
        "quote": SOURCE[0:4], "start_offset": 0, "end_offset": 4,
    }] if assessed else []
    return {
        "criterion_code": CODE, "status": "assessed" if assessed else "not_assessed",
        "score": 4 if assessed else None,
        "reason": "Synthetic, evidence-backed" if assessed else "Insufficient evidence",
        "strengths": [], "weaknesses": [], "recommendations": [],
        "evidence": evidence,
    }


def answer(result=None, *, finish="stop", model="approved-local-model"):
    return httpx.Response(200, json={
        "model": model, "choices": [{
            "finish_reason": finish,
            "message": {"content": json.dumps(result if result is not None else expected_result(),
                                              ensure_ascii=False)},
        }],
    })


def invoke(provider):
    return provider.evaluate_async(
        source_text=SOURCE, criterion_code=CODE,
        instructions="Assess synthetic clarity", rubric_checksum=FIXED,
    )


def test_success_structured_output_pooled_client_model_metadata_and_health():
    requests = []
    def handler(req):
        requests.append(req)
        if req.url.path == "/health":
            return httpx.Response(200)
        if req.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "approved-local-model"}]})
        assert req.url.path == "/v1/chat/completions"
        payload = json.loads(req.content)
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["strict"] is True
        assert payload["stream"] is False and "tools" not in payload
        assert payload["model"] == "approved-local-model"
        assert "thinking" not in payload
        assert SOURCE in payload["messages"][1]["content"]
        return answer()
    provider = make_provider(handler)
    async def run():
        assert (await provider.model_metadata_async())["revision_verified"] == "false"
        assert await provider.health_async()
        client = provider._client
        a, b = await invoke(provider), await invoke(provider)
        assert a.score == b.score == 4
        assert provider._client is client
        await provider.aclose()
        with pytest.raises(LlmProviderError, match="^LLM_PROVIDER_CLOSED$"):
            await invoke(provider)
    asyncio.run(run())
    assert len(requests) == 4


def test_not_assessed_abstains_without_score_or_evidence():
    provider = make_provider(lambda _: answer(expected_result(assessed=False)))
    async def run():
        output = await invoke(provider)
        assert output.status == "not_assessed"
        assert output.score is None and not output.evidence
        await provider.aclose()
    asyncio.run(run())


@pytest.mark.parametrize("mutate", [
    lambda d: d.pop("reason"),
    lambda d: d.update(score=True),
    lambda d: d.update(score=6),
    lambda d: d.update(status="unknown"),
    lambda d: d.update(final_score=83),
    lambda d: d.update(criterion_code="media_tone"),
    lambda d: d["evidence"][0].update(quote="fabricated"),
    lambda d: d["evidence"][0].update(start_offset=999),
    lambda d: d["evidence"][0].update(end_offset=0),
    lambda d: d.update(status="not_assessed", score=None),
])
def test_invalid_output_never_produces_a_score(mutate):
    data = expected_result()
    mutate(data)
    provider = make_provider(lambda _: answer(data))
    async def run():
        with pytest.raises(LlmProviderError, match="^LLM_SCHEMA_REJECTED$") as err:
            await invoke(provider)
        assert SOURCE not in str(err.value)
        await provider.aclose()
    asyncio.run(run())


@pytest.mark.parametrize("raw", [
    '{"criterion_code":"speech_clarity","criterion_code":"speech_clarity"}',
    '{"score":NaN}',
    '{"score":Infinity}',
    "not-json",
    "[]" ,
])
def test_invalid_json_strict_decoder_rejects(raw):
    with pytest.raises((ValueError, ValidationError)):
        decode_criterion_response(raw, expected_code=CODE,
                                  source_text=SOURCE, max_response_bytes=4096)


@pytest.mark.parametrize("endpoint,environment", [
    ("https://api.external.example:443/v1", "production"),
    ("https://8.8.8.8:443/v1", "production"),
    ("http://10.2.3.4:8000/v1", "production"),
    ("http://127.0.0.1:8080/v1", "production"),
    ("https://10.2.3.4:443/v1?forward=elsewhere", "production"),
    ("https://10.2.3.4:443/v1/../../external", "production"),
    ("https://user:secret@10.2.3.4:443/v1", "production"),
])
def test_external_and_ambiguous_endpoints_denied(endpoint, environment):
    calls = []
    provider = make_provider(lambda req: calls.append(req) or answer(),
                             endpoint=endpoint, environment=environment)
    async def run():
        with pytest.raises(LlmProviderError, match="^LLM_ENDPOINT_DENIED$"):
            await invoke(provider)
        await provider.aclose()
    asyncio.run(run())
    assert calls == []


def test_staging_needs_secret_reference_and_rejects_leak():
    calls = []
    provider = make_provider(lambda req: calls.append(req) or answer(),
                             environment="staging", endpoint="https://10.1.2.3:443/v1",
                             overrides={"credential_ref": None})
    async def run():
        with pytest.raises(LlmProviderError, match="LLM_ENDPOINT_DENIED"):
            await invoke(provider)
        await provider.aclose()
    asyncio.run(run())
    assert not calls


def test_staging_auth_header_comes_from_secret_reference_and_is_never_logged():
    seen = []
    provider = make_provider(lambda request: seen.append(request) or answer(),
                             environment="staging", endpoint="https://10.1.2.3:443/v1",
                             overrides={"credential_ref": "env://TES_STAGE07_SYNTHETIC_TOKEN"},
                             secrets={"env://TES_STAGE07_SYNTHETIC_TOKEN": "synthetic-secret-not-for-logs"})
    async def run():
        assert (await invoke(provider)).score == 4
        await provider.aclose()
    asyncio.run(run())
    assert seen[0].headers["authorization"] == "Bearer synthetic-secret-not-for-logs"


@pytest.mark.parametrize("code", [400, 401, 403, 404, 422])
def test_4xx_no_retry_or_raw_response_leak(code):
    hits = []
    provider = make_provider(lambda _: hits.append(1) or
                             httpx.Response(code, text="sensitive-prompt-and-token"))
    async def run():
        with pytest.raises(LlmProviderError, match="^LLM_HTTP_REJECTED$") as err:
            await invoke(provider)
        assert "sensitive" not in str(err.value)
        await provider.aclose()
    asyncio.run(run())
    assert len(hits) == 1


@pytest.mark.parametrize("code", [429, 500, 502, 503, 504])
def test_transient_5xx_backoff_then_success(code):
    hits = []
    def handler(_):
        hits.append(1)
        return httpx.Response(code, text="private-error") if len(hits) == 1 else answer()
    provider = make_provider(handler)
    async def run():
        assert (await invoke(provider)).score == 4
        await provider.aclose()
    asyncio.run(run())
    assert hits == [1, 1]


def test_retry_exhaustion_and_circuit_open():
    provider = make_provider(lambda _: httpx.Response(503, text="private-server-stack"),
                             overrides={"circuit_failures": 2, "max_attempts": 2})
    async def run():
        with pytest.raises(LlmProviderError, match="^LLM_CIRCUIT_OPEN$"):
            await invoke(provider)
        await provider.aclose()
    asyncio.run(run())


def test_network_timeout_and_cancellation_propagate_safely():
    async def timed_out(_):
        raise httpx.ReadTimeout("private-connect-diagnostics")
    provider = make_provider(timed_out, overrides={"max_attempts": 1})
    async def run():
        with pytest.raises(LlmProviderError, match="^LLM_RETRY_EXHAUSTED$") as err:
            await invoke(provider)
        assert "private" not in str(err.value)
        await provider.aclose()
    asyncio.run(run())

    async def cancelled(_):
        raise asyncio.CancelledError()
    provider2 = make_provider(cancelled)
    async def run_cancel():
        with pytest.raises(asyncio.CancelledError):
            await invoke(provider2)
        await provider2.aclose()
    asyncio.run(run_cancel())


@pytest.mark.parametrize("response", [
    httpx.Response(302, headers={"location": "https://external.example/"}),
    httpx.Response(200, text="{bad-json"),
    httpx.Response(200, json={"model": "other", "choices": []}),
    httpx.Response(200, json={"model": "approved-local-model", "choices": []}),
    answer(finish="length"),
])
def test_incompatible_responses_fail_closed(response):
    provider = make_provider(lambda _: response)
    async def run():
        with pytest.raises(LlmProviderError):
            await invoke(provider)
        await provider.aclose()
    asyncio.run(run())


def test_unavailable_model_and_input_too_long_and_max_token_guard():
    provider = make_provider(lambda _: httpx.Response(200, json={"data": []}))
    async def run():
        with pytest.raises(LlmProviderError, match="^LLM_MODEL_UNAVAILABLE$"):
            await provider.model_metadata_async()
        with pytest.raises(LlmProviderError, match="^LLM_INPUT_REJECTED$"):
            await provider.evaluate_async(
                source_text="x" * 3000, criterion_code=CODE,
                instructions="synthetic", rubric_checksum=FIXED,
            )
        await provider.aclose()
    asyncio.run(run())
    provider2 = make_provider(lambda _: answer(), overrides={
        "max_context_tokens": 100, "max_output_tokens": 101,
    })
    async def run2():
        with pytest.raises(LlmProviderError, match="^LLM_CONFIG_INVALID$"):
            await invoke(provider2)
    asyncio.run(run2())
