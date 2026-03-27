import logging
import traceback
from dataclasses import asdict
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from src.ingestion.client import UFCStatsClient
from src.ingestion.loaders.events import upsert_events
from src.ingestion.loaders.fight_stats import upsert_fight_stats
from src.ingestion.loaders.fighters import upsert_fighters
from src.ingestion.loaders.fights import upsert_fights
from src.ingestion.scrapers.event_detail import fetch_event_detail
from src.ingestion.scrapers.events_index import EventIndexItem, fetch_events_index
from src.ingestion.scrapers.fight_detail import fetch_fight_detail
from src.ingestion.scrapers.fighter_profile import fetch_fighter_profile
from src.models.ingestion import IngestionState
from src.models.raw import Event

logger = logging.getLogger("ufc.ingestion")


def _build_event_dict(event_detail, raw_html: str = "") -> dict:
    return {
        "source_id": event_detail.source_id,
        "event_name": event_detail.event_name,
        "event_date": event_detail.event_date,
        "location": event_detail.location,
        "promotion": "UFC",
        "raw_payload": {
            "event_name": event_detail.event_name,
            "event_date": str(event_detail.event_date),
            "location": event_detail.location,
        },
    }


def _build_fighter_dict(profile) -> dict:
    payload = asdict(profile)
    if payload.get("date_of_birth"):
        payload["date_of_birth"] = str(payload["date_of_birth"])
    return {
        "source_id": profile.source_id,
        "full_name": profile.full_name,
        "first_name": profile.full_name.split()[0] if profile.full_name else None,
        "last_name": " ".join(profile.full_name.split()[1:]) if profile.full_name and len(profile.full_name.split()) > 1 else None,
        "nickname": profile.nickname,
        "date_of_birth": profile.date_of_birth,
        "height_cm": profile.height_cm,
        "reach_cm": profile.reach_cm,
        "stance": profile.stance,
        "weight_class": None,
        "wins": profile.wins,
        "losses": profile.losses,
        "draws": profile.draws,
        "raw_payload": payload,
    }


def _build_fight_dict(fight_detail, event_source_id: str, fight_order: int) -> dict:
    return {
        "source_id": fight_detail.source_id,
        "event_source_id": event_source_id,
        "fighter_1_source_id": fight_detail.fighter_1_source_id,
        "fighter_2_source_id": fight_detail.fighter_2_source_id,
        "winner_source_id": fight_detail.winner_source_id,
        "weight_class": fight_detail.weight_class,
        "gender": fight_detail.gender,
        "fight_order": fight_order,
        "scheduled_rounds": fight_detail.scheduled_rounds,
        "finish_round": fight_detail.finish_round,
        "finish_time_seconds": fight_detail.finish_time_seconds,
        "result_method": fight_detail.result_method,
        "result_details": fight_detail.result_details,
        "referee": fight_detail.referee,
        "title_fight": fight_detail.title_fight,
        "performance_bonus": fight_detail.performance_bonus,
        "fight_of_the_night": fight_detail.fight_of_the_night,
        "raw_payload": {
            "weight_class": fight_detail.weight_class,
            "result_method": fight_detail.result_method,
            "result_details": fight_detail.result_details,
            "referee": fight_detail.referee,
        },
    }


def _build_stats_dicts(fight_detail) -> list[dict]:
    result = []
    for s in fight_detail.stats:
        d = {
            "fight_source_id": fight_detail.source_id,
            "fighter_source_id": s.fighter_source_id,
            "knockdowns": s.knockdowns,
            "sig_strikes_landed": s.sig_strikes_landed,
            "sig_strikes_attempted": s.sig_strikes_attempted,
            "total_strikes_landed": s.total_strikes_landed,
            "total_strikes_attempted": s.total_strikes_attempted,
            "takedowns_landed": s.takedowns_landed,
            "takedowns_attempted": s.takedowns_attempted,
            "submissions_attempted": s.submissions_attempted,
            "reversals": s.reversals,
            "control_time_seconds": s.control_time_seconds,
            "head_strikes_landed": s.head_strikes_landed,
            "head_strikes_attempted": s.head_strikes_attempted,
            "body_strikes_landed": s.body_strikes_landed,
            "body_strikes_attempted": s.body_strikes_attempted,
            "leg_strikes_landed": s.leg_strikes_landed,
            "leg_strikes_attempted": s.leg_strikes_attempted,
            "distance_strikes_landed": s.distance_strikes_landed,
            "distance_strikes_attempted": s.distance_strikes_attempted,
            "clinch_strikes_landed": s.clinch_strikes_landed,
            "clinch_strikes_attempted": s.clinch_strikes_attempted,
            "ground_strikes_landed": s.ground_strikes_landed,
            "ground_strikes_attempted": s.ground_strikes_attempted,
            "raw_payload": {},
        }
        result.append(d)
    return result


