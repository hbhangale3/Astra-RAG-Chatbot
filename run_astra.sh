#!/bin/bash
set -e

echo "======================================="
echo "Starting Astra RAG Chatbot"
echo "======================================="

echo "DOCUMENTS_DIR=$DOCUMENTS_DIR"
echo "VECTOR_STORE_DIR=$VECTOR_STORE_DIR"
echo "COLLECTION_NAME=$COLLECTION_NAME"
echo "MODEL_NAME=$MODEL_NAME"

if [ ! -d "$VECTOR_STORE_DIR" ] || [ -z "$(ls -A "$VECTOR_STORE_DIR" 2>/dev/null)" ]; then
  echo "Vector store not found or empty. Running ingestion..."
  .venv/bin/python -m src.rag_doc_ingestion.ingest_doc
else
  echo "Vector store already exists. Skipping ingestion."
fi

echo "Starting FastAPI backend..."
.venv/bin/python -m src.backend.main &

sleep 10

echo "Starting Streamlit frontend..."
.venv/bin/streamlit run src/frontend/app.py \
  --server.address=0.0.0.0 \
  --server.port=8501
