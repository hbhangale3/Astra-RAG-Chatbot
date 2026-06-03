import streamlit as st

st.title("📊 Dashboard")

st.markdown(
    """
    This dashboard will later show application and RAG metrics.

    Planned metrics:
    - Total documents uploaded
    - Total storage used
    - Chat requests
    - Quiz generations
    - RAG retrieval latency
    - LLM generation latency
    - Ingestion success/failure count
    """
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Documents", "Coming soon")

with col2:
    st.metric("Storage Used", "Coming soon")

with col3:
    st.metric("Quiz Count", "Coming soon")