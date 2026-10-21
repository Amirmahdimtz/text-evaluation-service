"""Synthetic, offline unit tests for the Stage 03 result validator."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_stage03_outputs import inspect_file, validate_record


def record() -> dict:
    return {
        "run_id": "run-synthetic", "attempt_id": "1", "case_id": "SP-01",
        "model_id": "local-test-only", "domain": "speech",
        "rubric_version": "candidate-0.1", "original_text": "متن نمونه‌ی فارسی است.",
        "output": {
            "criterion_code": "speech_clarity", "status": "assessed",
            "score": 4, "reason": "Clear short text.",
            "strengths": [], "weaknesses": [], "recommendations": [],
            "evidence": [{
                "source_kind": "original_submission", "quote": "متن",
                "start_offset": 0, "end_offset": 3,
            }],
        },
    }


class ValidatorTests(unittest.TestCase):
    def test_valid_unicode_source_span(self):
        self.assertEqual(validate_record(record()), [])

    def test_score_is_not_bool(self):
        value = record()
        value["output"]["score"] = True
        self.assertIn("INVALID_SCORE", validate_record(value))

    def test_invalid_zwnj_offset(self):
        value = record()
        value["output"]["evidence"][0]["end_offset"] = 4
        self.assertIn("QUOTE_MISMATCH", validate_record(value))

    def test_not_assessed_requires_null_and_no_evidence(self):
        value = record()
        value["output"]["status"] = "not_assessed"
        self.assertIn("INVALID_ABSTENTION", validate_record(value))
        self.assertIn("EVIDENCE_WITH_ABSTENTION", validate_record(value))
        value["output"]["score"] = None
        value["output"]["evidence"] = []
        self.assertEqual(validate_record(value), [])

    def test_unknown_code(self):
        value = record()
        value["output"]["criterion_code"] = "research_novelty"
        self.assertIn("INVALID_CRITERION", validate_record(value))

    def test_unhashable_criterion_is_rejected(self):
        value = record()
        value["output"]["criterion_code"] = {"nested": "bad"}
        self.assertIn("INVALID_CRITERION", validate_record(value))

    def test_corpus_requires_external_validation(self):
        value = record()
        value["output"]["evidence"][0]["source_kind"] = "approved_reference_corpus"
        self.assertIn("UNVERIFIABLE_SOURCE", validate_record(value))

    def test_invalid_extra_result_key(self):
        value = record()
        value["output"]["final_score"] = 99
        self.assertIn("INVALID_SCHEMA", validate_record(value))

    def test_zero_records_is_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "empty.jsonl"
            file.write_text("", encoding="utf-8")
            self.assertEqual(inspect_file(file)[0], 0)

    def test_duplicate_attempt_detected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cases.jsonl"
            line = json.dumps(record(), ensure_ascii=False) + "\n"
            path.write_text(line + line, encoding="utf-8")
            total, invalid, errors = inspect_file(path)
            self.assertEqual((total, invalid, errors["DUPLICATE_ATTEMPT"]), (2, 1, 1))

    def test_invalid_json_is_sanitized(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cases.jsonl"
            path.write_bytes(b"{secret\n")
            total, invalid, errors = inspect_file(path)
            self.assertEqual((total, invalid, errors["INVALID_JSON"]), (1, 1, 1))


if __name__ == "__main__":
    unittest.main()
