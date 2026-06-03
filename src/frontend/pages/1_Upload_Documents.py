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


def fetch_documents_and_storage():
    """
    Fetches uploaded documents and storage quota information from the backend.
    """
    response = requests.get(settings.DOCUMENT_LIST_URL, timeout=30)

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


def upload_selected_files(uploaded_files):
    """
    Uploads selected PDF files one-by-one to the backend.

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


def delete_document(filename: str):
    """
    Deletes a selected document through the backend API.
    """
    try:
        response = requests.delete(
            f"{settings.DOCUMENT_DELETE_BASE_URL}/{filename}",
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
    "Upload PDF documents",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("Upload and Ingest"):
    if not uploaded_files:
        st.warning("Please select at least one PDF file first.")
    else:
        upload_selected_files(uploaded_files)
        st.rerun()

st.divider()

st.subheader("Uploaded Documents")

if not documents:
    st.info("No documents uploaded yet.")
else:
    for doc in documents:
        col1, col2, col3 = st.columns([5, 2, 1])

        with col1:
            st.write(f"**{doc['filename']}**")

        with col2:
            st.write(f"{doc['size_mb']} MB")

        with col3:
            if st.button("Delete", key=f"delete_{doc['filename']}"):
                delete_document(doc["filename"])