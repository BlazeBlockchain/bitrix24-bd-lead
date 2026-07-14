"""T009: Add full Postgres models per data-model.md (leads, user_memory_profiles, outreach_history, usage_ledger) + indexes + relationships prep.

Adds tables for memory, leads, history, usage. pgvector already enabled in 001.
Matches data-model columns/types exactly (JSONB where json, Text for signals/notes, UUID FKs, etc).
Encrypted stays Text-compatible for vault.

Revision ID: 002
Revises: 001_initial
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# T009: pgvector for embeddings (profile + history). Installed via requirements; extension in 001.
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None  # type: ignore  # fallback only for rare mig gen without pkg

# revision identifiers
revision = "002_add_full_data_model"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: 001_initial.py was later expanded to create ALL tables (leads,
    # user_memory_profiles, outreach_history, usage_ledger) per data-model.md,
    # making this migration's create_table calls duplicates that fail with
    # DuplicateTableError on a fresh database. Kept as a no-op (rather than
    # deleted) to preserve the revision chain for any environment that already
    # has this revision stamped in alembic_version.
    pass


def downgrade() -> None:
    pass
