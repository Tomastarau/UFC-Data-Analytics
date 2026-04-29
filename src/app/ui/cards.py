from html import escape
from urllib.parse import urlencode

import streamlit as st

from src.app.formatters import int_value, is_missing, text_value


def _initials(name: str | None) -> str:
    if not name:
        return "?"
    parts = name.split()
    return "".join(p[0] for p in parts[:2]).upper()

def fighter_card_html(fighter: dict) -> str:
    name = escape(text_value(fighter.get("Name"), "Unknown"))
    initials = _initials(text_value(fighter.get("Name"), ""))
    fighter_id = fighter.get("ID")
    w = 0 if is_missing(fighter.get("W")) else fighter.get("W") or 0
    l = 0 if is_missing(fighter.get("L")) else fighter.get("L") or 0
    d = 0 if is_missing(fighter.get("D")) else fighter.get("D") or 0
    record = f"{w}-{l}-{d}"
    photo_url = fighter.get("Photo URL")
    profile_url = f"/Fighter_Profile?{urlencode({'fighter_id': fighter_id})}"

    if not is_missing(photo_url) and photo_url:
        photo_html = (
            f'<img class="ufc-fighter-card__photo" src="{escape(str(photo_url))}" '
            f'alt="{name}" loading="lazy" '
            f'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
            f'<div class="ufc-fighter-card__placeholder" style="display:none">{initials}</div>'
        )
    else:
        photo_html = f'<div class="ufc-fighter-card__placeholder">{initials}</div>'

    stance = escape(text_value(fighter.get("Stance")))
    height = int_value(fighter.get("Height (cm)"), " cm")
    reach = int_value(fighter.get("Reach (cm)"), " cm")
    weight_class = escape(text_value(fighter.get("Weight Class")))

    return (
        f'<a class="ufc-fighter-card-link" href="{profile_url}" target="_self">'
        f'<div class="ufc-fighter-card">'
        f'{photo_html}'
        f'<div class="ufc-fighter-card__body">'
        f'<div class="ufc-fighter-card__name" title="{name}">{name}</div>'
        f'<div class="ufc-fighter-card__record">{record}</div>'
        f'<div class="ufc-fighter-card__division">{weight_class}</div>'
        f'<div class="ufc-fighter-card__meta">'
        f'{stance} · {height} · {reach}'
        f'</div></div></div></a>'
    )


def display_fighter_grid(
    fighters: list[dict], page_size: int = 24, key: str = "fighter_grid"
) -> None:
    if not fighters:
        st.info("No fighters found.")
        return

    shown_key = f"{key}_shown"
    sig_key = f"{key}_sig"
    signature = (len(fighters), fighters[0].get("ID"), fighters[-1].get("ID"))

    if st.session_state.get(sig_key) != signature:
        st.session_state[sig_key] = signature
        st.session_state[shown_key] = page_size

    shown = min(st.session_state[shown_key], len(fighters))

    grid_html = '<div class="ufc-fighter-grid">'
    for fighter in fighters[:shown]:
        grid_html += fighter_card_html(fighter)
    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

    remaining = len(fighters) - shown
    if remaining > 0:
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            next_chunk = min(page_size, remaining)
            if st.button(
                f"Afficher {next_chunk} de plus · {remaining} restants",
                key=f"{key}_more",
                use_container_width=True,
            ):
                st.session_state[shown_key] += page_size
                st.rerun()
    else:
        st.caption(f"{len(fighters)} fighters affichés")
