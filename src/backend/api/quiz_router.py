from fastapi import APIRouter
from pydantic import BaseModel

from src.backend.services.quiz_service import (
    generate_quiz,
    QuizGenerateRequest,
)
from src.backend.services.quiz_history_service import (
    save_quiz_attempt,
    load_quiz_attempts,
    get_quiz_summary,
)


DEFAULT_USER_ID = "default_user"

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
    user_id: str = DEFAULT_USER_ID


@router.post("/attempts")
def save_quiz_attempt_endpoint(request: QuizAttemptSaveRequest):
    """
    Saves a completed quiz attempt for the selected user after submission.
    """
    attempt_data = request.model_dump()

    saved_attempt = save_quiz_attempt(
        attempt_data=attempt_data,
        user_id=request.user_id,
    )

    return {
        "message": "Quiz attempt saved successfully.",
        "attempt": saved_attempt,
    }


@router.get("/attempts")
def list_quiz_attempts_endpoint(user_id: str = DEFAULT_USER_ID):
    """
    Returns all saved quiz attempts for the selected user.
    """
    return {
        "attempts": load_quiz_attempts(user_id=user_id)
    }


@router.get("/summary")
def quiz_summary_endpoint(user_id: str = DEFAULT_USER_ID):
    """
    Returns quiz summary metrics for dashboard display for the selected user.
    """
    return {
        "summary": get_quiz_summary(user_id=user_id)
    }


@router.post("/generate")
def generate_quiz_endpoint(request: QuizGenerateRequest):
    """
    Generates a source-grounded quiz from uploaded documents.

    Flow:
    1. Receive topic, question count, and difficulty.
    2. Retrieve relevant chunks from ChromaDB.
    3. Reject the request if uploaded material is insufficient.
    4. Generate quiz questions from the retrieved source material.
    5. Return questions, answers, explanations, and sources.
    """
    return generate_quiz(request)