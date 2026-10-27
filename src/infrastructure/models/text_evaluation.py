"""Stage 05 candidate relational schema. Confidential prose is never stored in plaintext."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint, ForeignKeyConstraint, Index, Numeric, SmallInteger, String,
    UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.context.sql_db.psql_dbcontext import Base


def _pk():
    return mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


def _at():
    return mapped_column(nullable=False, server_default=func.now())


class RubricVersion(Base):
    __tablename__ = "rubric_versions"
    id: Mapped[UUID] = _pk()
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    evaluation_type: Mapped[str] = mapped_column(String(16), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft", server_default="draft")
    criteria_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    __table_args__ = (
        UniqueConstraint("organization_id", "evaluation_type", "code", "version", name="uq_rubric_version"),
        UniqueConstraint("id", "organization_id", "evaluation_type", name="uq_rubric_id_scope_type"),
        CheckConstraint("evaluation_type IN ('speech','media','research')", name="ck_rubric_type"),
        CheckConstraint("status IN ('draft','published','retired')", name="ck_rubric_status"),
        CheckConstraint("length(checksum) = 64", name="ck_rubric_checksum"),
        CheckConstraint("(status = 'draft' AND published_at IS NULL) OR (status <> 'draft' AND published_at IS NOT NULL)", name="ck_rubric_publication"),
    )


class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[UUID] = _pk()
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False)
    evaluation_type: Mapped[str] = mapped_column(String(16), nullable=False)
    rubric_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    protected_text_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending")
    overall_score: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    coverage: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    model_revision: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(
            ["rubric_version_id", "organization_id", "evaluation_type"],
            ["rubric_versions.id", "rubric_versions.organization_id", "rubric_versions.evaluation_type"],
            name="fk_evaluation_rubric_scope_type", ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "organization_id", name="uq_evaluation_id_org"),
        UniqueConstraint("organization_id", "owner_id", "idempotency_key", name="uq_evaluation_idempotency"),
        CheckConstraint("evaluation_type IN ('speech','media','research')", name="ck_evaluation_type"),
        CheckConstraint("status IN ('pending','processing','completed','failed_retryable','failed_terminal','partial','needs_human_review')", name="ck_evaluation_status"),
        CheckConstraint("length(request_fingerprint) = 64", name="ck_evaluation_fingerprint"),
        CheckConstraint("overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)", name="ck_evaluation_score"),
        CheckConstraint("coverage IS NULL OR (coverage >= 0 AND coverage <= 1)", name="ck_evaluation_coverage"),
        Index("ix_evaluation_scoped_read", "organization_id", "owner_id", "created_at"),
    )


class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"
    id: Mapped[UUID] = _pk()
    evaluation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, unique=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", server_default="pending")
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")
    fencing_generation: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    attempt_token: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(nullable=True)
    retry_after: Mapped[datetime | None] = mapped_column(nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        ForeignKeyConstraint(["evaluation_id", "organization_id"], ["evaluations.id", "evaluations.organization_id"], name="fk_job_evaluation_scope", ondelete="RESTRICT"),
        CheckConstraint("status IN ('pending','processing','completed','failed_retryable','failed_terminal')", name="ck_job_status"),
        CheckConstraint("attempts >= 0 AND fencing_generation >= 0", name="ck_job_attempts"),
        CheckConstraint("(status <> 'processing') OR (lease_until IS NOT NULL AND worker_id IS NOT NULL AND attempt_token IS NOT NULL)", name="ck_job_processing_lease"),
        Index("ix_job_claim", "created_at", "id", postgresql_where=text("status IN ('pending','failed_retryable')")),
    )


class CriterionResult(Base):
    __tablename__ = "criterion_results"
    id: Mapped[UUID] = _pk()
    evaluation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    criterion_code: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    encrypted_details: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    __table_args__ = (
        ForeignKeyConstraint(["evaluation_id", "organization_id"], ["evaluations.id", "evaluations.organization_id"], name="fk_criterion_evaluation_scope", ondelete="RESTRICT"),
        UniqueConstraint("evaluation_id", "criterion_code", name="uq_criterion_eval_code"),
        CheckConstraint("(status = 'assessed' AND score BETWEEN 0 AND 5) OR (status = 'not_assessed' AND score IS NULL)", name="ck_criterion_score_status"),
        CheckConstraint("octet_length(encrypted_details) > 0", name="ck_criterion_ciphertext"),
    )


class EvaluationFeedback(Base):
    __tablename__ = "evaluation_feedback"
    id: Mapped[UUID] = _pk()
    evaluation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    revision: Mapped[int] = mapped_column(nullable=False)
    decision_code: Mapped[str] = mapped_column(String(64), nullable=False)
    encrypted_details: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    __table_args__ = (
        ForeignKeyConstraint(["evaluation_id", "organization_id"], ["evaluations.id", "evaluations.organization_id"], name="fk_feedback_evaluation_scope", ondelete="RESTRICT"),
        UniqueConstraint("evaluation_id", "revision", name="uq_feedback_eval_revision"),
        CheckConstraint("revision > 0", name="ck_feedback_revision"),
        CheckConstraint("octet_length(encrypted_details) > 0", name="ck_feedback_ciphertext"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[UUID] = _pk()
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action_code: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    __table_args__ = (Index("ix_audit_scoped_time", "organization_id", "created_at"),)
