"""add github_token and classroom_url fields

Revision ID: a1b2c3d4e5f6
Revises: cefa39428d67
Create Date: 2026-03-10 22:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "cefa39428d67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("github_token", sa.String(), nullable=True))
    op.add_column("exercises", sa.Column("classroom_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("exercises", "classroom_url")
    op.drop_column("users", "github_token")
