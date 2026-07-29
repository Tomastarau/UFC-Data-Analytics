import logging
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.pipeline.models.raw import Event, Fighter, Fight

logger = logging.getLogger("ufc.loader.fights")


@dataclass
class UpsertResult:
    inserted: int
    updated: int


def _resolve_foreign_keys(session: Session, fights: list[dict]) -> list[dict]:
    event_sids = {f["event_source_id"] for f in fights if f.get("event_source_id")}
    event_map: dict[str, int] = {}
    if event_sids:
        rows = session.execute(
            select(Event.source_id, Event.id).where(Event.source_id.in_(event_sids))
        )
        event_map = {r[0]: r[1] for r in rows}

    fighter_sids: set[str] = set()
    for f in fights:
        for key in ("fighter_1_source_id", "fighter_2_source_id", "winner_source_id"):
            if f.get(key):
                fighter_sids.add(f[key])

    fighter_map: dict[str, int] = {}
    if fighter_sids:
        rows = session.execute(
            select(Fighter.source_id, Fighter.id).where(
                Fighter.source_id.in_(fighter_sids)
            )
        )
        fighter_map = {r[0]: r[1] for r in rows}

    for f in fights:
        f["event_id"] = event_map.get(f.get("event_source_id"))
        f["fighter_1_id"] = fighter_map.get(f.get("fighter_1_source_id"))
        f["fighter_2_id"] = fighter_map.get(f.get("fighter_2_source_id"))
        f["winner_id"] = fighter_map.get(f.get("winner_source_id"))

    return fights


def upsert_fights(session: Session, fights: list[dict]) -> UpsertResult:
    if not fights:
        return UpsertResult(0, 0)

    fights = _resolve_foreign_keys(session, fights)

    source_ids = [f["source_id"] for f in fights]
    existing = set(
        row[0]
        for row in session.execute(
            select(Fight.source_id).where(Fight.source_id.in_(source_ids))
        )
    )

    stmt = insert(Fight.__table__).values(fights)
    stmt = stmt.on_conflict_do_update(
        index_elements=["source_id"],
        set_={
            "event_id": stmt.excluded.event_id,
            "fighter_1_id": stmt.excluded.fighter_1_id,
            "fighter_2_id": stmt.excluded.fighter_2_id,
            "winner_source_id": stmt.excluded.winner_source_id,
            "winner_id": stmt.excluded.winner_id,
            "weight_class": stmt.excluded.weight_class,
            "gender": stmt.excluded.gender,
            "fight_order": stmt.excluded.fight_order,
            "scheduled_rounds": stmt.excluded.scheduled_rounds,
            "time_format_raw": stmt.excluded.time_format_raw,
            "finish_round": stmt.excluded.finish_round,
            "finish_time_seconds": stmt.excluded.finish_time_seconds,
            "result_method": stmt.excluded.result_method,
            "result_details": stmt.excluded.result_details,
            "referee": stmt.excluded.referee,
            "title_fight": stmt.excluded.title_fight,
            "performance_bonus": stmt.excluded.performance_bonus,
            "fight_of_the_night": stmt.excluded.fight_of_the_night,
            "raw_payload": stmt.excluded.raw_payload,
            "updated_at": func.now(),
        },
    )
    session.execute(stmt)

    updated = sum(1 for sid in source_ids if sid in existing)
    inserted = len(source_ids) - updated
    logger.info("Fights upserted: %d inserted, %d updated", inserted, updated)
    return UpsertResult(inserted, updated)
