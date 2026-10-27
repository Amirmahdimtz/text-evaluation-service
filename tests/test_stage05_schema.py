"""Stage05 offline metadata, security and Alembic DDL contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect as pg_dialect
from sqlalchemy.schema import CreateTable

from src.infrastructure.context.sql_db.psql_dbcontext import Base, get_test_database_url
from src.infrastructure.models import text_evaluation  # noqa: F401


MODELS = {
    "rubric_versions", "evaluations", "evaluation_jobs",
    "criterion_results", "evaluation_feedback", "audit_events",
}
ROOT = Path(__file__).resolve().parents[1]


def test_stage05_metadata_has_expected_tables_and_scope_constraints():
    assert set(Base.metadata.tables) == MODELS
    tables = Base.metadata.tables
    for name in MODELS:
        assert "organization_id" in tables[name].c
        assert "id" in tables[name].c
    for name, fk_name in (
        ("evaluations", "fk_evaluation_rubric_scope_type"),
        ("evaluation_jobs", "fk_job_evaluation_scope"),
        ("criterion_results", "fk_criterion_evaluation_scope"),
        ("evaluation_feedback", "fk_feedback_evaluation_scope"),
    ):
        fk = next(c for c in tables[name].constraints
                  if isinstance(c, ForeignKeyConstraint) and c.name == fk_name)
        assert "organization_id" in {col.name for col in fk.columns}
    for name, index in (
        ("evaluations", "ix_evaluation_scoped_read"),
        ("evaluation_jobs", "ix_job_claim"),
        ("audit_events", "ix_audit_scoped_time"),
    ):
        assert index in {item.name for item in tables[name].indexes}


def test_stage05_timestamps_aware_and_pg_ddl_compilable():
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if (column.name.endswith("_at") or column.name in ("lease_until", "retry_after", "published_at")):
                assert isinstance(column.type, DateTime)
                assert column.type.timezone is True
        ddl = str(CreateTable(table).compile(dialect=pg_dialect()))
        assert "CREATE TABLE" in ddl
    rubric_ddl = str(CreateTable(Base.metadata.tables["rubric_versions"]).compile(dialect=pg_dialect()))
    assert "ck_rubric_publication" in rubric_ddl
    assert "uq_rubric_id_scope_type" in rubric_ddl


def test_stage05_never_store_plaintext_submissions_or_feedback():
    for table in Base.metadata.tables.values():
        column_names = set(table.c.keys())
        assert not column_names & {
            "source_text", "raw_text", "reason", "evidence_quote", "prompt",
            "model_response", "reviewer_comment", "api_key", "password",
        }
    from sqlalchemy.dialects.postgresql import UUID as PGUUID, BYTEA
    assert isinstance(Base.metadata.tables["evaluations"].c.protected_text_ref.type, PGUUID)
    assert isinstance(Base.metadata.tables["criterion_results"].c.encrypted_details.type, BYTEA)
    assert isinstance(Base.metadata.tables["evaluation_feedback"].c.encrypted_details.type, BYTEA)


@pytest.mark.parametrize("url", (
    "", "sqlite+aiosqlite:///:memory:",
    "postgresql+asyncpg://user@simorgh/tes_stage05_fake",
    "postgresql+asyncpg://user@127.0.0.1/postgres",
    "postgresql+psycopg://user@127.0.0.1/tes_stage05_tmp",
    "postgresql+asyncpg://user@127.0.0.1/tes_stage05_tmp?sslmode=disable",
))
def test_stage05_database_preflight_rejects_unapproved_targets(monkeypatch, url):
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    monkeypatch.setenv("TES_STAGE05_DATABASE_URL", url)
    with pytest.raises(ValueError, match="STAGE05_ISOLATED_DATABASE_URL_REQUIRED"):
        get_test_database_url()


def test_stage05_database_preflight_blocks_non_dev(monkeypatch):
    monkeypatch.setenv("TES_ENVIRONMENT", "production")
    monkeypatch.setenv("TES_STAGE05_DATABASE_URL",
                       "postgresql+asyncpg://synthetic@127.0.0.1/tes_stage05_sandbox")
    with pytest.raises(ValueError, match="STAGE05_LOCAL_DATABASE_ONLY"):
        get_test_database_url()


def test_stage05_database_preflight_allows_explicit_local_test_only(monkeypatch):
    url = "postgresql+asyncpg://synthetic@127.0.0.1/tes_stage05_sandbox"
    monkeypatch.setenv("TES_ENVIRONMENT", "development")
    monkeypatch.setenv("TES_STAGE05_DATABASE_URL", url)
    assert get_test_database_url() == url


def test_stage05_migration_has_guarded_ddl_and_no_destructive_downgrade():
    source = (ROOT / "src/infrastructure/alembic/versions/20261027_05_initial_schema.py").read_text()
    assert "CREATE TRIGGER trg_stage05_rubric_guard" in source
    assert "CREATE TRIGGER trg_stage05_append_" in source
    assert "FOR UPDATE" not in source or "SKIP LOCKED" not in source
    assert "STAGE05_DESTRUCTIVE_DOWNGRADE_REQUIRES_EXPLICIT_APPROVAL" in source
    runner = (ROOT / "scripts/verification/run_stage05_migrations.py").read_text()
    assert 'choices=("current", "upgrade")' in runner
    assert 'get_test_database_url()' in runner


def test_stage05_index_and_status_checks():
    tables = Base.metadata.tables
    for name in ("rubric_versions", "evaluations", "evaluation_jobs", "criterion_results"):
        assert any(isinstance(c, CheckConstraint) for c in tables[name].constraints)
    job_index = next(x for x in tables["evaluation_jobs"].indexes if x.name == "ix_job_claim")
    assert job_index.dialect_options["postgresql"]["where"] is not None
    assert any(isinstance(c, UniqueConstraint) and c.name == "uq_evaluation_idempotency"
               for c in tables["evaluations"].constraints)
