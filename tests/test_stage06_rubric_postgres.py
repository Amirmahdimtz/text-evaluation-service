"""Stage06 real PostgreSQL publication, immutable history and race verification.

Test database only. No shared DB, no destructive migrations, no confidential data.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from src.core.services.text_evaluation.rubric_schema import RubricSnapshot
from src.core.services.text_evaluation.rubric_service import RubricService
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext, get_test_database_url
from src.infrastructure.models.text_evaluation import AuditEvent, Evaluation, EvaluationJob, RubricVersion
from src.infrastructure.repositories.text_evaluation.evaluation_repository import EvaluationRepository
from src.infrastructure.repositories.text_evaluation.rubric_version_repository import RubricVersionRepository

FIXTURES = Path(__file__).resolve().parent / "fixtures/stage06_candidate_rubrics.json"

@pytest.fixture(scope="module", autouse=True)
def isolated_db():
    if not os.getenv("TES_STAGE05_DATABASE_URL"):
        pytest.skip("PENDING_LOCAL_DB: isolated PostgreSQL DSN not provided")
    pytest.importorskip("asyncpg")
    get_test_database_url()
    from alembic import command
    from alembic.config import Config
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "src/infrastructure/alembic"))
    command.upgrade(config, "head")


def candidate(domain: str) -> RubricSnapshot:
    return RubricSnapshot.model_validate(json.loads(FIXTURES.read_text(encoding="utf-8"))[domain])


def test_stage06_publish_snapshot_audit_immutability_retirement_and_binding(isolated_db):
    async def exercise():
        db = PsqlDbContext()
        service = RubricService(RubricVersionRepository(db))
        org = "synthetic-stage06-" + uuid4().hex
        actor, correlation = "synthetic-curator", uuid4()
        source = candidate("speech")
        try:
            rid = await service.create_candidate_draft_async(
                organization_id=org, actor_id=actor, correlation_id=correlation, candidate=source,
            )
            with pytest.raises(ValueError, match="RUBRIC_PUBLISHED_VERSION_NOT_FOUND"):
                await service.resolve_published_async(
                    organization_id=org, evaluation_type="speech",
                    code=source.code, version=source.version,
                )
            assert await service.publish_candidate_async(
                organization_id=org, actor_id=actor, correlation_id=correlation,
                evaluation_type="speech", code=source.code, version=source.version,
            ) == rid
            pinned = await service.resolve_published_async(
                organization_id=org, evaluation_type="speech",
                code=source.code, version=source.version,
            )
            assert pinned.rubric_version_id == rid
            assert pinned.version == "candidate-0.1"
            assert pinned.snapshot == source
            with pytest.raises(ValueError, match="RUBRIC_PUBLISHED_VERSION_NOT_FOUND"):
                await service.resolve_published_async(
                    organization_id="foreign-"+org, evaluation_type="speech",
                    code=source.code, version=source.version,
                )
            with pytest.raises(ValueError, match="RUBRIC_NOT_DRAFT"):
                await service.publish_candidate_async(
                    organization_id=org, actor_id=actor, correlation_id=correlation,
                    evaluation_type="speech", code=source.code, version=source.version,
                )
            # Stage05 published rubric database trigger rejects all content edits.
            with pytest.raises(DBAPIError):
                async with db.session() as session:
                    async with session.begin():
                        await session.execute(
                            text("UPDATE rubric_versions SET checksum=:value WHERE id=:rid"),
                            {"value": "f"*64, "rid": rid},
                        )
            # Stage05 evaluation creation pins the exact published row via scoped FK.
            evaluation_id, job_id = uuid4(), uuid4()
            evaluation = Evaluation(
                id=evaluation_id, organization_id=org, owner_id="synthetic-author",
                evaluation_type="speech", rubric_version_id=pinned.rubric_version_id,
                protected_text_ref=uuid4(), idempotency_key="fixture-"+uuid4().hex,
                request_fingerprint="c"*64, status="pending",
            )
            job = EvaluationJob(id=job_id, evaluation_id=evaluation_id, organization_id=org, status="pending")
            assert await EvaluationRepository(db).create_with_job_async(
                evaluation, job, organization_id=org,
                owner_id="synthetic-author", correlation_id=uuid4(),
            ) == (evaluation_id, job_id, False)
            assert await service.retire_candidate_async(
                organization_id=org, actor_id=actor,
                correlation_id=correlation, rubric_version_id=rid,
            ) == rid
            with pytest.raises(ValueError, match="RUBRIC_PUBLISHED_VERSION_NOT_FOUND"):
                await service.resolve_published_async(
                    organization_id=org, evaluation_type="speech",
                    code=source.code, version=source.version,
                )
            async with db.session() as session:
                record = await session.get(RubricVersion, rid)
                assert record.status == "retired"
                assert record.checksum == pinned.checksum
                assert record.criteria_snapshot == source.canonical_dict()
                assert (await session.scalar(select(func.count()).select_from(AuditEvent).where(
                    AuditEvent.organization_id == org,
                    AuditEvent.resource_kind == "rubric",
                ))) == 3
                assert (await session.get(Evaluation, evaluation_id)).rubric_version_id == rid
            with pytest.raises(ValueError, match="RUBRIC_NOT_PUBLISHED"):
                await service.retire_candidate_async(
                    organization_id=org, actor_id=actor,
                    correlation_id=correlation, rubric_version_id=rid,
                )
        finally:
            await db.close()
    asyncio.run(exercise())


def test_stage06_concurrent_publication_only_one_audit_and_version(isolated_db):
    async def exercise():
        db = PsqlDbContext()
        repo = RubricVersionRepository(db)
        service = RubricService(repo)
        org = "synthetic-race-" + uuid4().hex
        source = candidate("media")
        try:
            rid = await service.create_candidate_draft_async(
                organization_id=org, actor_id="synthetic-curator",
                correlation_id=uuid4(), candidate=source,
            )
            async def publish():
                try:
                    return await service.publish_candidate_async(
                        organization_id=org, actor_id="synthetic-curator",
                        correlation_id=uuid4(), evaluation_type="media",
                        code=source.code, version=source.version,
                    )
                except ValueError as exc:
                    return str(exc)
            outcomes = await asyncio.gather(publish(), publish())
            assert outcomes.count(rid) == 1
            assert len([v for v in outcomes if isinstance(v, str) and "RUBRIC_NOT_DRAFT" in v]) == 1
            async with db.session() as session:
                assert (await session.scalar(select(func.count()).select_from(AuditEvent).where(
                    AuditEvent.organization_id == org,
                    AuditEvent.action_code == "RUBRIC_CANDIDATE_PUBLISHED",
                ))) == 1
                assert (await session.get(RubricVersion, rid)).status == "published"
        finally:
            await db.close()
    asyncio.run(exercise())


def test_stage06_duplicate_version_and_invalid_draft_fail_without_publication(isolated_db):
    async def exercise():
        db = PsqlDbContext()
        repo = RubricVersionRepository(db)
        service = RubricService(repo)
        org = "synthetic-duplicate-" + uuid4().hex
        source = candidate("research")
        try:
            rid = await service.create_candidate_draft_async(
                organization_id=org, actor_id="synthetic-curator",
                correlation_id=uuid4(), candidate=source,
            )
            with pytest.raises(ValueError, match="RUBRIC_VERSION_CONFLICT"):
                await service.create_candidate_draft_async(
                    organization_id=org, actor_id="synthetic-curator",
                    correlation_id=uuid4(), candidate=source,
                )
            # Deliberately store invalid, synthetic Draft using raw infrastructure path:
            async with db.session() as session:
                async with session.begin():
                    row = await session.get(RubricVersion, rid)
                    row.criteria_snapshot = {"criteria": []}
            with pytest.raises((ValueError, Exception)) as exc:
                await service.publish_candidate_async(
                    organization_id=org, actor_id="synthetic-curator",
                    correlation_id=uuid4(), evaluation_type="research",
                    code=source.code, version=source.version,
                )
            assert exc.value is not None
            async with db.session() as session:
                assert (await session.get(RubricVersion, rid)).status == "draft"
                assert (await session.scalar(select(func.count()).select_from(AuditEvent).where(
                    AuditEvent.organization_id == org,
                    AuditEvent.action_code == "RUBRIC_CANDIDATE_PUBLISHED",
                ))) == 0
        finally:
            await db.close()
    asyncio.run(exercise())
