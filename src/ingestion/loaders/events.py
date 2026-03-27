import logging
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.models.raw import Event

logger = logging.getLogger("ufc.loader.events")


@dataclass
class UpsertResult:
    inserted: int
    updated: int


def upsert_events(session: Session, events: list[dict]) -> UpsertResult:
    if not events:
        return UpsertResult(0, 0)

    source_ids = [e["source_id"] for e in events]
    existing = set(
        row[0]
        for row in session.execute(
            select(Event.source_id).where(Event.source_id.in_(source_ids))
        )
    )

    stmt = insert(Event.__table__).values(events)
    stmt = stmt.on_conflict_do_update(
        index_elements=["source_id"],
        set_={
            "event_name": stmt.excluded.event_name,
            "event_date": stmt.excluded.event_date,
            "location": stmt.excluded.location,
            "promotion": stmt.excluded.promotion,
            "raw_payload": stmt.excluded.raw_payload,
            "updated_at": func.now(),
        },
    )
    session.execute(stmt)

    updated = sum(1 for sid in source_ids if sid in existing)
    inserted = len(source_ids) - updated
    logger.info("Events upserted: %d inserted, %d updated", inserted, updated)
    return UpsertResult(inserted, updated)
