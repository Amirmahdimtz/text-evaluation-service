"""Offline HTTP, schema, evidence and privacy checks for the real criterion contract."""
from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest

from scripts.verification.stage11_criterion_contract_smoke import (
    _CRITERION, _SOURCE, _validated_completion, main, make_request, run,
)
from src.infrastructure.providers.llm.structured_response import (
    CriterionInference, decode_criterion_response,
)

_MODEL = "private/internal-server-model"


def _valid_criterion(*, evidence=True):
    return {
        "criterion_code": "clarity", "status": "assessed", "score": 4,
        "reason": "متن کوتاه و روشن است.", "strengths": ["بیان ساده"],
        "weaknesses": [], "recommendations": ["مثال بیفزایید"],
        "evidence": [{"source_kind": "original_submission", "quote": _SOURCE,
                      "start_offset": 0, "end_offset": len(_SOURCE)}] if evidence else [],
    }


def _response_json(*, content=None, model=_MODEL, finish="stop"):
    if content is None:
        content = json.dumps(_valid_criterion(), ensure_ascii=False)
    return json.dumps({"model": model, "choices": [{"finish_reason": finish,
          "message": {"role": "assistant", "content": content}}],
          "usage": {"prompt_tokens": 150, "completion_tokens": 90, "total_tokens": 240}},
          ensure_ascii=False).encode()


def _reply(payload: bytes, status=200):
    r = Mock(status=status)
    r.read.side_effect = lambda limit: payload[:limit]
    return r


def _connections(*, model_json=None, completion=None):
    m = _reply(model_json if model_json is not None else json.dumps({"data": [{"id": _MODEL}]}).encode())
    c = _reply(completion if completion is not None else _response_json())
    a, b = Mock(), Mock()
    a.getresponse.return_value = m
    b.getresponse.return_value = c
    return a, b


def test_actual_pydantic_schema_and_assessment_validate():
    schema = make_request(_MODEL)["response_format"]["json_schema"]["schema"]
    assert schema == CriterionInference.model_json_schema()
    result = decode_criterion_response(json.dumps(_valid_criterion(), ensure_ascii=False),
                                       expected_code=_CRITERION, source_text=_SOURCE,
                                       max_response_bytes=16384)
    assert result.status == "assessed"
    assert result.evidence[0].quote == _SOURCE
    assert result.evidence[0].end_offset == len(_SOURCE)


def test_one_get_one_post_real_schema_and_private_redaction():
    a, b = _connections()
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as conn:
        result = run(port=8000)
    assert result["status"] == "PASS_SYNTHETIC_CRITERION_CONTRACT"
    assert result["criterion_schema_valid"] and result["grounded_evidence_valid"]
    assert result["usage_tokens"]["total_tokens"] == 240
    assert _MODEL not in json.dumps(result)
    assert _SOURCE not in json.dumps(result, ensure_ascii=False)
    assert conn.call_count == 2
    assert conn.call_args_list[0].args == ("127.0.0.1",)
    assert conn.call_args_list[1].args == ("127.0.0.1",)
    assert conn.call_args_list[0].kwargs == {"port":8000,"timeout":4}
    assert conn.call_args_list[1].kwargs == {"port":8000,"timeout":45}
    assert a.request.call_args.args == ("GET", "/v1/models")
    assert b.request.call_args.args[:2] == ("POST", "/v1/chat/completions")
    data = json.loads(b.request.call_args.kwargs["body"])
    assert data["model"] == _MODEL
    assert data["max_tokens"] == 320 and data["temperature"] == 0
    assert data["stream"] is False
    assert "tools" not in data
    assert "Authorization" not in b.request.call_args.kwargs["headers"]
    a.close.assert_called_once(); b.close.assert_called_once()


