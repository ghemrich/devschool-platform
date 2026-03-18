"""merge github_token and promotion branches

Revision ID: 159fc8b4fb51
Revises: b3c4d5e6f7a8, e2f3a4b5c6d7
Create Date: 2026-03-18 19:35:55.871028

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "159fc8b4fb51"
down_revision: str | None = ("b3c4d5e6f7a8", "e2f3a4b5c6d7")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
