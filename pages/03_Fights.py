import pandas as pd
import streamlit as st

from src.app.db import get_session
from src.app.services.fights import count_fights, finish_rate, get_all_fights, get_fight_weight_classes, get_result_methods
from src.app.ui.filters import apply_filter, method_filter, weight_class_filter
from src.app.ui.metrics import display_metrics
from src.app.ui.styles import inject_styles
from src.app.ui.tables import display_table

inject_styles()

st.header("Fights")

session = get_session()

display_metrics({
    "Total Fights": count_fights(session),
    "Finish Rate": f"{finish_rate(session)}%",
})

col1, col2 = st.columns(2)
with col1:
    methods = get_result_methods(session)
    selected_method = method_filter(methods)
with col2:
    classes = get_fight_weight_classes(session)
    selected_wc = weight_class_filter(classes, key="fights_wc_filter")

data = get_all_fights(session)
df = pd.DataFrame(data)
df = apply_filter(df, "Method Group", selected_method)
df = apply_filter(df, "Weight Class", selected_wc)

display_table(df.to_dict("records"))

session.close()
