"""Stage 05 persistence candidates; never expose ORM entities as API DTOs."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, Numeric,
    String, Text, UniqueConstraint, Uuid, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.context.sql_db.psql_dbcontext import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RubricVersion(Base):
    __tablename__ = "rubric_versions"
    __table_args__ = (
        UniqueConstraint("organization_id", "evaluation_type", "version", name="uq_rubric_scope_type_version"),
        CheckConstraint("evaluation_type IN ('speech','media','research')", name="ck_rubric_type"),
        CheckConstraint("status IN ('draft','published','retired')", name="ck_rubric_status"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    evaluation_type: Mapped[str] = mapped_column(String(16), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    criteria_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint("evaluation_type IN ('speech','media','research')", name="ck_evaluation_type"),
        CheckConstraint("processing_status IN ('pending','processing','completed','failed_retryable','failed_terminal')", name="ck_evaluation_status"),
        CheckConstraint("result_status IS NULL OR result_status IN ('assessed','partial','not_assessed')", name="ck_evaluation_result_status"),
        CheckConstraint("overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 5)", name="ck_evaluation_score"),
        CheckConstraint("coverage IS NULL OR (coverage >= 0 AND coverage <= 1)", name="ck_evaluation_coverage"),
        Index("ix_evaluation_scope_created", "organization_id", "owner_id", "created_at"),
        UniqueConstraint("organization_id", "owner_id", "idempotency_key", name="uq_evaluation_scope_idempotency"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False)
    evaluation_type: Mapped[str] = mapped_column(String(16), nullable=False)
    rubric_version_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("rubric_versions.id", ondelete="RESTRICT"), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    result_status: Mapped[str | None] = mapped_column(String(24))
    overall_score: Mapped[float | None] = mapped_column(Numeric(5, 3, asdecimal=True))
    coverage: Mapped[float | None] = mapped_column(Numeric(5, 4, asdecimal=True))
    model_revision: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now(), nullable=False)

class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"
    __table_args__ = (
        CheckConstraint("status IN ('pending','processing','completed','failed_retryable','failed_terminal')", name="ck_job_status"),
        CheckConstraint("attempt_count >= 0 AND fencing_token >= 0", name="ck_job_counters"),
        Index("ix_job_claim", "status", "retry_after", "lease_until"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fencing_token: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    worker_id: Mapped[str | None] = mapped_column(String(128))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retry_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    safe_error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, server_default=func.now(), nullable=False)

class CriterionResult(Base):
    __tablename__ = "criterion_results"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "criterion_code", name="uq_criterion_evaluation_code"),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 5)", name="ck_criterion_score"),
        CheckConstraint("status IN ('assessed','not_assessed','not_applicable')", name="ck_criterion_status"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_code: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 3, asdecimal=True))
    reason: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSON)
    recommendations: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)

class EvaluationFeedback(Base):
    __tablename__ = "evaluation_feedback"
    __table_args__ = (UniqueConstraint("evaluation_id", "revision", name="uq_feedback_revision"), CheckConstraint("revision > 0", name="ck_feedback_revision"))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_scope_time", "organization_id", "created_at"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    correlation_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)
