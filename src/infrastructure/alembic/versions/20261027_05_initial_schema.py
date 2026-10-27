"""Stage05 candidate schema, organization-scoped and append-only audited.

Revision ID: 20261027_05
Revises:
Create Date: 2026-10-27
"""
from alembic import op

revision = "20261027_05"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE rubric_versions (
            id uuid PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            evaluation_type varchar(16) NOT NULL
                CONSTRAINT ck_rubric_type CHECK (evaluation_type IN ('speech','media','research')),
            code varchar(100) NOT NULL,
            version varchar(50) NOT NULL,
            status varchar(16) NOT NULL DEFAULT 'draft'
                CONSTRAINT ck_rubric_status CHECK (status IN ('draft','published','retired')),
            criteria_snapshot jsonb NOT NULL,
            checksum varchar(64) NOT NULL
                CONSTRAINT ck_rubric_checksum CHECK (length(checksum)=64),
            created_at timestamptz NOT NULL DEFAULT now(),
            published_at timestamptz,
            CONSTRAINT uq_rubric_version UNIQUE (organization_id,evaluation_type,code,version),
            CONSTRAINT uq_rubric_id_scope_type UNIQUE (id,organization_id,evaluation_type),
            CONSTRAINT ck_rubric_publication CHECK (
                (status='draft' AND published_at IS NULL)
                OR (status<>'draft' AND published_at IS NOT NULL))
        )
    """)
    op.execute("""
        CREATE TABLE evaluations (
            id uuid PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            owner_id varchar(128) NOT NULL,
            evaluation_type varchar(16) NOT NULL
                CONSTRAINT ck_evaluation_type CHECK (evaluation_type IN ('speech','media','research')),
            rubric_version_id uuid NOT NULL,
            protected_text_ref uuid NOT NULL,
            idempotency_key varchar(128) NOT NULL,
            request_fingerprint varchar(64) NOT NULL
                CONSTRAINT ck_evaluation_fingerprint CHECK (length(request_fingerprint)=64),
            status varchar(24) NOT NULL DEFAULT 'pending'
                CONSTRAINT ck_evaluation_status CHECK (status IN
                    ('pending','processing','completed','failed_retryable',
                     'failed_terminal','partial','needs_human_review')),
            overall_score numeric(6,3) CONSTRAINT ck_evaluation_score CHECK
                (overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)),
            coverage numeric(5,4) CONSTRAINT ck_evaluation_coverage CHECK
                (coverage IS NULL OR (coverage >= 0 AND coverage <= 1)),
            model_revision varchar(128),
            prompt_version varchar(128),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            completed_at timestamptz,
            CONSTRAINT fk_evaluation_rubric_scope_type FOREIGN KEY
                (rubric_version_id, organization_id, evaluation_type)
                REFERENCES rubric_versions(id, organization_id, evaluation_type) ON DELETE RESTRICT,
            CONSTRAINT uq_evaluation_id_org UNIQUE (id,organization_id),
            CONSTRAINT uq_evaluation_idempotency UNIQUE
                (organization_id,owner_id,idempotency_key)
        )
    """)
    op.execute("CREATE INDEX ix_evaluation_scoped_read ON evaluations (organization_id,owner_id,created_at)")
    op.execute("""
        CREATE TABLE evaluation_jobs (
            id uuid PRIMARY KEY,
            evaluation_id uuid NOT NULL UNIQUE,
            organization_id varchar(128) NOT NULL,
            status varchar(24) NOT NULL DEFAULT 'pending'
                CONSTRAINT ck_job_status CHECK (status IN
                    ('pending','processing','completed','failed_retryable','failed_terminal')),
            attempts smallint NOT NULL DEFAULT 0,
            fencing_generation integer NOT NULL DEFAULT 0,
            attempt_token uuid,
            worker_id varchar(128),
            lease_until timestamptz,
            retry_after timestamptz,
            error_code varchar(64),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_job_attempts CHECK (attempts >= 0 AND fencing_generation >= 0),
            CONSTRAINT ck_job_processing_lease CHECK
                (status <> 'processing' OR (lease_until IS NOT NULL AND worker_id IS NOT NULL AND attempt_token IS NOT NULL)),
            CONSTRAINT fk_job_evaluation_scope FOREIGN KEY (evaluation_id,organization_id)
                REFERENCES evaluations(id,organization_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""CREATE INDEX ix_job_claim ON evaluation_jobs (organization_id,created_at,id)
                  WHERE status IN ('pending','failed_retryable')""")
    op.execute("""
        CREATE TABLE criterion_results (
            id uuid PRIMARY KEY,
            evaluation_id uuid NOT NULL,
            organization_id varchar(128) NOT NULL,
            criterion_code varchar(100) NOT NULL,
            status varchar(16) NOT NULL,
            score smallint,
            encrypted_details bytea NOT NULL
                CONSTRAINT ck_criterion_ciphertext CHECK (octet_length(encrypted_details)>0),
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_criterion_score_status CHECK
                ((status='assessed' AND score BETWEEN 0 AND 5)
                OR (status='not_assessed' AND score IS NULL)),
            CONSTRAINT uq_criterion_eval_code UNIQUE (evaluation_id,criterion_code),
            CONSTRAINT fk_criterion_evaluation_scope FOREIGN KEY (evaluation_id,organization_id)
                REFERENCES evaluations(id,organization_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE evaluation_feedback (
            id uuid PRIMARY KEY,
            evaluation_id uuid NOT NULL,
            organization_id varchar(128) NOT NULL,
            reviewer_id varchar(128) NOT NULL,
            revision integer NOT NULL CONSTRAINT ck_feedback_revision CHECK (revision > 0),
            decision_code varchar(64) NOT NULL,
            encrypted_details bytea NOT NULL
                CONSTRAINT ck_feedback_ciphertext CHECK (octet_length(encrypted_details)>0),
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_feedback_eval_revision UNIQUE (evaluation_id,revision),
            CONSTRAINT fk_feedback_evaluation_scope FOREIGN KEY (evaluation_id,organization_id)
                REFERENCES evaluations(id,organization_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE audit_events (
            id uuid PRIMARY KEY,
            organization_id varchar(128) NOT NULL,
            actor_id varchar(128) NOT NULL,
            action_code varchar(64) NOT NULL,
            resource_kind varchar(32) NOT NULL,
            resource_id uuid NOT NULL,
            correlation_id uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_audit_scoped_time ON audit_events (organization_id,created_at)")
    # Published content cannot be modified, including its identity, timestamps or
    # checksum. Publication can become retired without changing that snapshot.
    op.execute("""
        CREATE FUNCTION stage05_rubric_guard() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            IF OLD.status IN ('published','retired') THEN
              RAISE EXCEPTION 'IMMUTABLE_RUBRIC_VERSION';
            END IF;
            RETURN OLD;
          END IF;
          IF OLD.status IN ('published','retired') THEN
            IF OLD.status='retired' OR NEW.status NOT IN ('published','retired')
              OR (to_jsonb(OLD) - 'status') IS DISTINCT FROM (to_jsonb(NEW) - 'status') THEN
              RAISE EXCEPTION 'IMMUTABLE_RUBRIC_VERSION';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_stage05_rubric_guard
        BEFORE UPDATE OR DELETE ON rubric_versions
        FOR EACH ROW EXECUTE FUNCTION stage05_rubric_guard()
    """)
    op.execute("""
        CREATE FUNCTION stage05_append_only() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'APPEND_ONLY_RECORD';
        END;
        $$ LANGUAGE plpgsql
    """)
    for table in ("criterion_results", "evaluation_feedback", "audit_events"):
        op.execute(f"""
            CREATE TRIGGER trg_stage05_append_{table}
            BEFORE UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION stage05_append_only()
        """)


def downgrade() -> None:
    # Intentionally reject destructive downgrade until owner approves data loss.
    raise RuntimeError("STAGE05_DESTRUCTIVE_DOWNGRADE_REQUIRES_EXPLICIT_APPROVAL")
