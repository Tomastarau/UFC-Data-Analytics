"""add derived fighter fields to staging

Revision ID: b59a0ab8c6f2
Revises: 83f1bda52f1a
Create Date: 2026-04-12 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b59a0ab8c6f2"
down_revision: Union[str, Sequence[str], None] = "83f1bda52f1a"
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
    lf.weight_class                                 AS weight_class_current,
    NULLIF(TRIM(f.photo_url), '')                   AS photo_url,
    NULLIF(TRIM(f.photo_source), '')                AS photo_source,
    NULLIF(TRIM(f.photo_status), '')                AS photo_status,
    f.photo_last_checked_at
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
),
fighter_fights AS (
    SELECT
        fighter_1_id                                AS fighter_id,
        winner_id,
        result_method,
        is_finish,
        is_decision,
        event_date
    FROM staging.stg_fights
    WHERE fighter_1_id IS NOT NULL

    UNION ALL

    SELECT
        fighter_2_id                                AS fighter_id,
        winner_id,
        result_method,
        is_finish,
        is_decision,
        event_date
    FROM staging.stg_fights
    WHERE fighter_2_id IS NOT NULL
),
fighter_summary AS (
    SELECT
        fighter_id,
        COUNT(*)                                    AS total_fights,
        COUNT(*) FILTER (
            WHERE winner_id = fighter_id
        )                                           AS wins_count,
        COUNT(*) FILTER (
            WHERE winner_id IS NOT NULL
              AND winner_id != fighter_id
        )                                           AS losses_count,
        COUNT(*) FILTER (
            WHERE result_method ILIKE '%Draw%'
              AND result_method NOT ILIKE '%No Contest%'
              AND result_method NOT ILIKE 'NC%'
        )                                           AS draws_count,
        ROUND(
            COUNT(*) FILTER (
                WHERE winner_id = fighter_id
            )::NUMERIC
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE winner_id = fighter_id
                       OR (
                           winner_id IS NOT NULL
                           AND winner_id != fighter_id
                       )
                       OR (
                           result_method ILIKE '%Draw%'
                           AND result_method NOT ILIKE '%No Contest%'
                           AND result_method NOT ILIKE 'NC%'
                       )
                ),
                0
            ),
            3
        )                                           AS win_rate,
        COUNT(*) FILTER (
            WHERE winner_id = fighter_id
              AND is_finish
        )                                           AS finish_wins_count,
        COUNT(*) FILTER (
            WHERE winner_id = fighter_id
              AND is_decision
        )                                           AS decision_wins_count,
        MAX(event_date)                             AS last_fight_date
    FROM fighter_fights
    GROUP BY fighter_id
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
    f.photo_last_checked_at,
    COALESCE(fs.total_fights, 0)                    AS total_fights,
    COALESCE(fs.wins_count, 0)                      AS wins_count,
    COALESCE(fs.losses_count, 0)                    AS losses_count,
    COALESCE(fs.draws_count, 0)                     AS draws_count,
    COALESCE(fs.win_rate, 0::NUMERIC)               AS win_rate,
    COALESCE(fs.finish_wins_count, 0)               AS finish_wins_count,
    COALESCE(fs.decision_wins_count, 0)             AS decision_wins_count,
    fs.last_fight_date
FROM raw.fighters f
LEFT JOIN latest_fight lf ON f.id = lf.fighter_id
LEFT JOIN fighter_summary fs ON f.id = fs.fighter_id
"""


def upgrade() -> None:
    op.execute(NEW_STG_FIGHTERS)


def downgrade() -> None:
    op.execute(OLD_STG_FIGHTERS)
