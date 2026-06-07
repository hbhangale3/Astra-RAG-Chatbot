#!/bin/bash
set -e

echo "======================================="
echo "Starting Astra RAG Study Buddy"
echo "======================================="

echo "MODE=${MODE:-all}"
echo "PYTHONPATH=$PYTHONPATH"
echo "BACKEND_BASE_URL=$BACKEND_BASE_URL"
echo "OPENAI_MODEL=$OPENAI_MODEL"
echo "MODEL_NAME=$MODEL_NAME"

mkdir -p data/users

start_backend() {
  echo "Starting FastAPI backend on port 8000..."
  python -m src.backend.main
}

start_frontend() {
  echo "Starting Streamlit frontend on port 8501..."
  streamlit run src/frontend/app.py \
    --server.address=0.0.0.0 \
    --server.port=8501
}

case "${MODE:-all}" in
  backend)
    start_backend
    ;;

  frontend)
    start_frontend
    ;;

  all)
    echo "Starting backend and frontend in the same container..."
    python -m src.backend.main &

    echo "Waiting for backend to start..."
    sleep 8

    streamlit run src/frontend/app.py \
      --server.address=0.0.0.0 \
      --server.port=8501
    ;;

  *)
    echo "Invalid MODE: $MODE"
    echo "Allowed values: backend, frontend, all"
    exit 1
    ;;
esac