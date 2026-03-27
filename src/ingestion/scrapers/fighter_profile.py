import logging
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup

from src.ingestion.client import UFCStatsClient
from src.ingestion.config import BASE_URL
from src.ingestion.scrapers.parsers.fighter_profile_parsers import (
    parse_fighter_identity,
    parse_physical_attributes,
    parse_record,
)

logger = logging.getLogger("ufc.scraper.fighter_profile")


@dataclass
class FighterProfile:
    source_id: str
    full_name: str
    nickname: str | None
    height_cm: float | None
    reach_cm: float | None
    stance: str | None
    date_of_birth: date | None
    wins: int | None
    losses: int | None
    draws: int | None


def parse_fighter_profile(html: str, fighter_source_id: str) -> FighterProfile:
    soup = BeautifulSoup(html, "html.parser")

    identity = parse_fighter_identity(soup)
    record = parse_record(soup)
    physical = parse_physical_attributes(soup)

    logger.info("Parsed fighter %s (%s)", identity["full_name"], fighter_source_id[:8])
    return FighterProfile(
        source_id=fighter_source_id, **identity, **record, **physical
    )


def fetch_fighter_profile(client: UFCStatsClient, fighter_source_id: str) -> FighterProfile:
    url = f"{BASE_URL}/fighter-details/{fighter_source_id}"
    html = client.get(url)
    return parse_fighter_profile(html, fighter_source_id)
