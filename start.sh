#!/bin/bash

echo "======================================="
echo "Starting Astra RAG Chatbot"
echo "======================================="

# Activate virtual environment

source .venv/bin/activate

# Check if vector store exists

VECTOR_DB="./vectorDB"

if [ ! -d "$VECTOR_DB" ]; then
echo ""
echo "Vector store not found."
echo "Running document ingestion..."
echo ""

```
python3 -m src.rag_doc_ingestion.ingest_doc

if [ $? -ne 0 ]; then
    echo "Document ingestion failed."
    exit 1
fi

echo ""
echo "Document ingestion completed."
echo ""
```

else
echo ""
echo "Vector store already exists."
echo "Skipping ingestion."
echo ""
fi

echo "Starting FastAPI backend..."

python3 -m src.backend.main &
BACKEND_PID=$!

sleep 5

echo ""
echo "Backend running on http://localhost:8000"
echo ""

echo "Starting Streamlit frontend..."

streamlit run src/frontend/app.py

echo ""
echo "Stopping backend..."
kill $BACKEND_PID

