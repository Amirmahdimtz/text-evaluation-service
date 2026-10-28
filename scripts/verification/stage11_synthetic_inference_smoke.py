"""One bounded synthetic structured-output smoke against a loopback-only model API.

Explicitly authorized Stage11 smoke only: one GET /v1/models, at most one POST
/v1/chat/completions, no retries, proxies, remote hosts, credentials, or private
inputs. Model identifiers and model-generated content never appear in output.
"""
from __future__ import annotations

import argparse
import http.client
import json
import sys
import time
from typing import Any

_MAX_MODELS_BYTES = 16384
_MAX_COMPLETION_BYTES = 32768
_SYNTHETIC_MESSAGES = [
    {"role": "system", "content": "Return only a JSON object matching the schema. Do not use tools or external information."},
    {"role": "user", "content": "این فقط آزمون ساختگی و بدون دادهٔ محرمانه است. در JSON مقدار ack را برابر ok قرار بده."},
]
_SMOKE_SCHEMA = {
    "type": "object",
    "properties": {"ack": {"type": "string", "enum": ["ok"]}},
    "required": ["ack"],
    "additionalProperties": False,
}


def _object_unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON property")
        result[name] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError("invalid non-finite number")


def _safe_json(raw: bytes, *, limit: int) -> dict[str, Any]:
    if not raw or len(raw) > limit:
        raise ValueError("invalid payload size")
    obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_unique,
                     parse_constant=_reject_nonfinite)
    if not isinstance(obj, dict):
        raise ValueError("not a JSON object")
    return obj


def _single_model(data: dict[str, Any]) -> str:
    models = data.get("data")
    if not isinstance(models, list) or len(models) != 1:
        raise ValueError("one advertised model required")
    first = models[0]
    if not isinstance(first, dict) or not isinstance(first.get("id"), str):
        raise ValueError("model metadata missing")
    model_id = first["id"]
    if not model_id or len(model_id) > 512 or any(ord(ch) < 32 or ord(ch) == 127 for ch in model_id):
        raise ValueError("invalid opaque model id")
    return model_id


def _read_response(response: http.client.HTTPResponse, *, limit: int) -> bytes:
    return response.read(limit + 1)


def _connection(port: int, timeout: int) -> http.client.HTTPConnection:
    return http.client.HTTPConnection("127.0.0.1", port=port, timeout=timeout)


def _status(name: str, *, http_status: int | None = None) -> dict[str, Any]:
    return {
        "schema_version": "stage11-single-synthetic-inference-v1",
        "status": name,
        "http_status": http_status,
        "private_model_id_logged": False,
        "model_output_logged": False,
        "requests_limit": {"metadata_get": 1, "inference_post": 1, "retries": 0},
        "enterprise_stage11_gate": "BLOCKED",
    }


def _extract_completion(data: dict[str, Any], *, expected_model: str) -> dict[str, Any]:
    if data.get("model") != expected_model:
        raise ValueError("unexpected served model")
    choices = data.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("invalid choice envelope")
    choice = choices[0]
    if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
        raise ValueError("generation unfinished")
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise ValueError("invalid assistant envelope")
    content = message.get("content")
    if not isinstance(content, str) or len(content.encode("utf-8")) > 1024:
        raise ValueError("invalid bounded content")
    parsed = _safe_json(content.encode("utf-8"), limit=1024)
    if parsed != {"ack": "ok"}:
        raise ValueError("schema value mismatch")
    usage = data.get("usage")
    token_counts: dict[str, int] = {}
    if isinstance(usage, dict):
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = usage.get(key)
            if type(value) is int and 0 <= value <= 100000:
                token_counts[key] = value
    return {"schema_valid": True, "finish_reason": "stop", "usage_tokens": token_counts}


def _query_one_model(*, port: int) -> tuple[str | None, dict[str, Any] | None]:
    connection = _connection(port, 4)
    try:
        connection.request("GET", "/v1/models", headers={"Accept": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            return None, _status("MODEL_METADATA_HTTP_REJECTED", http_status=response.status)
        model_id = _single_model(_safe_json(_read_response(response, limit=_MAX_MODELS_BYTES),
                                            limit=_MAX_MODELS_BYTES))
        return model_id, None
    except (OSError, TimeoutError, http.client.HTTPException, ValueError, UnicodeError,
            RecursionError, OverflowError):
        return None, _status("MODEL_METADATA_UNVERIFIED")
    finally:
        connection.close()


def run_smoke(*, port: int) -> dict[str, Any]:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("invalid loopback port")
    model_id, error = _query_one_model(port=port)
    if error is not None:
        return error
    assert model_id is not None
    request = {
        "model": model_id,
        "messages": _SYNTHETIC_MESSAGES,
        "max_tokens": 64,
        "temperature": 0,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "synthetic_smoke_ack_v1",
                "strict": True,
                "schema": _SMOKE_SCHEMA,
            },
        },
    }
    body = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    start = time.monotonic()
    connection = _connection(port, 40)
    try:
        connection.request("POST", "/v1/chat/completions", body=body, headers={
            "Accept": "application/json", "Content-Type": "application/json",
        })
        response = connection.getresponse()
        if response.status != 200:
            elapsed = max(0, int((time.monotonic() - start) * 1000))
            return _status("INFERENCE_HTTP_REJECTED", http_status=response.status) | {"elapsed_ms": elapsed}
        data = _safe_json(_read_response(response, limit=_MAX_COMPLETION_BYTES),
                          limit=_MAX_COMPLETION_BYTES)
        elapsed = max(0, int((time.monotonic() - start) * 1000))
        try:
            evidence = _extract_completion(data, expected_model=model_id)
        except (ValueError, UnicodeError, RecursionError, OverflowError):
            return _status("INFERENCE_SCHEMA_UNVERIFIED", http_status=200) | {"elapsed_ms": elapsed}
        return _status("PASS_SYNTHETIC_STRUCTURED_SMOKE", http_status=200) | {"elapsed_ms": elapsed} | evidence
    except (OSError, TimeoutError, http.client.HTTPException):
        return _status("INFERENCE_TRANSPORT_OR_TIMEOUT")
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        return _status("INFERENCE_INVALID_RESPONSE")
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000, help="Approved loopback API port (default 8000)")
    parser.add_argument("--dry-run", action="store_true", help="Never connect or generate")
    args = parser.parse_args(argv)
    try:
        if type(args.port) is not int or not 1 <= args.port <= 65535:
            parser.error("port must be within 1..65535")
        result = _status("DRY_RUN_NO_REQUESTS") if args.dry_run else run_smoke(port=args.port)
    except ValueError:
        result = _status("LOCAL_VALIDATION_FAILED")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"] in ("PASS_SYNTHETIC_STRUCTURED_SMOKE", "DRY_RUN_NO_REQUESTS") else 1


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
