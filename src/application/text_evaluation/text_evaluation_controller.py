"""Thin authenticated HTTP router; all business actions delegated to Core."""
from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request

from src.application.text_evaluation.dtos.text_evaluation_dto import (
    CreateEvaluationDto, CreatedEvaluationDto, EvaluationResponseDto,
    RubricResponseDto, CreateFeedbackDto, FeedbackResponseDto,
)
from src.core.services.text_evaluation.evaluation_api_service import (
    EvaluationApiService, AccessDenied, ResourceHidden, Conflict,
    CapacityExceeded, ApiNotConfigured,
)
from src.infrastructure.di.inject import inject
from src.infrastructure.security.signed_identity import (
    AuthenticationError, SignedIdentityVerifier,
)

_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}$")


@inject
class TextEvaluationController:
    def __init__(
        self, evaluation_api_service: EvaluationApiService,
        signed_identity_verifier: SignedIdentityVerifier,
    ) -> None:
        self._service = evaluation_api_service
        self._auth = signed_identity_verifier

    @staticmethod
    def _map_error(exc: Exception) -> HTTPException:
        if isinstance(exc, AuthenticationError):
            return HTTPException(status_code=401, detail="AUTHENTICATION_REQUIRED")
        if isinstance(exc, AccessDenied):
            return HTTPException(status_code=403, detail="FORBIDDEN")
        if isinstance(exc, ResourceHidden):
            return HTTPException(status_code=404, detail="NOT_FOUND")
        if isinstance(exc, Conflict):
            return HTTPException(status_code=409, detail="CONFLICT")
        if isinstance(exc, CapacityExceeded):
            return HTTPException(status_code=429, detail="RATE_LIMITED")
        if isinstance(exc, ApiNotConfigured):
            return HTTPException(status_code=503, detail="SERVICE_UNAVAILABLE")
        return HTTPException(status_code=503, detail="SERVICE_UNAVAILABLE")

    async def _identity(self, request: Request, operation: str):
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer ") or len(authorization) > 8200:
            raise HTTPException(status_code=401, detail="AUTHENTICATION_REQUIRED")
        try:
            identity = self._auth.verify(authorization[7:])
            await self._service.authenticate_action_async(identity, operation)
            return identity
        except (AuthenticationError, AccessDenied, CapacityExceeded, ApiNotConfigured) as exc:
            raise self._map_error(exc) from None

    def api(self) -> APIRouter:
        router = APIRouter(prefix="", tags=["Text Evaluation"])

        @router.post(
            "/evaluations", response_model=CreatedEvaluationDto,
            status_code=202, summary="Submit an encrypted evaluation job",
        )
        async def submit(request: Request, payload: CreateEvaluationDto,
                         idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
            identity = await self._identity(request, "evaluation:submit")
            if not isinstance(idempotency_key, str) or not _KEY.fullmatch(idempotency_key):
                raise HTTPException(status_code=422, detail="VALIDATION_ERROR")
            try:
                result = await self._service.submit_async(
                    identity=identity, text=payload.text,
                    evaluation_type=payload.evaluation_type,
                    rubric_code=payload.rubric_code,
                    rubric_version=payload.rubric_version,
                    target_audience=payload.target_audience,
                    purpose=payload.purpose, idempotency_key=idempotency_key,
                    correlation_id=UUID(request.state.correlation_id),
                )
                return CreatedEvaluationDto(
                    evaluation_id=result.evaluation_id,
                    job_id=result.job_id, repeated=result.repeated,
                )
            except (AccessDenied, ResourceHidden, Conflict,
                    CapacityExceeded, ApiNotConfigured) as exc:
                raise self._map_error(exc) from None

        @router.get(
            "/evaluations/{evaluation_id}", response_model=EvaluationResponseDto,
            summary="Read an authorized private evaluation report",
        )
        async def get_evaluation(evaluation_id: UUID, request: Request):
            identity = await self._identity(request, "evaluation:read")
            try:
                return EvaluationResponseDto.model_validate(
                    await self._service.get_evaluation_async(
                        identity=identity, evaluation_id=evaluation_id,
                    )
                )
            except (AccessDenied, ResourceHidden, ApiNotConfigured) as exc:
                raise self._map_error(exc) from None

        @router.get(
            "/rubrics", response_model=list[RubricResponseDto],
            summary="List tenant-visible technically published candidate rubrics",
        )
        async def list_rubrics(request: Request):
            identity = await self._identity(request, "evaluation:submit")
            try:
                return [RubricResponseDto.model_validate(item) for item in
                        await self._service.list_rubrics_async(identity=identity)]
            except (AccessDenied, ApiNotConfigured) as exc:
                raise self._map_error(exc) from None

        @router.post(
            "/evaluations/{evaluation_id}/feedback",
            response_model=FeedbackResponseDto, status_code=201,
            summary="Append a scoped encrypted reviewer comment",
        )
        async def create_feedback(
            evaluation_id: UUID, payload: CreateFeedbackDto, request: Request,
        ):
            identity = await self._identity(request, "feedback:create")
            try:
                item_id, revision = await self._service.add_feedback_async(
                    identity=identity, evaluation_id=evaluation_id,
                    comment=payload.comment,
                    correlation_id=UUID(request.state.correlation_id),
                )
                return FeedbackResponseDto(
                    feedback_id=item_id, evaluation_id=evaluation_id,
                    revision=revision,
                )
            except (AccessDenied, ResourceHidden, ApiNotConfigured) as exc:
                raise self._map_error(exc) from None
        return router
