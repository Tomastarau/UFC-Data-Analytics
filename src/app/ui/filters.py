import pandas as pd
import streamlit as st


def year_filter(years: list[int], key: str = "year_filter") -> int | None:
    options = ["All"] + years
    selected = st.selectbox("Year", options, key=key)
    return None if selected == "All" else selected


def weight_class_filter(classes: list[str], key: str = "wc_filter") -> str | None:
    options = ["All"] + classes
    selected = st.selectbox("Weight Class", options, key=key)
    return None if selected == "All" else selected


def method_filter(methods: list[str], key: str = "method_filter") -> str | None:
    options = ["All"] + methods
    selected = st.selectbox("Method", options, key=key)
    return None if selected == "All" else selected


def apply_filter(df: pd.DataFrame, column: str, value) -> pd.DataFrame:
    if value is None:
        return df
    return df[df[column] == value]
