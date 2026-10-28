"""Stage11 read-only *host-local* inventory; never a production acceptance test.

No network, Docker daemon, database, model inference, secrets or filesystem writes.
Output must stay with the authorized operator, not in the public repository.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

GPU_QUERY = (
    "nvidia-smi",
    "--query-gpu=index,name,memory.total,memory.used,driver_version",
    "--format=csv,noheader,nounits",
)
MAX_GPU_RECORDS = 32


def _mib(value: str) -> int:
    amount = int(value.strip())
    if amount < 0:
        raise ValueError("negative value")
    return amount


def parse_gpu_csv(raw: str) -> list[dict[str, Any]]:
    """Reject anomalous output instead of guessing GPU identity/capacity."""
    lines = raw.splitlines()
    if not lines or len(lines) > MAX_GPU_RECORDS:
        raise ValueError("missing or excessive GPU records")
    result: list[dict[str, Any]] = []
    seen: set[int] = set()
    for line in lines:
        fields = [part.strip() for part in line.split(",")]
        if len(fields) != 5:
            raise ValueError("unexpected nvidia-smi fields")
        number = int(fields[0])
        total = _mib(fields[2])
        used = _mib(fields[3])
        if number < 0 or number in seen or not total or used > total:
            raise ValueError("invalid GPU values")
        if not fields[1] or not fields[4] or len(fields[1]) > 128:
            raise ValueError("incomplete GPU metadata")
        seen.add(number)
        result.append({
            "index": number,
            "model": fields[1],
            "vram_total_mib": total,
            "vram_used_mib_at_probe": used,
            "driver_version": fields[4],
        })
    return result


def probe_gpu() -> dict[str, Any]:
    """Run a single bounded, nonprivileged read-only NVIDIA metadata query."""
    if not shutil.which("nvidia-smi"):
        return {"status": "TOOL_NOT_FOUND", "gpus": []}
    try:
        completed = subprocess.run(
            GPU_QUERY,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "gpus": []}
    except OSError:
        return {"status": "QUERY_FAILED", "gpus": []}
    if completed.returncode != 0 or len(completed.stdout) > 16384:
        return {"status": "QUERY_FAILED", "gpus": []}
    try:
        gpus = parse_gpu_csv(completed.stdout)
    except (ValueError, UnicodeError):
        return {"status": "UNVERIFIED_OUTPUT", "gpus": []}
    return {"status": "OBSERVED_READ_ONLY", "gpus": gpus}


def read_memory_summary(path: Path = Path("/proc/meminfo")) -> dict[str, Any]:
    """Read aggregate RAM counters only; no process/environment inspection."""
    try:
        raw = path.read_text(encoding="ascii")
        data: dict[str, int] = {}
        for line in raw.splitlines():
            key, _, val = line.partition(":")
            if key in {"MemTotal", "MemAvailable"}:
                parts = val.strip().split()
                if len(parts) != 2 or parts[1] != "kB":
                    raise ValueError("unexpected unit")
                amount = int(parts[0])
                if amount < 0:
                    raise ValueError("negative memory")
                data[key] = amount // 1024
        if set(data) != {"MemTotal", "MemAvailable"} or data["MemAvailable"] > data["MemTotal"]:
            raise ValueError("incomplete memory")
        return {"status": "OBSERVED_READ_ONLY", "total_mib": data["MemTotal"], "available_mib": data["MemAvailable"]}
    except (OSError, ValueError, UnicodeError):
        return {"status": "UNVERIFIED"}


def local_distribution_version(name: str) -> str:
    """Only the calling Python environment, NOT a running container or GPU stack."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED_IN_THIS_PYTHON"
    except (OSError, ValueError):
        return "UNVERIFIED"


def collect_inventory(*, include_gpu: bool = True) -> dict[str, Any]:
    try:
        root = shutil.disk_usage("/")
        root_fs: dict[str, Any] = {
            "status": "OBSERVED_READ_ONLY",
            "total_gib": round(root.total / 2**30, 2),
            "free_gib_at_probe": round(root.free / 2**30, 2),
            "scope": "root_filesystem_only_not_model_registry",
        }
    except OSError:
        root_fs = {"status": "UNVERIFIED"}
    return {
        "schema_version": "stage11-readonly-inventory-v1",
        "scope": "HOST_LOCAL_METADATA_ONLY",
        "stage11_acceptance": "BLOCKED_PENDING_APPROVALS_AND_REAL_TESTS",
        "host": {
            "os": platform.system(),
            "arch": platform.machine(),
            "kernel_release": platform.release(),
            "libc": " ".join(platform.libc_ver()),
            "cpu_logical_count": os.cpu_count(),
            "ram": read_memory_summary(),
            "root_filesystem": root_fs,
        },
        "gpu": probe_gpu() if include_gpu else {"status": "SKIPPED_BY_OPERATOR", "gpus": []},
        "python_interpreter": {
            "version": platform.python_version(),
            "installed_vllm_distribution": local_distribution_version("vllm"),
            "installed_torch_distribution": local_distribution_version("torch"),
            "note": "Package metadata for this interpreter; not the existing vLLM container/runtime.",
        },
        "docker_cli_detected": shutil.which("docker") is not None,
        "not_examined": [
            "container_names_and_images", "running_model_and_model_id", "host_service_ports",
            "enterprise_identity", "secret_material", "network_egress_or_tls",
            "corporate_database", "gpu_compute_or_model_inference", "supply_chain_provenance",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-gpu", action="store_true", help="Skip the read-only nvidia-smi query")
    args = parser.parse_args(argv)
    print(json.dumps(collect_inventory(include_gpu=not args.no_gpu), sort_keys=True, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
