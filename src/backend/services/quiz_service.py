import json
import os
import time
from pathlib import Path
from typing import Dict, List

import chromadb
from fastapi import HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from src.agents.config.agent_settings import AgentSettings
from src.backend.services.metrics_service import (
    rag_retrieval_latency_seconds,
    llm_generation_latency_seconds,
    llm_input_tokens_total,
    llm_output_tokens_total,
)


DEFAULT_USER_ID = "default_user"
BASE_DATA_DIR = Path("data/users")

embed_model = HuggingFaceEmbedding()

settings = AgentSettings()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MIN_RETRIEVAL_SCORE = 0.60
MIN_REQUIRED_CHUNKS = 2
SIMILARITY_TOP_K = 6


class QuizGenerateRequest(BaseModel):
    """
    Request body for generating a quiz from uploaded study material.
    """
    topic: str = Field(..., min_length=2)
    num_questions: int = Field(default=5, ge=1, le=15)
    difficulty: str = Field(default="Medium")
    question_type: str = Field(default="MCQ")
    user_id: str = DEFAULT_USER_ID


def get_user_chroma_dir(user_id: str = DEFAULT_USER_ID) -> Path:
    """
    Returns the ChromaDB directory for the selected user.

    Parameters:
        user_id (str): Authenticated user identifier.

    Returns:
        Path: User-specific ChromaDB directory path.
    """
    return BASE_DATA_DIR / user_id / "chroma"


def get_chroma_collection(user_id: str = DEFAULT_USER_ID):
    """
    Loads the existing ChromaDB collection used by the quiz RAG pipeline.

    Important:
    Retrieval must use get_collection(), not get_or_create_collection().
    If the collection does not exist, we want to fail clearly instead of silently
    creating an empty collection.

    Parameters:
        user_id (str): Authenticated user identifier.

    Returns:
        Collection: ChromaDB collection for the selected user's uploaded documents.
    """
    vector_store_dir = get_user_chroma_dir(user_id)

    print(f"[QUIZ RETRIEVAL] USER_ID = {user_id}")
    print(f"[QUIZ RETRIEVAL] VECTOR_STORE_DIR = {vector_store_dir}")
    print(f"[QUIZ RETRIEVAL] COLLECTION_NAME = {settings.COLLECTION_NAME}")

    if not vector_store_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="No uploaded documents found for this user. Please upload notes first.",
        )

    db = chromadb.PersistentClient(path=str(vector_store_dir))
    collection = db.get_collection(name=settings.COLLECTION_NAME)

    print(f"[QUIZ RETRIEVAL] Collection count = {collection.count()}")

    return collection


def retrieve_relevant_chunks(
    topic: str,
    user_id: str = DEFAULT_USER_ID,
) -> List[dict]:
    """
    Retrieves source chunks from the selected user's ChromaDB for the quiz topic.

    If the topic is not present in the uploaded material, this function returns
    too few chunks and the quiz request is rejected.

    Parameters:
        topic (str): Topic entered by the user.
        user_id (str): Authenticated user identifier.

    Returns:
        List[dict]: Relevant source chunks with text, score, and source filename.
    """
    retrieval_start_time = time.time()

    try:
        collection = get_chroma_collection(user_id)

        vector_store = ChromaVectorStore(
            chroma_collection=collection
        )

        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model,
        )

        retriever = index.as_retriever(
            similarity_top_k=SIMILARITY_TOP_K
        )

        retrieved_nodes = retriever.retrieve(topic)

    finally:
        retrieval_duration = time.time() - retrieval_start_time

        rag_retrieval_latency_seconds.labels(
            user_id=user_id,
        ).observe(retrieval_duration)

    relevant_chunks = []

    for node_with_score in retrieved_nodes:
        score = node_with_score.score or 0.0

        # Keep only chunks that are sufficiently related to the requested topic.
        if score >= MIN_RETRIEVAL_SCORE:
            source_file = node_with_score.node.metadata.get(
                "file_name",
                "unknown_source"
            )

            relevant_chunks.append(
                {
                    "text": node_with_score.node.get_text(),
                    "score": score,
                    "source": source_file,
                }
            )

    return relevant_chunks


def build_quiz_prompt(request: QuizGenerateRequest, chunks: List[dict]) -> str:
    """
    Builds the LLM prompt for quiz generation.

    The model is instructed to generate questions only from the retrieved source
    chunks and return valid JSON.

    Parameters:
        request (QuizGenerateRequest): Quiz generation request payload.
        chunks (List[dict]): Retrieved source chunks.

    Returns:
        str: Prompt sent to the LLM.
    """
    source_context = "\n\n".join(
        [
            f"Source: {chunk['source']}\nContent:\n{chunk['text']}"
            for chunk in chunks
        ]
    )

    return f"""
You are a quiz generation assistant for a Study Buddy AI application.

Generate a source-grounded quiz using ONLY the source material below.

Topic:
{request.topic}

Number of questions:
{request.num_questions}

Difficulty:
{request.difficulty}

Question type:
{request.question_type}

Source material:
{source_context}

Return ONLY valid JSON in this exact format:

{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct_answer": "A",
      "explanation": "Explain why the correct answer is right using the source material.",
      "source": "source_filename.pdf"
    }}
  ]
}}

Rules:
- Generate exactly {request.num_questions} questions.
- Use only the uploaded source material.
- Do not use outside knowledge.
- Each question must have exactly 4 options.
- correct_answer must be one of A, B, C, or D.
- Explanation must be concise but useful.
"""


def generate_quiz_with_llm(
    request: QuizGenerateRequest,
    chunks: List[dict],
) -> Dict:
    """
    Calls the LLM to generate quiz questions from retrieved source chunks.

    Parameters:
        request (QuizGenerateRequest): Quiz generation request payload.
        chunks (List[dict]): Retrieved source chunks.

    Returns:
        Dict: Parsed quiz JSON returned by the LLM.
    """
    prompt = build_quiz_prompt(request, chunks)

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    llm_start_time = time.time()

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You generate valid JSON quizzes from source material."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    llm_duration = time.time() - llm_start_time

    llm_generation_latency_seconds.labels(
        user_id=request.user_id,
        model=model_name,
    ).observe(llm_duration)

    usage = getattr(response, "usage", None)

    if usage:
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0

        llm_input_tokens_total.labels(
            user_id=request.user_id,
            model=model_name,
        ).inc(input_tokens)

        llm_output_tokens_total.labels(
            user_id=request.user_id,
            model=model_name,
        ).inc(output_tokens)

    raw_content = response.choices[0].message.content

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Quiz generation failed because the model returned invalid JSON.",
        )


def generate_quiz(request: QuizGenerateRequest) -> Dict:
    """
    Main quiz generation workflow.

    Flow:
    1. Retrieve chunks for the requested topic from the selected user's ChromaDB.
    2. Reject unsupported topics.
    3. Generate MCQs using the LLM.
    4. Return quiz data to the frontend.

    Parameters:
        request (QuizGenerateRequest): Quiz generation request payload.

    Returns:
        Dict: Quiz response returned to the frontend.
    """
    chunks = retrieve_relevant_chunks(
        topic=request.topic,
        user_id=request.user_id,
    )

    if len(chunks) < MIN_REQUIRED_CHUNKS:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Not enough uploaded material found for topic '{request.topic}'. "
                "Please upload relevant notes first or choose another topic."
            ),
        )

    quiz = generate_quiz_with_llm(request, chunks)

    return {
        "topic": request.topic,
        "difficulty": request.difficulty,
        "question_type": request.question_type,
        "source_chunks_used": len(chunks),
        "user_id": request.user_id,
        "quiz": quiz,
    }