import logging
import re
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup

from src.pipeline.client import UFCStatsClient
from src.pipeline.config import EVENTS_INDEX_URL
from src.pipeline.errors import ContractError
from src.pipeline.scrapers.parsers import clean_text, parse_date

logger = logging.getLogger("ufc.scraper.events_index")

MIN_INDEX_ROWS = 100


@dataclass
class EventIndexItem:
    source_id: str
    url: str
    event_name: str
    event_date: date | None
    location: str


def _extract_source_id(url: str) -> str | None:
    match = re.search(r"/event-details/([a-f0-9]+)", url)
    return match.group(1) if match else None


def parse_events_index(html: str) -> list[EventIndexItem]:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.b-statistics__table-row")
    events: list[EventIndexItem] = []

    for row in rows:
        link = row.select_one("a.b-link")
        if not link or not link.get("href"):
            continue

        url = link["href"].strip()
        source_id = _extract_source_id(url)
        if not source_id:
            continue

        event_name = clean_text(link.get_text())
        date_span = row.select_one("span.b-statistics__date")
        event_date_str = clean_text(date_span.get_text()) if date_span else None
        cols = row.select("td")
        location = clean_text(cols[1].get_text()) if len(cols) > 1 else ""

        events.append(EventIndexItem(
            source_id=source_id,
            url=url,
            event_name=event_name,
            event_date=parse_date(event_date_str),
            location=location,
        ))

    events.sort(key=lambda e: e.event_date or date.min)

    if len(events) < MIN_INDEX_ROWS:
        raise ContractError(
            f"Events index yielded {len(events)} rows, expected at least {MIN_INDEX_ROWS}. "
            "The page structure changed, or this is not the events index."
        )

    logger.info("Parsed %d events from index", len(events))
    return events


def fetch_events_index(client: UFCStatsClient) -> list[EventIndexItem]:
    logger.info("Fetching events index")
    html = client.get(EVENTS_INDEX_URL)
    return parse_events_index(html)
