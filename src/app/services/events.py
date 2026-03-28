from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.raw import Event, Fight


def get_all_events(session: Session) -> list[dict]:
    fight_count = (
        select(Fight.event_id, func.count().label("fight_count"))
        .group_by(Fight.event_id)
        .subquery()
    )
    stmt = (
        select(
            Event.event_name,
            Event.event_date,
            Event.location,
            fight_count.c.fight_count,
        )
        .outerjoin(fight_count, Event.id == fight_count.c.event_id)
        .order_by(Event.event_date.desc())
    )
    rows = session.execute(stmt).all()
    return [
        {
            "Event": r.event_name,
            "Date": r.event_date,
            "Location": r.location,
            "Fights": r.fight_count or 0,
        }
        for r in rows
    ]


def get_event_years(session: Session) -> list[int]:
    stmt = (
        select(func.extract("year", Event.event_date).label("year"))
        .where(Event.event_date.isnot(None))
        .distinct()
        .order_by(func.extract("year", Event.event_date).desc())
    )
    rows = session.execute(stmt).all()
    return [int(r.year) for r in rows]


def count_events(session: Session) -> int:
    stmt = select(func.count()).select_from(Event)
    return session.execute(stmt).scalar_one()
