"""Stage11 independent API and Worker processes on isolated PostgreSQL.

Explicitly opt-in on a dedicated CI test database: TES_STAGE11_PROCESS_E2E=1.
The inference endpoint is an in-process loopback synthetic stub. Never points
to vLLM, uses GPU, launches Docker, or touches an organization database.
"""
from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timezone
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import time
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
import yaml
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy import select

from src.core.services.text_evaluation.rubric_schema import RubricSnapshot
from src.infrastructure.context.sql_db.psql_dbcontext import (
    PsqlDbContext, get_test_database_url,
)
from src.infrastructure.models.text_evaluation import (
    CriterionResult, Evaluation, ProtectedText, RubricVersion,
)
from src.infrastructure.utils.config_reader import ConfigReader

ROOT = Path(__file__).resolve().parents[1]
RUBRICS = ROOT / "tests/fixtures/stage06_candidate_rubrics.json"
SOURCE = "این یک متن کاملاً ساختگی برای آزمون ایزوله و امن است. 🌱"
MODEL_ID = "synthetic-process-stub"


def _unused_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _SyntheticInferenceHandler(BaseHTTPRequestHandler):
    """Returns only deterministic JSON with evidence copied from test text."""

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        try:
            length = int(self.headers["Content-Length"])
            if not 0 < length <= 65536:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            if payload["model"] != MODEL_ID or payload["stream"] is not False:
                raise ValueError
            prompt = payload["messages"][1]["content"]
            criterion = re.search(r"\nCriterion: ([a-z][a-z0-9_]*)\n", prompt)
            if not criterion:
                raise ValueError
            source = prompt.rsplit("\n<source>\n", 1)[1].rsplit("\n</source>", 1)[0]
            if source != SOURCE:
                raise ValueError
            quote = source[:12]
            record = {
                "criterion_code": criterion.group(1),
                "status": "assessed",
                "score": 4,
                "reason": "Synthetic stub: no model quality assertion",
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "evidence": [{
                    "source_kind": "original_submission",
                    "quote": quote, "start_offset": 0, "end_offset": len(quote),
                }],
            }
            result = {
                "model": MODEL_ID, "choices": [{
                    "finish_reason": "stop",
                    "message": {"content": json.dumps(record, ensure_ascii=False)},
                }],
            }
            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.server.request_count += 1
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (KeyError, ValueError, TypeError, IndexError):
            self.send_error(400)

    def log_message(self, _fmt, *_args):
        # Neither source text nor inference request metadata enters test logs.
        pass


def _wait_for_api(process: subprocess.Popen, base_url: str) -> None:
    with httpx.Client(timeout=0.5, trust_env=False) as client:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail("STAGE11_API_EXITED_BEFORE_READY")
            try:
                result = client.get(base_url + "/health/ready")
                if result.status_code == 200:
                    return
            except httpx.RequestError:
                pass
            time.sleep(0.1)
    pytest.fail("STAGE11_API_START_TIMEOUT")


