"""add fighter photo fields

Revision ID: 83f1bda52f1a
Revises: 586da7944e62
Create Date: 2026-04-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "83f1bda52f1a"
down_revision: Union[str, Sequence[str], None] = "586da7944e62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_STG_FIGHTERS = """
CREATE OR REPLACE VIEW staging.stg_fighters AS
WITH latest_fight AS (
    SELECT fighter_id, weight_class
    FROM (
        SELECT
            fighter_id,
            fi.weight_class,
            ROW_NUMBER() OVER (
                PARTITION BY fighter_id
                ORDER BY e.event_date DESC NULLS LAST, fi.id DESC
            ) AS rn
        FROM (
            SELECT fighter_1_id AS fighter_id, id, event_id, weight_class FROM raw.fights
            UNION ALL
            SELECT fighter_2_id AS fighter_id, id, event_id, weight_class FROM raw.fights
        ) fi
        JOIN raw.events e ON fi.event_id = e.id
        WHERE fi.fighter_id IS NOT NULL
          AND fi.weight_class IS NOT NULL
    ) ranked
    WHERE rn = 1
)
SELECT
    f.id                                            AS fighter_id,
    f.source_id                                     AS fighter_source_id,
    NULLIF(TRIM(f.full_name), '')                   AS fighter_name,
    NULLIF(TRIM(f.first_name), '')                  AS first_name,
    NULLIF(TRIM(f.last_name), '')                   AS last_name,
    NULLIF(TRIM(f.nickname), '')                    AS nickname,
    CASE
        WHEN LOWER(TRIM(f.stance)) IN ('orthodox')          THEN 'Orthodox'
        WHEN LOWER(TRIM(f.stance)) IN ('southpaw')          THEN 'Southpaw'
        WHEN LOWER(TRIM(f.stance)) IN ('switch', 'open stance') THEN 'Switch'
        WHEN f.stance IS NULL OR TRIM(f.stance) = ''        THEN NULL
        ELSE INITCAP(TRIM(f.stance))
    END                                             AS stance_normalized,
    f.height_cm,
    f.reach_cm,
    f.date_of_birth                                 AS birth_date,
    f.wins,
    f.losses,
    f.draws,
    lf.weight_class                                 AS weight_class_current
FROM raw.fighters f
LEFT JOIN latest_fight lf ON f.id = lf.fighter_id
"""


NEW_STG_FIGHTERS = """
CREATE OR REPLACE VIEW staging.stg_fighters AS
WITH latest_fight AS (
    SELECT fighter_id, weight_class
    FROM (
        SELECT
            fighter_id,
            fi.weight_class,
            ROW_NUMBER() OVER (
                PARTITION BY fighter_id
                ORDER BY e.event_date DESC NULLS LAST, fi.id DESC
            ) AS rn
        FROM (
            SELECT fighter_1_id AS fighter_id, id, event_id, weight_class FROM raw.fights
            UNION ALL
            SELECT fighter_2_id AS fighter_id, id, event_id, weight_class FROM raw.fights
        ) fi
        JOIN raw.events e ON fi.event_id = e.id
        WHERE fi.fighter_id IS NOT NULL
          AND fi.weight_class IS NOT NULL
    ) ranked
    WHERE rn = 1
)
SELECT
    f.id                                            AS fighter_id,
    f.source_id                                     AS fighter_source_id,
    NULLIF(TRIM(f.full_name), '')                   AS fighter_name,
    NULLIF(TRIM(f.first_name), '')                  AS first_name,
    NULLIF(TRIM(f.last_name), '')                   AS last_name,
    NULLIF(TRIM(f.nickname), '')                    AS nickname,
    CASE
        WHEN LOWER(TRIM(f.stance)) IN ('orthodox')          THEN 'Orthodox'
        WHEN LOWER(TRIM(f.stance)) IN ('southpaw')          THEN 'Southpaw'
        WHEN LOWER(TRIM(f.stance)) IN ('switch', 'open stance') THEN 'Switch'
        WHEN f.stance IS NULL OR TRIM(f.stance) = ''        THEN NULL
        ELSE INITCAP(TRIM(f.stance))
    END                                             AS stance_normalized,
    f.height_cm,
    f.reach_cm,
    f.date_of_birth                                 AS birth_date,
    f.wins,
    f.losses,
    f.draws,
    lf.weight_class                                 AS weight_class_current,
    NULLIF(TRIM(f.photo_url), '')                   AS photo_url,
    NULLIF(TRIM(f.photo_source), '')                AS photo_source,
    NULLIF(TRIM(f.photo_status), '')                AS photo_status,
    f.photo_last_checked_at
FROM raw.fighters f
LEFT JOIN latest_fight lf ON f.id = lf.fighter_id
"""


def upgrade() -> None:
    op.add_column("fighters", sa.Column("photo_url", sa.Text(), nullable=True), schema="raw")
    op.add_column("fighters", sa.Column("photo_source", sa.Text(), nullable=True), schema="raw")
    op.add_column("fighters", sa.Column("photo_status", sa.Text(), nullable=True), schema="raw")
    op.add_column("fighters", sa.Column("photo_last_checked_at", sa.DateTime(timezone=True), nullable=True), schema="raw")
    op.execute(NEW_STG_FIGHTERS)


def downgrade() -> None:
    op.execute(OLD_STG_FIGHTERS)
    op.drop_column("fighters", "photo_last_checked_at", schema="raw")
    op.drop_column("fighters", "photo_status", schema="raw")
    op.drop_column("fighters", "photo_source", schema="raw")
    op.drop_column("fighters", "photo_url", schema="raw")