@pytest.mark.parametrize("wrong", ["quote", "offset", "score", "criterion", "extra"])
def test_strict_criterion_contract_rejects_invalid(wrong):
    body = _valid_criterion()
    if wrong == "quote": body["evidence"][0]["quote"] = "ساخته‌شده"
    if wrong == "offset": body["evidence"][0]["end_offset"] -= 1
    if wrong == "score": body["score"] = "4"
    if wrong == "criterion": body["criterion_code"] = "fluency"
    if wrong == "extra": body["unapproved_field"] = "x"
    with pytest.raises(ValueError):
        decode_criterion_response(json.dumps(body, ensure_ascii=False),
                                  expected_code=_CRITERION, source_text=_SOURCE,
                                  max_response_bytes=16384)


@pytest.mark.parametrize("invalid", [0,-1,65536,"8000",True])
def test_invalid_ports_never_connect(invalid):
    with pytest.raises(ValueError), patch("http.client.HTTPConnection") as http:
        run(port=invalid)
        http.assert_not_called()


def test_ambiguous_models_no_post():
    a,b = _connections(model_json=b'{"data":[{"id":"one"},{"id":"two"}]}')
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as http:
        result = run(port=8000)
    assert result["status"] == "MODEL_METADATA_UNVERIFIED"
    assert http.call_count == 1


def test_non200_metadata_no_post():
    a,b = _connections()
    a.getresponse.return_value = _reply(b'{"secret":"private"}', 401)
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as http:
        result=run(port=8000)
    assert result["status"] == "MODEL_METADATA_UNVERIFIED"
    assert http.call_count == 1


@pytest.mark.parametrize("status", [400,401,403,429,500,503])
def test_http_errors_not_retried_and_raw_body_hidden(status):
    a,b=_connections()
    b.getresponse.return_value=_reply(b'{"error":"SECRET_RAW_RESPONSE"}',status)
    with patch("http.client.HTTPConnection", side_effect=[a,b]) as http:
        result=run(port=8000)
    assert http.call_count == 2
    assert result["status"] == "INFERENCE_HTTP_REJECTED"
    assert result["http_status"] == status
    assert "SECRET" not in json.dumps(result)
    b.getresponse.return_value.read.assert_not_called()


@pytest.mark.parametrize("value", ["not json", "{}", "[]", '{"criterion_code":"clarity"}', '{"status":"assessed","status":"assessed"}'])
def test_invalid_json_or_partial_contract_fails_closed(value):
    a,b=_connections(completion=_response_json(content=value))
    with patch("http.client.HTTPConnection", side_effect=[a,b]):
        result=run(port=8000)
    assert result["status"] == "CRITERION_CONTRACT_UNVERIFIED"
    assert value not in json.dumps(result)


def test_abstention_is_valid_shape_but_not_a_grounded_assessment():
    body=_valid_criterion()
    body.update(status="not_assessed",score=None,evidence=[])
    a,b=_connections(completion=_response_json(content=json.dumps(body,ensure_ascii=False)))
    with patch("http.client.HTTPConnection",side_effect=[a,b]):
        result=run(port=8000)
    assert result["status"] == "CRITERION_CONTRACT_UNVERIFIED"


def test_model_mismatch_refused():
    with pytest.raises(ValueError):
        _validated_completion(json.loads(_response_json(model="another-model")), _MODEL)


def test_unfinished_generation_refused():
    with pytest.raises(ValueError):
        _validated_completion(json.loads(_response_json(finish="length")), _MODEL)


def test_timeout_is_not_retried():
    a,b=_connections()
    b.getresponse.side_effect=TimeoutError("SECRET")
    with patch("http.client.HTTPConnection",side_effect=[a,b]) as http:
        result=run(port=8000)
    assert result["status"] == "INFERENCE_TRANSPORT_OR_TIMEOUT"
    assert http.call_count==2
    assert "SECRET" not in json.dumps(result)


def test_dry_run_is_network_free(capsys):
    with patch("http.client.HTTPConnection") as http:
        assert main([])==0
        http.assert_not_called()
    result=json.loads(capsys.readouterr().out)
    assert result["status"]=="DRY_RUN_NO_NETWORK"


