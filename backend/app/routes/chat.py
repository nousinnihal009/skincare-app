"""
chat.py — AI Dermatologist Chatbot API
"""

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.chatbot import get_chatbot_response

router = APIRouter(prefix="/api", tags=["chat"])


class ChatMessage(BaseModel):
    message: str


@router.post("/chat")
async def chat(payload: ChatMessage):
    """AI Dermatologist chatbot endpoint."""
    response = get_chatbot_response(payload.message)
    return response
