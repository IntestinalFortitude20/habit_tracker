from typing import Literal

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
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


def _prepare_messages(payload: ChatRequest, db: Session) -> list[dict]:
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    try:
        context = chat_service.build_context(db, payload.habit_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Habit not found")
    history = [m.model_dump() for m in payload.history]
    return chat_service.build_messages(context, payload.message, history)


def _sse(data: dict, event: str | None = None) -> str:
    return (f"event: {event}\n" if event else "") + f"data: {json.dumps(data)}\n\n"


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    messages = _prepare_messages(payload, db)
    try:
        reply = chat_service.call_llm(messages)
    except chat_service.LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return ChatResponse(reply=reply)


@router.post("/stream")
def chat_stream(payload: ChatRequest, db: Session = Depends(get_db)):
    messages = _prepare_messages(payload, db)
    tokens = chat_service.stream_llm(messages)
    try:
        first = next(tokens)
    except StopIteration:
        raise HTTPException(status_code=502, detail="The AI service returned an empty response.")
    except chat_service.LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    def events():
        try:
            yield _sse({"token": first})
            for token in tokens:
                yield _sse({"token": token})
            yield _sse({}, event="done")
        except chat_service.LLMError as e:
            yield _sse({"detail": e.message}, event="error")
        finally:
            tokens.close()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
