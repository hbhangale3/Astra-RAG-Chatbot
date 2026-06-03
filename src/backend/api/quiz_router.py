from fastapi import APIRouter

from src.backend.services.quiz_service import generate_quiz
from src.backend.services.quiz_service import QuizGenerateRequest


router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"],
)


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