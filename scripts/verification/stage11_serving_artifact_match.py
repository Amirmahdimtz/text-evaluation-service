"""Stage11 owner-gated offline comparison of two approved local artifact folders.

Default mode prints a zero-access plan. --emit-runtime-script emits a
fixed Python child that reads only allowlisted configuration/tokenizer
files from two owner-supplied absolute folders. It compares bytes without
printing paths, file contents, identifiers or hashes. It cannot independently
verify the model, tokenizer or guided decoder selected by live vLLM.
"""
from __future__ import annotations

import argparse
import json


_RUNTIME = r'''"""Stage11 bounded local tokenizer file comparison; no model execution."""
import hashlib
import json
import os
import resource
import signal
import socket
import sys

ALLOWED_FILES = (
    "tokenizer.json", "tokenizer.model", "tokenizer_config.json",
    "special_tokens_map.json", "added_tokens.json",
    "vocab.json", "merges.txt", "chat_template.jinja",
)
CORE_FILES = ("tokenizer.json", "tokenizer.model", "vocab.json")
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 192 * 1024 * 1024


def _deny(*_args, **_kwargs):
    raise RuntimeError("STAGE11_NETWORK_DENIED")


def _stop(*_args):
    raise TimeoutError("STAGE11_LOCAL_ARTIFACT_BUDGET_EXCEEDED")


def _report(status, exit_code=0, **fields):
    result = {
        "status": status,
        "source_files_or_paths_emitted": False,
        "network_requests": 0,
        "gpu_model_execution": False,
        "model_inference_requests": 0,
        "effective_live_backend_verified": False,
        "live_served_artifact_provenance_verified": False,
        "model_weights_compared": False,
        "model_changed": False,
        "container_changed": False,
    }
    result.update(fields)
    print(json.dumps(result, sort_keys=True), flush=True)
    return exit_code


def _digest(path, budget):
    if not os.path.isfile(path):
        return None
    if os.path.getsize(path) > MAX_FILE_BYTES:
        raise ValueError("STAGE11_FILE_LIMIT")
    hasher = hashlib.sha256()
    size = 0
    with open(path, "rb") as stream:
        while True:
            chunk = stream.read(512 * 1024)
            if not chunk:
                break
            size += len(chunk)
            budget[0] += len(chunk)
            if size > MAX_FILE_BYTES or budget[0] > MAX_TOTAL_BYTES:
                raise ValueError("STAGE11_TOTAL_BYTES_LIMIT")
            hasher.update(chunk)
    return hasher.digest()


def main():
    # Never expose error messages, filenames, paths or stack traces.
    null_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null_fd, 2)
    finally:
        os.close(null_fd)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (15, 16))
    signal.signal(signal.SIGALRM, _stop)
    signal.signal(signal.SIGXCPU, _stop)
    signal.alarm(30)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    socket.socket = _deny
    socket.create_connection = _deny
    socket.getaddrinfo = _deny

    cached = os.environ.get("STAGE11_LOCAL_TOKENIZER_DIR", "")
    served = os.environ.get("STAGE11_OWNER_SERVED_ARTIFACT_DIR", "")
    if not (cached and served and os.path.isabs(cached)
            and os.path.isabs(served) and os.path.isdir(cached)
            and os.path.isdir(served)):
        return _report("OWNER_APPROVED_DIRECTORIES_NOT_CONFIGURED", 3)
    if os.path.realpath(cached) == os.path.realpath(served):
        return _report("SAME_DIRECTORY_NOT_INDEPENDENT_EVIDENCE", 3)

    try:
        budget = [0]
        config_cached = _digest(os.path.join(cached, "config.json"), budget)
        config_served = _digest(os.path.join(served, "config.json"), budget)
        if config_cached is None or config_served is None:
            return _report("CONFIG_FILE_MISSING", 3)
        config_match = config_cached == config_served
        tokenizer_matches = 0
        tokenizer_mismatches = 0
        tokenizer_present_one_side = 0
        core_matches = 0
        for name in ALLOWED_FILES:
            left = _digest(os.path.join(cached, name), budget)
            right = _digest(os.path.join(served, name), budget)
            if left is None and right is None:
                continue
            if left is None or right is None:
                tokenizer_present_one_side += 1
                continue
            if left != right:
                tokenizer_mismatches += 1
            else:
                tokenizer_matches += 1
                if name in CORE_FILES:
                    core_matches += 1

        all_tokenizer_files_match = (
            core_matches >= 1
            and tokenizer_mismatches == 0
            and tokenizer_present_one_side == 0
        )
        return _report(
            "OWNER_SUPPLIED_ARTIFACT_FILES_COMPARED", 0,
            local_config_files_match=config_match,
            local_tokenizer_files_all_match=all_tokenizer_files_match,
            tokenizer_files_matching_count=tokenizer_matches,
            tokenizer_files_different_count=tokenizer_mismatches,
            tokenizer_files_present_only_one_side_count=(
                tokenizer_present_one_side
            ),
            matched_core_tokenizer_files_count=core_matches,
            independent_served_runtime_attestation_required=True,
            owner_must_confirm_served_directory_from_trusted_deployment_record=True,
        )
    except TimeoutError:
        return _report("RESOURCE_BUDGET_EXCEEDED", 4)
    except Exception:
        return _report("LOCAL_ARTIFACT_COMPARE_FAILED", 3)


if __name__ == "__main__":
    try:
        result = main()
    except TimeoutError:
        result = _report("RESOURCE_BUDGET_EXCEEDED", 4)
    except Exception:
        result = _report("STAGE11_ARTIFACT_ATTESTATION_ABORTED", 3)
    sys.exit(result)
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emit-runtime-script", action="store_true",
        help="Emit, but do not execute, local read-only comparison code.",
    )
    args = parser.parse_args(argv)
    if args.emit_runtime_script:
        print(_RUNTIME, end="")
    else:
        print(json.dumps({
            "status": "OFFLINE_OWNER_ARTIFACT_ATTESTATION_PLAN",
            "container_execution_requires_owner_approval": True,
            "owner_must_supply_verified_served_artifact_directory": True,
            "matching_local_files_will_not_prove_live_serving_provenance": True,
            "effective_live_backend_verified": False,
            "network_requests": 0,
            "model_inference_requests": 0,
            "docker_commands": 0,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
