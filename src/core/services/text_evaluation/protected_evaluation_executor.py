"""Scoped encrypted-source execution for a provisional Stage11 evaluation.

No standalone deployment or secret management. This adapter uses the existing
validated rubric, evaluation engine and authenticated encryption. It must be
explicitly wired into a permissioned worker; it never publishes an official grade.
"""
from __future__ import annotations

import json
from uuid import UUID

from src.core.services.text_evaluation.criterion_evaluation_service import CriterionAssessment
from src.core.services.text_evaluation.evaluation_worker_service import (
    WorkerResult, WorkerTerminalError,
)
from src.core.services.text_evaluation.rubric_schema import validated_persisted_snapshot
from src.core.services.text_evaluation.rubric_service import RubricBinding
from src.core.services.text_evaluation.text_evaluation_service import TextEvaluationService
from src.infrastructure.di.inject import inject
from src.infrastructure.models.text_evaluation import CriterionResult
from src.infrastructure.repositories.text_evaluation.evaluation_repository import (
    EvaluationRepository, WorkerEvaluationContext,
)
from src.infrastructure.security.encrypted_content import EncryptedContentService
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class ProtectedEvaluationExecutor:
    """Worker's per-job trusted callback; never loads raw text into an ordinary log."""

    def __init__(
        self,
        evaluation_repository: EvaluationRepository,
        text_evaluation_service: TextEvaluationService,
        encrypted_content_service: EncryptedContentService,
        config_reader: ConfigReader,
    ) -> None:
        self._repository = evaluation_repository
        self._engine = text_evaluation_service
        self._encryption = encrypted_content_service
        self._config = config_reader

    async def __call__(self, context: WorkerEvaluationContext) -> WorkerResult:
        settings = self._config.settings
        if (not isinstance(context, WorkerEvaluationContext)
                or self._config.environment != "development"
                or not settings.security.deny_external_egress
                or not settings.worker.enabled
                or not settings.llm.enabled
                or not settings.http_security.enabled
                or settings.worker.organization_id != context.organization_id
                or not settings.http_security.key_id
                or not isinstance(settings.llm.max_input_characters, int)
                or not 32 <= settings.llm.max_input_characters <= 100_000):
            raise WorkerTerminalError("WORKER_PROTECTED_EXECUTION_NOT_APPROVED")

        material = await self._repository.load_protected_worker_material_async(
            context=context,
        )
        if material is None:
            raise WorkerTerminalError("WORKER_PROTECTED_SOURCE_NOT_FOUND")
        protected, rubric = material
        if protected.key_id != settings.http_security.key_id:
            # The current crypto adapter cannot resolve historical key versions.
            # Never attempt to decrypt under an unknown/currently wrong key.
            raise WorkerTerminalError("WORKER_PROTECTED_KEY_UNAVAILABLE")

        snapshot = validated_persisted_snapshot(rubric)
        if (rubric.id != context.rubric_version_id
                or rubric.organization_id != context.organization_id
                or rubric.evaluation_type != context.evaluation_type):
            raise WorkerTerminalError("WORKER_RUBRIC_SCOPE_INVALID")
        binding = RubricBinding(
            rubric_version_id=rubric.id,
            organization_id=context.organization_id,
            evaluation_type=context.evaluation_type,
            code=rubric.code,
            version=rubric.version,
            checksum=rubric.checksum,
            snapshot=snapshot,
        )
        source = self._encryption.decrypt(
            ciphertext=protected.ciphertext,
            organization_id=context.organization_id,
            owner_id=context.owner_id,
            resource_id=context.protected_text_ref,
            kind="original",
        )
        limit = settings.llm.max_input_characters
        report = await self._engine.evaluate_async(
            original_text=source,
            rubric=binding,
            chunk_char_limit=min(limit, 4096),
            max_inference_characters=limit,
        )
        if (report.rubric_version_id != context.rubric_version_id
                or report.evaluation_type != context.evaluation_type
                or report.rubric_checksum != rubric.checksum
                or report.publishable_as_official_score
                or report.result_status not in (
                    "partial", "needs_human_review", "not_assessed",
                )):
            raise WorkerTerminalError("WORKER_UNTRUSTED_REPORT")

        expected_codes = {item.criterion_code for item in snapshot.criteria}
        criteria = report.criteria
        if (not isinstance(criteria, tuple) or len(criteria) != len(expected_codes)
                or {getattr(item, "criterion_code", None) for item in criteria}
                != expected_codes):
            raise WorkerTerminalError("WORKER_CRITERION_SET_INVALID")

        rows: list[CriterionResult] = []
        for item in criteria:
            if (not isinstance(item, CriterionAssessment)
                    or item.status not in ("assessed", "not_assessed")
                    or (item.status == "assessed" and (
                        type(item.score) is not int or not 0 <= item.score <= 5
                        or not item.evidence))
                    or (item.status == "not_assessed" and item.score is not None)):
                raise WorkerTerminalError("WORKER_CRITERION_INVALID")
            evidence = []
            for quote, start, end in item.evidence:
                if (not isinstance(quote, str) or not quote
                        or type(start) is not int or type(end) is not int
                        or not 0 <= start < end <= len(source)
                        or source[start:end] != quote):
                    raise WorkerTerminalError("WORKER_EVIDENCE_INVALID")
                evidence.append({
                    "quote": quote, "start_offset": start, "end_offset": end,
                })
            details = json.dumps({
                "criterion_code": item.criterion_code,
                "status": item.status,
                "score": item.score,
                "reason": item.reason,
                "reason_code": item.reason_code,
                "strengths": list(item.strengths),
                "weaknesses": list(item.weaknesses),
                "recommendations": list(item.recommendations),
                "evidence": evidence,
                "quality_flags": list(item.quality_flags),
            }, ensure_ascii=False, sort_keys=True, allow_nan=False)
            rows.append(CriterionResult(
                evaluation_id=context.evaluation_id,
                organization_id=context.organization_id,
                criterion_code=item.criterion_code,
                status=item.status,
                score=item.score,
                encrypted_details=self._encryption.encrypt(
                    value=details,
                    organization_id=context.organization_id,
                    owner_id=context.owner_id,
                    resource_id=context.evaluation_id,
                    kind="criterion",
                ),
            ))

        return WorkerResult(
            criterion_results=tuple(rows),
            coverage=float(report.coverage_fraction),
            model_revision=report.model_revision,
            prompt_version=report.prompt_version,
            result_status="partial" if report.result_status == "partial"
                          else "needs_human_review",
        )

    async def aclose(self) -> None:
        """Close only the inference client that actually served these evaluations."""
        await self._engine.close_async()

