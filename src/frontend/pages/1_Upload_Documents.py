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

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    accept_multiple_files=False,
)

if st.button("Upload and Ingest"):
    if uploaded_file is None:
        st.warning("Please select a PDF file first.")
    else:
        with st.spinner("Uploading and ingesting document..."):
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
                    st.success("Document uploaded and ingested successfully.")
                    st.json(response.json())
                else:
                    st.error("Upload failed.")
                    st.write(response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to backend: {e}")

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