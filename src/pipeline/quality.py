import logging

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.pipeline.models.raw import Event, Fight, FightStats, Fighter

logger = logging.getLogger("ufc.quality")


def check_event_uniqueness(session: Session) -> list[str]:
    stmt = (
        select(Event.source_id, func.count().label("cnt"))
        .group_by(Event.source_id)
        .having(func.count() > 1)
    )
    rows = session.execute(stmt).all()
    return [f"Duplicate event source_id: {r[0]} (count={r[1]})" for r in rows]


def check_fight_uniqueness(session: Session) -> list[str]:
    stmt = (
        select(Fight.source_id, func.count().label("cnt"))
        .group_by(Fight.source_id)
        .having(func.count() > 1)
    )
    rows = session.execute(stmt).all()
    return [f"Duplicate fight source_id: {r[0]} (count={r[1]})" for r in rows]


def check_fighter_mapping(session: Session) -> list[str]:
    stmt = select(Fight.source_id).where(
        (Fight.fighter_1_id.is_(None) & Fight.fighter_1_source_id.isnot(None))
        | (Fight.fighter_2_id.is_(None) & Fight.fighter_2_source_id.isnot(None))
    )
    rows = session.execute(stmt).all()
    return [f"Fight {r[0]}: fighter FK not resolved" for r in rows]


def check_missing_stats(session: Session) -> list[str]:
    stmt = (
        select(Fight.source_id)
        .outerjoin(FightStats, Fight.id == FightStats.fight_id)
        .where(FightStats.id.is_(None))
    )
    rows = session.execute(stmt).all()
    return [f"Fight {r[0]}: no fight_stats rows" for r in rows]


def check_orphan_fights(session: Session) -> list[str]:
    stmt = select(Fight.source_id).where(Fight.event_id.is_(None))
    rows = session.execute(stmt).all()
    return [f"Fight {r[0]}: event_id is NULL" for r in rows]


STALE_PROFILES_CHECK_SQL = text("""
    select f.source_id, f.full_name, max(e.event_date) as last_fight, f.profile_fetched_at
    from raw.fighters f
    join raw.fights ft on f.id in (ft.fighter_1_id, ft.fighter_2_id)
    join raw.events e on e.id = ft.event_id
    where e.event_date is not null
    group by f.id, f.source_id, f.full_name, f.profile_fetched_at
    having f.profile_fetched_at is null
        or max(e.event_date) > f.profile_fetched_at::date
""")


def check_stale_fighter_profiles(session: Session) -> list[str]:
    rows = session.execute(STALE_PROFILES_CHECK_SQL).all()
    return [
        f"Fighter {r[1]} ({r[0]}): last fight {r[2]}, profile read {r[3]}"
        for r in rows
    ]


def run_all_checks(session: Session) -> dict[str, list[str]]:
    checks = {
        "event_uniqueness": check_event_uniqueness,
        "fight_uniqueness": check_fight_uniqueness,
        "fighter_mapping": check_fighter_mapping,
        "missing_stats": check_missing_stats,
        "orphan_fights": check_orphan_fights,
        "stale_fighter_profiles": check_stale_fighter_profiles,
    }
    results = {}
    for name, check_fn in checks.items():
        issues = check_fn(session)
        results[name] = issues
        if issues:
            logger.warning("Check %s: %d issues found", name, len(issues))
        else:
            logger.info("Check %s: OK", name)
    return results
