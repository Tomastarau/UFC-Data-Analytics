import logging
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlencode, urljoin, urlparse

from bs4 import BeautifulSoup
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.pipeline.client import UFCStatsClient
from src.pipeline.models.raw import Fighter

logger = logging.getLogger("ufc.enrichment.fighter_photos")

UFC_BASE_URL = "https://www.ufc.com"
UFC_SEARCH_URL = f"{UFC_BASE_URL}/search"
UFC_PHOTO_SOURCE = "ufc.com"
RECORD_PATTERN = re.compile(r"(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*\(W-L-D\)", re.IGNORECASE)


FALLBACK_CANDIDATE_LIMIT = 5


@dataclass(frozen=True)
class FighterRow:
    id: int
    full_name: str | None
    first_name: str | None
    last_name: str | None
    nickname: str | None
    wins: int | None
    losses: int | None
    draws: int | None

    @property
    def record(self) -> tuple[int, int, int] | None:
        if None in {self.wins, self.losses, self.draws}:
            return None
        return self.wins, self.losses, self.draws


@dataclass(frozen=True)
class AthleteProfile:
    url: str
    full_name: str
    nickname: str | None
    photo_url: str | None
    wins: int | None
    losses: int | None
    draws: int | None

    @property
    def record(self) -> tuple[int, int, int] | None:
        if None in {self.wins, self.losses, self.draws}:
            return None
        return self.wins, self.losses, self.draws


@dataclass(frozen=True)
class FighterPhotoEnrichmentResult:
    total: int
    matched: int
    missing_image: int
    ambiguous: int
    not_found: int
    missing_name: int


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", without_accents).strip().lower()
    return re.sub(r"\s+", " ", cleaned)


def load_fighters(session: Session, only_missing: bool, limit: int | None) -> list[FighterRow]:
    stmt = (
        select(
            Fighter.id,
            Fighter.full_name,
            Fighter.first_name,
            Fighter.last_name,
            Fighter.nickname,
            Fighter.wins,
            Fighter.losses,
            Fighter.draws,
        )
        .order_by(Fighter.id)
    )
    if only_missing:
        stmt = stmt.where(Fighter.photo_url.is_(None))
    if limit:
        stmt = stmt.limit(limit)
    return [FighterRow(*row) for row in session.execute(stmt).all()]


def search_athlete_urls(client: UFCStatsClient, name: str, limit: int = 1) -> list[str]:
    query = urlencode({"query": name, "type": "athletes"})
    html = client.get(f"{UFC_SEARCH_URL}?{query}")
    soup = BeautifulSoup(html, "html.parser")
    results_view = soup.select_one(".view-display-id-athletes_search_results")
    if not results_view or results_view.select_one(".view-empty"):
        return []
    urls: list[str] = []
    for anchor in results_view.select('a[href*="/athlete/"]'):
        href = anchor.get("href")
        if not href:
            continue
        absolute = urljoin(UFC_BASE_URL, href)
        slug = urlparse(absolute).path.split("/athlete/", 1)[-1].strip("/").split("/", 1)[0]
        if not slug:
            continue
        url = f"{UFC_BASE_URL}/athlete/{slug}"
        if url not in urls:
            urls.append(url)
        if len(urls) >= limit:
            break
    return urls


def search_athlete_url(client: UFCStatsClient, name: str) -> str | None:
    urls = search_athlete_urls(client, name, limit=1)
    return urls[0] if urls else None


def extract_meta_content(soup: BeautifulSoup, attribute: str, value: str) -> str | None:
    tag = soup.find("meta", attrs={attribute: value})
    if not tag:
        return None
    content = tag.get("content")
    return content.strip() if content and content.strip() else None


def extract_name(soup: BeautifulSoup, fallback: str) -> str:
    candidates = [
        extract_meta_content(soup, "property", "og:title"),
        extract_meta_content(soup, "name", "twitter:title"),
        soup.title.get_text(" ", strip=True) if soup.title else None,
    ]
    for value in candidates:
        if not value:
            continue
        cleaned = re.sub(r"\s*\|\s*UFC\s*$", "", value).strip()
        if cleaned:
            return cleaned
    return fallback


def extract_nickname(soup: BeautifulSoup) -> str | None:
    element = soup.select_one(".hero-profile__nickname")
    if not element:
        return None
    text = element.get_text(" ", strip=True).strip('"\u201c\u201d\u2018\u2019 ')
    return text or None


def extract_record(html: str, soup: BeautifulSoup) -> tuple[int | None, int | None, int | None]:
    match = RECORD_PATTERN.search(html) or RECORD_PATTERN.search(soup.get_text(" ", strip=True))
    if not match:
        return None, None, None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def fetch_athlete_profile(client: UFCStatsClient, url: str) -> AthleteProfile:
    html = client.get(url)
    soup = BeautifulSoup(html, "html.parser")
    slug = urlparse(url).path.split("/athlete/", 1)[-1].strip("/").split("/", 1)[0]
    full_name = extract_name(soup, slug.replace("-", " ").title())
    hero_image = soup.select_one("img.hero-profile__image")
    photo_url = hero_image.get("src") if hero_image else None
    if not photo_url:
        photo_url = (
            extract_meta_content(soup, "property", "og:image")
            or extract_meta_content(soup, "name", "twitter:image")
            or extract_meta_content(soup, "property", "og:image:url")
        )
    wins, losses, draws = extract_record(html, soup)
    return AthleteProfile(
        url=url,
        full_name=full_name,
        nickname=extract_nickname(soup),
        photo_url=photo_url,
        wins=wins,
        losses=losses,
        draws=draws,
    )


