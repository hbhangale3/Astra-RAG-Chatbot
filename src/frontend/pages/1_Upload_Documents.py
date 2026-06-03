import streamlit as st
import requests

from src.frontend.config.frontend_config import Settings


settings = Settings()

st.title("📂 Upload Documents")

st.markdown(
    """
    Upload PDF course material. Once uploaded, the document is ingested into ChromaDB
    and becomes available in **Chat With Notes**.
    """
)

uploaded_files = st.file_uploader(
    "Upload PDF documents",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("Upload and Ingest"):
    if not uploaded_files:
        st.warning("Please select at least one PDF file first.")
    else:
        for uploaded_file in uploaded_files:
            with st.spinner(f"Uploading and ingesting {uploaded_file.name}..."):
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf",
                    )
                }

                try:
                    response = requests.post(
                        settings.DOCUMENT_UPLOAD_URL,
                        files=files,
                        timeout=300,
                    )

                    if response.status_code == 200:
                        st.success(f"{uploaded_file.name} uploaded and ingested successfully.")
                    else:
                        st.error(f"Upload failed for {uploaded_file.name}.")
                        st.write(response.text)

                except requests.exceptions.RequestException as e:
                    st.error(f"Could not connect to backend for {uploaded_file.name}: {e}")

st.divider()

st.subheader("Uploaded Documents")

if st.button("Refresh Document List"):
    try:
        response = requests.get(settings.DOCUMENT_LIST_URL, timeout=30)

        if response.status_code == 200:
            documents = response.json().get("documents", [])

            if not documents:
                st.info("No documents uploaded yet.")
            else:
                for doc in documents:
                    st.write(f"- **{doc['filename']}** — {doc['size_mb']} MB")
        else:
            st.error("Could not fetch document list.")
            st.write(response.text)

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}")