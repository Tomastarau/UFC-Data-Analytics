import logging
import re

from bs4 import BeautifulSoup

from src.ingestion.scrapers.parsers.common import clean_text, parse_date

logger = logging.getLogger("ufc.scraper.event_detail")


def _extract_source_id(url: str) -> str | None:
    match = re.search(r"/([a-f0-9]{16,})$", url.strip())
    return match.group(1) if match else None


def parse_event_metadata(soup: BeautifulSoup) -> dict:
    title_el = soup.select_one("h2.b-content__title span")
    event_name = clean_text(title_el.get_text()) if title_el else ""
    if not event_name:
        logger.warning("Empty event title")

    event_date = None
    location = ""
    for item in soup.select("li.b-list__box-list-item"):
        text = item.get_text()
        if "Date:" in text:
            event_date = parse_date(text.replace("Date:", "").strip())
        elif "Location:" in text:
            location = clean_text(text.replace("Location:", "").strip())

    return {"event_name": event_name, "event_date": event_date, "location": location}


def parse_fight_rows(soup: BeautifulSoup, event_source_id: str) -> list:
    from src.ingestion.scrapers.event_detail import FightListItem

    fight_rows = soup.select(
        "tr.b-fight-details__table-row.b-fight-details__table-row__hover"
    )
    fights: list[FightListItem] = []

    for idx, row in enumerate(reversed(fight_rows), start=1):
        fight_link = row.get("data-link", "")
        fight_source_id = _extract_source_id(fight_link)
        if not fight_source_id:
            logger.warning("Skipping fight row without source_id in event %s", event_source_id)
            continue

        fighter_links = row.select("a.b-link.b-link_style_black")
        if len(fighter_links) < 2:
            logger.warning("Skipping fight %s: less than 2 fighter links", fight_source_id)
            continue

        f1_source_id = _extract_source_id(fighter_links[0].get("href", ""))
        f2_source_id = _extract_source_id(fighter_links[1].get("href", ""))
        if not f1_source_id or not f2_source_id:
            logger.warning("Skipping fight %s: missing fighter source_id", fight_source_id)
            continue

        cols = row.select("td")
        col_texts = [clean_text(c.get_text()) for c in cols]

        weight_class = col_texts[6] if len(col_texts) > 6 else None
        method = col_texts[7] if len(col_texts) > 7 else None
        rnd = None
        if len(col_texts) > 8:
            try:
                rnd = int(col_texts[8])
            except ValueError:
                pass
        finish_time = col_texts[9] if len(col_texts) > 9 else None

        fights.append(FightListItem(
            source_id=fight_source_id,
            url=fight_link.strip(),
            fighter_1_name=clean_text(fighter_links[0].get_text()),
            fighter_2_name=clean_text(fighter_links[1].get_text()),
            fighter_1_source_id=f1_source_id,
            fighter_2_source_id=f2_source_id,
            result_method=method,
            finish_round=rnd,
            finish_time=finish_time,
            weight_class=weight_class,
            fight_order=idx,
        ))

    return fights
