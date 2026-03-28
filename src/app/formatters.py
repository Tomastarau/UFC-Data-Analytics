def format_fight_duration(finish_round: int | None, finish_time_seconds: int | None) -> str | None:
    if finish_round is None or finish_time_seconds is None:
        return None
    minutes = finish_time_seconds // 60
    seconds = finish_time_seconds % 60
    return f"Round {finish_round}, {minutes}:{seconds:02d}"
