"""Strict Stage06 synthetic-candidate rubric contract; not an approved business rubric."""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Domain = Literal["speech", "media", "research"]
_Code = str

class RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    criterion_code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1, max_length=200)
    operational_definition: str = Field(min_length=5, max_length=2000)
    weight: int = Field(strict=True, ge=1, le=100)
    required: bool
    scoring_anchors: dict[str, str]
    evaluation_instructions: str = Field(min_length=5, max_length=3000)
    evidence_requirements: str = Field(min_length=5, max_length=2000)
    applicability_rules: str = Field(min_length=5, max_length=2000)

    @field_validator("scoring_anchors")
    @classmethod
    def all_anchors(cls, value: dict[str, str]) -> dict[str, str]:
        if set(value) != {str(i) for i in range(6)}:
            raise ValueError("RUBRIC_ANCHORS_0_TO_5_REQUIRED")
        if any(not isinstance(v, str) or not v.strip() or len(v) > 1000 for v in value.values()):
            raise ValueError("RUBRIC_ANCHOR_DEFINITION_INVALID")
        return value

class CoveragePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    status: Literal["PROPOSED"] = "PROPOSED"
    insufficient_evidence: Literal["not_assessed"] = "not_assessed"
    non_applicable: Literal["record_explicit_justification"] = "record_explicit_justification"
    required_missing: Literal["flag_for_human_review"] = "flag_for_human_review"
    # No invented business thresholds or numerical scoring policy.

class RubricSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    schema_version: Literal["rubric-candidate-v1"] = "rubric-candidate-v1"
    approval_status: Literal["PROPOSED"] = "PROPOSED"
    code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    version: str = Field(min_length=5, max_length=50, pattern=r"^candidate-[0-9]+(?:\.[0-9]+){1,2}$")
    evaluation_type: Domain
    criteria: tuple[RubricCriterion, ...] = Field(min_length=1, max_length=32)
    coverage_policy: CoveragePolicy = Field(default_factory=CoveragePolicy)

    @model_validator(mode="after")
    def validate_criteria(self) -> "RubricSnapshot":
        codes = [item.criterion_code for item in self.criteria]
        if len(codes) != len(set(codes)):
            raise ValueError("RUBRIC_DUPLICATE_CRITERION")
        if sum(item.weight for item in self.criteria) != 100:
            raise ValueError("RUBRIC_WEIGHTS_NOT_100")
        if any(not item.criterion_code.startswith(self.evaluation_type + "_") for item in self.criteria):
            raise ValueError("RUBRIC_DOMAIN_CRITERION_MISMATCH")
        return self

    def canonical_dict(self) -> dict:
        return self.model_dump(mode="json")

    def fingerprint(self) -> str:
        payload = json.dumps(self.canonical_dict(), ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

def validated_persisted_snapshot(row: object) -> RubricSnapshot:
    """Reject incomplete, corrupt or unapproved persisted rows before they are consumed."""
    try:
        if getattr(row, "status", None) != "published":
            raise ValueError("RUBRIC_NOT_PUBLISHED")
        snapshot = RubricSnapshot.model_validate(getattr(row, "criteria_snapshot"))
        if (snapshot.code != row.code or snapshot.version != row.version
                or snapshot.evaluation_type != row.evaluation_type
                or snapshot.fingerprint() != row.checksum):
            raise ValueError("RUBRIC_SNAPSHOT_INTEGRITY")
        return snapshot
    except (AttributeError, TypeError) as exc:
        raise ValueError("RUBRIC_SNAPSHOT_INTEGRITY") from None
