"""Initial migration stub (T004).

Creates tables for stub models (users, crm_connections) per data-model.md.
Use `alembic revision --autogenerate` later to expand.

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
    # Enable pgvector extension (for future memory profiles; harmless if already enabled)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("google_sub", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

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

    # Add indexes (mirrors data-model guidance)
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_crm_connections_user_id", "crm_connections", ["user_id"])


def downgrade() -> None:
    op.drop_table("crm_connections")
    op.drop_table("users")
    # Do not drop extension on downgrade
