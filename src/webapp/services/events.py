from sqlalchemy import text
from sqlalchemy.orm import Session


def get_all_events(session: Session) -> list[dict]:
    stmt = text("""
        SELECT
            e.event_name  AS "Event",
            e.event_date  AS "Date",
            e.location    AS "Location",
            e.event_year  AS "Year",
            COUNT(f.fight_id) AS "Fights"
        FROM staging.stg_events e
        LEFT JOIN staging.stg_fights f ON e.event_id = f.event_id
        GROUP BY e.event_id, e.event_name, e.event_date, e.location, e.event_year
        ORDER BY e.event_date DESC
    """)
    return [dict(r._mapping) for r in session.execute(stmt)]


def get_event_years(session: Session) -> list[int]:
    stmt = text("""
        SELECT DISTINCT event_year AS year
        FROM staging.stg_events
        WHERE event_year IS NOT NULL
        ORDER BY event_year DESC
    """)
    return [r.year for r in session.execute(stmt)]


def count_events(session: Session) -> int:
    stmt = text("SELECT COUNT(*) AS cnt FROM staging.stg_events")
    return session.execute(stmt).scalar_one()
