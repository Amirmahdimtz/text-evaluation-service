"""Stage11 bounded read-only metadata check of a named internal vLLM container.

Does not reveal image/registry references, Docker environment/command, raw model IDs,
credentials, network topology, or inference. Docker exec runs *only* Python package
metadata introspection; it does not load vLLM or invoke model inference.
"""
from __future__ import annotations

import argparse
import http.client
import json
import re
import shutil
import subprocess
import sys
from typing import Any

_CONTAINER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+){1,3}(?:[a-zA-Z0-9.+-]{0,40})?\Z")
_KNOWN_PUBLIC_IDS = frozenset({
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen3-14B",
})
_MAX_MODELS_BYTES = 65536
_RUNTIME_CODE = 'from importlib.metadata import version; print(version("vllm"))'


def _docker_argv(container: str, *, sudo: bool) -> list[str]:
    if not _CONTAINER.fullmatch(container):
        raise ValueError("Container name is invalid")
    return (["sudo", "-n", "docker"] if sudo else ["docker"])


def _run_readonly(argv: list[str]) -> str | None:
    """Never surface stderr, which might contain sensitive daemon diagnostics."""
    try:
        proc = subprocess.run(
            argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=8, check=False, text=True, encoding="utf-8", errors="replace",
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0 or len(proc.stdout) > 4096:
        return None
    return proc.stdout.strip()


def inspect_runtime(container: str, *, sudo: bool = False) -> dict[str, Any]:
    """Fetch only running boolean, then version of *installed* vLLM distribution.

    A Python metadata-only child process is created by docker exec; nothing is
    added to or reconfigured in the target container. This is not a GPU test.
    """
    base = _docker_argv(container, sudo=sudo)
    result = {
        "container_running": "UNVERIFIED",
        "installed_vllm_version": "UNVERIFIED",
        "version_evidence": "NOT_OBSERVED",
    }
    state = _run_readonly(base + ["inspect", "--type", "container", "--format", "{{.State.Running}}", container])
    if state not in ("true", "false"):
        return result
    result["container_running"] = state == "true"
    if state != "true":
        return result
    version = _run_readonly(base + [
        "exec", "--env", "PYTHONDONTWRITEBYTECODE=1", container,
        "python3", "-B", "-c", _RUNTIME_CODE,
    ])
    if version and _VERSION.fullmatch(version):
        result["installed_vllm_version"] = version
        result["version_evidence"] = "PACKAGE_METADATA_INSIDE_RUNNING_CONTAINER"
    return result


def parse_model_metadata(raw: bytes) -> dict[str, Any]:
    """Never print arbitrary internal model IDs; only exact known public candidates."""
    if not raw or len(raw) > _MAX_MODELS_BYTES:
        raise ValueError("Invalid model metadata size")
    try:
        payload = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("Malformed model metadata") from exc
    models = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(models, list) or len(models) > 32:
        raise ValueError("Invalid model list")
    names: list[str] = []
    for item in models:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("Invalid model record")
        names.append(item["id"])
    known = sorted({name for name in names if name in _KNOWN_PUBLIC_IDS})
    return {
        "model_count": len(names),
        "known_public_candidate_ids": known,
        "other_model_ids_redacted_count": len(names) - sum(n in _KNOWN_PUBLIC_IDS for n in names),
        "model_identity_evidence": "UNAUTHENTICATED_LOCAL_METADATA_NOT_ARTIFACT_PROOF",
    }


def probe_loopback_models(port: int) -> dict[str, Any]:
    """GET metadata on literal 127.0.0.1 only. No authentication or prompts."""
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("Invalid loopback port")
    conn = http.client.HTTPConnection("127.0.0.1", port=port, timeout=4)
    try:
        conn.request("GET", "/v1/models", headers={"Accept": "application/json"})
        response = conn.getresponse()
        if response.status != 200:
            return {"status": "HTTP_NOT_200", "model_metadata": "UNVERIFIED"}
        # A bounded read prevents memory amplification by another local service.
        raw = response.read(_MAX_MODELS_BYTES + 1)
        try:
            info = parse_model_metadata(raw)
        except ValueError:
            return {"status": "UNVERIFIED_RESPONSE", "model_metadata": "UNVERIFIED"}
        return {"status": "OBSERVED_LOOPBACK_METADATA", "model_metadata": info}
    except (OSError, TimeoutError, http.client.HTTPException):
        return {"status": "UNREACHABLE_OR_INVALID", "model_metadata": "UNVERIFIED"}
    finally:
        conn.close()


def collect(*, container: str, port: int | None, sudo: bool) -> dict[str, Any]:
    _docker_argv(container, sudo=sudo)
    if port is not None and (type(port) is not int or not 1 <= port <= 65535):
        raise ValueError("Invalid loopback port")
    # No Docker calls when the client is not present: prevents fallbacks to
    # alternate endpoints or elevated access beyond operator's explicit choice.
    docker_available = shutil.which("sudo" if sudo else "docker") is not None
    runtime = inspect_runtime(container, sudo=sudo) if docker_available else {
        "container_running": "UNVERIFIED",
        "installed_vllm_version": "UNVERIFIED",
        "version_evidence": "NOT_OBSERVED",
    }
    return {
        "schema_version": "stage11-container-metadata-v1",
        "scope": "OPT_IN_READONLY_CONTAINER_AND_LOOPBACK_METADATA",
        "stage11_acceptance": "BLOCKED_PENDING_APPROVALS_AND_REAL_TESTS",
        "container": runtime,
        "local_model_endpoint": probe_loopback_models(port) if port is not None else {
            "status": "SKIPPED_BY_OPERATOR", "model_metadata": "UNVERIFIED"
        },
        "not_examined": [
            "container_image_registry_or_private_reference", "environment_variables_or_secrets",
            "container_entrypoint_or_command", "running_processes_or_logs", "model_artifact_hash_or_license",
            "gpu_capacity_or_inference", "enterprise_identity", "network_egress_or_tls",
            "database_or_customer_text", "deployment_approval",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True, help="Exact running container name; never printed")
    parser.add_argument("--port", type=int, help="Optional local-only vLLM /v1/models port")
    parser.add_argument("--sudo-docker", action="store_true", help="Use sudo -n docker (no password prompt)")
    args = parser.parse_args(argv)
    try:
        result = collect(container=args.container, port=args.port, sudo=args.sudo_docker)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
