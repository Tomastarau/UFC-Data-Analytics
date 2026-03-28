from sqlalchemy import text
from sqlalchemy.orm import Session


def get_all_fighters(session: Session) -> list[dict]:
    stmt = text("""
        SELECT
            fighter_name        AS "Name",
            nickname            AS "Nickname",
            stance_normalized   AS "Stance",
            weight_class_current AS "Weight Class",
            height_cm           AS "Height (cm)",
            reach_cm            AS "Reach (cm)",
            wins                AS "W",
            losses              AS "L",
            draws               AS "D"
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
