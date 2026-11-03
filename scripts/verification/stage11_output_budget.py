"""Offline-only Stage11 JSON encoding size experiment (not a tokenizer benchmark).

Uses the actual per-criterion Pydantic model and synthetic fixture cases.
No model inference, network, filesystem writes, or confidential input.
"""
from __future__ import annotations

import json

from scripts.verification.stage11_real_model_criterion_probe import _load_selected_rubrics
from src.infrastructure.providers.llm.structured_response import (
    CriterionInference, decode_criterion_response,
)

_REQUIRED_KEYS = frozenset(CriterionInference.model_fields)


def _synthetic_candidate(*, code: str, text: str, assessed: bool) -> dict:
    """Controlled identical-content sample; NOT an expert rubric judgment."""
    return {
        "criterion_code": code,
        "status": "assessed" if assessed else "not_assessed",
        "score": 3 if assessed else None,
        "reason": (
            "متن ساختگی دارای نشانه‌ای از وضوح است؛ نیازمند بازبینی کارشناس."
            if assessed else
            "شواهد کافی برای ارزیابی مستقل وجود ندارد."
        ),
        "strengths": ["نمونه آزمایشی"] if assessed else [],
        "weaknesses": [],
        "recommendations": [],
        "evidence": [{
            "source_kind": "original_submission",
            "quote": text[:16],
            "start_offset": 0,
            "end_offset": 16,
        }] if assessed else [],
    }


def analyze_offline() -> dict:
    rows = []
    for case, criterion, _ in _load_selected_rubrics():
        for assessed in (True, False):
            candidate = _synthetic_candidate(
                code=criterion.criterion_code,
                text=case.original_text,
                assessed=assessed,
            )
            assert set(candidate) == _REQUIRED_KEYS
            parsed = CriterionInference.model_validate(candidate)
            spaced = json.dumps(candidate, ensure_ascii=False)
            compact = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))
            # Both representations must round-trip through the real strict
            # decoder, retaining the same evidence and all other fields.
            from_spaced = decode_criterion_response(
                spaced, expected_code=criterion.criterion_code,
                source_text=case.original_text, max_response_bytes=65536,
            )
            from_compact = decode_criterion_response(
                compact, expected_code=criterion.criterion_code,
                source_text=case.original_text, max_response_bytes=65536,
            )
            assert parsed == from_spaced == from_compact
            before = len(spaced.encode("utf-8"))
            after = len(compact.encode("utf-8"))
            rows.append({
                "domain": case.domain,
                "criterion_code": case.criterion_code,
                "sample_status": "assessed" if assessed else "not_assessed",
                "spaced_bytes": before,
                "compact_bytes": after,
                "byte_reduction": before - after,
                "required_keys_preserved": len(_REQUIRED_KEYS),
                "strict_decoder_valid": True,
            })
    return {
        "status": "OFFLINE_STRUCTURAL_ONLY_NOT_MODEL_QUALITY",
        "samples": rows,
        "sample_count": len(rows),
        "network_calls": 0,
        "tokenizer_counts_measured": False,
        "real_model_latency_measured": False,
        "semantic_quality_verified": False,
    }


def main() -> int:
    try:
        print(json.dumps(analyze_offline(), ensure_ascii=False, sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({"status": "STAGE11_OFFLINE_OUTPUT_BUDGET_FAILED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
