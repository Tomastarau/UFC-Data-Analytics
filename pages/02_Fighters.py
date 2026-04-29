import pandas as pd
import streamlit as st

from src.app.db import get_session
from src.app.services.fighters import count_fighters, get_all_fighters, get_weight_classes
from src.app.ui.cards import display_fighter_grid
from src.app.ui.filters import (
    apply_filter,
    apply_name_filter,
    apply_sort,
    name_filter,
    sort_filter,
    weight_class_filter,
)
from src.app.ui.metrics import display_metrics
from src.app.ui.styles import inject_styles
from src.app.ui.tables import display_table

inject_styles()

st.header("Fighters")

session = get_session()
total = count_fighters(session)
classes = get_weight_classes(session)
data = get_all_fighters(session)
session.close()

display_metrics({"Total Fighters": total})

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = name_filter()
with col2:
    selected_class = weight_class_filter(classes)
with col3:
    sort_label = sort_filter()

df = pd.DataFrame(data)
df = apply_filter(df, "Weight Class", selected_class)
df = apply_name_filter(df, "Name", search_query)
df = apply_sort(df, sort_label)
records = df.astype(object).where(pd.notna(df), None).to_dict("records")

view = st.radio("View", ["Cards", "Table"], horizontal=True, label_visibility="collapsed")

if view == "Cards":
    display_fighter_grid(records)
else:
    display_table(records)
