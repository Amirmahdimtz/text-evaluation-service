"""Stage11: measure XGrammar's schema-to-grammar conversion without inference.

Default mode reports safe static schema facts. --emit-runtime-script prints a
self-contained, bounded, synthetic-free Python program intended for piping to
an explicitly authorized existing local vLLM container's Python on stdin.
No Docker or network calls, model/tokenizer loading, GPU operations, or files
are performed by this script. Only JSON Schema generated from code is sent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

from src.infrastructure.providers.llm.structured_response import CriterionInference


def _canonical_schema() -> tuple[dict[str, Any], str, str]:
    schema = CriterionInference.model_json_schema()
    encoded = json.dumps(schema, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return schema, encoded, hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _conflict_count(value: object) -> int:
    """Find combinations not jointly enforced in observed XGrammar 0.1.23."""
    if isinstance(value, list):
        return sum(_conflict_count(item) for item in value)
    if isinstance(value, dict):
        overlap = (
            value.get("type") == "string"
            and "pattern" in value
            and any(k in value for k in ("minLength", "maxLength", "format"))
        )
        return int(overlap) + sum(_conflict_count(v) for v in value.values())
    return 0


def offline_report() -> dict[str, Any]:
    schema, _, digest = _canonical_schema()
    return {
        "status": "OFFLINE_GRAMMAR_CONVERSION_PREFLIGHT",
        "schema_sha256": digest,
        "pattern_with_length_or_format_count": _conflict_count(schema),
        "compatibility_note": "XGRAMMAR_MAY_IGNORE_COMBINED_STRING_CONSTRAINTS",
        "source": "CriterionInference.model_json_schema",
        "cpu_conversion_measured": False,
        "tokenizer_aware_compilation_measured": False,
        "per_token_masking_measured": False,
        "request_latency_measured": False,
        "model_inference_requests": 0,
        "network_requests": 0,
        "docker_commands": 0,
    }


def build_runtime_script() -> str:
    """Embed only the current application JSON Schema in a no-inference probe.

    A runtime probe measures Grammar.from_json_schema only; it intentionally
    does not claim to measure the tokenizer-aware vLLM GrammarCompiler or
    per-token bitmask generation/application. No arbitrary user input is used.
    """
    _, encoded, digest = _canonical_schema()
    # The embedded JSON schema is code-defined, contains no user text, and
    # is sent on stdin rather than as process arguments or an on-disk file.
    return f'''"""Generated Stage11 XGrammar CPU-only schema conversion check."""
import importlib.metadata
import json
import time

SCHEMA = json.loads({encoded!r})
SCHEMA_SHA256 = {digest!r}


def package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "UNAVAILABLE"


def main():
    versions = {{name: package_version(name) for name in ("vllm", "xgrammar")}}
    try:
        import xgrammar as xgr
    except Exception:
        print(json.dumps({{
            "status": "XGRAMMAR_IMPORT_UNAVAILABLE", "versions": versions,
            "schema_sha256": SCHEMA_SHA256, "model_inference_requests": 0,
        }}, sort_keys=True))
        return 3
    timings_ms = []
    for _ in range(2):
        start = time.perf_counter()
        try:
            xgr.Grammar.from_json_schema(SCHEMA)
        except Exception:
            print(json.dumps({{
                "status": "XGRAMMAR_CONVERSION_FAILED", "versions": versions,
                "schema_sha256": SCHEMA_SHA256, "model_inference_requests": 0,
            }}, sort_keys=True))
            return 2
        timings_ms.append(round((time.perf_counter() - start) * 1000, 3))
    print(json.dumps({{
        "status": "CPU_GRAMMAR_CONVERSION_OBSERVED",
        "versions": versions, "schema_sha256": SCHEMA_SHA256,
        "conversion_ms_first": timings_ms[0],
        "conversion_ms_second": timings_ms[1],
        "runs": 2,
        "tokenizer_aware_compilation_measured": False,
        "per_token_masking_measured": False,
        "request_latency_measured": False,
        "model_inference_requests": 0,
    }}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emit-runtime-script", action="store_true",
        help="Print only an audited CPU-only Python script for stdin execution.",
    )
    args = parser.parse_args(argv)
    if args.emit_runtime_script:
        print(build_runtime_script(), end="")
    else:
        print(json.dumps(offline_report(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
