"""Stage11 vLLM 0.10.2 guided-decoding inspection without inference.

Default: inspect only the application's local Pydantic schema.
Opt-in container mode: use read-only Docker inspect for the two launch
argument arrays. Raw arguments, env, credentials, model IDs, process lists
and image references are NEVER emitted. A launch flag is not proof of the
engine's effective request-level backend (especially with backend=auto).
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import subprocess
from typing import Any

from src.infrastructure.providers.llm.structured_response import CriterionInference

_CONTAINER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_ALLOWED_BACKENDS = frozenset({
    "auto", "xgrammar", "guidance", "outlines", "lm-format-enforcer",
})
_MAX_DOCKER_STDOUT = 16384
_FORMATS = ("{{json .Config.Entrypoint}}", "{{json .Config.Cmd}}")


def _unsupported_xgrammar_keywords(schema: dict) -> list[str]:
    """Static keyword check mirrored from vLLM 0.10.2, NOT compilation."""
    unsupported: set[str] = set()

    def visit(obj: object) -> None:
        if isinstance(obj, list):
            for item in obj:
                visit(item)
        elif isinstance(obj, dict):
            node_type = obj.get("type")
            if node_type in ("integer", "number") and "multipleOf" in obj:
                unsupported.add("multipleOf")
            if node_type == "array":
                unsupported.update(
                    key for key in ("uniqueItems", "contains", "minContains", "maxContains")
                    if key in obj
                )
            if node_type == "string" and "format" in obj:
                unsupported.add("format")
            if node_type == "object":
                unsupported.update(
                    key for key in (
                        "minProperties", "maxProperties", "propertyNames", "patternProperties",
                    ) if key in obj
                )
            for item in obj.values():
                visit(item)
    visit(schema)
    return sorted(unsupported)


def schema_report() -> dict[str, Any]:
    """Report counts/constraints, never print schema or any source text."""
    schema = CriterionInference.model_json_schema()
    keyword_counts: Counter[str] = Counter()
    array_limits: list[int] = []

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for name, child in value.items():
                keyword_counts[name] += 1
                if name == "maxItems" and type(child) is int:
                    array_limits.append(child)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(schema)
    props = schema.get("properties", {})
    unsupported = _unsupported_xgrammar_keywords(schema)
    return {
        "scope": "STAGE11_OFFLINE_SCHEMA_STATIC_INSPECTION",
        "schema_top_level_fields": len(props),
        "schema_definitions": len(schema.get("$defs", {})),
        "array_max_items": sorted(array_limits),
        "any_of_nodes": keyword_counts["anyOf"],
        "ref_nodes": keyword_counts["$ref"],
        "additional_properties_false_count": sum(
            1 for node in (schema, *schema.get("$defs", {}).values())
            if isinstance(node, dict) and node.get("additionalProperties") is False
        ),
        "xgrammar_v0102_static_unsupported_keywords": unsupported,
        "xgrammar_v0102_compiler_validation": "NOT_RUN",
        "pydantic_cross_field_validation_in_json_schema": False,
        "model_inference_requests": 0,
        "network_requests": 0,
    }


def _inspect_array(container: str, field: str, sudo: bool) -> list[str] | None:
    base = ["sudo", "-n", "docker"] if sudo else ["docker"]
    try:
        proc = subprocess.run(
            [*base, "inspect", "--type", "container", "--format", field, container],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=6, check=False, text=True, encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not (0 < len(proc.stdout) <= _MAX_DOCKER_STDOUT):
        return None
    try:
        values = json.loads(proc.stdout)
    except (TypeError, ValueError):
        return None
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > 128:
        return None
    if any(not isinstance(arg, str) or len(arg) > 4096 for arg in values):
        return None
    return values


def parse_launch_arguments(entrypoint: list[str], command: list[str]) -> dict:
    """Only emit allowlisted backend/whitespace flags, no raw argv."""
    args = [*entrypoint, *command]
    if any(token in ("sh", "/bin/sh", "bash", "/bin/bash", "-c", "-lc")
           for token in args):
        return {
            "launch_metadata_status": "SHELL_WRAPPED_UNVERIFIED",
            "declared_backend": "UNVERIFIED",
            "effective_request_backend": "UNVERIFIED",
        }

    selected: list[str] = []
    whitespace_flags: list[str] = []
    for index, arg in enumerate(args):
        if arg == "--guided-decoding-backend":
            selected.append(args[index + 1] if index + 1 < len(args) else "")
        elif arg.startswith("--guided-decoding-backend="):
            selected.append(arg.partition("=")[2])
        elif arg in (
            "--guided-decoding-disable-any-whitespace",
            "--no-guided-decoding-disable-any-whitespace",
        ):
            whitespace_flags.append(arg)

    if len(selected) > 1 or (selected and selected[0] not in _ALLOWED_BACKENDS):
        declared = "INVALID_OR_AMBIGUOUS"
        status = "FLAG_UNVERIFIED"
    elif selected:
        declared = selected[0]
        status = "EXPLICIT_LAUNCH_FLAG_OBSERVED"
    else:
        declared = "NOT_DECLARED_DOCUMENTED_DEFAULT_AUTO"
        status = "LAUNCH_FLAG_ABSENT"

    if len(set(whitespace_flags)) > 1:
        whitespace = "AMBIGUOUS"
    elif whitespace_flags:
        whitespace = ("DISABLED" if whitespace_flags[0].startswith("--no-")
                      else "ENABLED")
    else:
        whitespace = "NOT_DECLARED_DOCUMENTED_DEFAULT_FALSE"
    return {
        "launch_metadata_status": status,
        "declared_backend": declared,
        "disable_any_whitespace_flag": whitespace,
        "effective_request_backend": "UNVERIFIED",
    }


def inspect_container_launch(container: str, *, sudo: bool = False) -> dict:
    if not isinstance(container, str) or not _CONTAINER.fullmatch(container):
        raise ValueError("INVALID_CONTAINER_NAME")
    observed = [_inspect_array(container, field, sudo) for field in _FORMATS]
    if any(item is None for item in observed):
        return {
            "launch_metadata_status": "DOCKER_INSPECT_UNAVAILABLE",
            "declared_backend": "UNVERIFIED",
            "effective_request_backend": "UNVERIFIED",
        }
    return parse_launch_arguments(observed[0], observed[1])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", help="Optional authorized Docker container")
    parser.add_argument("--sudo-docker", action="store_true",
                        help="Use only sudo -n docker inspect, without password prompts")
    args = parser.parse_args(argv)
    if args.sudo_docker and args.container is None:
        parser.error("--sudo-docker requires --container")
    result = {
        "status": "READ_ONLY_BACKEND_PREFLIGHT",
        "runtime_version_assumption": "vLLM 0.10.2; not verified by this script",
        "version_specific_backend_flag": "--guided-decoding-backend",
        "documented_default_backend": "auto",
        "schema": schema_report(),
        "container": (
            inspect_container_launch(args.container, sudo=args.sudo_docker)
            if args.container is not None else {
                "launch_metadata_status": "NOT_REQUESTED",
                "declared_backend": "UNVERIFIED",
                "effective_request_backend": "UNVERIFIED",
            }
        ),
        "raw_docker_command_logged": False,
        "container_environment_inspected": False,
        "container_processes_or_logs_inspected": False,
        "container_changed": False,
        "gpu_inference_requests": 0,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
