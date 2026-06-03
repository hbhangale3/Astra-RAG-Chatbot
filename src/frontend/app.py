import streamlit as st

st.set_page_config(
    page_title="Study Buddy AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Study Buddy AI")

st.markdown(
    """
    Study Buddy AI helps students upload course material, chat with their notes,
    and generate source-grounded quizzes from uploaded documents.

    ### Current Features
    - 💬 Chat with ingested documents
    - 📚 Source-grounded answers using RAG
    - ⚡ FastAPI backend + Streamlit frontend
    - 🧠 ChromaDB vector storage
    - 🤖 CrewAI + OpenAI orchestration and Groq-based RAG generation

    ### Upcoming Features
    - 📂 Upload documents from the UI
    - 📝 Generate MCQs and quizzes
    - 👤 Multi-user authentication
    - 📊 Prometheus and Grafana monitoring
    """
)

st.info("Use the sidebar to navigate between Upload, Chat, Quiz, and Dashboard pages.")