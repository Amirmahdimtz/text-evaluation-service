"""Stage10 strict public API shapes. Never include original text in responses."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

class ApiDto(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CreateEvaluationDto(ApiDto):
    model_config = ConfigDict(
        extra="forbid", strict=True,
        json_schema_extra={"examples": [{
            "text": "Synthetic text for isolated validation only.",
            "evaluation_type": "speech",
            "rubric_code": "speech_quality",
            "rubric_version": "candidate-0.1",
            "purpose": "Synthetic contract smoke test",
        }]},
    )
    text: str = Field(min_length=1, max_length=2000000)
    evaluation_type: Literal["speech", "media", "research"]
    rubric_code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    rubric_version: str = Field(min_length=5, max_length=50)
    target_audience: str | None = Field(default=None, max_length=512)
    purpose: str | None = Field(default=None, max_length=512)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if (not value.strip()
                or any(ord(c) == 0 or 0xD800 <= ord(c) <= 0xDFFF for c in value)):
            raise ValueError("INPUT_TEXT_INVALID")
        return value


class CreatedEvaluationDto(ApiDto):
    evaluation_id: UUID
    job_id: UUID
    repeated: bool
    status: Literal["accepted"] = "accepted"


class CriterionResponseDto(ApiDto):
    criterion_code: str
    status: Literal["assessed", "not_assessed"]
    score: int | None
    details: dict


class EvaluationStatusDto(ApiDto):
    evaluation_id: UUID
    status: str
    evaluation_type: Literal["speech", "media", "research"]
    rubric_version_id: UUID
    created_at: datetime
    completed_at: datetime | None
    needs_human_review: bool
    publishable_as_official_score: bool = False


class EvaluationResponseDto(EvaluationStatusDto):
    provisional_score: Decimal | None
    coverage: Decimal | None
    model_revision: str | None
    prompt_version: str | None
    criteria: list[CriterionResponseDto]


class RubricResponseDto(ApiDto):
    rubric_version_id: UUID
    evaluation_type: Literal["speech", "media", "research"]
    code: str
    version: str
    checksum: str
    approval_status: Literal["PROPOSED"]


class CreateFeedbackDto(ApiDto):
    model_config = ConfigDict(
        extra="forbid", strict=True,
        json_schema_extra={"examples": [{
            "comment": "Synthetic reviewer comment. No confidential material.",
            "decision_code": "COMMENT",
        }]},
    )
    comment: str = Field(min_length=1, max_length=8192)
    decision_code: Literal["COMMENT"] = "COMMENT"

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("FEEDBACK_EMPTY")
        return value


class FeedbackResponseDto(ApiDto):
    feedback_id: UUID
    evaluation_id: UUID
    revision: int
    status: Literal["recorded"] = "recorded"
