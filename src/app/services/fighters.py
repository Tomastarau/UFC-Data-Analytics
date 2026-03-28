from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.raw import Fighter


def get_all_fighters(session: Session) -> list[dict]:
    stmt = (
        select(
            Fighter.full_name,
            Fighter.nickname,
            Fighter.stance,
            Fighter.weight_class,
            Fighter.height_cm,
            Fighter.reach_cm,
            Fighter.wins,
            Fighter.losses,
            Fighter.draws,
        )
        .order_by(Fighter.full_name)
    )
    rows = session.execute(stmt).all()
    return [
        {
            "Name": r.full_name,
            "Nickname": r.nickname,
            "Stance": r.stance,
            "Weight Class": r.weight_class,
            "Height (cm)": r.height_cm,
            "Reach (cm)": r.reach_cm,
            "W": r.wins,
            "L": r.losses,
            "D": r.draws,
        }
        for r in rows
    ]


def get_weight_classes(session: Session) -> list[str]:
    stmt = (
        select(Fighter.weight_class)
        .where(Fighter.weight_class.isnot(None))
        .distinct()
        .order_by(Fighter.weight_class)
    )
    rows = session.execute(stmt).all()
    return [r[0] for r in rows]


def count_fighters(session: Session) -> int:
    stmt = select(func.count()).select_from(Fighter)
    return session.execute(stmt).scalar_one()
