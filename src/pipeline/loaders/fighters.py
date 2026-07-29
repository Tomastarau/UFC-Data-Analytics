import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.pipeline.models.raw import Fighter

logger = logging.getLogger("ufc.loader.fighters")


@dataclass
class UpsertResult:
    inserted: int
    updated: int


def upsert_fighters(session: Session, fighters: list[dict]) -> UpsertResult:
    if not fighters:
        return UpsertResult(0, 0)

    source_ids = [f["source_id"] for f in fighters]
    existing = set(
        row[0]
        for row in session.execute(
            select(Fighter.source_id).where(Fighter.source_id.in_(source_ids))
        )
    )

    now = datetime.now(timezone.utc)
    rows = [{**f, "profile_fetched_at": now} for f in fighters]

    stmt = insert(Fighter.__table__).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["source_id"],
        set_={
            "full_name": stmt.excluded.full_name,
            "nickname": stmt.excluded.nickname,
            "height_cm": stmt.excluded.height_cm,
            "reach_cm": stmt.excluded.reach_cm,
            "stance": stmt.excluded.stance,
            "date_of_birth": stmt.excluded.date_of_birth,
            "weight_class": stmt.excluded.weight_class,
            "wins": stmt.excluded.wins,
            "losses": stmt.excluded.losses,
            "draws": stmt.excluded.draws,
            "raw_payload": stmt.excluded.raw_payload,
            "updated_at": func.now(),
            "profile_fetched_at": stmt.excluded.profile_fetched_at,
        },
    )
    session.execute(stmt)

    updated = sum(1 for sid in source_ids if sid in existing)
    inserted = len(source_ids) - updated
    logger.info("Fighters upserted: %d inserted, %d updated", inserted, updated)
    return UpsertResult(inserted, updated)