def test_explicit_opt_in_required(capsys):
    a,b=_connections()
    with patch("http.client.HTTPConnection",side_effect=[a,b]):
        assert main(["--execute-approved"])==0
    result=json.loads(capsys.readouterr().out)
    assert result["status"]=="PASS_SYNTHETIC_CRITERION_CONTRACT"


def test_explicit_bad_cli_port_refuses_network():
    with patch("http.client.HTTPConnection") as http, pytest.raises(SystemExit) as info:
        main(["--execute-approved","--port","65536"])
    assert info.value.code==2
    http.assert_not_called()


@pytest.mark.parametrize("field,value", [("role","tool"),("refusal","rejected"),("tool_calls",[{"id":"x"}])])
def test_reject_non_assistant_or_refusal_or_tool_calls(field,value):
    envelope=json.loads(_response_json())
    envelope["choices"][0]["message"][field]=value
    with pytest.raises(ValueError):
        _validated_completion(envelope,_MODEL)


def test_direct_cli_dry_run_in_isolated_python_without_pythonpath():
    """Regression for the real Simorgh script-path ModuleNotFoundError."""
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "verification" / "stage11_criterion_contract_smoke.py"
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(script)],
        cwd=root, capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0
    assert not result.stderr
    data = json.loads(result.stdout)
    assert data["status"] == "DRY_RUN_NO_NETWORK"
    assert data["stage11_gate"] == "BLOCKED"


