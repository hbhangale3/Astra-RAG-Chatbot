import mimetypes

import requests
import streamlit as st

from src.frontend.config.frontend_config import Settings
from src.frontend.auth.auth_manager import require_login


settings = Settings()
username = require_login()

SUPPORTED_FILE_TYPES = ["pdf", "docx", "pptx", "txt", "md"]

st.title("📂 Upload Documents")

st.markdown(
    """
    Upload course material in **PDF, DOCX, PPTX, TXT, or MD** format.
    Once uploaded, the document is converted, ingested into ChromaDB,
    and becomes available in **Chat With Notes** and **Generate Quiz**.
    """
)


def fetch_documents_and_storage():
    """
    Fetches uploaded documents and storage quota information from the backend.
    """
    response = requests.get(
        settings.DOCUMENT_LIST_URL,
        params={"user_id": username},
        timeout=30,
    )

    if response.status_code != 200:
        st.error("Could not fetch uploaded documents.")
        st.write(response.text)
        return [], None

    data = response.json()
    return data.get("documents", []), data.get("storage")


def render_storage_usage(storage: dict | None):
    """
    Displays user's current storage usage and quota limit.
    """
    if not storage:
        st.info("Storage usage unavailable.")
        return

    used_mb = storage["used_mb"]
    limit_mb = storage["limit_mb"]

    st.metric("Storage Used", f"{used_mb} MB / {limit_mb} MB")

    # Show a visual progress bar for storage usage.
    progress_value = min(used_mb / limit_mb, 1.0) if limit_mb else 0
    st.progress(progress_value)


def get_content_type(filename: str) -> str:
    """
    Returns the best-effort MIME type for an uploaded file.

    Parameters:
        filename (str): Uploaded filename.

    Returns:
        str: MIME type string.
    """
    guessed_type, _ = mimetypes.guess_type(filename)

    return guessed_type or "application/octet-stream"


def upload_selected_files(uploaded_files):
    """
    Uploads selected supported documents one-by-one to the backend.

    Current MVP behavior:
    - Each file upload triggers ingestion.
    - Future improvement:
      send all files in one request and ingest once.
    """
    for uploaded_file in uploaded_files:
        with st.spinner(f"Uploading and ingesting {uploaded_file.name}..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    get_content_type(uploaded_file.name),
                )
            }

            try:
                response = requests.post(
                    settings.DOCUMENT_UPLOAD_URL,
                    files=files,
                    params={"user_id": username},
                    timeout=300,
                )

                if response.status_code == 200:
                    st.success(f"{uploaded_file.name} uploaded and ingested successfully.")
                else:
                    st.error(f"Upload failed for {uploaded_file.name}.")
                    st.write(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to backend for {uploaded_file.name}: {e}")


def delete_document(filename: str):
    """
    Deletes a selected document through the backend API.
    """
    try:
        response = requests.delete(
            f"{settings.DOCUMENT_DELETE_BASE_URL}/{filename}",
            params={"user_id": username},
            timeout=300,
        )

        if response.status_code == 200:
            st.success(f"{filename} deleted successfully.")
            st.rerun()
        else:
            st.error(f"Could not delete {filename}.")
            st.write(response.text)

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}")


# Fetch latest document and storage information.
documents, storage = fetch_documents_and_storage()

render_storage_usage(storage)

st.divider()

uploaded_files = st.file_uploader(
    "Upload documents",
    type=SUPPORTED_FILE_TYPES,
    accept_multiple_files=True,
)

if st.button("Upload and Ingest"):
    if not uploaded_files:
        st.warning("Please select at least one supported document first.")
    else:
        upload_selected_files(uploaded_files)
        st.rerun()

st.divider()

st.subheader("Uploaded Documents")

if not documents:
    st.info("No documents uploaded yet.")
else:
    for doc in documents:
        col1, col2, col3, col4 = st.columns([5, 1, 2, 1])

        with col1:
            st.write(f"**{doc['filename']}**")

        with col2:
            st.write(doc.get("extension", "N/A"))

        with col3:
            st.write(f"{doc['size_mb']} MB")

        with col4:
            if st.button("Delete", key=f"delete_{doc['filename']}"):
                delete_document(doc["filename"])