"""Stage08 evaluation orchestration; no DB write or real model startup."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.core.services.text_evaluation.criterion_evaluation_service import (
    CriterionAssessment, CriterionEvaluationService, PROMPT_VERSION, abstain,
)
from src.core.services.text_evaluation.rubric_service import RubricBinding
from src.core.services.text_evaluation.scoring_service import (
    CriterionScore, ScoringService,
)
from src.core.services.text_evaluation.text_preprocessing_service import (
    TextPreprocessingService,
)
from src.infrastructure.di.inject import inject


@dataclass(frozen=True)
class EvaluationReport:
    evaluation_type: str
    rubric_version_id: UUID
    rubric_code: str
    rubric_version: str
    rubric_checksum: str
    prompt_version: str
    model_id: str
    model_revision: str
    model_revision_verified: bool
    inference_settings: tuple[tuple[str, str], ...]
    source_sha256: str
    source_length: int
    chunk_ranges: tuple[tuple[int, int], ...]
    criteria: tuple[CriterionAssessment, ...]
    provisional_score_0_100: Decimal | None
    coverage_fraction: Decimal
    result_status: str
    needs_human_review: bool
    publishable_as_official_score: bool
    rounding_policy: str
    required_missing: tuple[str, ...]
    exact_score_ratio: tuple[int, int] | None
    exact_coverage_ratio: tuple[int, int]


@inject
class TextEvaluationService:
    def __init__(
        self, text_preprocessing_service: TextPreprocessingService,
        criterion_evaluation_service: CriterionEvaluationService,
        scoring_service: ScoringService,
    ) -> None:
        self._preprocessing = text_preprocessing_service
        self._criteria = criterion_evaluation_service
        self._scoring = scoring_service

    async def evaluate_async(
        self, *, original_text: str, rubric: RubricBinding,
        chunk_char_limit: int, max_inference_characters: int,
    ) -> EvaluationReport:
        if (not isinstance(rubric, RubricBinding) or not rubric.organization_id
                or not isinstance(rubric.rubric_version_id, UUID)
                or not isinstance(rubric.snapshot, object)
                or rubric.code != rubric.snapshot.code
                or rubric.version != rubric.snapshot.version
                or rubric.evaluation_type != rubric.snapshot.evaluation_type
                or rubric.checksum != rubric.snapshot.fingerprint()):
            raise ValueError("ENGINE_RUBRIC_BINDING_INVALID")
        if (type(max_inference_characters) is not int
                or not 32 <= max_inference_characters <= 100_000):
            raise ValueError("ENGINE_LIMIT_INVALID")
        prepared = self._preprocessing.prepare(
            original_text, chunk_char_limit=chunk_char_limit,
        )
        provenance = self._criteria.declared_provenance()
        if (not isinstance(provenance, dict) or not provenance.get("model_id")
                or not provenance.get("model_revision")
                or provenance.get("revision_verified") is not False):
            raise ValueError("ENGINE_MODEL_PROVENANCE_INVALID")
        provider_limit = provenance.get("max_input_characters")
        if (type(provider_limit) is not int
                or not 32 <= provider_limit <= 2_000_000
                or max_inference_characters > provider_limit):
            raise ValueError("ENGINE_PROVIDER_LIMIT_MISMATCH")
        criteria: list[CriterionAssessment] = []
        # A chunk-by-chunk average is NOT a valid document-level assessment.
        # Without approved hierarchical synthesis and real tokenizer evidence,
        # fail closed rather than suppressing global context or fabricating scores.
        if len(original_text) > max_inference_characters:
            for criterion in rubric.snapshot.criteria:
                criteria.append(
                    await self._criteria.evaluate_document_chunks_async(
                        criterion=criterion, original_text=original_text,
                        chunks=prepared.chunks, rubric_checksum=rubric.checksum,
                        max_input_characters=max_inference_characters,
                    )
                )
        else:
            for criterion in rubric.snapshot.criteria:
                criteria.append(await self._criteria.evaluate_criterion_async(
                    criterion=criterion, original_text=original_text,
                    rubric_checksum=rubric.checksum,
                ))
        score = self._scoring.calculate(
            rubric=rubric.snapshot,
            outcomes=tuple(CriterionScore(
                criterion_code=c.criterion_code, status=c.status,
                score=c.score, reason_code=c.reason_code,
            ) for c in criteria),
        )
        return EvaluationReport(
            evaluation_type=rubric.evaluation_type,
            rubric_version_id=rubric.rubric_version_id,
            rubric_code=rubric.code,
            rubric_version=rubric.version,
            rubric_checksum=rubric.checksum,
            prompt_version=PROMPT_VERSION,
            model_id=str(provenance["model_id"]),
            model_revision=str(provenance["model_revision"]),
            model_revision_verified=False,
            inference_settings=tuple(sorted(
                (str(key), str(value)) for key, value in provenance.items()
                if key not in {"model_id", "model_revision", "revision_verified"}
            )),
            source_sha256=prepared.source_sha256,
            source_length=len(prepared.original),
            chunk_ranges=tuple(
                (chunk.start_offset, chunk.end_offset) for chunk in prepared.chunks
            ),
            criteria=tuple(criteria),
            provisional_score_0_100=score.provisional_score_0_100,
            coverage_fraction=score.coverage_fraction,
            result_status=score.result_status,
            needs_human_review=score.needs_human_review,
            publishable_as_official_score=score.publishable_as_official_score,
            rounding_policy=score.rounding_policy,
            required_missing=score.required_missing,
            exact_score_ratio=score.exact_score_ratio,
            exact_coverage_ratio=score.exact_coverage_ratio,
        )
