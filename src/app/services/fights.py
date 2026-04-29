from sqlalchemy import text
from sqlalchemy.orm import Session

from src.app.formatters import format_fight_duration


def get_all_fights(session: Session) -> list[dict]:
    stmt = text("""
        SELECT
            event_name          AS "Event",
            event_date          AS "Date",
            fighter_1_name      AS "Fighter 1",
            fighter_2_name      AS "Fighter 2",
            weight_class        AS "Weight Class",
            result_method       AS "Method",
            result_method_group AS "Method Group",
            scheduled_rounds,
            finish_round,
            finish_time_seconds,
            referee             AS "Referee",
            title_fight         AS "Title Fight"
        FROM staging.stg_fights
        ORDER BY event_date DESC, fight_order DESC
    """)
    rows = []
    for r in session.execute(stmt):
        row = dict(r._mapping)
        scheduled = row.pop("scheduled_rounds")
        row["Duration"] = f"{scheduled} Rounds" if scheduled else None
        row["Stop Time"] = format_fight_duration(
            row.pop("finish_round"),
            row.pop("finish_time_seconds"),
        )
        rows.append(row)
    return rows


def get_result_methods(session: Session) -> list[str]:
    stmt = text("""
        SELECT DISTINCT result_method_group
        FROM staging.stg_fights
        WHERE result_method_group IS NOT NULL
        ORDER BY result_method_group
    """)
    return [r.result_method_group for r in session.execute(stmt)]


def get_fight_weight_classes(session: Session) -> list[str]:
    stmt = text("""
        SELECT DISTINCT weight_class
        FROM staging.stg_fights
        WHERE weight_class IS NOT NULL
        ORDER BY weight_class
    """)
    return [r.weight_class for r in session.execute(stmt)]


def count_fights(session: Session) -> int:
    stmt = text("SELECT COUNT(*) AS cnt FROM staging.stg_fights")
    return session.execute(stmt).scalar_one()


def finish_rate(session: Session) -> float:
    stmt = text("""
        SELECT
            COUNT(*) FILTER (WHERE is_finish) AS finishes,
            COUNT(*) AS total
        FROM staging.stg_fights
        WHERE result_method IS NOT NULL
    """)
    row = session.execute(stmt).one()
    if row.total == 0:
        return 0.0
    return round(row.finishes / row.total * 100, 1)
