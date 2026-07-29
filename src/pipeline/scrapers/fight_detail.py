import logging
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from src.pipeline.client import UFCStatsClient
from src.pipeline.errors import ContractError
from src.pipeline.scrapers.parsers.fight_detail_parsers import (
    parse_bonus_flags,
    parse_fight_type,
    parse_fighters,
    parse_result_metadata,
    parse_sig_strikes_stats,
    parse_totals_stats,
)

logger = logging.getLogger("ufc.scraper.fight_detail")


@dataclass
class FightStatsData:
    fighter_source_id: str
    knockdowns: int | None = None
    sig_strikes_landed: int | None = None
    sig_strikes_attempted: int | None = None
    total_strikes_landed: int | None = None
    total_strikes_attempted: int | None = None
    takedowns_landed: int | None = None
    takedowns_attempted: int | None = None
    submissions_attempted: int | None = None
    reversals: int | None = None
    control_time_seconds: int | None = None
    head_strikes_landed: int | None = None
    head_strikes_attempted: int | None = None
    body_strikes_landed: int | None = None
    body_strikes_attempted: int | None = None
    leg_strikes_landed: int | None = None
    leg_strikes_attempted: int | None = None
    distance_strikes_landed: int | None = None
    distance_strikes_attempted: int | None = None
    clinch_strikes_landed: int | None = None
    clinch_strikes_attempted: int | None = None
    ground_strikes_landed: int | None = None
    ground_strikes_attempted: int | None = None


@dataclass
class FightDetail:
    source_id: str
    fighter_1_source_id: str
    fighter_2_source_id: str
    winner_source_id: str | None
    result_method: str | None
    result_details: str | None
    finish_round: int | None
    finish_time_seconds: int | None
    scheduled_rounds: int | None
    time_format_raw: str | None
    referee: str | None
    weight_class: str | None
    title_fight: bool
    performance_bonus: bool
    fight_of_the_night: bool
    gender: str | None
    stats: list[FightStatsData] = field(default_factory=list)
    raw_html: str = ""


def parse_fight_detail(html: str, fight_source_id: str) -> FightDetail:
    soup = BeautifulSoup(html, "html.parser")

    f1_sid, f2_sid, winner_source_id = parse_fighters(soup, fight_source_id)

    if not f1_sid or not f2_sid:
        raise ContractError(
            f"Fight {fight_source_id}: expected two fighters, got {f1_sid!r} and {f2_sid!r}"
        )
    result_meta = parse_result_metadata(soup)
    fight_type = parse_fight_type(soup)
    perf_bonus, fotn = parse_bonus_flags(soup)

    sections = soup.select("section.b-fight-details__section")
    stats = [
        FightStatsData(fighter_source_id=f1_sid),
        FightStatsData(fighter_source_id=f2_sid),
    ]
    parse_totals_stats(sections, stats)
    parse_sig_strikes_stats(sections, stats)

    logger.info("Parsed fight %s: %s vs %s", fight_source_id, f1_sid[:8], f2_sid[:8])
    return FightDetail(
        source_id=fight_source_id,
        fighter_1_source_id=f1_sid,
        fighter_2_source_id=f2_sid,
        winner_source_id=winner_source_id,
        stats=stats,
        raw_html=html,
        **result_meta,
        **fight_type,
        performance_bonus=perf_bonus,
        fight_of_the_night=fotn,
    )


def fetch_fight_detail(
    client: UFCStatsClient, fight_url: str, fight_source_id: str
) -> FightDetail:
    html = client.get(fight_url)
    return parse_fight_detail(html, fight_source_id)
