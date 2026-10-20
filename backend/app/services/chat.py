from datetime import date, timedelta
import json
import logging
import time
from collections.abc import Iterator

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Entry, Habit, Metric
from app.services.goals import goal_context_lines, rest_dates
from app.services.stats import compute_stats

MAX_HISTORY = 10
RECENT_DAYS = 30
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a supportive, encouraging habit coach inside a habit tracker app. "
    "Give concise, practical, non-judgmental advice grounded in the user's data below. "
    "If the data is insufficient, say so rather than inventing details."
    "Don't ask unnecessary date/clarification questions."

)

RESPONSE_STYLE_PROMPT = (
    "Coaching behavior: "
    "Be warm and concise. Focus on one habit at a time when possible. "
    "Start by briefly reflecting the user's current status from their stats. "
    "Then provide 1-3 concrete next steps. "
    "Prefer actionable suggestions over theory. "
    "If chat context is global and the target habit is unclear, ask exactly one short question: "
    "'Which habit should we focus on right now?' and wait for the answer. "
    "If chat context is already habit-specific, do not ask which habit. "
    "Avoid mentioning date uncertainty unless explicitly relevant. "
    "Do not provide medical diagnosis or treatment; for high-risk health concerns, suggest professional help."
)

class LLMError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _stats_for(db: Session, habit_id: int, today: date) -> dict:
    rows = db.query(Entry.date, Entry.completed).filter(Entry.habit_id == habit_id).all()
    return compute_stats([(r.date, r.completed) for r in rows], today=today, rest_days=rest_dates(db, habit_id))


def _fmt_value(metric: Metric, value: float) -> str:
    text = f"{value:g}"
    return f"{text} {metric.unit}" if metric.unit else text


def build_context(db: Session, habit_id: int | None, today: date | None = None) -> str:
    today = today or date.today()
    if habit_id is None:
        habits = db.query(Habit).filter(Habit.archived.is_(False)).order_by(Habit.created_at.desc()).all()
        if not habits:
            return "The user has no habits yet."
        lines = ["The user's habits (name: current streak):"]
        for h in habits:
            lines.append(f"- {h.name}: {_stats_for(db, h.id, today)['current_streak']}-day streak")
        return "\n".join(lines)

    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if habit is None:
        raise LookupError("Habit not found")
    stats = _stats_for(db, habit.id, today)
    metrics = db.query(Metric).filter(Metric.habit_id == habit.id).all()
    lines = [f"Habit: {habit.name}"]
    if habit.description:
        lines.append(f"Description: {habit.description}")
    if metrics:
        lines.append("Metrics: " + ", ".join(f"{m.name} ({m.type}{', ' + m.unit if m.unit else ''})" for m in metrics))
    lines.append(
        f"Stats: current streak {stats['current_streak']} days, longest streak {stats['longest_streak']} days, "
        f"7-day completion {round(stats['completion_rate_7d'] * 100)}%, "
        f"30-day completion {round(stats['completion_rate_30d'] * 100)}%."
    )
    lines.extend(goal_context_lines(db, habit.id, today))
    since = today - timedelta(days=RECENT_DAYS - 1)
    entries = (
        db.query(Entry)
        .filter(Entry.habit_id == habit.id, Entry.date >= since, Entry.date <= today)
        .order_by(Entry.date)
        .all()
    )
    lines.append(f"Entries in the last {RECENT_DAYS} days:" if entries else f"No entries in the last {RECENT_DAYS} days.")
    by_id = {m.id: m for m in metrics}
    for e in entries:
        vals = [
            f"{by_id[mv.metric_id].name}={_fmt_value(by_id[mv.metric_id], mv.value)}"
            for mv in e.metric_values
            if mv.metric_id in by_id
        ]
        lines.append(f"- {e.date.isoformat()}: {'done' if e.completed else 'not done'}" + (f" ({', '.join(vals)})" if vals else ""))
    return "\n".join(lines)


def build_messages(context: str, message: str, history: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    #system = f"{SYSTEM_PROMPT}\n\nToday's date: {today.isoformat()}\n\n{context}"
    system = (
    f"{SYSTEM_PROMPT}\n"
    f"{RESPONSE_STYLE_PROMPT}\n\n"
    f"Today's date: {today.isoformat()}\n\n"
    f"{context}"
    )
    return [{"role": "system", "content": system}, *history[-MAX_HISTORY:], {"role": "user", "content": message}]


def call_llm(messages: list[dict]) -> str:
    started_at = time.perf_counter()
    try:
        if not settings.llm_api_key:
            raise LLMError(503, "AI chat is not configured. Set LLM_API_KEY in backend/.env and restart the backend.")
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        try:
            resp = httpx.post(
                url,
                headers={"Authorization": "Bearer " + settings.llm_api_key},
                json={"model": settings.llm_model, "messages": messages},
                timeout=settings.llm_timeout_seconds,
            )
        except httpx.TimeoutException:
            raise LLMError(504, "The AI service took too long to respond. Please try again.")
        except httpx.HTTPError:
            raise LLMError(502, "Could not reach the AI service. Please try again later.")
        if resp.status_code >= 400:
            raise LLMError(502, "The AI service returned an error. Please try again later.")
        try:
            reply = resp.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise LLMError(502, "The AI service returned an unexpected response.")
        if not isinstance(reply, str) or not reply.strip():
            raise LLMError(502, "The AI service returned an empty response.")
        return reply.strip()
    finally:
        logger.info(
            "LLM response model=%s duration_seconds=%.3f",
            settings.llm_model,
            time.perf_counter() - started_at,
        )


def stream_llm(messages: list[dict]) -> Iterator[str]:
    """Yield reply tokens from the OpenAI-compatible endpoint using SSE streaming."""
    started_at = time.perf_counter()
    try:
        if not settings.llm_api_key:
            raise LLMError(503, "AI chat is not configured. Set LLM_API_KEY in backend/.env and restart the backend.")
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        received = False
        try:
            with httpx.stream(
                "POST",
                url,
                headers={"Authorization": "Bearer " + settings.llm_api_key},
                json={"model": settings.llm_model, "messages": messages, "stream": True},
                timeout=settings.llm_timeout_seconds,
            ) as resp:
                if resp.status_code >= 400:
                    raise LLMError(502, "The AI service returned an error. Please try again later.")
                for line in resp.iter_lines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        token = json.loads(data)["choices"][0]["delta"].get("content")
                    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
                        raise LLMError(502, "The AI service returned an unexpected response.")
                    if isinstance(token, str) and token:
                        received = True
                        yield token
        except httpx.TimeoutException:
            raise LLMError(504, "The AI service took too long to respond. Please try again.")
        except httpx.HTTPError:
            raise LLMError(502, "Could not reach the AI service. Please try again later.")
        if not received:
            raise LLMError(502, "The AI service returned an empty response.")
    finally:
        logger.info(
            "LLM stream model=%s duration_seconds=%.3f",
            settings.llm_model,
            time.perf_counter() - started_at,
        )
