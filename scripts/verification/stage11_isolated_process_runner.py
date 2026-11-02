"""Opt-in Stage11 real API/Worker process test in a fresh Docker test database.

Never use shared PostgreSQL, vLLM, GPU, Docker network aliases, or production
credentials. Default invocation is dry-run and performs no subprocess actions.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from urllib.parse import quote
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "compose.stage11-isolated-db.yml"


class IsolatedRunFailed(RuntimeError):
    """Only an allowlisted phase can appear in a user-visible error."""

    def __init__(self, phase: str) -> None:
        self.phase = phase
        super().__init__("STAGE11_ISOLATED_RUN_ABORTED")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


async def _wait_for_database(env: dict[str, str], *, timeout: float = 30.0) -> None:
    import asyncpg

    deadline = time.monotonic() + timeout
    # Pass credentials in memory only, never in command arguments.
    while time.monotonic() < deadline:
        try:
            conn = await asyncpg.connect(
                host="127.0.0.1", port=int(env["TES_STAGE11_DB_PORT"]),
                user=env["TES_STAGE11_DB_USER"],
                password=env["TES_STAGE11_DB_PASSWORD"],
                database=env["TES_STAGE11_DB_NAME"],
                timeout=1.5,
            )
            await conn.close()
            return
        except (OSError, asyncpg.PostgresError, asyncio.TimeoutError):
            await asyncio.sleep(0.3)
    raise RuntimeError("STAGE11_ISOLATED_DATABASE_NOT_READY")


def _invoke(args: list[str], *, env: dict[str, str],
            suppress_output: bool = False) -> None:
    subprocess.run(
        args, check=True, cwd=ROOT, env=env, timeout=120,
        stdout=subprocess.DEVNULL if suppress_output else None,
        stderr=subprocess.DEVNULL if suppress_output else None,
    )


def execute_isolated() -> int:
    """Start only a unique loopback-only PostgreSQL container and test processes."""
    forbidden = (
        "TES_STAGE05_DATABASE_URL", "TES_STAGE11_SETTINGS_FILE",
        "TES_STAGE11_DB_PASSWORD", "TES_STAGE11_DB_PORT",
    )
    if (os.environ.get("TES_ENVIRONMENT", "development") != "development"
            or any(os.environ.get(key) for key in forbidden)):
        raise RuntimeError("STAGE11_EXISTING_ENVIRONMENT_REFUSED")

    # Validate prerequisites before creating any Docker resource.
    phase = "image_check"
    try:
        _invoke(["docker", "image", "inspect", "postgres:17"],
                env=os.environ.copy(), suppress_output=True)
        phase = "compose_check"
        _invoke(["docker", "compose", "version"],
                env=os.environ.copy(), suppress_output=True)
    except Exception:
        raise IsolatedRunFailed(phase) from None

    project = "tes-stage11-" + uuid4().hex[:12]
    user = "tes_stage11"
    password = secrets.token_urlsafe(32)
    database = "tes_stage05_" + uuid4().hex[:12]
    port = _free_port()
    env = os.environ.copy()
    env.update({
        "TES_ENVIRONMENT": "development",
        "TES_STAGE11_DB_USER": user,
        "TES_STAGE11_DB_PASSWORD": password,
        "TES_STAGE11_DB_NAME": database,
        "TES_STAGE11_DB_PORT": str(port),
        "TES_STAGE05_DATABASE_URL": (
            "postgresql+asyncpg://"
            + quote(user, safe="") + ":" + quote(password, safe="")
            + "@127.0.0.1:" + str(port) + "/" + quote(database, safe="")
        ),
        "TES_STAGE11_PROCESS_E2E": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    compose = [
        "docker", "compose", "--project-name", project,
        "-f", str(COMPOSE), "--profile", "isolated",
    ]
    attempted_start = False
    phase = "compose_up"
    print(json.dumps({"status": "STARTING_ISOLATED_TEST_DATABASE", "project": project}),
          flush=True)
    try:
        # Compose may partially create a container before returning nonzero.
        attempted_start = True
        _invoke(compose + ["up", "--pull", "never", "-d", "postgres"],
                env=env, suppress_output=True)
        phase = "postgres_readiness"
        print(json.dumps({"status": "CHECKING_ISOLATED_POSTGRES", "project": project}),
              flush=True)
        asyncio.run(_wait_for_database(env))
        phase = "schema_migration"
        print(json.dumps({"status": "MIGRATING_ISOLATED_TEST_DATABASE",
                          "project": project}), flush=True)
        _invoke([sys.executable, "-m",
                 "scripts.verification.run_stage05_migrations", "upgrade"],
                env=env, suppress_output=True)
        phase = "api_worker_e2e"
        print(json.dumps({"status": "RUNNING_SYNTHETIC_API_WORKER_E2E",
                          "project": project}), flush=True)
        _invoke([
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "tests/test_stage11_process_e2e.py",
        ], env=env, suppress_output=True)
        print(json.dumps({"status": "ISOLATED_PROCESS_E2E_PASS",
                          "project": project, "gpu_requests": 0}), flush=True)
        return 0
    except Exception:
        # Never include subprocess command, DSN, secret or traceback.
        raise IsolatedRunFailed(phase) from None
    finally:
        # Never delete test volumes or modify other Compose projects.
        if attempted_start:
            try:
                _invoke(compose + ["stop", "postgres"], env=env, suppress_output=True)
                print(json.dumps({
                    "status": "ISOLATED_TEST_DATABASE_STOPPED_VOLUME_RETAINED",
                    "project": project,
                }), flush=True)
            except Exception:
                print(json.dumps({"status": "ISOLATED_TEST_DATABASE_STOP_FAILED",
                                  "project": project}), flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-isolated", action="store_true",
                        help="Create and stop a new dedicated Docker test DB.")
    arguments = parser.parse_args(argv)
    if not arguments.execute_isolated:
        print(json.dumps({"status": "DRY_RUN_NO_DOCKER_NO_NETWORK",
                          "execution_requires": "--execute-isolated"}))
        return 0
    try:
        return execute_isolated()
    except Exception as exc:
        # Return an allowlisted phase only, never the exception or its arguments.
        phase = exc.phase if isinstance(exc, IsolatedRunFailed) else "environment"
        print(json.dumps({"status": "ISOLATED_PROCESS_E2E_FAILED",
                          "error_code": "STAGE11_ISOLATED_RUN_ABORTED",
                          "failure_phase": phase}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
