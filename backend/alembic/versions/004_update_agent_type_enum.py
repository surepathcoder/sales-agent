"""Update agent type enum to include missing values.

Revision ID: 004
Revises: 003
Create Date: 2026-06-08

"""
from typing import Sequence, Union
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Commit active transaction since ALTER TYPE ADD VALUE cannot run inside a transaction
    op.execute("COMMIT")
    op.execute("ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'enrichment'")
    op.execute("ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'qualification'")
    op.execute("ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'manager'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing values from an ENUM type easily,
    # so we leave it as a no-op on downgrade.
    pass
