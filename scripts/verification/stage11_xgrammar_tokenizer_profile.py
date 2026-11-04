"""Stage11 CPU-only, owner-gated tokenizer-aware XGrammar investigation.

Default CLI emits an offline plan. Opt-in emits a self-contained runtime
program for a separate, approved read-only Docker exec. The program loads
ONLY an already-present local tokenizer, never model weights or model text.
It does not make network or inference requests, modify the serving process,
or measure GPU logit-mask application or effective backend selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

from src.infrastructure.providers.llm.structured_response import CriterionInference


_SCHEMA = CriterionInference.model_json_schema()
_SCHEMA_STRING = json.dumps(_SCHEMA, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
_SCHEMA_SHA256 = hashlib.sha256(_SCHEMA_STRING.encode("ascii")).hexdigest()

# A complete, deliberately synthetic abstention, never an actual evaluation.
_SYNTHETIC_OUTPUT: dict[str, Any] = {
    "criterion_code": "sample_code",
    "status": "not_assessed",
    "score": None,
    "reason": "Synthetic diagnostic only.",
    "strengths": [],
    "weaknesses": [],
    "recommendations": [],
    "evidence": [],
}
# Prove the fixture fits exactly the schema used for compilation.
CriterionInference.model_validate(_SYNTHETIC_OUTPUT)

_RUNTIME_TEMPLATE = r'''"""Stage11 generated CPU-only tokenizer grammar diagnostic. No inference."""
import importlib.metadata
import json
import os
import resource
import signal
import socket
import sys
import time
import warnings

SCHEMA_JSON = __SCHEMA_JSON__
SCHEMA_SHA256 = __SCHEMA_SHA256__
SYNTHETIC_OUTPUT_JSON = __SYNTHETIC_OUTPUT_JSON__
MAX_STEPS = 24
MAX_CPU_SECONDS = 25
MAX_WALL_SECONDS = 45


def _report(status, *, exit_code, **fields):
    fixed = {
        "status": status,
        "schema_sha256": SCHEMA_SHA256,
        "model_inference_requests": 0,
        "network_requests": 0,
        "gpu_model_execution": False,
        "effective_live_backend_verified": False,
        "real_request_latency_measured": False,
        "gpu_token_mask_application_measured": False,
        "shared_service_cache_measured": False,
    }
    fixed.update(fields)
    print(json.dumps(fixed, sort_keys=True), flush=True)
    return exit_code


def _deny_network(*_args, **_kwargs):
    raise RuntimeError("STAGE11_NETWORK_DENIED")


class _NetworkDeniedSocket(socket.socket):
    """Remain subclassable for ssl and transformers while denying egress.

    A plain function in socket.socket breaks modules which inherit from
    that class at import time. Network operations are still prohibited.
    """

    def connect(self, *_args, **_kwargs):
        _deny_network()

    def connect_ex(self, *_args, **_kwargs):
        _deny_network()

    def sendto(self, *_args, **_kwargs):
        _deny_network()

    def sendmsg(self, *_args, **_kwargs):
        _deny_network()

    def send(self, *_args, **_kwargs):
        _deny_network()

    def sendall(self, *_args, **_kwargs):
        _deny_network()


def _stop(_signal, _frame):
    raise TimeoutError("STAGE11_RESOURCE_LIMIT")


def _elapsed_ms(start):
    return round((time.perf_counter() - start) * 1000.0, 3)


def _mask_fill_distribution(fill_ms):
    """Compare first-use cost with subsequent synthetic mask fills.

    Values are rounded observations, not latency estimates for live
    inference. P95 uses nearest-rank and at most 23 later samples.
    """
    if len(fill_ms) < 2:
        return None
    rest = fill_ms[1:]
    ordered = sorted(rest)
    n = len(rest)
    median = (ordered[(n - 1) // 2] + ordered[n // 2]) / 2
    total = sum(fill_ms)
    return {
        "cpu_synthetic_mask_fill_first_ms": fill_ms[0],
        "cpu_synthetic_mask_fill_first_share_percent": (
            round(100 * fill_ms[0] / total, 2) if total else None
        ),
        "cpu_synthetic_mask_fill_rest_steps": n,
        "cpu_synthetic_mask_fill_rest_total_ms": round(sum(rest), 3),
        "cpu_synthetic_mask_fill_rest_mean_ms": round(sum(rest) / n, 3),
        "cpu_synthetic_mask_fill_rest_median_ms": round(median, 3),
        "cpu_synthetic_mask_fill_rest_p95_nearest_rank_ms": (
            ordered[(95 * n + 99) // 100 - 1]
        ),
        "cpu_synthetic_mask_fill_rest_max_ms": ordered[-1],
    }


def main():
    # This is an ephemeral child process, not the running vLLM engine.
    # Suppress libraries' warnings and exceptions to protect local paths.
    null_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null_fd, 2)
    finally:
        os.close(null_fd)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_SECONDS, MAX_CPU_SECONDS + 1))
    signal.signal(signal.SIGXCPU, _stop)
    signal.signal(signal.SIGALRM, _stop)
    signal.alarm(MAX_WALL_SECONDS)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    socket.socket = _NetworkDeniedSocket
    socket.create_connection = _deny_network
    socket.getaddrinfo = _deny_network
    warnings.simplefilter("ignore")

    tokenizer_dir = os.environ.get("STAGE11_LOCAL_TOKENIZER_DIR", "")
    if not (tokenizer_dir and os.path.isabs(tokenizer_dir)
            and os.path.isdir(tokenizer_dir)
            and os.path.isfile(os.path.join(tokenizer_dir, "config.json"))):
        return _report("LOCAL_TOKENIZER_DIRECTORY_NOT_CONFIGURED", exit_code=3)
    try:
        versions = {
            name: importlib.metadata.version(name)
            for name in ("vllm", "xgrammar")
        }
    except importlib.metadata.PackageNotFoundError:
        return _report("RUNTIME_PACKAGES_UNAVAILABLE", exit_code=3)
    if versions != {"vllm": "0.10.2", "xgrammar": "0.1.23"}:
        return _report("UNVERIFIED_RUNTIME_VERSION", exit_code=3,
                       versions=versions)

    try:
        import xgrammar as xgr
    except Exception:
        return _report("XGRAMMAR_IMPORT_FAILED", exit_code=3,
                       versions=versions)
    try:
        from transformers import AutoConfig, AutoTokenizer
    except Exception:
        return _report("TRANSFORMERS_IMPORT_FAILED", exit_code=3,
                       versions=versions)

    try:
        start = time.perf_counter()
        config = AutoConfig.from_pretrained(
            tokenizer_dir, local_files_only=True, trust_remote_code=False)
        vocab_size = getattr(config, "vocab_size", None)
        if type(vocab_size) is not int or not 256 <= vocab_size <= 500_000:
            return _report("MODEL_VOCAB_SIZE_UNVERIFIED", exit_code=3,
                           versions=versions)
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_dir, local_files_only=True, trust_remote_code=False,
            use_fast=True)
        tokenizer_load_ms = _elapsed_ms(start)
    except TimeoutError:
        return _report("RESOURCE_BUDGET_EXCEEDED", exit_code=4,
                       versions=versions)
    except Exception:
        return _report("LOCAL_TOKENIZER_LOAD_FAILED", exit_code=3,
                       versions=versions)

    try:
        start = time.perf_counter()
        info = xgr.TokenizerInfo.from_huggingface(
            tokenizer, vocab_size=vocab_size)
        tokenizer_info_ms = _elapsed_ms(start)
        start = time.perf_counter()
        compiler = xgr.GrammarCompiler(
            info, max_threads=1, cache_enabled=True,
            cache_limit_bytes=32 * 1024 * 1024)
        compiler_init_ms = _elapsed_ms(start)
        start = time.perf_counter()
        compiled = compiler.compile_json_schema(SCHEMA_JSON, any_whitespace=True)
        compile_cold_ms = _elapsed_ms(start)
        start = time.perf_counter()
        compiler.compile_json_schema(SCHEMA_JSON, any_whitespace=True)
        compile_warm_ms = _elapsed_ms(start)
    except TimeoutError:
        return _report("RESOURCE_BUDGET_EXCEEDED", exit_code=4,
                       versions=versions)
    except Exception:
        return _report("TOKENIZER_GRAMMAR_COMPILE_FAILED", exit_code=2,
                       versions=versions)

    try:
        matcher = xgr.GrammarMatcher(compiled)
        bitmask = xgr.allocate_token_bitmask(1, vocab_size)
        # No prompt or model output. Token IDs come from one fixed synthetic JSON.
        ids = tokenizer.encode(SYNTHETIC_OUTPUT_JSON, add_special_tokens=False)
        if not isinstance(ids, list) or not ids or not all(
                type(token) is int and 0 <= token < vocab_size for token in ids):
            return _report("SYNTHETIC_TOKENIZATION_UNVERIFIED", exit_code=2,
                           versions=versions)
        fill_ms = []
        accept_ms = []
        for token in ids[:MAX_STEPS]:
            start = time.perf_counter()
            matcher.fill_next_token_bitmask(bitmask, 0)
            fill_ms.append(_elapsed_ms(start))
            start = time.perf_counter()
            accepted = matcher.accept_token(token)
            accept_ms.append(_elapsed_ms(start))
            if not accepted:
                return _report("SYNTHETIC_GRAMMAR_TOKEN_REJECTED", exit_code=2,
                               versions=versions)
        distribution = _mask_fill_distribution(fill_ms)
        if distribution is None:
            return _report("SYNTHETIC_MASK_STEPS_INSUFFICIENT", exit_code=2,
                           versions=versions)
    except TimeoutError:
        return _report("RESOURCE_BUDGET_EXCEEDED", exit_code=4,
                       versions=versions)
    except Exception:
        return _report("SYNTHETIC_MASK_BENCHMARK_FAILED", exit_code=2,
                       versions=versions)

    return _report(
        "CPU_TOKENIZER_GRAMMAR_PROFILE_OBSERVED", exit_code=0,
        versions=versions, vocab_size=vocab_size,
        tokenizer_load_ms=tokenizer_load_ms,
        tokenizer_info_ms=tokenizer_info_ms,
        compiler_init_ms=compiler_init_ms,
        compile_cold_ms=compile_cold_ms,
        compile_warm_ms=compile_warm_ms,
        cpu_synthetic_mask_fill_steps=len(fill_ms),
        cpu_synthetic_mask_fill_total_ms=round(sum(fill_ms), 3),
        cpu_synthetic_mask_fill_max_ms=round(max(fill_ms), 3),
        **distribution,
        cpu_synthetic_token_accept_total_ms=round(sum(accept_ms), 3),
        tokenizer_aware_compilation_measured=True,
        cpu_synthetic_mask_fill_measured=True,
        compiler_thread_limit=1,
        grammar_cache_limit_mib=32,
        caveat="ISOLATED_CHILD_PROCESS_NOT_LIVE_VLLM_REQUEST",
    )


if __name__ == "__main__":
    try:
        result = main()
    except TimeoutError:
        result = _report("RESOURCE_BUDGET_EXCEEDED", exit_code=4)
    except Exception:
        result = _report("STAGE11_PROFILE_ABORTED", exit_code=2)
    sys.exit(result)
'''


def offline_report() -> dict[str, Any]:
    return {
        "status": "OFFLINE_TOKENIZER_PROFILE_PLAN",
        "schema_sha256": _SCHEMA_SHA256,
        "synthetic_fixture_contract": "VALIDATED_BY_PYDANTIC",
        "live_tokenizer_loaded": False,
        "tokenizer_aware_compilation_measured": False,
        "cpu_token_mask_fill_measured": False,
        "gpu_token_mask_application_measured": False,
        "live_backend_verified": False,
        "model_inference_requests": 0,
        "network_requests": 0,
        "docker_commands": 0,
        "container_execution_requires_owner_approval": True,
        "requires_existing_local_tokenizer_dir": True,
    }


def build_runtime_script() -> str:
    """Return static operator-reviewed code, not shell commands or actions."""
    sample_properties = json.loads(_SCHEMA_STRING)["properties"]
    sample = json.dumps(
        {key: _SYNTHETIC_OUTPUT[key] for key in sample_properties},
        ensure_ascii=True, separators=(",", ":"),
    )
    return (
        _RUNTIME_TEMPLATE
        .replace("__SCHEMA_JSON__", repr(_SCHEMA_STRING))
        .replace("__SCHEMA_SHA256__", repr(_SCHEMA_SHA256))
        .replace("__SYNTHETIC_OUTPUT_JSON__", repr(sample))
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-runtime-script", action="store_true",
                        help="Emit opt-in CPU-only child script, no execution.")
    args = parser.parse_args(argv)
    if args.emit_runtime_script:
        print(build_runtime_script(), end="")
    else:
        print(json.dumps(offline_report(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
