import logging
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup

from src.pipeline.client import UFCStatsClient
from src.pipeline.errors import ContractError
from src.pipeline.scrapers.parsers.event_detail_parsers import (
    parse_event_metadata,
    parse_fight_rows,
)

logger = logging.getLogger("ufc.scraper.event_detail")


@dataclass
class FightListItem:
    source_id: str
    url: str
    fighter_1_name: str
    fighter_2_name: str
    fighter_1_source_id: str
    fighter_2_source_id: str
    result_method: str | None
    finish_round: int | None
    finish_time: str | None
    weight_class: str | None
    fight_order: int


@dataclass
class EventDetail:
    source_id: str
    event_name: str
    event_date: date | None
    location: str
    fights: list[FightListItem]


def parse_event_detail(html: str, event_source_id: str) -> EventDetail:
    soup = BeautifulSoup(html, "html.parser")

    metadata = parse_event_metadata(soup)
    fights = parse_fight_rows(soup, event_source_id)

    if not fights:
        raise ContractError(
            f"Event {event_source_id} yielded no fights. "
            "Only completed events are ingested, so an empty card is a parse failure."
        )

    logger.info("Parsed %d fights for event %s", len(fights), metadata["event_name"])
    return EventDetail(source_id=event_source_id, fights=fights, **metadata)


def fetch_event_detail(
    client: UFCStatsClient, event_url: str, event_source_id: str
) -> EventDetail:
    html = client.get(event_url)
    return parse_event_detail(html, event_source_id)
