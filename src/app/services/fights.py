from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.raw import Event, Fight, Fighter


def get_all_fights(session: Session) -> list[dict]:
    f1 = Fighter.__table__.alias("f1")
    f2 = Fighter.__table__.alias("f2")

    stmt = (
        select(
            Event.event_name,
            Event.event_date,
            f1.c.full_name.label("fighter_1"),
            f2.c.full_name.label("fighter_2"),
            Fight.weight_class,
            Fight.result_method,
            Fight.finish_round,
            Fight.referee,
            Fight.title_fight,
        )
        .outerjoin(Event, Fight.event_id == Event.id)
        .outerjoin(f1, Fight.fighter_1_id == f1.c.id)
        .outerjoin(f2, Fight.fighter_2_id == f2.c.id)
        .order_by(Event.event_date.desc(), Fight.fight_order.desc())
    )
    rows = session.execute(stmt).all()
    return [
        {
            "Event": r.event_name,
            "Date": r.event_date,
            "Fighter 1": r.fighter_1,
            "Fighter 2": r.fighter_2,
            "Weight Class": r.weight_class,
            "Method": r.result_method,
            "Round": r.finish_round,
            "Referee": r.referee,
            "Title Fight": r.title_fight,
        }
        for r in rows
    ]


def get_result_methods(session: Session) -> list[str]:
    stmt = (
        select(Fight.result_method)
        .where(Fight.result_method.isnot(None))
        .distinct()
        .order_by(Fight.result_method)
    )
    rows = session.execute(stmt).all()
    return [r[0] for r in rows]


def count_fights(session: Session) -> int:
    stmt = select(func.count()).select_from(Fight)
    return session.execute(stmt).scalar_one()


def finish_rate(session: Session) -> float:
    total = count_fights(session)
    if total == 0:
        return 0.0
    non_decision = session.execute(
        select(func.count())
        .select_from(Fight)
        .where(Fight.result_method.notin_(["Decision - Unanimous", "Decision - Split", "Decision - Majority"]))
        .where(Fight.result_method.isnot(None))
    ).scalar_one()
    return round(non_decision / total * 100, 1)
