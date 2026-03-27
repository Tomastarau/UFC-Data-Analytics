import logging
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.models.raw import Fight, Fighter, FightStats

logger = logging.getLogger("ufc.loader.fight_stats")


@dataclass
class UpsertResult:
    inserted: int
    updated: int


def _resolve_foreign_keys(session: Session, stats: list[dict]) -> list[dict]:
    fight_sids = {s["fight_source_id"] for s in stats if s.get("fight_source_id")}
    fight_map: dict[str, int] = {}
    if fight_sids:
        rows = session.execute(
            select(Fight.source_id, Fight.id).where(Fight.source_id.in_(fight_sids))
        )
        fight_map = {r[0]: r[1] for r in rows}

    fighter_sids = {s["fighter_source_id"] for s in stats if s.get("fighter_source_id")}
    fighter_map: dict[str, int] = {}
    if fighter_sids:
        rows = session.execute(
            select(Fighter.source_id, Fighter.id).where(
                Fighter.source_id.in_(fighter_sids)
            )
        )
        fighter_map = {r[0]: r[1] for r in rows}

    resolved = []
    for s in stats:
        fight_id = fight_map.get(s.get("fight_source_id"))
        fighter_id = fighter_map.get(s.get("fighter_source_id"))
        if fight_id is None or fighter_id is None:
            logger.warning(
                "Skipping stats: fight_source_id=%s fighter_source_id=%s (FK not found)",
                s.get("fight_source_id"),
                s.get("fighter_source_id"),
            )
            continue
        row = {k: v for k, v in s.items() if k not in ("fight_source_id", "fighter_source_id")}
        row["fight_id"] = fight_id
        row["fighter_id"] = fighter_id
        resolved.append(row)

    return resolved


def upsert_fight_stats(session: Session, stats: list[dict]) -> UpsertResult:
    if not stats:
        return UpsertResult(0, 0)

    resolved = _resolve_foreign_keys(session, stats)
    if not resolved:
        return UpsertResult(0, 0)

    pairs = [(r["fight_id"], r["fighter_id"]) for r in resolved]
    existing: set[tuple[int, int]] = set()
    for fight_id, fighter_id in pairs:
        rows = session.execute(
            select(FightStats.fight_id, FightStats.fighter_id).where(
                FightStats.fight_id == fight_id,
                FightStats.fighter_id == fighter_id,
            )
        )
        for r in rows:
            existing.add((r[0], r[1]))

    stmt = insert(FightStats.__table__).values(resolved)
    stmt = stmt.on_conflict_do_update(
        constraint="fight_stats_fight_id_fighter_id_key",
        set_={
            "knockdowns": stmt.excluded.knockdowns,
            "sig_strikes_landed": stmt.excluded.sig_strikes_landed,
            "sig_strikes_attempted": stmt.excluded.sig_strikes_attempted,
            "total_strikes_landed": stmt.excluded.total_strikes_landed,
            "total_strikes_attempted": stmt.excluded.total_strikes_attempted,
            "takedowns_landed": stmt.excluded.takedowns_landed,
            "takedowns_attempted": stmt.excluded.takedowns_attempted,
            "submissions_attempted": stmt.excluded.submissions_attempted,
            "reversals": stmt.excluded.reversals,
            "control_time_seconds": stmt.excluded.control_time_seconds,
            "head_strikes_landed": stmt.excluded.head_strikes_landed,
            "head_strikes_attempted": stmt.excluded.head_strikes_attempted,
            "body_strikes_landed": stmt.excluded.body_strikes_landed,
            "body_strikes_attempted": stmt.excluded.body_strikes_attempted,
            "leg_strikes_landed": stmt.excluded.leg_strikes_landed,
            "leg_strikes_attempted": stmt.excluded.leg_strikes_attempted,
            "distance_strikes_landed": stmt.excluded.distance_strikes_landed,
            "distance_strikes_attempted": stmt.excluded.distance_strikes_attempted,
            "clinch_strikes_landed": stmt.excluded.clinch_strikes_landed,
            "clinch_strikes_attempted": stmt.excluded.clinch_strikes_attempted,
            "ground_strikes_landed": stmt.excluded.ground_strikes_landed,
            "ground_strikes_attempted": stmt.excluded.ground_strikes_attempted,
            "raw_payload": stmt.excluded.raw_payload,
            "updated_at": func.now(),
        },
    )
    session.execute(stmt)

    updated = sum(1 for p in pairs if p in existing)
    inserted = len(pairs) - updated
    logger.info("Fight stats upserted: %d inserted, %d updated", inserted, updated)
    return UpsertResult(inserted, updated)
