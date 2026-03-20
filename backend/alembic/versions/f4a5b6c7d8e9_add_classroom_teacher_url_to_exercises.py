"""add classroom_teacher_url to exercises

Revision ID: f4a5b6c7d8e9
Revises: 159fc8b4fb51
Create Date: 2026-03-20 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4a5b6c7d8e9"
down_revision: str = "159fc8b4fb51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("classroom_teacher_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("exercises", "classroom_teacher_url")
