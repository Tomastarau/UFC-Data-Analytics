import streamlit as st

from src.webapp.db import get_session
from src.webapp.services.insights import get_fights_by_year, get_ko_tko_by_year
from src.webapp.ui.charts import display_bar_chart
from src.webapp.ui.styles import inject_styles

inject_styles()

st.header("Insights")

session = get_session()

st.subheader("Fights per Year")
display_bar_chart(get_fights_by_year(session), x="Year", y="Count")

st.subheader("KO/TKO per Year")
display_bar_chart(get_ko_tko_by_year(session), x="Year", y="Count")

session.close()
