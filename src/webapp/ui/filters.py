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


def name_filter(key: str = "name_filter") -> str | None:
    query = st.text_input("Search by name", key=key)
    return query.strip() if query.strip() else None


def apply_name_filter(df: pd.DataFrame, column: str, query: str | None) -> pd.DataFrame:
    if query is None:
        return df
    return df[df[column].str.contains(query, case=False, na=False)]


SORT_OPTIONS = {
    "Name A–Z": ("Name", True),
    "Most recent fight": ("Last Fight", False),
    "Most wins": ("W", False),
    "Most losses": ("L", False),
    "Best record": ("Win %", False),
    "Longest reach": ("Reach (cm)", False),
    "Tallest": ("Height (cm)", False),
}


def sort_filter(key: str = "sort_filter") -> str:
    return st.selectbox("Sort by", list(SORT_OPTIONS.keys()), key=key)


def apply_sort(df: pd.DataFrame, sort_label: str) -> pd.DataFrame:
    column, ascending = SORT_OPTIONS[sort_label]
    if column == "Win %":
        total = df["W"] + df["L"] + df["D"]
        df = df.copy()
        df["Win %"] = (df["W"] / total.replace(0, pd.NA)).fillna(0)
    return df.sort_values(column, ascending=ascending, na_position="last")


def apply_filter(df: pd.DataFrame, column: str, value) -> pd.DataFrame:
    if value is None:
        return df
    return df[df[column] == value]
