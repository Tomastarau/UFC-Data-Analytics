import pandas as pd


def is_missing(value) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def text_value(value, fallback: str = "—") -> str:
    if is_missing(value):
        return fallback
    text = str(value).strip()
    return text or fallback


def int_value(value, suffix: str = "") -> str:
    if is_missing(value):
        return "—"
    return f"{int(value)}{suffix}"


def format_fight_duration(finish_round: int | None, finish_time_seconds: int | None) -> str | None:
    if finish_round is None or finish_time_seconds is None:
        return None
    minutes = finish_time_seconds // 60
    seconds = finish_time_seconds % 60
    return f"Round {finish_round}, {minutes}:{seconds:02d}"
