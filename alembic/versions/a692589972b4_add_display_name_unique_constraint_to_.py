"""add display_name unique constraint to users

Revision ID: a692589972b4
Revises: 001
Create Date: 2026-03-22 15:21:26.487944
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a692589972b4'
down_revision: str | None = '001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint('uq_users_display_name', 'users', ['display_name'])


def downgrade() -> None:
    op.drop_constraint('uq_users_display_name', 'users', type_='unique')
