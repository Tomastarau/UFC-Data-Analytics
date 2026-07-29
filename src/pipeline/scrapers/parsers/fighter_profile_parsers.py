import logging
import re

from bs4 import BeautifulSoup

from src.pipeline.scrapers.parsers.common import (
    clean_text,
    parse_date,
    parse_height_to_cm,
    parse_reach_to_cm,
)

logger = logging.getLogger("ufc.scraper.fighter_profile")


def parse_fighter_identity(soup: BeautifulSoup) -> dict:
    name_el = soup.select_one("span.b-content__title-highlight")
    full_name = clean_text(name_el.get_text()) if name_el else ""
    if not full_name:
        logger.warning("Empty fighter name")

    nick_el = soup.select_one("p.b-content__Nickname")
    nickname = clean_text(nick_el.get_text()) if nick_el else None
    if nickname == "":
        nickname = None

    return {"full_name": full_name, "nickname": nickname}


def parse_record(soup: BeautifulSoup) -> dict:
    record_el = soup.select_one("span.b-content__title-record")
    if not record_el:
        return {"wins": None, "losses": None, "draws": None}

    record_text = clean_text(record_el.get_text()).replace("Record:", "").strip()
    match = re.match(r"(\d+)-(\d+)-(\d+)", record_text)
    if not match:
        logger.warning("Unexpected record format: %s", record_text)
        return {"wins": None, "losses": None, "draws": None}

    return {
        "wins": int(match.group(1)),
        "losses": int(match.group(2)),
        "draws": int(match.group(3)),
    }


def parse_physical_attributes(soup: BeautifulSoup) -> dict:
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

    return {
        "height_cm": height_cm,
        "reach_cm": reach_cm,
        "stance": stance,
        "date_of_birth": date_of_birth,
    }
