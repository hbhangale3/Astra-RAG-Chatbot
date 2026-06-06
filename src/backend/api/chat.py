import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from src.backend.services.chat import get_answer
from src.backend.services.metrics_service import chat_requests_total

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatHistoryRequest(BaseModel):
    chat_history: List[ChatMessage]
    user_id: str = "default_user"

@router.post("/chat/answer")
def chat_answer(request: ChatHistoryRequest):
    logger.info(f"Received API request with chat_history: {request.chat_history}")
    try:
        chat_history = [msg.dict() for msg in request.chat_history]
        chat_requests_total.labels(user_id=request.user_id).inc()
        result = get_answer(chat_history, user_id=request.user_id)
        logger.info(f"API response: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in chat_answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))