def _filter_events(
    events: list[EventIndexItem],
    date_from: date | None,
    date_to: date | None,
) -> list[EventIndexItem]:
    filtered = []
    for e in events:
        if e.event_date is None:
            continue
        if date_from and e.event_date < date_from:
            continue
        if date_to and e.event_date > date_to:
            continue
        filtered.append(e)
    return filtered


def run_ingestion(
    session_factory: sessionmaker,
    client: UFCStatsClient,
    date_from: date | None = None,
    date_to: date | None = None,
) -> IngestionState:
    session: Session = session_factory()

    state = IngestionState(
        source_name="ufcstats",
        date_from=date_from,
        date_to=date_to,
        status="running",
    )
    session.add(state)
    session.commit()

    try:
        all_events = fetch_events_index(client)
        events = _filter_events(all_events, date_from, date_to)

        existing_sids = set(
            row[0]
            for row in session.execute(
                select(Event.source_id).where(
                    Event.source_id.in_([e.source_id for e in events])
                )
            )
        )
        new_events = [e for e in events if e.source_id not in existing_sids]
        logger.info(
            "Processing %d new events (%d already in DB, %d total on source)",
            len(new_events), len(events) - len(new_events), len(all_events),
        )
        events = new_events

        for event_item in events:
            try:
                _process_event(session, client, state, event_item)
                session.commit()
            except Exception:
                logger.exception("Failed to process event %s (%s)", event_item.event_name, event_item.source_id)
                session.rollback()
                continue

        state.status = "completed"
        state.finished_at = datetime.now(timezone.utc)
        session.commit()

    except Exception as exc:
        logger.exception("Ingestion failed globally")
        session.rollback()
        state.status = "failed"
        state.error_message = str(exc)
        state.error_traceback = traceback.format_exc()
        state.finished_at = datetime.now(timezone.utc)
        session.add(state)
        session.commit()

    finally:
        logger.info(
            "Ingestion %s: events=%d/%d fighters=%d/%d fights=%d/%d stats=%d/%d",
            state.status,
            state.events_inserted, state.events_updated,
            state.fighters_inserted, state.fighters_updated,
            state.fights_inserted, state.fights_updated,
            state.fight_stats_inserted, state.fight_stats_updated,
        )
        session.expunge(state)
        session.close()

    return state


def _process_event(
    session: Session,
    client: UFCStatsClient,
    state: IngestionState,
    event_item: EventIndexItem,
) -> None:
    logger.info("Processing event: %s (%s)", event_item.event_name, event_item.event_date)

    event_detail = fetch_event_detail(client, event_item.url, event_item.source_id)
    fight_details, fighter_profiles = _fetch_event_data(client, event_detail)
    _upsert_event_data(session, state, event_detail, fight_details, fighter_profiles)

    state.last_event_date = event_detail.event_date
    state.last_event_source_id = event_detail.source_id


def _fetch_event_data(client, event_detail):
    fight_details = []
    fighter_sids_seen: set[str] = set()
    fighter_profiles = []

    for fight_item in event_detail.fights:
        fight = fetch_fight_detail(client, fight_item.url, fight_item.source_id)
        fight_details.append((fight, fight_item.fight_order))

        for sid in (fight.fighter_1_source_id, fight.fighter_2_source_id):
            if sid not in fighter_sids_seen:
                fighter_sids_seen.add(sid)
                profile = fetch_fighter_profile(client, sid)
                fighter_profiles.append(profile)

    return fight_details, fighter_profiles


def _upsert_event_data(session, state, event_detail, fight_details, fighter_profiles):
    event_result = upsert_events(session, [_build_event_dict(event_detail)])
    state.events_inserted += event_result.inserted
    state.events_updated += event_result.updated

    fighter_dicts = [_build_fighter_dict(p) for p in fighter_profiles]
    fighter_result = upsert_fighters(session, fighter_dicts)
    state.fighters_inserted += fighter_result.inserted
    state.fighters_updated += fighter_result.updated

    fight_dicts = [
        _build_fight_dict(fd, event_detail.source_id, order)
        for fd, order in fight_details
    ]
    fight_result = upsert_fights(session, fight_dicts)
    state.fights_inserted += fight_result.inserted
    state.fights_updated += fight_result.updated

    stats_dicts = []
    for fd, _ in fight_details:
        stats_dicts.extend(_build_stats_dicts(fd))
    stats_result = upsert_fight_stats(session, stats_dicts)
    state.fight_stats_inserted += stats_result.inserted
    state.fight_stats_updated += stats_result.updated
