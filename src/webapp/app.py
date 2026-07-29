import streamlit as st

from src.webapp.db import get_session
from src.webapp.services.events import count_events
from src.webapp.services.fighters import count_fighters
from src.webapp.services.fights import count_fights, finish_rate
from src.webapp.ui.styles import inject_styles

st.set_page_config(
    page_title="UFC Data Analytics",
    page_icon="🥊",
    layout="wide",
)

inject_styles()

st.markdown(
    '<h1 class="ufc-hero">UFC <span class="ufc-hero-accent">Data Analytics</span></h1>'
    '<div class="ufc-hero-tagline">Events · Fighters · Fights · Insights</div>',
    unsafe_allow_html=True,
)

session = get_session()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Events", count_events(session))
c2.metric("Fighters", count_fighters(session))
c3.metric("Fights", count_fights(session))
c4.metric("Finish Rate", f"{finish_rate(session)}%")
session.close()

st.markdown("&nbsp;")
st.subheader("Explore")

pages = [
    ("Events", "Events", "Browse UFC events by year"),
    ("Fighters", "Fighters", "Search fighters by weight class"),
    ("Fights", "Fights", "Explore fight results and methods"),
    ("Insights", "Insights", "Charts and analytics"),
]

cards_html = '<div class="ufc-nav-grid">'
for slug, title, desc in pages:
    cards_html += (
        f'<a class="ufc-nav-card" href="/{slug}" target="_self">'
        f'<h3>{title}</h3><p>{desc}</p></a>'
    )
cards_html += "</div>"
st.markdown(cards_html, unsafe_allow_html=True)
