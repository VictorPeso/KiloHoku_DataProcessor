"""Create astronomy schema.

Revision ID: 20260626_0001
Revises:
Create Date: 2026-06-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260626_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS "astronomy"')


def downgrade() -> None:
    op.execute('DROP SCHEMA IF EXISTS "astronomy"')
