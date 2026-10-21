"""Validate Stage 03 synthetic/authorized model outputs without disclosing text.

This standalone CLI verifies JSON structure and original-source quote offsets.
It does not verify factual relevance, expert agreement, or model quality.
Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import json
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
MAX_LINE_BYTES = 10 * 1024 * 1024


def validate_record(record: Any) -> list[str]:
    """Return safe machine-readable errors; never return source text."""
    if not isinstance(record, dict):
        return ["INVALID_RECORD"]
    for name in ("run_id", "attempt_id", "case_id", "model_id"):
        if not isinstance(record.get(name), str) or not record[name].strip():
            return ["INVALID_IDENTIFIERS"]
    if record.get("rubric_version") != "candidate-0.1":
        return ["INVALID_RUBRIC_VERSION"]
    domain = record.get("domain")
    if not isinstance(domain, str) or domain not in CRITERIA:
        return ["INVALID_DOMAIN"]
    original = record.get("original_text")
    if not isinstance(original, str) or not original.strip():
        return ["INVALID_ORIGINAL_TEXT"]
    result = record.get("output")
    if not isinstance(result, dict) or result.keys() != RESPONSE_FIELDS:
        return ["INVALID_SCHEMA"]
    errors: list[str] = []
    if (not isinstance(result["criterion_code"], str)
            or result["criterion_code"] not in CRITERIA[domain]):
        errors.append("INVALID_CRITERION")
    status = result["status"]
    score = result["score"]
    if status == "assessed":
        if type(score) is not int or not 0 <= score <= 5:
            errors.append("INVALID_SCORE")
    elif status == "not_assessed":
        if score is not None:
            errors.append("INVALID_ABSTENTION")
    else:
        errors.append("INVALID_STATUS")
    if not isinstance(result["reason"], str) or not result["reason"].strip():
        errors.append("INVALID_REASON")
    for field in ("strengths", "weaknesses", "recommendations"):
        value = result[field]
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
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


def inspect_file(path: Path) -> tuple[int, int, Counter[str]]:
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
            try:
                record = json.loads(line.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                invalid += 1
                failures["INVALID_JSON"] += 1
                continue
            errors = validate_record(record)
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
                failures.update(errors)
    return total, invalid, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="Approved local JSONL. Raw source text stays on host.")
    args = parser.parse_args(argv)
    try:
        total, invalid, failures = inspect_file(args.input)
    except OSError:
        print(json.dumps({"status": "FAIL", "error": "INPUT_IO_ERROR"}))
        return 2
    result = {
        "status": "PASS" if total and not invalid else "FAIL",
        "records": total,
        "valid": total - invalid,
        "invalid": invalid,
        "error_counts": dict(sorted(failures.items())),
        "scope": "structure_and_exact_source_offsets_only; NOT_AI_QUALITY",
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if total and not invalid else 1


if __name__ == "__main__":
    sys.exit(main())
