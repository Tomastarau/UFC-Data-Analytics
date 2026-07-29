import pandas as pd
import plotly.graph_objects as go
import streamlit as st

UFC_RED = "#D20A0A"
UFC_TEXT = "#1A1A1A"
UFC_GRID = "#E0E0E0"
UFC_BG = "#FFFFFF"


def display_bar_chart(
    data: list[dict],
    x: str,
    y: str,
    title: str | None = None,
    height: int = 280,
) -> None:
    if not data:
        st.info("No data available.")
        return

    df = pd.DataFrame(data)
    fig = go.Figure(
        go.Bar(
            x=df[x],
            y=df[y],
            marker_color=UFC_RED,
            marker_line_color=UFC_RED,
            hovertemplate=f"<b>%{{x}}</b><br>{y}: %{{y}}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title or "", font=dict(size=16, color=UFC_TEXT, family="sans serif")),
        plot_bgcolor=UFC_BG,
        paper_bgcolor=UFC_BG,
        font=dict(color=UFC_TEXT, family="sans serif", size=12),
        xaxis=dict(title=x, gridcolor=UFC_GRID, showline=True, linecolor=UFC_GRID, fixedrange=True),
        yaxis=dict(title=y, gridcolor=UFC_GRID, showline=True, linecolor=UFC_GRID, fixedrange=True),
        margin=dict(l=60, r=20, t=40 if title else 20, b=50),
        hoverlabel=dict(bgcolor=UFC_RED, font_color="#FFFFFF", font_size=13),
        bargap=0.3,
        dragmode=False,
        height=height,
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False},
    )
