from sqlalchemy import select
from sqlalchemy.orm import Session

from src.ingestion.quality import run_all_checks
from src.models.ingestion import IngestionState


def get_quality_results(session: Session) -> dict[str, list[str]]:
    return run_all_checks(session)


def get_last_ingestion(session: Session) -> dict | None:
    stmt = (
        select(IngestionState)
        .order_by(IngestionState.started_at.desc())
        .limit(1)
    )
    row = session.execute(stmt).scalar_one_or_none()
    if not row:
        return None
    return {
        "Status": row.status,
        "Started": row.started_at,
        "Finished": row.finished_at,
        "Events": f"{row.events_inserted} inserted / {row.events_updated} updated",
        "Fighters": f"{row.fighters_inserted} inserted / {row.fighters_updated} updated",
        "Fights": f"{row.fights_inserted} inserted / {row.fights_updated} updated",
        "Fight Stats": f"{row.fight_stats_inserted} inserted / {row.fight_stats_updated} updated",
        "Error": row.error_message,
    }
