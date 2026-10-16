from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import chat as chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    habit_id: int | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=100)


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    try:
        context = chat_service.build_context(db, payload.habit_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Habit not found")
    history = [m.model_dump() for m in payload.history]
    messages = chat_service.build_messages(context, payload.message, history)
    try:
        reply = chat_service.call_llm(messages)
    except chat_service.LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return ChatResponse(reply=reply)
