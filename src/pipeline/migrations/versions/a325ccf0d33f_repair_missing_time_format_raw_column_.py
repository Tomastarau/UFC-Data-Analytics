"""repair missing time_format_raw column on fights

Revision ID: a325ccf0d33f
Revises: 37eb91f40c30
Create Date: 2026-07-29 14:06:51.490926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a325ccf0d33f'
down_revision: Union[str, Sequence[str], None] = '37eb91f40c30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add raw.fights.time_format_raw if it is missing.

    Revision 586da7944e62 declares this column in its upgrade(), and is recorded as
    applied, yet the column is absent from the database. The most likely cause is that
    the add_column line was appended to that migration file after it had already run.
    The model (models/raw.py) and the loader (loaders/fights.py) both reference the
    column, so every fight upsert has been failing since it was declared.

    Guarded with IF NOT EXISTS so it is a no-op on databases where 586da7944e62 did
    create the column.
    """
    op.execute("ALTER TABLE raw.fights ADD COLUMN IF NOT EXISTS time_format_raw TEXT")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE raw.fights DROP COLUMN IF EXISTS time_format_raw")