def _stop_child(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


async def _seed_and_verify(*, org: str, after: bool = False) -> UUID | None:
    db = PsqlDbContext()
    try:
        if not after:
            snapshot = RubricSnapshot.model_validate(
                json.loads(RUBRICS.read_text(encoding="utf-8"))["speech"]
            )
            rubric_id = uuid4()
            async with db.session() as session:
                async with session.begin():
                    session.add(RubricVersion(
                        id=rubric_id, organization_id=org, evaluation_type="speech",
                        code=snapshot.code, version=snapshot.version,
                        status="published", checksum=snapshot.fingerprint(),
                        criteria_snapshot=snapshot.canonical_dict(),
                        published_at=datetime.now(timezone.utc),
                    ))
            return rubric_id
        async with db.session() as session:
            evaluation = (await session.scalars(select(Evaluation).where(
                Evaluation.organization_id == org,
            ))).one()
            protected = (await session.scalars(select(ProtectedText).where(
                ProtectedText.id == evaluation.protected_text_ref,
                ProtectedText.organization_id == org,
            ))).one()
            rows = (await session.scalars(select(CriterionResult).where(
                CriterionResult.evaluation_id == evaluation.id,
                CriterionResult.organization_id == org,
            ))).all()
            assert evaluation.status == "needs_human_review"
            assert evaluation.overall_score is None
            assert Decimal(evaluation.coverage) == Decimal(1)
            assert len(rows) == 6
            assert all(r.status == "assessed" and r.score == 4 for r in rows)
            assert SOURCE.encode("utf-8") not in protected.ciphertext
            assert all(SOURCE.encode("utf-8") not in r.encrypted_details for r in rows)
    finally:
        await db.close()
    return None


def _access_token(key, org: str) -> str:
    now = int(time.time())
    return jwt.encode({
        "sub": "synthetic-owner", "org": org,
        "iss": "synthetic-stage11-issuer", "aud": "synthetic-stage11-audience",
        "iat": now, "nbf": now, "exp": now + 180,
        "jti": uuid4().hex,
        "permissions": ["evaluation:submit", "evaluation:read"],
        "assigned_resource_ids": [],
    }, key, algorithm="RS256")


@pytest.mark.skipif(
    os.environ.get("TES_STAGE11_PROCESS_E2E") != "1",
    reason="PENDING_ISOLATED_PROCESS_E2E: explicit dedicated test DB opt-in required",
)
def test_stage11_real_api_and_worker_processes_with_isolated_postgres(monkeypatch):
    """Real child processes + real DB + loopback stub, never live inference."""
    if os.name != "posix":
        pytest.skip("Linux process integration only")
    get_test_database_url()  # Must reject non-development, shared, or remote DSNs.
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    org = "synthetic-realprocess-" + uuid4().hex
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    api_port = _unused_loopback_port()
    stub = ThreadingHTTPServer(("127.0.0.1", 0), _SyntheticInferenceHandler)
    stub.request_count = 0
    thread = Thread(target=stub.serve_forever, daemon=True)
    thread.start()

    base_url = "http://127.0.0.1:" + str(api_port)
    api = worker = None
    try:
        with TemporaryDirectory(prefix="tes-stage11-process-") as folder:
            base = ConfigReader().settings.model_dump()
            base["server"]["port"] = api_port
            base["http_security"] = {
                "enabled": True, "issuer": "synthetic-stage11-issuer",
                "audience": "synthetic-stage11-audience",
                "public_key_ref": "env://TES_STAGE11_PROCESS_PUBLIC",
                "encryption_key_ref": "env://TES_STAGE11_PROCESS_AES",
                "key_id": "synthetic-process-key",
                "max_request_bytes": 4096, "max_text_characters": 2048,
                "max_active_jobs": 4, "max_requests_per_minute": 100,
            }
            base["worker"] = {
                "enabled": True, "organization_id": org,
                "lease_seconds": 20.0, "heartbeat_seconds": 1.0,
                "execution_timeout_seconds": 12.0, "max_attempts": 1,
                "retry_base_seconds": 0.0, "retry_cap_seconds": 0.0,
                "max_inflight": 1, "max_queue_depth": 4,
                "poll_seconds": 0.1, "recovery_batch_size": 2,
                "drain_seconds": 3.0,
            }
            base["llm"] = {
                "enabled": True,
                "endpoint": "http://127.0.0.1:" + str(stub.server_address[1]) + "/v1",
                "model_id": MODEL_ID, "model_revision": "synthetic-process-revision",
                "max_input_characters": 4096, "max_context_tokens": 8192,
                "max_output_tokens": 512, "timeout_seconds": 4.0,
                "max_concurrency": 1, "max_attempts": 1,
                "retry_backoff_seconds": 0.0, "circuit_failures": 1,
                "circuit_reset_seconds": 10.0, "temperature": 0.0,
                "thinking_mode": "runtime_default",
            }
            private_file = Path(folder) / "stage11-dev-only.yaml"
            private_file.write_text(yaml.safe_dump(base), encoding="utf-8")
            private_file.chmod(0o600)
            env = os.environ.copy()
            env["TES_ENVIRONMENT"] = "development"
            env["TES_STAGE11_SETTINGS_FILE"] = str(private_file)
            env["TES_STAGE11_PROCESS_PUBLIC"] = (
                private_key.public_key().public_bytes(
                    Encoding.PEM, PublicFormat.SubjectPublicKeyInfo,
                ).decode("ascii")
            )
            env["TES_STAGE11_PROCESS_AES"] = base64.b64encode(os.urandom(32)).decode()

            # Fail closed before creating children if any config is unsafe.
            from scripts.verification.stage11_isolated_runtime_preflight import (
                verify_isolated_configuration,
            )
            for key in ("TES_STAGE11_SETTINGS_FILE", "TES_STAGE11_PROCESS_PUBLIC",
                        "TES_STAGE11_PROCESS_AES"):
                monkeypatch.setenv(key, env[key])
            assert verify_isolated_configuration()["status"] == (
                "CONFIG_VALIDATED_NO_NETWORK"
            )
            asyncio.run(_seed_and_verify(org=org))
            api = subprocess.Popen(
                [sys.executable, "-m", "src.host.app"],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            _wait_for_api(api, base_url)
            worker = subprocess.Popen(
                [sys.executable, "-m", "src.host.evaluation_worker"],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            with httpx.Client(base_url=base_url, timeout=2.0, trust_env=False) as client:
                auth = _access_token(private_key, org)
                headers = {
                    "Authorization": "Bearer " + auth,
                    "Idempotency-Key": "synthetic-process-" + uuid4().hex,
                }
                snapshot = RubricSnapshot.model_validate(
                    json.loads(RUBRICS.read_text(encoding="utf-8"))["speech"]
                )
                rejected = client.get("/api/v1/text_evaluation/rubrics")
                assert rejected.status_code == 401
                submit = client.post(
                    "/api/v1/text_evaluation/evaluations",
                    headers=headers, json={
                        "text": SOURCE, "evaluation_type": "speech",
                        "rubric_code": snapshot.code, "rubric_version": snapshot.version,
                    },
                )
                assert submit.status_code == 202, "STAGE11_PROCESS_SUBMISSION_FAILED"
                evaluation_id = UUID(submit.json()["evaluation_id"])
                path = "/api/v1/text_evaluation/evaluations/" + str(evaluation_id)
                deadline = time.monotonic() + 35
                report = None
                while time.monotonic() < deadline:
                    if worker.poll() is not None:
                        pytest.fail("STAGE11_WORKER_EXITED")
                    response = client.get(path, headers=headers)
                    assert response.status_code == 200
                    candidate = response.json()
                    if candidate["status"] == "needs_human_review":
                        report = candidate
                        break
                    if candidate["status"] in ("failed_terminal", "failed_retryable"):
                        pytest.fail("STAGE11_WORKER_PROCESSING_FAILED")
                    time.sleep(0.15)
                assert report is not None, "STAGE11_PROCESS_JOB_TIMEOUT"
                assert report["provisional_score"] == "80"
                assert Decimal(str(report["coverage"])) == Decimal(1)
                assert report["needs_human_review"] is True
                assert report["publishable_as_official_score"] is False
                assert len(report["criteria"]) == 6
                assert all(c["score"] == 4 for c in report["criteria"])
                for row in report["criteria"]:
                    ev = row["details"]["evidence"][0]
                    assert SOURCE[ev["start_offset"]:ev["end_offset"]] == ev["quote"]
                outsider = client.get(path, headers={
                    "Authorization": "Bearer " + _access_token(
                        private_key, "synthetic-other-organization",
                    ),
                })
                assert outsider.status_code == 404
                assert SOURCE not in outsider.text
            asyncio.run(_seed_and_verify(org=org, after=True))
            assert stub.request_count == 6
    finally:
        if worker is not None:
            _stop_child(worker)
        if api is not None:
            _stop_child(api)
        stub.shutdown()
        stub.server_close()
        thread.join(timeout=3)
