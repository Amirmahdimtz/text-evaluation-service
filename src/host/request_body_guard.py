"""ASGI-level bounded JSON body gate. Reject before FastAPI parses payloads.

Reads at most the configured cap, rejects ambiguous JSON and replays the exact
bytes without depending on Starlette private Request caching internals.
"""
from __future__ import annotations

import json
from uuid import uuid4

from starlette.responses import JSONResponse

from src.infrastructure.utils.config_reader import ConfigReader


class RequestBodyGuard:
    def __init__(self, app, config_reader: ConfigReader):
        self._app = app
        self._config = config_reader

    async def __call__(self, scope, receive, send):
        if (scope["type"] != "http"
                or not scope.get("path", "").startswith(
                    self._config.get_api_prefix() + "/text_evaluation/"
                )
                or scope.get("method", "").upper() not in ("POST", "PUT", "PATCH")):
            return await self._app(scope, receive, send)

        raw_headers = dict(scope.get("headers") or [])
        limit = self._config.settings.http_security.max_request_bytes or 65536

        async def reject(status: int, code: str):
            request_id = str(uuid4())
            response = JSONResponse(
                status_code=status,
                content={"error_code": code, "correlation_id": request_id},
                headers={"Cache-Control": "no-store", "X-Correlation-ID": request_id},
            )
            await response(scope, receive, send)

        content_type = raw_headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower()
        if content_type != b"application/json":
            return await reject(415, "UNSUPPORTED_MEDIA_TYPE")
        content_length = raw_headers.get(b"content-length")
        if content_length is not None:
            if not content_length.isdigit() or int(content_length) > limit:
                return await reject(413, "REQUEST_TOO_LARGE")

        data = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                return await reject(400, "VALIDATION_ERROR")
            part = message.get("body", b"")
            if len(data) + len(part) > limit:
                return await reject(413, "REQUEST_TOO_LARGE")
            data.extend(part)
            if not message.get("more_body", False):
                break

        def unique_pairs(pairs):
            output = {}
            for key, value in pairs:
                if key in output:
                    raise ValueError("AMBIGUOUS_JSON")
                output[key] = value
            return output

        def reject_constant(_):
            raise ValueError("NONFINITE_JSON")

        try:
            json.loads(
                data.decode("utf-8"), object_pairs_hook=unique_pairs,
                parse_constant=reject_constant,
            )
        except (ValueError, UnicodeError, RecursionError):
            return await reject(422, "VALIDATION_ERROR")

        data_bytes = bytes(data)
        first = True

        async def replay():
            nonlocal first
            if first:
                first = False
                return {"type": "http.request", "body": data_bytes, "more_body": False}
            return await receive()

        return await self._app(scope, replay, send)
