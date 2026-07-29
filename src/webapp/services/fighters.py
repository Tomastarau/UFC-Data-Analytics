from sqlalchemy import text
from sqlalchemy.orm import Session

from src.webapp.formatters import format_fight_duration


def get_all_fighters(session: Session) -> list[dict]:
    stmt = text("""
        SELECT
            fighter_id          AS "ID",
            fighter_name        AS "Name",
            nickname            AS "Nickname",
            stance_normalized   AS "Stance",
            weight_class_current AS "Weight Class",
            height_cm           AS "Height (cm)",
            reach_cm            AS "Reach (cm)",
            wins                AS "W",
            losses              AS "L",
            draws               AS "D",
            photo_url           AS "Photo URL",
            total_fights        AS "Total Fights",
            win_rate            AS "Win Rate",
            finish_wins_count   AS "Finish Wins",
            decision_wins_count AS "Decision Wins",
            last_fight_date     AS "Last Fight"
        FROM staging.stg_fighters
        ORDER BY fighter_name
    """)
    return [dict(r._mapping) for r in session.execute(stmt)]


def get_weight_classes(session: Session) -> list[str]:
    stmt = text("""
        SELECT DISTINCT weight_class_current
        FROM staging.stg_fighters
        WHERE weight_class_current IS NOT NULL
        ORDER BY weight_class_current
    """)
    return [r.weight_class_current for r in session.execute(stmt)]


def count_fighters(session: Session) -> int:
    stmt = text("SELECT COUNT(*) AS cnt FROM staging.stg_fighters")
    return session.execute(stmt).scalar_one()


def get_fighter_directory(session: Session) -> list[dict]:
    stmt = text("""
        SELECT
            fighter_id           AS "ID",
            fighter_name         AS "Name",
            weight_class_current AS "Weight Class"
        FROM staging.stg_fighters
        WHERE fighter_name IS NOT NULL
        ORDER BY fighter_name
    """)
    return [dict(r._mapping) for r in session.execute(stmt)]


def get_fighter_profile(session: Session, fighter_id: int) -> dict | None:
    stmt = text("""
        SELECT
            fighter_id            AS "ID",
            fighter_name          AS "Name",
            first_name            AS "First Name",
            last_name             AS "Last Name",
            nickname              AS "Nickname",
            stance_normalized     AS "Stance",
            weight_class_current  AS "Weight Class",
            height_cm             AS "Height (cm)",
            reach_cm              AS "Reach (cm)",
            birth_date            AS "Birth Date",
            wins                  AS "W",
            losses                AS "L",
            draws                 AS "D",
            photo_url             AS "Photo URL",
            photo_source          AS "Photo Source",
            photo_status          AS "Photo Status",
            total_fights          AS "Total Fights",
            wins_count            AS "UFC W",
            losses_count          AS "UFC L",
            draws_count           AS "UFC D",
            win_rate              AS "Win Rate",
            finish_wins_count     AS "Finish Wins",
            decision_wins_count   AS "Decision Wins",
            last_fight_date       AS "Last Fight"
        FROM staging.stg_fighters
        WHERE fighter_id = :fighter_id
    """)
    row = session.execute(stmt, {"fighter_id": fighter_id}).one_or_none()
    return dict(row._mapping) if row else None


def get_fighter_recent_fights(
    session: Session,
    fighter_id: int,
    limit: int = 5,
) -> list[dict]:
    stmt = text("""
        SELECT
            event_date AS "Date",
            event_name AS "Event",
            CASE
                WHEN fighter_1_id = :fighter_id THEN fighter_2_name
                ELSE fighter_1_name
            END AS "Opponent",
            CASE
                WHEN winner_id = :fighter_id THEN 'Win'
                WHEN result_method ILIKE '%Draw%'
                     AND result_method NOT ILIKE '%No Contest%'
                     AND result_method NOT ILIKE 'NC%' THEN 'Draw'
                WHEN winner_id IS NULL THEN 'No Contest'
                ELSE 'Loss'
            END AS "Result",
            result_method AS "Method",
            weight_class AS "Weight Class",
            title_fight AS "Title Fight",
            scheduled_rounds,
            finish_round,
            finish_time_seconds
        FROM staging.stg_fights
        WHERE fighter_1_id = :fighter_id
           OR fighter_2_id = :fighter_id
        ORDER BY event_date DESC NULLS LAST, fight_order DESC NULLS LAST
        LIMIT :limit
    """)
    rows = []
    params = {"fighter_id": fighter_id, "limit": limit}
    for row in session.execute(stmt, params):
        fight = dict(row._mapping)
        fight["Stop Time"] = format_fight_duration(
            fight.pop("finish_round"),
            fight.pop("finish_time_seconds"),
        )
        fight["Rounds"] = fight.pop("scheduled_rounds")
        rows.append(fight)
    return rows
