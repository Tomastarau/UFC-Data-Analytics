import pandas as pd
import streamlit as st

from src.app.db import get_session
from src.app.services.insights import get_fights_by_year, get_ko_tko_by_year

st.header("Insights")

session = get_session()

st.subheader("Fights per Year")
fights_data = get_fights_by_year(session)
df_fights = pd.DataFrame(fights_data).set_index("Year")
st.bar_chart(df_fights)

st.subheader("KO/TKO per Year")
ko_data = get_ko_tko_by_year(session)
df_ko = pd.DataFrame(ko_data).set_index("Year")
st.bar_chart(df_ko)

session.close()
