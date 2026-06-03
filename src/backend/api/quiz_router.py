from fastapi import APIRouter

from src.backend.services.quiz_service import generate_quiz
from src.backend.services.quiz_service import QuizGenerateRequest
from pydantic import BaseModel
from src.backend.services.quiz_history_service import (
    save_quiz_attempt,
    load_quiz_attempts,
    get_quiz_summary,
)

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"],
)

class QuizAttemptSaveRequest(BaseModel):
    """
    Request body for saving a completed quiz attempt.
    """
    topic: str
    difficulty: str
    question_type: str
    score: int
    total_questions: int
    percentage: float
    questions: list


@router.post("/attempts")
def save_quiz_attempt_endpoint(request: QuizAttemptSaveRequest):
    """
    Saves a completed quiz attempt after the student submits answers.
    """
    saved_attempt = save_quiz_attempt(
        attempt_data=request.model_dump()
    )

    return {
        "message": "Quiz attempt saved successfully.",
        "attempt": saved_attempt,
    }


@router.get("/attempts")
def list_quiz_attempts_endpoint():
    """
    Returns all saved quiz attempts for the default user.
    """
    return {
        "attempts": load_quiz_attempts()
    }


@router.get("/summary")
def quiz_summary_endpoint():
    """
    Returns quiz summary metrics for dashboard display.
    """
    return {
        "summary": get_quiz_summary()
    }

@router.post("/generate")
def generate_quiz_endpoint(request: QuizGenerateRequest):
    """
    Generates a source-grounded quiz from uploaded documents.

    Flow:
    1. Receive topic, question count, and difficulty.
    2. Retrieve relevant chunks from ChromaDB.
    3. Reject the request if uploaded material is insufficient.
    4. Generate MCQs from the retrieved source material.
    5. Return questions, options, answers, explanations, and sources.
    """
    return generate_quiz(request)