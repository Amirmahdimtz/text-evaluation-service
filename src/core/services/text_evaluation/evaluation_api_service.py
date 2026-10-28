"""Stage10 authenticated business flow, without HTTP or direct SQL code."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import Evaluation, EvaluationJob
from src.infrastructure.security.policy import Identity, ResourceScope, is_allowed
from src.infrastructure.security.encrypted_content import EncryptedContentService
from src.infrastructure.utils.config_reader import ConfigReader
from src.infrastructure.repositories.text_evaluation.evaluation_repository import EvaluationRepository
from src.infrastructure.repositories.text_evaluation.evaluation_feedback_repository import EvaluationFeedbackRepository
from src.infrastructure.repositories.text_evaluation.rubric_version_repository import RubricVersionRepository
from src.infrastructure.repositories.text_evaluation.http_rate_limit_repository import HttpRateLimitRepository
from src.core.services.text_evaluation.rubric_schema import validated_persisted_snapshot


class AccessDenied(ValueError):
    pass


class ResourceHidden(ValueError):
    pass


class Conflict(ValueError):
    pass


class CapacityExceeded(ValueError):
    pass


class ApiNotConfigured(ValueError):
    pass


@dataclass(frozen=True)
class AcceptedEvaluation:
    evaluation_id: UUID
    job_id: UUID
    repeated: bool


@inject
class EvaluationApiService:
    def __init__(
        self, evaluation_repository: EvaluationRepository,
        rubric_repository: RubricVersionRepository,
        feedback_repository: EvaluationFeedbackRepository,
        rate_repository: HttpRateLimitRepository,
        encryption: EncryptedContentService,
        config_reader: ConfigReader,
    ) -> None:
        self._evaluations = evaluation_repository
        self._rubrics = rubric_repository
        self._feedback = feedback_repository
        self._rate = rate_repository
        self._crypto = encryption
        self._config = config_reader

    def _settings(self):
        settings = self._config.settings.http_security
        if (not settings.enabled or self._config.environment != "development"
                or not settings.max_request_bytes or not settings.max_text_characters
                or not settings.max_active_jobs or not settings.max_requests_per_minute
                or not settings.key_id or not settings.encryption_key_ref):
            raise ApiNotConfigured("API_SECURITY_NOT_CONFIGURED")
        return settings

    async def authenticate_action_async(self, identity: Identity, operation: str) -> None:
        settings = self._settings()
        if (identity is None or not identity.is_authenticated
                or operation not in identity.permissions):
            raise AccessDenied("API_OPERATION_DENIED")
        try:
            allowed = await self._rate.consume_async(
                organization_id=identity.organization_id,
                user_id=identity.user_id,
                max_per_minute=settings.max_requests_per_minute,
            )
        except ValueError:
            raise ApiNotConfigured("API_RATE_UNAVAILABLE") from None
        if not allowed:
            raise CapacityExceeded("API_RATE_LIMITED")

    async def submit_async(
        self, *, identity: Identity, text: str, evaluation_type: str,
        rubric_code: str, rubric_version: str, idempotency_key: str,
        target_audience: str | None, purpose: str | None, correlation_id: UUID,
    ) -> AcceptedEvaluation:
        if not is_allowed(identity, "evaluation:submit"):
            raise AccessDenied("API_OPERATION_DENIED")
        settings = self._settings()
        if (not isinstance(text, str) or not text.strip()
                or len(text) > settings.max_text_characters
                or not isinstance(correlation_id, UUID)):
            raise ValueError("API_TEXT_INVALID")
        rubric = await self._rubrics.get_published_async(
            organization_id=identity.organization_id,
            evaluation_type=evaluation_type, code=rubric_code, version=rubric_version,
        )
        if rubric is None:
            raise ResourceHidden("API_RUBRIC_NOT_FOUND")
        validated_persisted_snapshot(rubric)
        source_ref = uuid4()
        cipher = self._crypto.encrypt(
            value=text, organization_id=identity.organization_id,
            owner_id=identity.user_id, resource_id=source_ref, kind="original",
        )
        fingerprint_input = json.dumps({
            "text": text, "evaluation_type": evaluation_type,
            "rubric_id": str(rubric.id), "target_audience": target_audience,
            "purpose": purpose,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        fingerprint = self._crypto.fingerprint(canonical_input=fingerprint_input)
        evaluation_id, job_id = uuid4(), uuid4()
        try:
            saved_id, saved_job, repeated = await self._evaluations.create_with_job_async(
                Evaluation(
                    id=evaluation_id, organization_id=identity.organization_id,
                    owner_id=identity.user_id, evaluation_type=evaluation_type,
                    rubric_version_id=rubric.id, protected_text_ref=source_ref,
                    idempotency_key=idempotency_key,
                    request_fingerprint=fingerprint, status="pending",
                ),
                EvaluationJob(
                    id=job_id, evaluation_id=evaluation_id,
                    organization_id=identity.organization_id, status="pending",
                ),
                organization_id=identity.organization_id,
                owner_id=identity.user_id, correlation_id=correlation_id,
                max_active_jobs=settings.max_active_jobs,
                encrypted_source=cipher, source_key_id=settings.key_id,
            )
        except ValueError as exc:
            if str(exc) in ("DB_IDEMPOTENCY_CONFLICT", "DB_CONSTRAINT_CONFLICT"):
                raise Conflict("API_IDEMPOTENCY_CONFLICT") from None
            if str(exc) == "DB_QUEUE_CAPACITY_EXCEEDED":
                raise CapacityExceeded("API_QUEUE_FULL") from None
            raise
        return AcceptedEvaluation(saved_id, saved_job, repeated)

    async def list_rubrics_async(self, *, identity: Identity) -> tuple[dict, ...]:
        if not is_allowed(identity, "evaluation:submit"):
            raise AccessDenied("API_OPERATION_DENIED")
        rows = await self._rubrics.list_published_async(
            organization_id=identity.organization_id,
        )
        results = []
        for row in rows:
            item = validated_persisted_snapshot(row)
            results.append({
                "rubric_version_id": row.id, "evaluation_type": row.evaluation_type,
                "code": row.code, "version": row.version,
                "checksum": row.checksum, "approval_status": item.approval_status,
            })
        return tuple(results)

    async def get_evaluation_async(self, *, identity: Identity, evaluation_id: UUID) -> dict:
        if "evaluation:read" not in identity.permissions:
            raise AccessDenied("API_OPERATION_DENIED")
        report = await self._evaluations.read_scoped_report_async(
            organization_id=identity.organization_id, evaluation_id=evaluation_id,
        )
        if report is None:
            raise ResourceHidden("API_EVALUATION_NOT_FOUND")
        evaluation, rows = report
        scope = ResourceScope(str(evaluation.id), evaluation.owner_id, evaluation.organization_id)
        if not is_allowed(identity, "evaluation:read", scope):
            raise ResourceHidden("API_EVALUATION_NOT_FOUND")
        details = []
        for row in rows:
            content = self._crypto.decrypt(
                ciphertext=row.encrypted_details, organization_id=identity.organization_id,
                owner_id=evaluation.owner_id, resource_id=evaluation.id, kind="criterion",
            )
            # Details in production are typed structured outputs, never assumed
            # trustworthy JSON or echoed by exception handlers.
            try:
                decoded = json.loads(content)
                if not isinstance(decoded, dict) or len(content) > 32768:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ApiNotConfigured("API_REPORT_INVALID") from None
            details.append({
                "criterion_code": row.criterion_code,
                "status": row.status, "score": row.score,
                "details": decoded,
            })
        return {
            "evaluation_id": evaluation.id,
            "status": evaluation.status,
            "evaluation_type": evaluation.evaluation_type,
            "rubric_version_id": evaluation.rubric_version_id,
            "provisional_score": evaluation.overall_score,
            "coverage": evaluation.coverage,
            "model_revision": evaluation.model_revision,
            "prompt_version": evaluation.prompt_version,
            "created_at": evaluation.created_at,
            "completed_at": evaluation.completed_at,
            "needs_human_review": evaluation.status in (
                "partial", "needs_human_review",
            ),
            "publishable_as_official_score": False,
            "criteria": details,
        }

    async def add_feedback_async(
        self, *, identity: Identity, evaluation_id: UUID,
        comment: str, correlation_id: UUID,
    ) -> tuple[UUID, int]:
        if "feedback:create" not in identity.permissions:
            raise AccessDenied("API_OPERATION_DENIED")
        # Revocation/assignment must be verified by the organization IdP; the
        # only accepted assignment is from a correctly signed token.
        assigned_ids = frozenset(
            UUID(v) for v in identity.assigned_resource_ids
        )
        if evaluation_id not in assigned_ids:
            raise ResourceHidden("API_EVALUATION_NOT_FOUND")
        if not comment.strip():
            raise ValueError("API_FEEDBACK_INVALID")
        ciphertext = self._crypto.encrypt(
            value=comment, organization_id=identity.organization_id,
            owner_id=identity.user_id, resource_id=evaluation_id, kind="feedback",
        )
        try:
            return await self._feedback.append_assigned_async(
                organization_id=identity.organization_id,
                reviewer_id=identity.user_id, assigned_evaluation_ids=assigned_ids,
                evaluation_id=evaluation_id, decision_code="COMMENT",
                encrypted_details=ciphertext, correlation_id=correlation_id,
            )
        except ValueError:
            raise ResourceHidden("API_EVALUATION_NOT_FOUND") from None
