"""Offline tests of the Stage11 loopback-only, one-shot synthetic inference probe."""
from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest

from scripts.verification.stage11_synthetic_inference_smoke import (
    _extract_completion, _query_one_model, _safe_json, _single_model, main,
    run_smoke,
)


def _models(name="internal/opaque-private-model-id"):
    return json.dumps({"data": [{"id": name}]}).encode()


def _completion(name="internal/opaque-private-model-id", content='{"ack":"ok"}'):
    return json.dumps({"model": name, "choices": [{
        "finish_reason": "stop", "message": {"role": "assistant", "content": content},
    }], "usage": {"prompt_tokens": 24, "completion_tokens": 9, "total_tokens": 33}}).encode()


def _fake_response(*, status=200, body=b"{}"):
    result = Mock(status=status)
    result.read.side_effect = lambda limit: body[:limit]
    return result


def _connections(*, first=None, second=None):
    first = first or _fake_response(body=_models())
    second = second or _fake_response(body=_completion())
    a, b = Mock(), Mock()
    a.getresponse.return_value = first
    b.getresponse.return_value = second
    return a, b


def test_one_synthetic_structured_post_and_bounded_metadata_get():
    a,b = _connections()
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as conn:
        result = run_smoke(port=8000)
    assert result["status"] == "PASS_SYNTHETIC_STRUCTURED_SMOKE"
    assert result["schema_valid"] is True
    assert result["usage_tokens"]["completion_tokens"] == 9
    assert "opaque-private" not in json.dumps(result)
    assert conn.call_args_list[0].args == ("127.0.0.1",)
    assert conn.call_args_list[0].kwargs == {"port": 8000, "timeout": 4}
    assert conn.call_args_list[1].kwargs == {"port": 8000, "timeout": 40}
    assert a.request.call_args.args == ("GET", "/v1/models")
    assert b.request.call_args.args[:2] == ("POST", "/v1/chat/completions")
    payload = json.loads(b.request.call_args.kwargs["body"])
    assert payload["model"] == "internal/opaque-private-model-id"
    assert payload["max_tokens"] == 64 and payload["temperature"] == 0
    assert payload["stream"] is False
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["messages"][-1]["content"].startswith("این فقط آزمون ساختگی")
    assert "tools" not in payload
    a.close.assert_called_once()
    b.close.assert_called_once()


@pytest.mark.parametrize("raw", [
    b"", b"{}", b"[]", b'{"data":[]}', b'{"data":[{},{}]}',
    b'{"data":[{}]}', b'{"data":[{"id":""}]}',
    b'{"data":[{"id":"a"}],"data":[]}', b'{"data":[{"id":"a\\nb"}]}',
    b'X' * 16385,
])
def test_model_id_fail_closed(raw):
    with pytest.raises((ValueError, UnicodeError)):
        _single_model(_safe_json(raw, limit=16384))


@pytest.mark.parametrize("invalid", [0, -1, 65536, "8000", True])
def test_invalid_port_causes_no_network(invalid):
    with patch("http.client.HTTPConnection") as client:
        with pytest.raises(ValueError):
            run_smoke(port=invalid)
        client.assert_not_called()


def test_non200_metadata_never_posts():
    a,b = _connections(first=_fake_response(status=401))
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as client:
        result = run_smoke(port=8000)
    assert result["status"] == "MODEL_METADATA_HTTP_REJECTED"
    assert client.call_count == 1
    a.getresponse.return_value.read.assert_not_called()


def test_many_models_never_posts():
    a,b = _connections(first=_fake_response(body=json.dumps({"data":[{"id":"one"},{"id":"two"}]}).encode()))
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as client:
        result = run_smoke(port=8000)
    assert result["status"] == "MODEL_METADATA_UNVERIFIED"
    assert client.call_count == 1


@pytest.mark.parametrize("status", [400, 401, 429, 503])
def test_non200_generation_only_one_post_and_no_raw_error(status):
    a,b = _connections(second=_fake_response(status=status, body=b'{"error":{"message":"VERY_SECRET"}}'))
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as client:
        result = run_smoke(port=8000)
    assert result["status"] == "INFERENCE_HTTP_REJECTED"
    assert result["http_status"] == status
    assert "VERY_SECRET" not in json.dumps(result)
    assert client.call_count == 2
    b.getresponse.return_value.read.assert_not_called()


@pytest.mark.parametrize("content", ["hello", "{}", '{"ack":"bad"}', '{"ack":"ok","other":1}', '{"ack":"ok","ack":"ok"}'])
def test_reject_non_schema_generation_without_exposing_text(content):
    a,b = _connections(second=_fake_response(body=_completion(content=content)))
    with patch("http.client.HTTPConnection", side_effect=[a,b]):
        result = run_smoke(port=8000)
    assert result["status"] == "INFERENCE_SCHEMA_UNVERIFIED"
    assert content not in json.dumps(result)


def test_reject_model_mismatch_and_length_finish_reason():
    bad = json.loads(_completion())
    bad["model"] = "unexpected/private"
    with pytest.raises(ValueError):
        _extract_completion(bad, expected_model="internal/opaque-private-model-id")
    bad["model"] = "internal/opaque-private-model-id"
    bad["choices"][0]["finish_reason"] = "length"
    with pytest.raises(ValueError):
        _extract_completion(bad, expected_model="internal/opaque-private-model-id")


def test_reject_oversized_response_no_text_leak():
    a,b = _connections(second=_fake_response(body=b"Z"*32769))
    with patch("http.client.HTTPConnection", side_effect=[a,b]):
        result = run_smoke(port=8000)
    assert result["status"] == "INFERENCE_INVALID_RESPONSE"


def test_dry_run_never_creates_connection(capsys):
    with patch("http.client.HTTPConnection") as client:
        assert main(["--dry-run"]) == 0
    client.assert_not_called()
    result=json.loads(capsys.readouterr().out)
    assert result["status"] == "DRY_RUN_NO_REQUESTS"


def test_cli_validation_before_network():
    with patch("http.client.HTTPConnection") as client, pytest.raises(SystemExit) as err:
        main(["--port", "0"])
    client.assert_not_called()
    assert err.value.code == 2


def test_synthetic_payload_no_private_text_and_no_tool_use():
    a,b=_connections()
    with patch("http.client.HTTPConnection", side_effect=[a,b]):
        run_smoke(port=8000)
    request=json.loads(b.request.call_args.kwargs["body"])
    assert len(json.dumps(request)) < 1500
    assert "JSON" in request["messages"][0]["content"]
    assert "ساختگی" in request["messages"][1]["content"]
    assert "Authorization" not in b.request.call_args.kwargs["headers"]


def test_socket_timeout_never_retries_or_leaks():
    a,b=_connections()
    b.getresponse.side_effect=TimeoutError("VERY_SECRET_NETWORK_MESSAGE")
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as conn:
        result=run_smoke(port=8000)
    assert result["status"] == "INFERENCE_TRANSPORT_OR_TIMEOUT"
    assert "VERY_SECRET" not in json.dumps(result)
    assert conn.call_count==2


def test_model_endpoint_redirect_never_posts():
    a,b = _connections(first=_fake_response(status=302))
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as conn:
        result=run_smoke(port=8000)
    assert result["status"] == "MODEL_METADATA_HTTP_REJECTED"
    assert conn.call_count==1


def test_json_nonfinite_and_duplicate_fields_fail_closed():
    for bad in (b'{"x":NaN}', b'{"x":2,"x":3}', b'{"x":Infinity}', b'{"x":-Infinity}'):
        with pytest.raises(ValueError):
            _safe_json(bad, limit=100)
