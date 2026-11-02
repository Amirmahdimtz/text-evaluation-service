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

    # Do not download an image or change existing deployment/container state.
    _invoke(["docker", "image", "inspect", "postgres:17"],
            env=os.environ.copy(), suppress_output=True)
    _invoke(["docker", "compose", "version"],
            env=os.environ.copy(), suppress_output=True)

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
    started = False
    print(json.dumps({"status": "STARTING_ISOLATED_TEST_DATABASE", "project": project}),
          flush=True)
    try:
        # --pull never ensures this operation cannot silently download an image.
        _invoke(compose + ["up", "--pull", "never", "-d", "postgres"],
                env=env, suppress_output=True)
        started = True
        asyncio.run(_wait_for_database(env))
        _invoke([sys.executable, "-m",
                 "scripts.verification.run_stage05_migrations", "upgrade"], env=env)
        _invoke([
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "tests/test_stage11_process_e2e.py",
        ], env=env)
        print(json.dumps({"status": "ISOLATED_PROCESS_E2E_PASS",
                          "project": project, "gpu_requests": 0}), flush=True)
        return 0
    finally:
        # Do not remove named volumes or other Docker resources.
        if started:
            try:
                _invoke(compose + ["stop", "postgres"], env=env, suppress_output=True)
                print(json.dumps({
                    "status": "ISOLATED_TEST_DATABASE_STOPPED_VOLUME_RETAINED",
                    "project": project,
                }), flush=True)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
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
    except (RuntimeError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, ValueError):
        # Never print a DSN, password or subprocess exception/command line.
        print(json.dumps({"status": "ISOLATED_PROCESS_E2E_FAILED",
                          "error_code": "STAGE11_ISOLATED_RUN_ABORTED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
