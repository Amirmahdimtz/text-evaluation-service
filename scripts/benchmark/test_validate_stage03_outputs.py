"""Synthetic, offline unit tests for the Stage 03 result validator."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from validate_stage03_outputs import inspect_file, load_manifest, main, validate_record


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



def manifest_record(value: dict | None = None) -> dict:
    value = value or record()
    return {
        "dataset_id": "synthetic-set", "dataset_version": "v1",
        "case_id": value["case_id"], "group_id": "group1",
        "domain": value["domain"], "source_classification": "synthetic",
        "provenance": "manually written synthetic fixture",
        "license_permission": "synthetic test fixture only",
        "language": "fa", "length_bucket": "short", "quality_bucket": "mid",
        "edge_case_tags": ["unicode"], "split": "development",
        "source_sha256": hashlib.sha256(value["original_text"].encode("utf-8")).hexdigest(),
        "expert_labels_revision": None,
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


    def test_reject_duplicate_json_keys_top_level_and_nested(self):
        sample = json.dumps(record(), ensure_ascii=False)
        top = sample.replace('"run_id":', '"run_id":"unexpected","run_id":', 1)
        nested = sample.replace('"score": 4', '"score": 2,"score": 4', 1)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "invalid.jsonl"
            path.write_text(top + "\n" + nested + "\n", encoding="utf-8")
            self.assertEqual(inspect_file(path)[2]["INVALID_JSON"], 2)

    def test_reject_nan_and_infinity(self):
        sample = json.dumps(record(), ensure_ascii=False)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "invalid.jsonl"
            cases = [sample.replace('"score": 4', f'"score": {constant}', 1)
                     for constant in ("NaN", "Infinity", "-Infinity")]
            path.write_text("\n".join(cases) + "\n", encoding="utf-8")
            self.assertEqual(inspect_file(path)[2]["INVALID_JSON"], 3)

    def test_reject_float_overflow(self):
        sample = json.dumps(record(), ensure_ascii=False)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "invalid.jsonl"
            path.write_text(sample.replace('"score": 4', '"score": 1e9999') + "\n", encoding="utf-8")
            self.assertEqual(inspect_file(path)[2]["INVALID_JSON"], 1)

    def test_deeply_nested_input_is_caught_without_crash(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "deep.jsonl"
            path.write_bytes(("[" * 20000 + "0" + "]" * 20000 + "\n").encode())
            self.assertEqual(inspect_file(path)[:2], (1, 1))
            self.assertEqual(inspect_file(path)[2]["INVALID_JSON"], 1)

    def test_invalid_and_valid_record_continuity(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mixed.jsonl"
            path.write_text("NaN\n" + json.dumps(record(), ensure_ascii=False) + "\n", encoding="utf-8")
            self.assertEqual(inspect_file(path)[:2], (2, 1))

    def test_surrogate_original_text_rejected(self):
        value = record()
        value["original_text"] = "\ud800"
        self.assertIn("INVALID_ORIGINAL_TEXT", validate_record(value))

    def test_reject_wrong_domain_for_known_synthetic_case(self):
        value = record()
        value["case_id"] = "RE-01"
        self.assertIn("INVALID_CASE_DOMAIN", validate_record(value))

    def test_unknown_case_is_structural_only_without_manifest(self):
        value = record()
        value["case_id"] = "custom-dataset-item"
        self.assertEqual(validate_record(value), [])

    def test_research_novelty_assessed_is_unverifiable(self):
        value = record()
        value["case_id"] = "RE-01"
        value["domain"] = "research"
        value["output"]["criterion_code"] = "research_novelty"
        self.assertIn("UNVERIFIABLE_NOVELTY", validate_record(value))

    def test_research_novelty_abstention_is_valid(self):
        value = record()
        value["case_id"] = "RE-01"
        value["domain"] = "research"
        value["output"]["criterion_code"] = "research_novelty"
        value["output"]["status"] = "not_assessed"
        value["output"]["score"] = None
        value["output"]["evidence"] = []
        self.assertEqual(validate_record(value), [])

    def test_manifest_matches_source_text_and_case_domain(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "manifest.jsonl").write_text(json.dumps(manifest_record()) + "\n", encoding="utf-8")
            (root / "result.jsonl").write_text(json.dumps(record(), ensure_ascii=False) + "\n", encoding="utf-8")
            manifest = load_manifest(root / "manifest.jsonl")
            self.assertEqual(inspect_file(root / "result.jsonl", manifest)[:2], (1, 0))

    def test_manifest_rejects_hash_mismatch_and_domain_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            value = record()
            (root / "manifest.jsonl").write_text(json.dumps(manifest_record()) + "\n", encoding="utf-8")
            manifest = load_manifest(root / "manifest.jsonl")
            value["original_text"] = "different text"
            (root / "result.jsonl").write_text(json.dumps(value) + "\n", encoding="utf-8")
            self.assertEqual(inspect_file(root / "result.jsonl", manifest)[2]["MANIFEST_SOURCE_MISMATCH"], 1)
            other = manifest_record()
            other["domain"] = "research"
            (root / "manifest.jsonl").write_text(json.dumps(other) + "\n", encoding="utf-8")
            manifest = load_manifest(root / "manifest.jsonl")
            self.assertEqual(inspect_file(root / "result.jsonl", manifest)[2]["MANIFEST_DOMAIN_MISMATCH"], 1)

    def test_manifest_rejects_unknown_case(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "manifest.jsonl").write_text(json.dumps(manifest_record()) + "\n", encoding="utf-8")
            value = record()
            value["case_id"] = "OTHER-04"
            (root / "result.jsonl").write_text(json.dumps(value) + "\n", encoding="utf-8")
            errors = inspect_file(root / "result.jsonl", load_manifest(root / "manifest.jsonl"))[2]
            self.assertEqual(errors["CASE_NOT_IN_MANIFEST"], 1)

    def test_reject_duplicate_manifest_ids(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.jsonl"
            line = json.dumps(manifest_record()) + "\n"
            path.write_text(line + line, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_reject_invalid_manifest_schema_and_hash(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.jsonl"
            value = manifest_record()
            value["source_sha256"] = "not-a-sha"
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)
            value = manifest_record()
            del value["provenance"]
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_reject_manifest_nested_duplicate_key(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.jsonl"
            value = json.dumps(manifest_record())
            path.write_text(value.replace('"case_id":', '"case_id": "WRONG","case_id":', 1) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_manifest_rejects_group_leakage_across_splits(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.jsonl"
            first = manifest_record()
            second = dict(first, case_id="SP-02", split="holdout",
                          source_sha256="0" * 64)
            path.write_text(json.dumps(first) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_manifest_rejects_same_source_across_splits(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.jsonl"
            first = manifest_record()
            second = dict(first, case_id="SP-02", group_id="another", split="holdout")
            path.write_text(json.dumps(first) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_invalid_manifest_cli_is_sanitized(self):
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "manifest.jsonl").write_text("{raw_secret\n", encoding="utf-8")
            (root / "results.jsonl").write_text(json.dumps(record(), ensure_ascii=False) + "\n", encoding="utf-8")
            stream = StringIO()
            with redirect_stdout(stream):
                code = main(["--input", str(root / "results.jsonl"),
                             "--manifest", str(root / "manifest.jsonl")])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(stream.getvalue())["error"], "INVALID_MANIFEST")
            self.assertNotIn("raw_secret", stream.getvalue())

    def test_manifest_missing_path_is_io_error(self):
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "results.jsonl").write_text(json.dumps(record(), ensure_ascii=False) + "\n", encoding="utf-8")
            stream = StringIO()
            with redirect_stdout(stream):
                code = main(["--input", str(root / "results.jsonl"),
                             "--manifest", str(root / "notfound.jsonl")])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(stream.getvalue())["error"], "MANIFEST_IO_ERROR")



    def test_reject_lone_surrogate_in_reason(self):
        value = record()
        value["output"]["reason"] = "\ud800"
        self.assertIn("INVALID_REASON", validate_record(value))

    def test_reject_lone_surrogate_in_recommendations(self):
        value = record()
        value["output"]["recommendations"] = ["\ud800"]
        self.assertIn("INVALID_RECOMMENDATIONS", validate_record(value))

    def test_reject_lone_surrogate_in_identifier(self):
        value = record()
        value["attempt_id"] = "\ud800"
        self.assertIn("INVALID_IDENTIFIERS", validate_record(value))

    def test_reject_lone_surrogate_in_manifest_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.jsonl"
            value = manifest_record()
            value["provenance"] = "\ud800"
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_reject_lone_surrogate_in_manifest_tag(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.jsonl"
            value = manifest_record()
            value["edge_case_tags"] = ["\ud800"]
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_reject_manifest_over_safety_limit(self):
        from unittest.mock import patch
        import validate_stage03_outputs as validator

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.jsonl"
            first = manifest_record()
            second = dict(first, case_id="SP-02", group_id="grp02",
                          source_sha256="0" * 64)
            path.write_text(json.dumps(first) + "\n" +
                            json.dumps(second) + "\n", encoding="utf-8")
            with patch.object(validator, "MAX_RECORDS", 1):
                with self.assertRaises(ValueError):
                    load_manifest(path)

    def test_fail_closed_attempts_over_safety_limit(self):
        from unittest.mock import patch
        import validate_stage03_outputs as validator

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "results.jsonl"
            first = record()
            second = record()
            second["attempt_id"] = "second"
            path.write_text(json.dumps(first) + "\n" +
                            json.dumps(second) + "\n", encoding="utf-8")
            with patch.object(validator, "MAX_RECORDS", 1):
                total, invalid, failures = inspect_file(path)
            self.assertEqual((total, invalid), (2, 1))
            self.assertEqual(failures["RECORD_LIMIT_EXCEEDED"], 1)



if __name__ == "__main__":
    unittest.main()
