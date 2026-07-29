"""add ingestion_state table

Revision ID: 220283d0f0c5
Revises: 29582dd407eb
Create Date: 2026-03-24 22:32:12.209040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '220283d0f0c5'
down_revision: Union[str, Sequence[str], None] = '29582dd407eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ingestion_state',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_name', sa.Text(), nullable=False),
    sa.Column('date_from', sa.Date(), nullable=True),
    sa.Column('date_to', sa.Date(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('last_event_date', sa.Date(), nullable=True),
    sa.Column('last_event_source_id', sa.Text(), nullable=True),
    sa.Column('events_inserted', sa.Integer(), nullable=False),
    sa.Column('events_updated', sa.Integer(), nullable=False),
    sa.Column('fighters_inserted', sa.Integer(), nullable=False),
    sa.Column('fighters_updated', sa.Integer(), nullable=False),
    sa.Column('fights_inserted', sa.Integer(), nullable=False),
    sa.Column('fights_updated', sa.Integer(), nullable=False),
    sa.Column('fight_stats_inserted', sa.Integer(), nullable=False),
    sa.Column('fight_stats_updated', sa.Integer(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('error_traceback', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='raw'
    )


def downgrade() -> None:
    op.drop_table('ingestion_state', schema='raw')
