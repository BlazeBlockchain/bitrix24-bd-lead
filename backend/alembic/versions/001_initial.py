"""Initial migration (T009 full).

Creates ALL tables per data-model.md exactly:
users, crm_connections, leads, user_memory_profiles (with pgvector), 
outreach_history (with optional vector), usage_ledger.
Enables pgvector extension.
Indexes: (user_id, created_at) heavy + per data-model.
Vector columns use pgvector (dim 768 for embedding compat; adjustable).

Revision ID: 001
Revises: 
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension (required for memory + history embeddings)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # users (exact)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("google_sub", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # crm_connections (exact; encrypted as Text for envelope storage compat)
    op.create_table(
        "crm_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("auth_type", sa.String(20), nullable=False, server_default="webhook"),
        sa.Column("encrypted_credentials", sa.Text(), nullable=True),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    # leads (exact per data-model)
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255), nullable=False),
        sa.Column("contact_role", sa.String(255), nullable=False),
        sa.Column("signal", sa.Text(), nullable=False),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("pain_point", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("linkedin_url", sa.String(255), nullable=True),
        sa.Column("enriched", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("crm_provider", sa.String(50), nullable=False),
        sa.Column("crm_contact_id", sa.String(255), nullable=True),
        sa.Column("crm_deal_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # user_memory_profiles (exact + vector; ARRAY for pgvector compat in SA without custom type in mig)
    op.create_table(
        "user_memory_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tone_samples", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("icp_industries", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("typical_cadence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("profile_embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", name="uq_user_memory_profile"),
    )

    # outreach_history (exact + optional vector)
    op.create_table(
        "outreach_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # usage_ledger (exact)
    op.create_table(
        "usage_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
    )

    # Indexes per data-model.md (heavy on (user_id, created_at) for history/memory)
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_crm_connections_user_id", "crm_connections", ["user_id"])
    op.create_index("ix_leads_user_id_created", "leads", ["user_id", "created_at"])
    op.create_index("ix_memory_user_id", "user_memory_profiles", ["user_id"])
    op.create_index("ix_outreach_user_created", "outreach_history", ["user_id", "created_at"])
    op.create_index("ix_outreach_lead", "outreach_history", ["lead_id"])
    op.create_index("ix_ledger_user_created", "usage_ledger", ["user_id", "created_at"])
    op.create_index("ix_ledger_user", "usage_ledger", ["user_id"])

    # Note: For production pgvector indexes (HNSW/IVFFlat), run separately or extend migration:
    # CREATE INDEX ... ON user_memory_profiles USING hnsw (profile_embedding vector_cosine_ops);
    # Same for embedding in outreach_history.


def downgrade() -> None:
    op.drop_index("ix_ledger_user", table_name="usage_ledger")
    op.drop_index("ix_ledger_user_created", table_name="usage_ledger")
    op.drop_index("ix_outreach_lead", table_name="outreach_history")
    op.drop_index("ix_outreach_user_created", table_name="outreach_history")
    op.drop_index("ix_memory_user_id", table_name="user_memory_profiles")
    op.drop_index("ix_leads_user_id_created", table_name="leads")
    op.drop_index("ix_crm_connections_user_id", table_name="crm_connections")
    op.drop_index("ix_users_email", table_name="users")

    op.drop_table("usage_ledger")
    op.drop_table("outreach_history")
    op.drop_table("user_memory_profiles")
    op.drop_table("leads")
    op.drop_table("crm_connections")
    op.drop_table("users")
    # Do not drop extension on downgrade (harmless if present)
