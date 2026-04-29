from datetime import date
from html import escape

import streamlit as st

from src.app.db import get_session
from src.app.formatters import int_value, is_missing, text_value
from src.app.services.fighters import (
    get_fighter_directory,
    get_fighter_profile,
    get_fighter_recent_fights,
)
from src.app.ui.styles import inject_styles

inject_styles()


def _initials(name: str | None) -> str:
    if not name:
        return "?"
    parts = name.split()
    return "".join(part[0] for part in parts[:2]).upper()


def _format_measure(value, suffix: str) -> str:
    return int_value(value, f" {suffix}")


def _format_date(value) -> str:
    if is_missing(value):
        return "—"
    return value.strftime("%b %d, %Y")


def _format_percent(value) -> str:
    if is_missing(value):
        return "—"
    return f"{float(value) * 100:.1f}%"


def _format_record(fighter: dict) -> str:
    wins = 0 if is_missing(fighter.get("W")) else fighter.get("W") or 0
    losses = 0 if is_missing(fighter.get("L")) else fighter.get("L") or 0
    draws = 0 if is_missing(fighter.get("D")) else fighter.get("D") or 0
    return f"{wins}-{losses}-{draws}"


def _format_ufc_record(fighter: dict) -> str:
    wins = 0 if is_missing(fighter.get("UFC W")) else fighter.get("UFC W") or 0
    losses = 0 if is_missing(fighter.get("UFC L")) else fighter.get("UFC L") or 0
    draws = 0 if is_missing(fighter.get("UFC D")) else fighter.get("UFC D") or 0
    return f"{wins}-{losses}-{draws}"


def _get_age(birth_date) -> int | None:
    if is_missing(birth_date):
        return None
    today = date.today()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def _parse_fighter_id(value) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _photo_html(fighter: dict) -> str:
    name = escape(text_value(fighter.get("Name"), "Unknown"))
    initials = _initials(text_value(fighter.get("Name"), ""))
    photo_url = fighter.get("Photo URL")
    if not is_missing(photo_url) and photo_url:
        return (
            '<div class="ufc-profile-photo-shell">'
            f'<img class="ufc-profile-photo" src="{escape(str(photo_url))}" alt="{name}" '
            'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
            f'<div class="ufc-profile-photo-placeholder" style="display:none">{initials}</div>'
            "</div>"
        )
    return (
        '<div class="ufc-profile-photo-shell">'
        f'<div class="ufc-profile-photo-placeholder">{initials}</div>'
        "</div>"
    )


def _header_html(fighter: dict) -> str:
    name = escape(text_value(fighter.get("Name"), "Unknown"))
    nickname = fighter.get("Nickname")
    division = escape(text_value(fighter.get("Weight Class"), "No division"))
    record = _format_record(fighter)
    last_fight = _format_date(fighter.get("Last Fight"))
    nickname_html = (
        f'<div class="ufc-profile-nickname">"{escape(text_value(nickname))}"</div>'
        if not is_missing(nickname) and str(nickname).strip()
        else ""
    )
    return (
        '<div class="ufc-profile-hero-copy">'
        f'<div class="ufc-profile-eyebrow">{division}</div>'
        f'<h1 class="ufc-profile-name">{name}</h1>'
        f"{nickname_html}"
        '<div class="ufc-profile-summary">'
        f'<span class="ufc-profile-summary-item">Career record {record}</span>'
        f'<span class="ufc-profile-summary-item">Last fight {last_fight}</span>'
        "</div>"
        "</div>"
    )


def _meta_html(items: list[tuple[str, str]]) -> str:
    html = ['<div class="ufc-profile-meta-grid">']
    for label, value in items:
        html.append(
            '<div class="ufc-profile-meta-item">'
            f'<div class="ufc-profile-meta-label">{escape(label)}</div>'
            f'<div class="ufc-profile-meta-value">{escape(value)}</div>'
            "</div>"
        )
    html.append("</div>")
    return "".join(html)


def _fight_row_html(fight: dict) -> str:
    result = text_value(fight.get("Result"))
    result_class = {
        "Win": "win",
        "Loss": "loss",
        "Draw": "draw",
        "No Contest": "draw",
    }.get(result, "draw")
    tags = []
    weight_class = fight.get("Weight Class")
    if not is_missing(weight_class) and str(weight_class).strip():
        tags.append(escape(text_value(weight_class)))
    if not is_missing(fight.get("Title Fight")) and fight.get("Title Fight"):
        tags.append("Title fight")
    if not is_missing(fight.get("Stop Time")) and str(fight["Stop Time"]).strip():
        tags.append(escape(text_value(fight["Stop Time"])))
    elif fight.get("Rounds"):
        tags.append(f"{fight['Rounds']} rounds")
    tags_html = "".join(
        f'<span class="ufc-profile-tag">{tag}</span>'
        for tag in tags
    )
    method = escape(text_value(fight.get("Method"), "Method unavailable"))
    opponent = escape(text_value(fight.get("Opponent"), "Unknown opponent"))
    event = escape(text_value(fight.get("Event"), "Unknown event"))
    event_date = _format_date(fight.get("Date"))
    return (
        '<div class="ufc-profile-fight-row">'
        '<div class="ufc-profile-fight-main">'
        f'<div class="ufc-profile-fight-result {result_class}">{escape(result)}</div>'
        '<div class="ufc-profile-fight-copy">'
        f'<div class="ufc-profile-fight-opponent">vs {opponent}</div>'
        f'<div class="ufc-profile-fight-event">{event} · {event_date}</div>'
        f'<div class="ufc-profile-fight-method">{method}</div>'
        "</div>"
        "</div>"
        f'<div class="ufc-profile-fight-tags">{tags_html}</div>'
        "</div>"
    )


