#!/bin/bash

echo "======================================="
echo "Starting Astra RAG Chatbot"
echo "======================================="

VECTOR_DB="./vectorDB"

if [ ! -d "$VECTOR_DB" ]; then
    echo "Vector store not found. Running ingestion..."
    uv run python -m src.rag_doc_ingestion.ingest_doc
else
    echo "Vector store already exists. Skipping ingestion."
fi

echo "Starting FastAPI backend..."
uv run python -m src.backend.main &
BACKEND_PID=$!

sleep 10

echo "Starting Streamlit frontend..."
uv run streamlit run src/frontend/app.py --server.address=0.0.0.0 --server.port=8501

echo "Stopping backend..."
kill $BACKEND_PID
