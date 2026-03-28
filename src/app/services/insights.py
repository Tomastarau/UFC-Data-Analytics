from sqlalchemy import text
from sqlalchemy.orm import Session


def get_ko_tko_by_year(session: Session) -> list[dict]:
    stmt = text("""
        SELECT event_year AS "Year", COUNT(*) AS "Count"
        FROM staging.stg_fights
        WHERE result_method_group = 'KO/TKO'
          AND event_year IS NOT NULL
        GROUP BY event_year
        ORDER BY event_year
    """)
    return [dict(r._mapping) for r in session.execute(stmt)]


def get_fights_by_year(session: Session) -> list[dict]:
    stmt = text("""
        SELECT event_year AS "Year", COUNT(*) AS "Count"
        FROM staging.stg_fights
        WHERE event_year IS NOT NULL
        GROUP BY event_year
        ORDER BY event_year
    """)
    return [dict(r._mapping) for r in session.execute(stmt)]
