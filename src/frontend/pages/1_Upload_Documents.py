import streamlit as st

st.title("📂 Upload Documents")

st.markdown(
    """
    Upload support will be added in the next phase.

    Planned behavior:
    - Upload PDF, DOCX, PPTX, and other study material
    - Enforce total storage limit per user
    - Convert uploaded files into text/Markdown
    - Ingest content into ChromaDB
    - Make uploaded content available for chat and quiz generation
    """
)

uploaded_files = st.file_uploader(
    "Upload documents",
    type=["pdf", "docx", "pptx", "txt", "md"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.info("Upload backend is not connected yet. This page is currently a UI skeleton.")

    total_size = sum(file.size for file in uploaded_files)
    st.write(f"Selected files: {len(uploaded_files)}")
    st.write(f"Total selected size: {total_size / (1024 * 1024):.2f} MB")

    for file in uploaded_files:
        st.write(f"- {file.name} — {file.size / (1024 * 1024):.2f} MB")