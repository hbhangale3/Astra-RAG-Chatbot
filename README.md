# AstraRAG - Agentic RAG Chatbot

## Overview

AstraRAG is an Agentic Retrieval-Augmented Generation (RAG) chatbot built using CrewAI, LlamaIndex, ChromaDB, FastAPI, Streamlit, and Large Language Models. The system allows users to upload domain-specific documents, ingest them into a vector database, and interact with them through a conversational interface.

The project combines:

* Retrieval-Augmented Generation (RAG)
* Agent-based orchestration using CrewAI
* Vector Search using ChromaDB
* FastAPI backend services
* Streamlit frontend UI
* OpenAI and Groq LLM integrations

---

# Features

* Conversational document question answering
* Context-aware responses using chat history
* Vector-based semantic retrieval
* Source attribution for every answer
* Agentic workflow using CrewAI
* FastAPI backend APIs
* Streamlit frontend interface
* Configurable LLM providers
* Persistent ChromaDB vector storage

---

# Architecture

```text
User
 │
 ▼
Streamlit Frontend
 │
 ▼
FastAPI Backend
 │
 ▼
CrewAI Crew
 │
 ▼
Question Answer Agent
 │
 ▼
RAG Tool
 │
 ▼
LlamaIndex Query Engine
 │
 ▼
ChromaDB Vector Store
 │
 ▼
Retrieved Chunks
 │
 ▼
LLM Generation
 │
 ▼
Answer + Sources
 │
 ▼
Frontend Response
```

---

# Tech Stack

## Frontend

* Streamlit

## Backend

* FastAPI
* Uvicorn

## Agent Framework

* CrewAI

## RAG Framework

* LlamaIndex

## Vector Database

* ChromaDB

## Embeddings

* HuggingFace Embeddings

## LLM Providers

* OpenAI
* Groq

## Configuration

* Pydantic Settings
* Python Dotenv

---

# Project Structure

```text
Astra_RAG/
│
├── Docs/
│
├── vectorDB/
│
├── src/
│   │
│   ├── agents/
│   │   ├── agent/
│   │   ├── tasks/
│   │   ├── tools/
│   │   ├── llm/
│   │   └── crew.py
│   │
│   ├── backend/
│   │   ├── api/
│   │   ├── services/
│   │   ├── config/
│   │   └── main.py
│   │
│   ├── frontend/
│   │   ├── config/
│   │   └── app.py
│   │
│   └── rag_doc_ingestion/
│       ├── config/
│       └── ingest_doc.py
│
├── .env
├── pyproject.toml
├── run_astra.sh
└── README.md
```

---

# Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=<your_groq_api_key>

OPENAI_API_KEY=<your_openai_api_key>

DOCUMENTS_DIR=./Docs

VECTOR_STORE_DIR=./vectorDB

COLLECTION_NAME=document_collection

MODEL_NAME="llama-3.1-8b-instant"

MODEL_TEMPERATURE=0.2

CHAT_ENDPOINT_URL=http://localhost:8000/chat/answer
```

---

# Installing Dependencies

Using uv:

```bash
uv sync
```

Or using pip:

```bash
pip install -r requirements.txt
```

---

# Adding Documents

Place all PDF documents inside:

```text
Docs/
```

Example:

```text
Docs/
├── Week1.pdf
├── Week2.pdf
├── Week3.pdf
└── Notes.pdf
```

---

# Document Ingestion

Generate embeddings and populate ChromaDB.

```bash
python3 -m src.rag_doc_ingestion.ingest_doc
```

This step performs:

1. PDF loading
2. Text extraction
3. Chunking
4. Embedding generation
5. ChromaDB insertion

---

# Running Backend

Start FastAPI:

```bash
python3 -m src.backend.main
```

Backend runs on:

```text
http://localhost:8000
```

---

# Running Frontend

Start Streamlit:

```bash
streamlit run src/frontend/app.py
```

Frontend runs on:

```text
http://localhost:8501
```

---

# Running Entire Application

A helper script is provided.

```bash
chmod +x run_astra.sh
```

Run:

```bash
./run_astra.sh
```

The script:

1. Checks vector database existence
2. Runs ingestion if required
3. Starts FastAPI backend
4. Starts Streamlit frontend

---

# RAG Pipeline

## Step 1

User submits query.

```text
"What is the DIV instruction?"
```

## Step 2

Query converted into embedding.

## Step 3

Vector similarity search performed.

```python
retriever.retrieve(query)
```

## Step 4

Top matching chunks retrieved.

## Step 5

Chunks passed to LLM.

```python
query_engine.query(query)
```

## Step 6

Answer generated.

## Step 7

Source documents attached.

---

# Agent Flow

## Crew

```python
qa_crew
```

Responsible for orchestrating tasks.

---

## Agent

```python
Question Answer Agent
```

Responsible for:

* Understanding query
* Calling retrieval tool
* Formatting answer

---

## Task

```python
Question Answering Task
```

Provides:

* User query
* Chat history
* Instructions
* Output schema

---

## Tool

```python
rag_query_tool
```

Responsible for:

* Vector retrieval
* LLM querying
* Source extraction

---

# Backend Flow

## Frontend Request

```text
POST /chat/answer
```

Payload:

```json
{
  "chat_history": [...]
}
```

---

## API Layer

File:

```text
backend/api/chat.py
```

Responsibilities:

* Receive request
* Validate payload
* Forward request to service layer

---

## Service Layer

File:

```text
backend/services/chat.py
```

Responsibilities:

* Extract latest user query
* Build CrewAI input
* Execute crew
* Return response

---

## Crew Execution

```python
qa_crew.kickoff(input_data)
```

---

# Frontend Flow

User enters prompt.

```text
Streamlit Chat Input
```

↓

Chat history stored in:

```python
st.session_state.chat_history
```

↓

POST request sent to backend.

↓

Backend response displayed.

↓

Sources and reasoning rendered.

---

# API Response Format

```json
{
  "answer": "...",
  "sources": [
    "Week5.pdf",
    "Week6.pdf"
  ],
  "tool_used": "RAG Retriever",
  "rationale": "Retrieved relevant context from vector database"
}
```

---

# Troubleshooting

## Empty Responses

Verify:

```bash
python3 -m src.rag_doc_ingestion.ingest_doc
```

Rebuild vector database.

---

## Incorrect Sources

Inspect retrieved nodes.

```python
retriever.retrieve(query)
```

Check scores and content.

---

## API Errors

Verify:

```text
OPENAI_API_KEY
GROQ_API_KEY
```

are correctly loaded.

---

## Vector Database Issues

Delete:

```text
vectorDB/
```

Re-run ingestion.

```bash
python3 -m src.rag_doc_ingestion.ingest_doc
```

---

# Future Improvements

* Multi-document collections
* Hybrid search (BM25 + Vector Search)
* Query rewriting
* Citation highlighting
* Conversation memory store
* Authentication
* Docker deployment
* Kubernetes deployment
* Agent evaluation metrics
* Multi-agent workflows

---

# Author

Harshwardhan Ashish Bhangale

MS Computer Engineering
San Jose State University

---

# License

MIT License
