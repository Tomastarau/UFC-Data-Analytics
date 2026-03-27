import logging
import re
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup

from src.ingestion.client import UFCStatsClient
from src.ingestion.config import BASE_URL
from src.ingestion.scrapers.parsers import clean_text, parse_date, parse_height_to_cm, parse_reach_to_cm

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

    name_el = soup.select_one("span.b-content__title-highlight")
    full_name = clean_text(name_el.get_text()) if name_el else ""

    nick_el = soup.select_one("p.b-content__Nickname")
    nickname = clean_text(nick_el.get_text()) if nick_el else None
    if nickname == "":
        nickname = None

    record_el = soup.select_one("span.b-content__title-record")
    wins, losses, draws = None, None, None
    if record_el:
        record_text = clean_text(record_el.get_text()).replace("Record:", "").strip()
        match = re.match(r"(\d+)-(\d+)-(\d+)", record_text)
        if match:
            wins, losses, draws = int(match.group(1)), int(match.group(2)), int(match.group(3))

    height_cm = None
    reach_cm = None
    stance = None
    date_of_birth = None

    for item in soup.select("li.b-list__box-list-item"):
        text = clean_text(item.get_text())
        if text.startswith("Height:"):
            height_cm = parse_height_to_cm(text.replace("Height:", "").strip())
        elif text.startswith("Reach:"):
            reach_cm = parse_reach_to_cm(text.replace("Reach:", "").strip())
        elif text.startswith("STANCE:"):
            val = text.replace("STANCE:", "").strip()
            stance = val if val else None
        elif text.startswith("DOB:"):
            date_of_birth = parse_date(text.replace("DOB:", "").strip())

    logger.info("Parsed fighter %s (%s)", full_name, fighter_source_id[:8])
    return FighterProfile(
        source_id=fighter_source_id,
        full_name=full_name,
        nickname=nickname,
        height_cm=height_cm,
        reach_cm=reach_cm,
        stance=stance,
        date_of_birth=date_of_birth,
        wins=wins,
        losses=losses,
        draws=draws,
    )


def fetch_fighter_profile(client: UFCStatsClient, fighter_source_id: str) -> FighterProfile:
    url = f"{BASE_URL}/fighter-details/{fighter_source_id}"
    html = client.get(url)
    return parse_fighter_profile(html, fighter_source_id)
