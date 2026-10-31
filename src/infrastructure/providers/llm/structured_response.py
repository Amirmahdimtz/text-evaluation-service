"""Strict Stage07 per-criterion model output; scoring and relevance belong to Stage08."""
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OriginalEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    source_kind: Literal["original_submission"]
    quote: str = Field(min_length=1, max_length=4096)
    start_offset: int = Field(strict=True, ge=0)
    end_offset: int = Field(strict=True, ge=1)


class CriterionInference(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    criterion_code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    status: Literal["assessed", "not_assessed"]
    score: int | None = Field(default=None, strict=True, ge=0, le=5)
    reason: str = Field(min_length=1, max_length=4096)
    strengths: list[str] = Field(max_length=32)
    weaknesses: list[str] = Field(max_length=32)
    recommendations: list[str] = Field(max_length=32)
    evidence: list[OriginalEvidence] = Field(max_length=32)

    @model_validator(mode="after")
    def check_status(self) -> "CriterionInference":
        if self.status == "assessed":
            if self.score is None or not self.evidence:
                raise ValueError("LLM_ASSESSMENT_EVIDENCE_REQUIRED")
        elif self.score is not None or self.evidence:
            raise ValueError("LLM_ABSTENTION_MUST_BE_EMPTY")
        if not self.reason.strip():
            raise ValueError("LLM_EMPTY_REASON")
        for items in (self.strengths, self.weaknesses, self.recommendations):
            if any(not isinstance(x, str) or not x.strip() or len(x) > 1000 for x in items):
                raise ValueError("LLM_INVALID_COMMENT")
        return self


def decode_criterion_response(raw: str, *, expected_code: str, source_text: str,
                              max_response_bytes: int) -> CriterionInference:
    """Reject duplicate keys, invalid JSON, wrong criterion, invalid offsets or quotes."""
    if not isinstance(raw, str):
        raise ValueError("LLM_INVALID_JSON")
    try:
        if len(raw.encode("utf-8")) > max_response_bytes:
            raise ValueError("LLM_RESPONSE_TOO_LARGE")

        def unique_pairs(pairs):
            seen = {}
            for key, value in pairs:
                if key in seen:
                    raise ValueError("LLM_DUPLICATE_JSON_KEY")
                seen[key] = value
            return seen

        def reject_constant(_):
            raise ValueError("LLM_NONFINITE_JSON_NUMBER")

        parsed = json.loads(raw, object_pairs_hook=unique_pairs,
                            parse_constant=reject_constant)
        result = CriterionInference.model_validate(parsed)
        if result.criterion_code != expected_code:
            raise ValueError("LLM_WRONG_CRITERION")
        for ev in result.evidence:
            if ev.end_offset <= ev.start_offset:
                raise ValueError("LLM_QUOTE_OFFSET_INVALID")
            if source_text[ev.start_offset:ev.end_offset] != ev.quote:
                # Do not guess, normalize, relocate, or accept invented evidence.
                if ev.quote not in source_text:
                    raise ValueError("LLM_QUOTE_NOT_FOUND")
                raise ValueError("LLM_QUOTE_OFFSET_INVALID")
        return result
    except (UnicodeError, RecursionError, OverflowError):
        raise ValueError("LLM_INVALID_JSON") from None
