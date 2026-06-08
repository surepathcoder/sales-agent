"""Update user roles to SaaS standard.

Revision ID: 002
Revises: 001
Create Date: 2026-06-07

"""
from typing import Sequence, Union
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Commit active transaction since ALTER TYPE ADD VALUE cannot run inside a transaction
    op.execute("COMMIT")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'owner'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'manager'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'agent'")
    
    # Migrate data
    op.execute("UPDATE users SET role = 'owner' WHERE role = 'admin'")
    op.execute("UPDATE users SET role = 'manager' WHERE role = 'sales_manager'")
    op.execute("UPDATE users SET role = 'agent' WHERE role = 'sales_rep'")


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'admin' WHERE role = 'owner'")
    op.execute("UPDATE users SET role = 'sales_manager' WHERE role = 'manager'")
    op.execute("UPDATE users SET role = 'sales_rep' WHERE role = 'agent'")
