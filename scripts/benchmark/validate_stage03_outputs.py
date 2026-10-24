"""Validate Stage 03 outputs without exposing source text.

This offline validator checks JSON structure, exact original-source offsets, and,
when a manifest is supplied, case/domain/source-hash consistency. It cannot
certify dataset authorization, evidence relevance, or model quality.
Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


CRITERIA = {
    "speech": frozenset({
        "speech_coherence", "speech_structure", "speech_clarity",
        "speech_writing", "speech_reasoning", "speech_audience_fit",
    }),
    "media": frozenset({
        "media_tone", "media_message_clarity", "media_writing",
        "media_structure", "media_audience_focus", "media_text_effectiveness",
    }),
    "research": frozenset({
        "research_coherence", "research_methodology", "research_reasoning",
        "research_academic_writing", "research_citations", "research_novelty",
    }),
}
RESPONSE_FIELDS = frozenset({
    "criterion_code", "status", "score", "reason", "strengths",
    "weaknesses", "recommendations", "evidence",
})
EVIDENCE_FIELDS = frozenset({
    "source_kind", "quote", "start_offset", "end_offset",
})
MANIFEST_FIELDS = frozenset({
    "dataset_id", "dataset_version", "case_id", "group_id", "domain",
    "source_classification", "provenance", "license_permission", "language",
    "length_bucket", "quality_bucket", "edge_case_tags", "split",
    "source_sha256", "expert_labels_revision",
})
SYNTHETIC_CASE_DOMAINS = {
    **{f"SP-{n:02}": "speech" for n in range(1, 5)},
    **{f"ME-{n:02}": "media" for n in range(1, 5)},
    **{f"RE-{n:02}": "research" for n in range(1, 5)},
}
MAX_LINE_BYTES = 10 * 1024 * 1024
MAX_RECORDS = 100_000  # Limit per-invocation tracking memory; not a quality threshold.


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ValueError("non-standard JSON constant")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("non-finite JSON number")
    return parsed


def strict_json_loads(data: bytes) -> Any:
    """Reject duplicate keys, NaN/Infinity, malformed UTF-8 and deep nesting."""
    return json.loads(
        data.decode("utf-8"), object_pairs_hook=_unique_object,
        parse_constant=_reject_constant, parse_float=_finite_float,
    )


def _valid_text(value: Any) -> bool:
    """Require nonempty, valid UTF-8 text without lone surrogate escapes."""
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def validate_record(record: Any) -> list[str]:
    """Return safe machine-readable errors; never return source text."""
    if not isinstance(record, dict):
        return ["INVALID_RECORD"]
    for name in ("run_id", "attempt_id", "case_id", "model_id"):
        if not _valid_text(record.get(name)):
            return ["INVALID_IDENTIFIERS"]
    if record.get("rubric_version") != "candidate-0.1":
        return ["INVALID_RUBRIC_VERSION"]
    domain = record.get("domain")
    if not isinstance(domain, str) or domain not in CRITERIA:
        return ["INVALID_DOMAIN"]
    original = record.get("original_text")
    if not _valid_text(original):
        return ["INVALID_ORIGINAL_TEXT"]
    result = record.get("output")
    if not isinstance(result, dict) or result.keys() != RESPONSE_FIELDS:
        return ["INVALID_SCHEMA"]
    errors: list[str] = []
    expected_domain = SYNTHETIC_CASE_DOMAINS.get(record["case_id"])
    if expected_domain is not None and domain != expected_domain:
        errors.append("INVALID_CASE_DOMAIN")
    if (not isinstance(result["criterion_code"], str)
            or result["criterion_code"] not in CRITERIA[domain]):
        errors.append("INVALID_CRITERION")
    status = result["status"]
    score = result["score"]
    if status == "assessed":
        if type(score) is not int or not 0 <= score <= 5:
            errors.append("INVALID_SCORE")
        if result["criterion_code"] == "research_novelty":
            # Source-text quotes cannot prove novelty without validated corpus.
            errors.append("UNVERIFIABLE_NOVELTY")
    elif status == "not_assessed":
        if score is not None:
            errors.append("INVALID_ABSTENTION")
    else:
        errors.append("INVALID_STATUS")
    if not _valid_text(result["reason"]):
        errors.append("INVALID_REASON")
    for field in ("strengths", "weaknesses", "recommendations"):
        value = result[field]
        if not isinstance(value, list) or any(
            not _valid_text(item) for item in value
        ):
            errors.append("INVALID_" + field.upper())
    evidence = result["evidence"]
    if not isinstance(evidence, list):
        errors.append("INVALID_EVIDENCE")
        return errors
    if status == "assessed" and not evidence:
        errors.append("MISSING_EVIDENCE")
    if status == "not_assessed" and evidence:
        errors.append("EVIDENCE_WITH_ABSTENTION")
    for item in evidence:
        if not isinstance(item, dict):
            errors.append("INVALID_EVIDENCE")
            continue
        if item.get("source_kind") != "original_submission":
            # Corpus evidence requires a separate approved corpus/provenance validator.
            errors.append("UNVERIFIABLE_SOURCE")
            continue
        if item.keys() != EVIDENCE_FIELDS:
            errors.append("INVALID_EVIDENCE_SCHEMA")
            continue
        start, end, quote = item["start_offset"], item["end_offset"], item["quote"]
        if (type(start) is not int or type(end) is not int
                or not isinstance(quote, str) or not quote
                or not (0 <= start < end <= len(original))
                or original[start:end] != quote):
            errors.append("QUOTE_MISMATCH")
    return sorted(set(errors))


def load_manifest(path: Path) -> dict[str, tuple[str, str]]:
    """Index versioned case metadata; never treat it as legal approval."""
    cases: dict[str, tuple[str, str]] = {}
    dataset_identity: tuple[str, str] | None = None
    group_splits: dict[str, str] = {}
    source_splits: dict[str, str] = {}
    with path.open("rb") as stream:
        while True:
            line = stream.readline(MAX_LINE_BYTES + 1)
            if not line:
                break
            if len(line) > MAX_LINE_BYTES or len(cases) >= MAX_RECORDS:
                raise ValueError("manifest safety limit exceeded")
            try:
                entry = strict_json_loads(line)
            except (ValueError, UnicodeDecodeError, RecursionError) as exc:
                raise ValueError("invalid manifest JSON") from exc
            if not isinstance(entry, dict) or entry.keys() != MANIFEST_FIELDS:
                raise ValueError("invalid manifest schema")
            if (any(not _valid_text(entry[field])
                    for field in MANIFEST_FIELDS - {
                        "edge_case_tags", "expert_labels_revision",
                    })
                    or not isinstance(entry["edge_case_tags"], list)
                    or any(not _valid_text(tag) for tag in entry["edge_case_tags"])
                    or (entry["expert_labels_revision"] is not None
                        and not _valid_text(entry["expert_labels_revision"]))
                    or entry["domain"] not in CRITERIA
                    or entry["split"] not in {"development", "calibration", "holdout"}
                    or re.fullmatch(r"[0-9a-fA-F]{64}", entry["source_sha256"]) is None
                    or entry["case_id"] in cases):
                raise ValueError("invalid manifest values")
            identity = (entry["dataset_id"], entry["dataset_version"])
            group_id, split = entry["group_id"], entry["split"]
            source_hash = entry["source_sha256"].lower()
            if (dataset_identity is not None and dataset_identity != identity
                    or group_id in group_splits and group_splits[group_id] != split
                    or source_hash in source_splits and source_splits[source_hash] != split):
                raise ValueError("mixed manifest dataset or split leakage")
            dataset_identity = identity
            group_splits[group_id] = split
            source_splits[source_hash] = split
            cases[entry["case_id"]] = (
                entry["domain"], entry["source_sha256"].lower(),
            )
    if not cases:
        raise ValueError("empty manifest")
    return cases


def inspect_file(
    path: Path, manifest: dict[str, tuple[str, str]] | None = None,
) -> tuple[int, int, Counter[str]]:
    total = invalid = 0
    failures: Counter[str] = Counter()
    seen: set[tuple[str, str, str, str]] = set()
    with path.open("rb") as stream:
        while True:
            line = stream.readline(MAX_LINE_BYTES + 1)
            if not line:
                break
            total += 1
            if len(line) > MAX_LINE_BYTES:
                invalid += 1
                failures["OVERSIZED_RECORD"] += 1
                break  # Do not parse partial lines or allocate beyond the safety cap.
            if total > MAX_RECORDS:
                invalid += 1
                failures["RECORD_LIMIT_EXCEEDED"] += 1
                break  # Fail closed; remaining attempts are not counted.
            try:
                record = strict_json_loads(line)
            except (ValueError, UnicodeDecodeError, RecursionError):
                invalid += 1
                failures["INVALID_JSON"] += 1
                continue
            errors = validate_record(record)
            if manifest is not None and isinstance(record, dict):
                case_id = record.get("case_id")
                known = manifest.get(case_id) if isinstance(case_id, str) else None
                if known is None:
                    errors.append("CASE_NOT_IN_MANIFEST")
                elif known[0] != record.get("domain"):
                    errors.append("MANIFEST_DOMAIN_MISMATCH")
                elif (not isinstance(record.get("original_text"), str)
                      or "INVALID_ORIGINAL_TEXT" in errors
                      or hashlib.sha256(record["original_text"].encode("utf-8")).hexdigest()
                      != known[1]):
                    errors.append("MANIFEST_SOURCE_MISMATCH")
            if not errors:
                key = (
                    record["run_id"], record["model_id"],
                    record["case_id"] + ":" + record["output"]["criterion_code"],
                    record["attempt_id"],
                )
                if key in seen:
                    errors = ["DUPLICATE_ATTEMPT"]
                else:
                    seen.add(key)
            if errors:
                invalid += 1
                failures.update(set(errors))
    return total, invalid, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="Approved local JSONL. Raw source text stays on host.")
    parser.add_argument("--manifest", type=Path,
                        help="Optional approved case manifest JSONL; checks case, domain and SHA-256.")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest) if args.manifest else None
    except OSError:
        print(json.dumps({"status": "FAIL", "error": "MANIFEST_IO_ERROR"}))
        return 2
    except ValueError:
        print(json.dumps({"status": "FAIL", "error": "INVALID_MANIFEST"}))
        return 2
    try:
        total, invalid, failures = inspect_file(args.input, manifest)
    except OSError:
        print(json.dumps({"status": "FAIL", "error": "INPUT_IO_ERROR"}))
        return 2
    result = {
        "status": "PASS" if total and not invalid else "FAIL",
        "records": total,
        "valid": total - invalid,
        "invalid": invalid,
        "error_counts": dict(sorted(failures.items())),
        "manifest_check": "STRUCTURE_AND_SOURCE_HASH" if manifest is not None else "NOT_PROVIDED",
        "scope": "structure_and_exact_source_offsets_only; NOT_AI_QUALITY_OR_AUTHORIZATION",
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if total and not invalid else 1


if __name__ == "__main__":
    sys.exit(main())
