import pandas as pd
import streamlit as st


def display_table(data: list[dict], page_size: int = 25) -> None:
    if not data:
        st.info("No data available.")
        return
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, height=min(len(df), page_size) * 35 + 38)
