import logging
import re

from bs4 import BeautifulSoup, Tag

from src.pipeline.scrapers.parsers.common import clean_text, parse_strike_stat, parse_time_to_seconds

logger = logging.getLogger("ufc.scraper.fight_detail")


def _extract_source_id(url: str) -> str | None:
    match = re.search(r"/([a-f0-9]{16,})$", url.strip())
    return match.group(1) if match else None


def _safe_int(text: str) -> int | None:
    try:
        return int(text.strip())
    except (ValueError, AttributeError):
        return None


def _get_cell_values(col: Tag) -> list[str]:
    return [clean_text(p.get_text()) for p in col.select("p")]


def _sum_per_round_stat(rows: list[Tag], col_index: int, fighter_index: int) -> tuple[int | None, int | None]:
    total_landed = 0
    total_attempted = 0
    has_data = False
    for row in rows:
        cols = row.select("td")
        if len(cols) <= col_index:
            continue
        vals = _get_cell_values(cols[col_index])
        if len(vals) <= fighter_index:
            continue
        landed, attempted = parse_strike_stat(vals[fighter_index])
        if landed is not None and attempted is not None:
            total_landed += landed
            total_attempted += attempted
            has_data = True
    if not has_data:
        return None, None
    return total_landed, total_attempted


def parse_fighters(soup: BeautifulSoup, fight_source_id: str) -> tuple[str, str, str | None]:
    persons = soup.select("div.b-fight-details__person")
    fighter_source_ids: list[str] = []
    winner_source_id: str | None = None

    for person in persons:
        link = person.select_one("h3.b-fight-details__person-name a")
        if not link:
            continue
        sid = _extract_source_id(link.get("href", ""))
        if not sid:
            continue
        fighter_source_ids.append(sid)

        status_el = person.select_one("i.b-fight-details__person-status")
        if status_el and clean_text(status_el.get_text()) == "W":
            winner_source_id = sid

    if len(fighter_source_ids) < 2:
        raise ValueError(f"Could not find 2 fighters on fight page {fight_source_id}")

    return fighter_source_ids[0], fighter_source_ids[1], winner_source_id


def parse_result_metadata(soup: BeautifulSoup) -> dict:
    method_el = soup.select_one("i.b-fight-details__text-item_first")
    result_method = None
    if method_el:
        texts = [clean_text(t) for t in method_el.stripped_strings]
        result_method = texts[1] if len(texts) > 1 else None

    detail_items = soup.select("i.b-fight-details__text-item")
    finish_round = None
    finish_time_seconds = None
    scheduled_rounds = None
    time_format_raw = None
    referee = None
    result_details = None

    for item in detail_items:
        text = clean_text(item.get_text())
        if text.startswith("Round:"):
            finish_round = _safe_int(text.replace("Round:", ""))
        elif text.startswith("Time:"):
            finish_time_seconds = parse_time_to_seconds(text.replace("Time:", "").strip())
        elif text.startswith("Time format:"):
            time_format_raw = text.replace("Time format:", "").strip() or None
            if time_format_raw:
                rnd_match = re.match(r"(\d+)\s+Rnd", time_format_raw)
                if rnd_match:
                    scheduled_rounds = int(rnd_match.group(1))
        elif text.startswith("Referee:"):
            referee = text.replace("Referee:", "").strip() or None
        elif text.startswith("Details:"):
            result_details = text.replace("Details:", "").strip() or None

    return {
        "result_method": result_method,
        "finish_round": finish_round,
        "finish_time_seconds": finish_time_seconds,
        "scheduled_rounds": scheduled_rounds,
        "time_format_raw": time_format_raw,
        "referee": referee,
        "result_details": result_details,
    }


def parse_fight_type(soup: BeautifulSoup) -> dict:
    fight_type_el = soup.select_one("i.b-fight-details__fight-title")
    fight_type_text = clean_text(fight_type_el.get_text()) if fight_type_el else ""
    title_fight = "title" in fight_type_text.lower()
    gender = "women" if "women" in fight_type_text.lower() else "men"
    weight_class_raw = fight_type_text.replace("Bout", "").strip()
    weight_class = re.sub(r"(?i)women'?s\s*", "", weight_class_raw).strip() or None
    if title_fight and weight_class:
        weight_class = re.sub(r"(?i)\s*title\s*", " ", weight_class).strip()

    return {
        "weight_class": weight_class,
        "title_fight": title_fight,
        "gender": gender,
    }


def parse_bonus_flags(soup: BeautifulSoup) -> tuple[bool, bool]:
    bonus_imgs = soup.select("img[src*='perf'], img[src*='fight']")
    img_srcs = " ".join(img.get("src", "") for img in bonus_imgs).lower()
    performance_bonus = "perf" in img_srcs
    fight_of_the_night = "fight" in img_srcs
    return performance_bonus, fight_of_the_night


def parse_totals_stats(sections: list[Tag], stats: list) -> None:
    totals_table = sections[1].select_one("table") if len(sections) > 1 else None
    if not totals_table:
        return

    data_rows = [r for r in totals_table.select("tr") if r.select("td")]
    if not data_rows:
        return

    row = data_rows[0]
    cols = row.select("td")
    for fi in range(2):
        s = stats[fi]
        if len(cols) > 1:
            vals = _get_cell_values(cols[1])
            s.knockdowns = _safe_int(vals[fi]) if len(vals) > fi else None
        if len(cols) > 2:
            vals = _get_cell_values(cols[2])
            if len(vals) > fi:
                s.sig_strikes_landed, s.sig_strikes_attempted = parse_strike_stat(vals[fi])
        if len(cols) > 4:
            vals = _get_cell_values(cols[4])
            if len(vals) > fi:
                s.total_strikes_landed, s.total_strikes_attempted = parse_strike_stat(vals[fi])
        if len(cols) > 5:
            vals = _get_cell_values(cols[5])
            if len(vals) > fi:
                s.takedowns_landed, s.takedowns_attempted = parse_strike_stat(vals[fi])
        if len(cols) > 7:
            vals = _get_cell_values(cols[7])
            s.submissions_attempted = _safe_int(vals[fi]) if len(vals) > fi else None
        if len(cols) > 8:
            vals = _get_cell_values(cols[8])
            s.reversals = _safe_int(vals[fi]) if len(vals) > fi else None
        if len(cols) > 9:
            vals = _get_cell_values(cols[9])
            if len(vals) > fi:
                s.control_time_seconds = parse_time_to_seconds(vals[fi])


def parse_sig_strikes_stats(sections: list[Tag], stats: list) -> None:
    sig_table = sections[4].select_one("table") if len(sections) > 4 else None
    if not sig_table:
        return

    data_rows = [r for r in sig_table.select("tr") if r.select("td")]
    for fi in range(2):
        s = stats[fi]
        s.head_strikes_landed, s.head_strikes_attempted = _sum_per_round_stat(data_rows, 3, fi)
        s.body_strikes_landed, s.body_strikes_attempted = _sum_per_round_stat(data_rows, 4, fi)
        s.leg_strikes_landed, s.leg_strikes_attempted = _sum_per_round_stat(data_rows, 5, fi)
        s.distance_strikes_landed, s.distance_strikes_attempted = _sum_per_round_stat(data_rows, 6, fi)
        s.clinch_strikes_landed, s.clinch_strikes_attempted = _sum_per_round_stat(data_rows, 7, fi)
        s.ground_strikes_landed, s.ground_strikes_attempted = _sum_per_round_stat(data_rows, 8, fi)