def _recent_fights_html(fights: list[dict]) -> str:
    if not fights:
        return '<div class="ufc-profile-empty">No recent fights found.</div>'
    rows = "".join(_fight_row_html(fight) for fight in fights)
    return f'<div class="ufc-profile-fights">{rows}</div>'


def _insights(fighter: dict, fights: list[dict]) -> list[tuple[str, str, str]]:
    wins = 0 if is_missing(fighter.get("W")) else fighter.get("W") or 0
    finish_wins = 0 if is_missing(fighter.get("Finish Wins")) else fighter.get("Finish Wins") or 0
    decision_wins = 0 if is_missing(fighter.get("Decision Wins")) else fighter.get("Decision Wins") or 0
    total_fights = 0 if is_missing(fighter.get("Total Fights")) else fighter.get("Total Fights") or 0
    form_sample = fights[:3]
    form_wins = sum(1 for fight in form_sample if fight.get("Result") == "Win")

    if finish_wins > decision_wins:
        result_profile = "More wins by finish than by decision"
    elif decision_wins > finish_wins:
        result_profile = "More wins by decision than by finish"
    else:
        result_profile = "Even split between finish and decision wins"

    finish_share = "—"
    if wins:
        finish_share = f"{round(finish_wins / wins * 100)}% of wins by finish"

    recent_form = "No recent sample"
    if form_sample:
        recent_form = f"{form_wins} win(s) in last {len(form_sample)} fight(s)"

    return [
        ("UFC win rate", _format_percent(fighter.get("Win Rate")), f"{total_fights} UFC fights in database"),
        ("Finish share", finish_share, result_profile),
        ("Recent form", recent_form, _format_date(fighter.get("Last Fight"))),
    ]


def _insights_html(items: list[tuple[str, str, str]]) -> str:
    html = ['<div class="ufc-profile-insights">']
    for label, value, detail in items:
        html.append(
            '<div class="ufc-profile-insight">'
            f'<div class="ufc-profile-insight-label">{escape(label)}</div>'
            f'<div class="ufc-profile-insight-value">{escape(value)}</div>'
            f'<div class="ufc-profile-insight-detail">{escape(detail)}</div>'
            "</div>"
        )
    html.append("</div>")
    return "".join(html)


st.caption("Fighter Profile")

session = get_session()
directory = get_fighter_directory(session)
query_fighter_id = _parse_fighter_id(st.query_params.get("fighter_id"))
fighter = get_fighter_profile(session, query_fighter_id) if query_fighter_id else None
recent_fights = get_fighter_recent_fights(session, query_fighter_id) if fighter else []

fighter_ids = [item["ID"] for item in directory]

if not fighter_ids:
    session.close()
    st.info("No fighters available yet.")
    st.stop()

st.page_link("pages/02_Fighters.py", label="Back to Fighters")

if not fighter:
    st.info("Open a fighter from the Fighters page to view the full profile.")
    session.close()
    st.stop()

physical_items = [
    ("Division", text_value(fighter.get("Weight Class"))),
    ("Stance", text_value(fighter.get("Stance"))),
    ("Height", _format_measure(fighter.get("Height (cm)"), "cm")),
    ("Reach", _format_measure(fighter.get("Reach (cm)"), "cm")),
    ("Born", _format_date(fighter.get("Birth Date"))),
    ("Age", str(_get_age(fighter.get("Birth Date"))) if _get_age(fighter.get("Birth Date")) is not None else "—"),
]

hero_left, hero_right = st.columns([0.48, 2.02], gap="large")
with hero_left:
    st.markdown(_photo_html(fighter), unsafe_allow_html=True)
with hero_right:
    st.markdown(_header_html(fighter), unsafe_allow_html=True)
    st.subheader("Global Stats")
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Career Record", _format_record(fighter))
    metric_2.metric("UFC Record", _format_ufc_record(fighter))
    metric_3.metric("UFC Win Rate", _format_percent(fighter.get("Win Rate")))
    metric_4, metric_5 = st.columns(2)
    metric_4.metric("Finish Wins", 0 if is_missing(fighter.get("Finish Wins")) else fighter.get("Finish Wins") or 0)
    metric_5.metric("Decision Wins", 0 if is_missing(fighter.get("Decision Wins")) else fighter.get("Decision Wins") or 0)

st.subheader("Physical Info")
st.markdown(_meta_html(physical_items), unsafe_allow_html=True)

st.subheader("Recent Fights")
st.markdown(_recent_fights_html(recent_fights), unsafe_allow_html=True)

st.subheader("Insights")
st.markdown(_insights_html(_insights(fighter, recent_fights)), unsafe_allow_html=True)

session.close()
