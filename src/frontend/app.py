import sys
import os
# Add project root to sys.path BEFORE any imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st
import requests
from src.frontend.config.frontend_config import Settings
from src.frontend.auth.auth_manager import require_login

settings = Settings()

st.set_page_config(
    page_title="AstraRAG",
    page_icon="🤖",
    layout="centered",
)

username = require_login()

st.title("💬 AstraRAG - Agentic RAG Chatbot")
st.title("📚 AstraRAG - Study Buddy AI")

st.markdown(
    """
    Welcome to **AstraRAG**, an Agentic RAG-powered Study Buddy application.

    This application helps you upload study material, chat with your notes,
    generate quizzes, track quiz performance, and monitor your learning progress.
    """
)

st.divider()

st.header("What You Can Do")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Upload Documents")
    st.write(
        """
        Upload one or more PDF files. The system stores your documents,
        ingests them into ChromaDB, and prepares them for retrieval-based question answering.
        """
    )

    st.subheader("💬 Chat With Notes")
    st.write(
        """
        Ask questions based on your uploaded documents. The chatbot retrieves
        relevant context from your notes and generates source-grounded answers.
        """
    )

with col2:
    st.subheader("📝 Generate Quiz")
    st.write(
        """
        Generate quizzes from your uploaded study material using custom topics,
        difficulty levels, and question types.
        """
    )

    st.subheader("📊 Dashboard")
    st.write(
        """
        View uploaded document count, storage usage, quiz attempts,
        average score, best score, and recent quiz history.
        """
    )

st.divider()

st.header("Suggested Workflow")

st.markdown(
    """
    1. Go to **Upload Documents** and upload your PDFs.
    2. Use **Chat With Notes** to ask questions from uploaded material.
    3. Open **Generate Quiz** to test your understanding.
    4. Track your progress from the **Dashboard**.
    """
)

st.info("Use the sidebar to navigate between pages.")