import streamlit as st
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from src.db import get_engine


@st.cache_resource
def get_cached_engine() -> Engine:
    return get_engine()


def get_session() -> Session:
    return Session(bind=get_cached_engine())
