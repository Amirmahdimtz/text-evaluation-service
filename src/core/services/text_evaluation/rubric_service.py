"""Rubric lifecycle and fixed-version resolution; no HTTP or SQL in Core."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from pydantic import ValidationError

from src.core.services.text_evaluation.rubric_schema import RubricSnapshot, validated_persisted_snapshot
from src.infrastructure.di.inject import inject
from src.infrastructure.repositories.text_evaluation.rubric_version_repository import RubricVersionRepository


@dataclass(frozen=True)
class RubricBinding:
    rubric_version_id: UUID
    organization_id: str
    evaluation_type: str
    code: str
    version: str
    checksum: str
    snapshot: RubricSnapshot


@inject
class RubricService:
    def __init__(self, rubric_repository: RubricVersionRepository) -> None:
        self._rubrics = rubric_repository

    async def create_candidate_draft_async(
        self, *, organization_id: str, actor_id: str,
        correlation_id: UUID, candidate: RubricSnapshot,
    ) -> UUID:
        candidate = RubricSnapshot.model_validate(candidate)
        if candidate.approval_status != "PROPOSED":
            raise ValueError("RUBRIC_NOT_APPROVED_FOR_SYNTHETIC_TEST")
        return await self._rubrics.insert_candidate_async(
            organization_id=organization_id, actor_id=actor_id,
            correlation_id=correlation_id,
            evaluation_type=candidate.evaluation_type,
            code=candidate.code, version=candidate.version,
            snapshot=candidate.canonical_dict(), checksum=candidate.fingerprint(),
        )

    async def publish_candidate_async(
        self, *, organization_id: str, actor_id: str, correlation_id: UUID,
        evaluation_type: str, code: str, version: str,
    ) -> UUID:
        """Technical publication is only usable with Stage05 local-test DB guard.

        Published here never means business approved (OD-03/04 are open).
        """
        draft = await self._rubrics.get_draft_async(
            organization_id=organization_id,
            evaluation_type=evaluation_type, code=code, version=version,
        )
        if draft is None:
            raise ValueError("RUBRIC_NOT_DRAFT")
        candidate = RubricSnapshot.model_validate(draft.criteria_snapshot)
        if (candidate.evaluation_type != draft.evaluation_type
                or candidate.code != draft.code or candidate.version != draft.version
                or candidate.fingerprint() != draft.checksum):
            raise ValueError("RUBRIC_SNAPSHOT_INTEGRITY")
        return await self._rubrics.publish_candidate_async(
            organization_id=organization_id, actor_id=actor_id,
            correlation_id=correlation_id, rubric_id=draft.id,
            expected_snapshot=candidate.canonical_dict(),
            expected_checksum=candidate.fingerprint(),
        )

    async def resolve_published_async(
        self, *, organization_id: str, evaluation_type: str,
        code: str, version: str | None = None,
    ) -> RubricBinding:
        if not code or not organization_id:
            raise ValueError("RUBRIC_SCOPE_REQUIRED")
        row = await self._rubrics.get_published_async(
            organization_id=organization_id, evaluation_type=evaluation_type,
            code=code, version=version,
        )
        if row is None:
            raise ValueError("RUBRIC_PUBLISHED_VERSION_NOT_FOUND")
        snapshot = validated_persisted_snapshot(row)
        if version is not None and row.version != version:
            raise ValueError("RUBRIC_VERSION_MISMATCH")
        return RubricBinding(
            rubric_version_id=row.id, organization_id=row.organization_id,
            evaluation_type=row.evaluation_type, code=row.code, version=row.version,
            checksum=row.checksum, snapshot=snapshot,
        )

    async def retire_candidate_async(
        self, *, organization_id: str, actor_id: str,
        correlation_id: UUID, rubric_version_id: UUID,
    ) -> UUID:
        return await self._rubrics.retire_candidate_async(
            organization_id=organization_id, actor_id=actor_id,
            correlation_id=correlation_id, rubric_id=rubric_version_id,
        )
