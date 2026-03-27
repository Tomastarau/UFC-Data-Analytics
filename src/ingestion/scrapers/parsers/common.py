import re
from datetime import date


def clean_text(text: str) -> str:
    return " ".join(text.split()).strip()


def parse_height_to_cm(height_str: str | None) -> float | None:
    if not height_str:
        return None
    match = re.match(r"(\d+)'\s*(\d+)\"?", height_str.strip())
    if not match:
        return None
    feet, inches = int(match.group(1)), int(match.group(2))
    return round((feet * 12 + inches) * 2.54, 1)


def parse_reach_to_cm(reach_str: str | None) -> float | None:
    if not reach_str:
        return None
    match = re.match(r"(\d+)\"?", reach_str.strip())
    if not match:
        return None
    return round(int(match.group(1)) * 2.54, 1)


def parse_time_to_seconds(time_str: str | None) -> int | None:
    if not time_str:
        return None
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        return None


def parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    cleaned = clean_text(date_str)
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%b. %d, %Y"):
        try:
            return date.fromisoformat(
                __import__("datetime").datetime.strptime(cleaned, fmt).date().isoformat()
            )
        except ValueError:
            continue
    return None


def parse_strike_stat(text: str) -> tuple[int | None, int | None]:
    match = re.match(r"(\d+)\s+of\s+(\d+)", text.strip())
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))
