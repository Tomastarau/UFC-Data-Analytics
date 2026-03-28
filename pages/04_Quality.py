import streamlit as st

from src.app.db import get_session
from src.app.services.quality import get_last_ingestion, get_quality_results

st.header("Quality & Ingestion")

session = get_session()

st.subheader("Last Ingestion")
ingestion = get_last_ingestion(session)
if ingestion:
    for key, value in ingestion.items():
        if value is not None:
            st.markdown(f"**{key}:** {value}")
else:
    st.info("No ingestion runs found.")

st.subheader("Quality Checks")
results = get_quality_results(session)
for check_name, issues in results.items():
    label = check_name.replace("_", " ").title()
    if not issues:
        st.success(f"{label}: PASS")
    else:
        st.error(f"{label}: {len(issues)} issues")
        with st.expander("Details"):
            for issue in issues[:10]:
                st.text(issue)

session.close()
