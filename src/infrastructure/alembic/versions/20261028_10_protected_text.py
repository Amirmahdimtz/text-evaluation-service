"""Stage10 isolated encrypted original-text storage and SQL admission limit.

Revision ID: 20261028_10
Revises: 20261027_05
No data-destructive downgrade is authorized.
"""
from alembic import op

revision = "20261028_10"
down_revision = "20261027_05"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
      CREATE TABLE protected_texts (
        id uuid PRIMARY KEY,
        organization_id varchar(128) NOT NULL,
        owner_id varchar(128) NOT NULL,
        key_id varchar(128) NOT NULL,
        ciphertext bytea NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_protected_text_scope UNIQUE(id, organization_id, owner_id),
        CONSTRAINT ck_protected_text_ciphertext CHECK(octet_length(ciphertext)>=29)
      )
    """)
    op.execute("CREATE INDEX ix_protected_text_scope ON protected_texts (organization_id,owner_id,id)")
    op.execute("""
      CREATE TRIGGER trg_stage10_protected_text_immutable
      BEFORE UPDATE OR DELETE ON protected_texts
      FOR EACH ROW EXECUTE FUNCTION stage05_append_only()
    """)

def downgrade() -> None:
    raise RuntimeError("STAGE10_DESTRUCTIVE_DOWNGRADE_REQUIRES_EXPLICIT_APPROVAL")
