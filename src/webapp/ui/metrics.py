import streamlit as st


def display_metrics(metrics: dict[str, any]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        col.metric(label, value)
