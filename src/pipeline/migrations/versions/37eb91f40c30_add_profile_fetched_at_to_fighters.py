"""add profile fetched at to fighters

Revision ID: 37eb91f40c30
Revises: b59a0ab8c6f2
Create Date: 2026-07-29 13:59:22.374037

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37eb91f40c30'
down_revision: Union[str, Sequence[str], None] = 'b59a0ab8c6f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "fighters",
        sa.Column("profile_fetched_at", sa.DateTime(timezone=True), nullable=True),
        schema="raw",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("fighters", "profile_fetched_at", schema="raw")