def test_module_cli_dry_run_without_pythonpath():
    """The alternate -m entrypoint also stays network-free by default."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "scripts.verification.stage11_criterion_contract_smoke"],
        cwd=root, env=env, capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0
    assert not result.stderr
    assert json.loads(result.stdout)["status"] == "DRY_RUN_NO_NETWORK"



@pytest.mark.parametrize("workflow_name", [
    "stage11-preflight.yml",
    "stage11-synthetic-smoke.yml",
    "stage11-criterion-contract.yml",
])
def test_stage11_workflow_yaml_is_valid(workflow_name):
    """Reject invalid YAML before publishing a non-starting GitHub workflow."""
    from pathlib import Path
    import yaml

    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github" / "workflows" / workflow_name).read_text())
    assert workflow["permissions"]["contents"] == "read"
    jobs = workflow["jobs"]
    assert jobs
    runs = [step.get("run", "") for job in jobs.values() for step in job["steps"]]
    assert any("--only-binary=:all:" in command for command in runs)
    assert all("--execute-approved" not in command for command in runs)


def _diagnostic_result(*, completion: bytes):
    """Only mocked HTTP responses; never connect to Simorgh."""
    a, b = _connections(completion=completion)
    with patch("http.client.HTTPConnection", side_effect=[a, b]) as http:
        result = run(port=8000)
    assert http.call_count == 2
    assert result["status"] == "CRITERION_CONTRACT_UNVERIFIED"
    assert result["model_output_logged"] is False
    assert result["model_id_logged"] is False
    assert _MODEL not in json.dumps(result, ensure_ascii=False)
    assert _SOURCE not in json.dumps(result, ensure_ascii=False)
    assert result["stage11_gate"] == "BLOCKED"
    return result


@pytest.mark.parametrize(("content", "expected"), [
    ("NOT_PRIVATE_VALID_JSON", "JSON_OR_SCHEMA_REJECTED"),
    ('{"status":"assessed","status":"assessed"}', "JSON_OR_SCHEMA_REJECTED"),
    ('{"criterion_code":"clarity"}', "SCHEMA_REJECTED"),
])
def test_diagnostic_invalid_json_or_schema_is_redacted(content, expected):
    result = _diagnostic_result(completion=_response_json(content=content))
    assert result["failure_class"] == expected
    assert result["usage_tokens"] == {
        "prompt_tokens": 150, "completion_tokens": 90, "total_tokens": 240,
    }
    assert "NOT_PRIVATE_VALID_JSON" not in json.dumps(result)


@pytest.mark.parametrize(("change", "category"), [
    ("wrong_code", "CRITERION_CODE_MISMATCH"),
    ("wrong_quote", "QUOTE_NOT_FOUND_IN_SOURCE"),
    ("wrong_offset", "QUOTE_OFFSET_INCORRECT"),
    ("wrong_score_type", "SCHEMA_REJECTED"),
    ("extra_field", "SCHEMA_REJECTED"),
    ("abstain", "VALID_ABSTENTION_NO_ASSESSMENT"),
])
def test_diagnostic_refines_real_decoder_failure_without_leaking_text(change, category):
    obj = _valid_criterion()
    if change == "wrong_code":
        obj["criterion_code"] = "another_criterion"
    elif change == "wrong_quote":
        obj["evidence"][0]["quote"] = "UNTRUSTED_MODEL_TEXT"
    elif change == "wrong_offset":
        obj["evidence"][0]["end_offset"] -= 1
    elif change == "wrong_score_type":
        obj["score"] = "4"
    elif change == "extra_field":
        obj["unexpected"] = "UNTRUSTED_MODEL_TEXT"
    else:
        obj.update(status="not_assessed", score=None, evidence=[])
    response = _response_json(content=json.dumps(obj, ensure_ascii=False))
    result = _diagnostic_result(completion=response)
    assert result["failure_class"] == category
    assert "UNTRUSTED_MODEL_TEXT" not in json.dumps(result)


def test_diagnostic_output_limit_is_distinct_from_schema_failure():
    outcome = _diagnostic_result(completion=_response_json(
        content="UNTRUSTED_MODEL_TEXT", finish="length",
    ))
    assert outcome["failure_class"] == "OUTPUT_TOKEN_LIMIT"
    assert outcome["http_status"] == 200


def test_diagnostic_wrong_model_does_not_expose_model_id():
    outcome = _diagnostic_result(completion=_response_json(
        model="ANOTHER_PRIVATE_MODEL",
    ))
    assert outcome["failure_class"] == "MODEL_MISMATCH"
    assert "ANOTHER_PRIVATE_MODEL" not in json.dumps(outcome)


def test_diagnostic_malformed_envelope_is_sanitized():
    outcome = _diagnostic_result(completion=b'{"model":"'+_MODEL.encode()+b'","choices":[]}')
    assert outcome["failure_class"] == "ENVELOPE_INVALID"


def test_diagnostic_assistant_refusal_is_not_silently_accepted():
    envelope = json.loads(_response_json())
    envelope["choices"][0]["message"]["refusal"] = "UNTRUSTED_PRIVATE_REFUSAL"
    outcome = _diagnostic_result(completion=json.dumps(envelope).encode())
    assert outcome["failure_class"] == "ASSISTANT_MESSAGE_INVALID"
    assert "UNTRUSTED_PRIVATE_REFUSAL" not in json.dumps(outcome)


def test_diagnostic_missing_or_untrusted_token_usage_not_echoed():
    envelope = json.loads(_response_json(content="not JSON"))
    envelope["usage"] = {
        "prompt_tokens": True, "completion_tokens": -1,
        "total_tokens": "PRIVATE_SECRET",
    }
    outcome = _diagnostic_result(completion=json.dumps(envelope).encode())
    assert outcome["usage_tokens"] == {}
    assert "PRIVATE_SECRET" not in json.dumps(outcome)


def test_diagnostic_dry_run_requires_no_network(capsys):
    with patch("http.client.HTTPConnection") as http:
        assert main([]) == 0
        http.assert_not_called()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "DRY_RUN_NO_NETWORK"
    assert "failure_class" not in result


def test_synthetic_prompt_has_deterministic_codepoint_boundaries():
    """The prompt must explain Unicode offsets without changing strict decoding."""
    request = make_request(_MODEL)
    content = request["messages"][1]["content"]
    assert "start_offset=0 and end_offset=" + str(len(_SOURCE)) in content
    assert "Offsets exclude the <source> tags" in content
    assert "UTF-8 bytes" in content
    assert _SOURCE in content
    assert request["max_tokens"] == 320
