import pandas as pd
import streamlit as st

from src.app.db import get_session
from src.app.services.events import count_events, get_all_events, get_event_years
from src.app.ui.filters import apply_filter, year_filter
from src.app.ui.metrics import display_metrics
from src.app.ui.styles import inject_styles
from src.app.ui.tables import display_table

inject_styles()

st.header("Events")

session = get_session()

display_metrics({"Total Events": count_events(session)})

years = get_event_years(session)
selected_year = year_filter(years)

data = get_all_events(session)
df = pd.DataFrame(data)
df = apply_filter(df, "Year", selected_year)

display_table(df.to_dict("records"))

session.close()
