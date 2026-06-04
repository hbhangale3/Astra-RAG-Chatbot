import requests
import streamlit as st

from src.frontend.config.frontend_config import Settings

from src.frontend.auth.auth_manager import require_login

settings = Settings()
username = require_login()


st.title("📊 Dashboard")

st.markdown(
    """
    Track your uploaded study material and quiz performance.
    """
)


def fetch_document_data():
    """
    Fetches uploaded document list and storage usage from the backend.
    """
    try:
        response = requests.get(settings.DOCUMENT_LIST_URL, params={"user_id": username}, timeout=30)

        if response.status_code == 200:
            return response.json()

        st.warning("Could not fetch document data.")
        return {}

    except requests.exceptions.RequestException as e:
        st.warning(f"Document backend unavailable: {e}")
        return {}


def fetch_quiz_summary():
    """
    Fetches quiz performance metrics from the backend.
    """
    try:
        response = requests.get(settings.QUIZ_SUMMARY_URL,params={"user_id": username}, timeout=30)

        if response.status_code == 200:
            return response.json().get("summary", {})

        st.warning("Could not fetch quiz summary.")
        return {}

    except requests.exceptions.RequestException as e:
        st.warning(f"Quiz backend unavailable: {e}")
        return {}


document_data = fetch_document_data()
documents = document_data.get("documents", [])
storage = document_data.get("storage", {})

quiz_summary = fetch_quiz_summary()

st.subheader("Document Storage")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Documents Uploaded", len(documents))

with col2:
    st.metric("Storage Used", f"{storage.get('used_mb', 0)} MB")

with col3:
    st.metric("Storage Limit", f"{storage.get('limit_mb', 0)} MB")

if storage:
    used_mb = storage.get("used_mb", 0)
    limit_mb = storage.get("limit_mb", 1)
    st.progress(min(used_mb / limit_mb, 1.0))

st.divider()

st.subheader("Quiz Performance")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Quizzes Attempted", quiz_summary.get("total_attempts", 0))

with col2:
    st.metric("Average Score", f"{quiz_summary.get('average_score_percentage', 0)}%")

with col3:
    st.metric("Best Score", f"{quiz_summary.get('best_score_percentage', 0)}%")

st.divider()

st.subheader("Recent Quiz Attempts")

recent_attempts = quiz_summary.get("recent_attempts", [])

if not recent_attempts:
    st.info("No quiz attempts saved yet.")
else:
    for attempt in recent_attempts:
        st.write(
            f"**{attempt.get('topic')}** — "
            f"{attempt.get('score')}/{attempt.get('total_questions')} "
            f"({attempt.get('percentage')}%)"
        )
        st.caption(f"Difficulty: {attempt.get('difficulty')} | Attempted at: {attempt.get('created_at')}")
        st.divider()