def slug_name_from_url(url: str) -> str:
    slug = urlparse(url).path.split("/athlete/", 1)[-1].strip("/").split("/", 1)[0]
    cleaned = re.sub(r"-\d+$", "", slug)
    return normalize_name(cleaned.replace("-", " "))


def candidate_canonical_names(fighter: FighterRow) -> set[str]:
    names = {normalize_name(fighter.full_name)}
    nick = normalize_name(fighter.nickname)
    first = normalize_name(fighter.first_name)
    last = normalize_name(fighter.last_name)
    if nick:
        names.add(nick)
        if first:
            names.add(f"{first} {nick}")
        if last:
            names.add(f"{nick} {last}")
    return {n for n in names if n}


def is_exact_profile_name_match(fighter: FighterRow, profile: AthleteProfile) -> bool:
    return normalize_name(profile.full_name) in candidate_canonical_names(fighter)


def choose_candidate(fighter: FighterRow, profile: AthleteProfile, allow_full_name_match: bool = False) -> str:
    canonical_names = candidate_canonical_names(fighter)
    if slug_name_from_url(profile.url) in canonical_names:
        return "matched"
    if allow_full_name_match and is_exact_profile_name_match(fighter, profile):
        return "matched"
    if fighter.record is not None and profile.record is not None and fighter.record == profile.record:
        return "matched"
    db_nick = normalize_name(fighter.nickname)
    ufc_nick = normalize_name(profile.nickname)
    if db_nick and ufc_nick and db_nick == ufc_nick:
        haystack = f"{slug_name_from_url(profile.url)} {normalize_name(profile.full_name)}".split()
        name_tokens = {t for t in (normalize_name(fighter.first_name).split() + normalize_name(fighter.last_name).split()) if t}
        if name_tokens & set(haystack):
            return "matched"
    return "ambiguous"


def resolve_fighter_profile(
    client: UFCStatsClient,
    fighter: FighterRow,
    profile_cache: dict[str, AthleteProfile],
) -> tuple[AthleteProfile | None, bool]:
    """Returns (matched_profile, any_candidate_seen). Profile is None if no match."""
    queries: list[tuple[str, int, bool]] = [(fighter.full_name, FALLBACK_CANDIDATE_LIMIT, True)]
    if fighter.nickname and fighter.first_name:
        queries.append((f"{fighter.first_name} {fighter.nickname}", 1, False))
    if fighter.nickname and fighter.last_name:
        queries.append((f"{fighter.nickname} {fighter.last_name}", 1, False))
    if fighter.nickname:
        queries.append((fighter.nickname, FALLBACK_CANDIDATE_LIMIT, False))
    if fighter.last_name:
        queries.append((fighter.last_name, FALLBACK_CANDIDATE_LIMIT, False))
    if fighter.first_name:
        queries.append((fighter.first_name, FALLBACK_CANDIDATE_LIMIT, False))

    any_candidate = False
    tried_urls: set[str] = set()

    for query, candidate_limit, is_exact_name_query in queries:
        if not query:
            continue
        urls = search_athlete_urls(client, query, limit=candidate_limit)
        allow_full_name_match = is_exact_name_query and len(urls) == 1
        for url in urls:
            if url in tried_urls:
                continue
            tried_urls.add(url)
            any_candidate = True
            if url not in profile_cache:
                profile_cache[url] = fetch_athlete_profile(client, url)
            profile = profile_cache[url]
            if choose_candidate(fighter, profile, allow_full_name_match=allow_full_name_match) == "matched":
                return profile, True

    return None, any_candidate


def enrich_fighter_photos(
    session: Session,
    client: UFCStatsClient,
    only_missing: bool = True,
    limit: int | None = None,
) -> FighterPhotoEnrichmentResult:
    fighters = load_fighters(session, only_missing=only_missing, limit=limit)
    if not fighters:
        return FighterPhotoEnrichmentResult(0, 0, 0, 0, 0, 0)

    counts = {"matched": 0, "missing_image": 0, "ambiguous": 0, "not_found": 0, "missing_name": 0}
    profile_cache: dict[str, AthleteProfile] = {}

    for fighter in fighters:
        if not fighter.full_name and not fighter.first_name and not fighter.last_name:
            counts["missing_name"] += 1
            session.execute(
                update(Fighter).where(Fighter.id == fighter.id).values(
                    photo_source=UFC_PHOTO_SOURCE,
                    photo_status="missing_name",
                    photo_last_checked_at=func.now(),
                    updated_at=func.now(),
                )
            )
            continue

        profile, any_candidate = resolve_fighter_profile(client, fighter, profile_cache)
        values: dict = {
            "photo_source": UFC_PHOTO_SOURCE,
            "photo_last_checked_at": func.now(),
            "updated_at": func.now(),
        }

        if profile and profile.photo_url:
            values["photo_url"] = profile.photo_url
            values["photo_status"] = "matched"
            counts["matched"] += 1
        elif profile:
            values["photo_status"] = "missing_image"
            counts["missing_image"] += 1
        elif any_candidate:
            values["photo_status"] = "ambiguous"
            counts["ambiguous"] += 1
        else:
            values["photo_status"] = "not_found"
            counts["not_found"] += 1

        session.execute(update(Fighter).where(Fighter.id == fighter.id).values(**values))

    logger.info(
        "Fighter photo enrichment finished: total=%d matched=%d missing_image=%d ambiguous=%d not_found=%d missing_name=%d",
        len(fighters), counts["matched"], counts["missing_image"], counts["ambiguous"], counts["not_found"], counts["missing_name"],
    )

    return FighterPhotoEnrichmentResult(
        total=len(fighters),
        matched=counts["matched"],
        missing_image=counts["missing_image"],
        ambiguous=counts["ambiguous"],
        not_found=counts["not_found"],
        missing_name=counts["missing_name"],
    )
