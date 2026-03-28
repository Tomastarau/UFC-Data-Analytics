import pandas as pd
import streamlit as st

from src.app.db import get_session
from src.app.services.fighters import count_fighters, get_all_fighters, get_weight_classes
from src.app.ui.filters import apply_filter, weight_class_filter
from src.app.ui.metrics import display_metrics
from src.app.ui.tables import display_table

st.header("Fighters")

session = get_session()

display_metrics({"Total Fighters": count_fighters(session)})

classes = get_weight_classes(session)
selected_class = weight_class_filter(classes)

data = get_all_fighters(session)
df = pd.DataFrame(data)
df = apply_filter(df, "Weight Class", selected_class)

display_table(df.to_dict("records"))

session.close()
