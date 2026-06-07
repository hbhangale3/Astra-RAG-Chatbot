import logging
import os
import time
from pathlib import Path

import chromadb
from crewai.tools import tool
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.backend.services.metrics_service import rag_retrieval_latency_seconds


logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "default_user"
BASE_DATA_DIR = Path("data/users")
COLLECTION_NAME = "document_collection"

DEFAULT_MODEL_NAME = "llama-3.3-70b-versatile"
DEFAULT_MODEL_TEMPERATURE = 0.2

logger.info("Loading HuggingFace embedding model...")
embed_model = HuggingFaceEmbedding()


def get_model_temperature() -> float:
    """
    Returns the model temperature from the environment.

    Returns:
        float: Model temperature value.
    """
    raw_temperature = os.getenv("MODEL_TEMPERATURE", str(DEFAULT_MODEL_TEMPERATURE))

    try:
        return float(raw_temperature)
    except ValueError:
        logger.warning(
            "Invalid MODEL_TEMPERATURE=%s. Falling back to default=%s",
            raw_temperature,
            DEFAULT_MODEL_TEMPERATURE,
        )
        return DEFAULT_MODEL_TEMPERATURE


def configure_llm() -> dict | None:
    """
    Configures the LlamaIndex LLM using environment variables.

    Returns:
        dict | None: Error response if configuration is missing, otherwise None.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        return {
            "answer": "GROQ_API_KEY is not configured for the backend.",
            "source_files": [],
        }

    model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)
    model_temperature = get_model_temperature()

    Settings.llm = Groq(
        model=model_name,
        temperature=model_temperature,
        api_key=groq_api_key,
    )

    return None


@tool
def rag_query_tool(query: str, user_id: str = DEFAULT_USER_ID) -> dict:
    """
    Answers a query by retrieving relevant user documents and generating a response.

    Args:
        query (str): User query to answer.
        user_id (str): Authenticated user identifier.

    Returns:
        dict: Response containing:
            - answer (str): Generated answer.
            - source_files (list[str]): Source filenames used for retrieval.
    """
    vector_store_path = BASE_DATA_DIR / user_id / "chroma"
    collection_name = COLLECTION_NAME

    print(f"[RETRIEVAL] USER_ID = {user_id}")
    print(f"[RETRIEVAL] VECTOR_STORE_DIR = {vector_store_path}")
    print(f"[RETRIEVAL] COLLECTION_NAME = {collection_name}")

    llm_error = configure_llm()

    if llm_error:
        return llm_error

    if not vector_store_path.exists():
        return {
            "answer": "No vector store found for this user. Please upload and ingest documents first.",
            "source_files": [],
        }

    try:
        db = chromadb.PersistentClient(path=str(vector_store_path))
        chroma_collection = db.get_collection(name=collection_name)

    except Exception:
        return {
            "answer": "Vector collection not found. Please upload and ingest documents first.",
            "source_files": [],
        }

    collection_count = chroma_collection.count()
    print(f"[RETRIEVAL] Collection count = {collection_count}")

    if collection_count == 0:
        return {
            "answer": "No documents have been ingested yet. The vector database is empty.",
            "source_files": [],
        }

    vector_store = ChromaVectorStore(
        chroma_collection=chroma_collection
    )

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    logger.info("Loading vector store index from ChromaDB")

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    query_engine = index.as_query_engine(
        similarity_top_k=3
    )

    logger.info("Querying the index with the provided query")

    retrieval_start_time = time.time()

    try:
        response = query_engine.query(query)

    finally:
        retrieval_duration = time.time() - retrieval_start_time

        rag_retrieval_latency_seconds.labels(
            user_id=user_id,
        ).observe(retrieval_duration)

    source_file_names = {
        metadata.get("file_name")
        for metadata in getattr(response, "metadata", {}).values()
        if metadata.get("file_name")
    }

    return {
        "answer": str(response.response).replace("\x08", "").strip(),
        "source_files": list(source_file_names),
    }