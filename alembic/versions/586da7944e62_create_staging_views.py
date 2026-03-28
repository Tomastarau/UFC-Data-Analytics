"""create staging views

Revision ID: 586da7944e62
Revises: 220283d0f0c5
Create Date: 2026-03-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "586da7944e62"
down_revision: Union[str, Sequence[str], None] = "220283d0f0c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STG_EVENTS = """
CREATE OR REPLACE VIEW staging.stg_events AS
SELECT
    e.id                                            AS event_id,
    e.source_id                                     AS event_source_id,
    NULLIF(TRIM(e.event_name), '')                  AS event_name,
    e.event_date,
    EXTRACT(YEAR FROM e.event_date)::INT            AS event_year,
    EXTRACT(MONTH FROM e.event_date)::INT           AS event_month,
    NULLIF(TRIM(e.location), '')                    AS location,
    NULLIF(TRIM(e.promotion), '')                   AS promotion,
    COALESCE(e.event_name ~* '^UFC\\s+\\d+', false) AS is_numbered_event,
    COALESCE(e.event_name ~* 'Fight Night', false)  AS is_fight_night
FROM raw.events e
"""


STG_FIGHTS = """
CREATE OR REPLACE VIEW staging.stg_fights AS
SELECT
    fi.id                                           AS fight_id,
    fi.source_id                                    AS fight_source_id,
    fi.event_id,
    NULLIF(TRIM(e.event_name), '')                  AS event_name,
    e.event_date,
    EXTRACT(YEAR FROM e.event_date)::INT            AS event_year,
    fi.fighter_1_id,
    f1.full_name                                    AS fighter_1_name,
    fi.fighter_2_id,
    f2.full_name                                    AS fighter_2_name,
    fi.winner_id,
    CASE
        WHEN fi.winner_id IS NOT NULL AND fi.winner_id = fi.fighter_1_id THEN fi.fighter_2_id
        WHEN fi.winner_id IS NOT NULL AND fi.winner_id = fi.fighter_2_id THEN fi.fighter_1_id
        ELSE NULL
    END                                             AS loser_id,
    NULLIF(TRIM(fi.weight_class), '')               AS weight_class,
    fi.gender,
    fi.fight_order,
    fi.scheduled_rounds,
    fi.finish_round,
    fi.finish_time_seconds,
    CASE
        WHEN fi.finish_round IS NOT NULL AND fi.finish_time_seconds IS NOT NULL
        THEN (fi.finish_round - 1) * 300 + fi.finish_time_seconds
        ELSE NULL
    END                                             AS fight_duration_seconds,
    fi.result_method,
    fi.referee,
    CASE
        WHEN fi.result_method ILIKE 'KO/TKO%'       THEN 'KO/TKO'
        WHEN fi.result_method ILIKE 'SUB%'           THEN 'Submission'
        WHEN fi.result_method ILIKE 'Decision%'      THEN 'Decision'
        WHEN fi.result_method ILIKE '%Draw%'
          OR fi.result_method ILIKE '%No Contest%'
          OR fi.result_method ILIKE 'NC%'            THEN 'Draw/NC'
        WHEN fi.result_method IS NULL                THEN NULL
        ELSE 'Other'
    END                                             AS result_method_group,
    COALESCE(fi.title_fight, false)                 AS title_fight,
    COALESCE(fi.performance_bonus, false)           AS performance_bonus,
    COALESCE(fi.fight_of_the_night, false)          AS fight_of_the_night,
    COALESCE(
        fi.result_method ILIKE 'KO/TKO%'
        OR fi.result_method ILIKE 'SUB%',
        false
    )                                               AS is_finish,
    COALESCE(fi.result_method ILIKE 'Decision%', false)
                                                    AS is_decision,
    COALESCE(
        fi.result_method ILIKE '%Draw%'
        OR fi.result_method ILIKE '%No Contest%'
        OR fi.result_method ILIKE 'NC%',
        false
    )                                               AS is_draw_or_nc
FROM raw.fights fi
LEFT JOIN raw.events e    ON fi.event_id = e.id
LEFT JOIN raw.fighters f1 ON fi.fighter_1_id = f1.id
LEFT JOIN raw.fighters f2 ON fi.fighter_2_id = f2.id
"""


STG_FIGHTERS = """
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


STG_FIGHT_STATS = """
CREATE OR REPLACE VIEW staging.stg_fight_stats AS
SELECT
    fs.fight_id,
    fs.fighter_id,
    CASE
        WHEN fi.fighter_1_id = fs.fighter_id THEN fi.fighter_2_id
        WHEN fi.fighter_2_id = fs.fighter_id THEN fi.fighter_1_id
        ELSE NULL
    END                                             AS opponent_id,
    fi.event_id,
    e.event_date,
    NULLIF(TRIM(fi.weight_class), '')               AS weight_class,
    fs.sig_strikes_landed,
    fs.sig_strikes_attempted,
    CASE
        WHEN fs.sig_strikes_attempted > 0
        THEN ROUND(fs.sig_strikes_landed::NUMERIC / fs.sig_strikes_attempted, 3)
        ELSE NULL
    END                                             AS sig_strikes_accuracy,
    opp.sig_strikes_landed                          AS sig_strikes_absorbed,
    fs.sig_strikes_landed - opp.sig_strikes_landed  AS strike_differential,
    fs.total_strikes_landed,
    fs.total_strikes_attempted,
    CASE
        WHEN fs.total_strikes_attempted > 0
        THEN ROUND(fs.total_strikes_landed::NUMERIC / fs.total_strikes_attempted, 3)
        ELSE NULL
    END                                             AS total_strikes_accuracy,
    fs.takedowns_landed,
    fs.takedowns_attempted,
    CASE
        WHEN fs.takedowns_attempted > 0
        THEN ROUND(fs.takedowns_landed::NUMERIC / fs.takedowns_attempted, 3)
        ELSE NULL
    END                                             AS takedown_accuracy,
    opp.takedowns_landed                            AS takedowns_absorbed,
    fs.takedowns_landed - opp.takedowns_landed      AS takedown_differential,
    fs.control_time_seconds,
    fs.knockdowns,
    fs.submissions_attempted
FROM raw.fight_stats fs
JOIN raw.fights fi       ON fs.fight_id = fi.id
LEFT JOIN raw.events e   ON fi.event_id = e.id
LEFT JOIN raw.fight_stats opp
    ON  opp.fight_id  = fs.fight_id
    AND opp.fighter_id != fs.fighter_id
"""


def upgrade() -> None:
    op.add_column('fights', sa.Column('time_format_raw', sa.Text(), nullable=True), schema='raw')
    op.execute("CREATE SCHEMA IF NOT EXISTS staging")
    op.execute(STG_EVENTS)
    op.execute(STG_FIGHTS)
    op.execute(STG_FIGHTERS)
    op.execute(STG_FIGHT_STATS)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS staging.stg_fight_stats")
    op.execute("DROP VIEW IF EXISTS staging.stg_fighters")
    op.execute("DROP VIEW IF EXISTS staging.stg_fights")
    op.execute("DROP VIEW IF EXISTS staging.stg_events")
    op.execute("DROP SCHEMA IF EXISTS staging")
    op.drop_column('fights', 'time_format_raw', schema='raw')
