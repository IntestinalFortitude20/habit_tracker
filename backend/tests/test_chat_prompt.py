from datetime import date, timedelta

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.session import Base
from app.models.models import Entry, Habit, Metric, MetricValue, User
from app.services import chat as chat_service
from app.services.chat import (
    MAX_HISTORY,
    RESPONSE_STYLE_PROMPT,
    SYSTEM_PROMPT,
    LLMError,
    build_context,
    build_messages,
    call_llm,
)

TODAY = date(2024, 6, 15)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(User(id=1, email="u@example.com"))
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def running(db):
    habit = Habit(user_id=1, name="Running", description="Morning runs")
    db.add(habit)
    db.flush()
    metric = Metric(habit_id=habit.id, name="Distance", type="count", unit="km")
    db.add(metric)
    db.flush()
    for days_ago, done in [(2, True), (1, True), (0, False)]:
        entry = Entry(habit_id=habit.id, date=TODAY - timedelta(days=days_ago), completed=done)
        db.add(entry)
        db.flush()
        if done:
            db.add(MetricValue(entry_id=entry.id, metric_id=metric.id, value=5))
    db.add(Entry(habit_id=habit.id, date=TODAY - timedelta(days=60), completed=True))
    db.commit()
    return habit


def test_context_no_habits(db):
    assert build_context(db, None, today=TODAY) == "The user has no habits yet."


def test_context_global_lists_habits_with_streaks(db, running):
    db.add(Habit(user_id=1, name="Reading"))
    db.add(Habit(user_id=1, name="Old", archived=True))
    db.commit()
    ctx = build_context(db, None, today=TODAY)
    assert "- Running:" in ctx and "- Reading: 0-day streak" in ctx
    assert "Old" not in ctx


def test_context_habit_specific(db, running):
    ctx = build_context(db, running.id, today=TODAY)
    assert "Habit: Running" in ctx
    assert "Description: Morning runs" in ctx
    assert "Metrics: Distance (count, km)" in ctx
    assert "Stats: current streak" in ctx and "longest streak" in ctx
    assert "Entries in the last 30 days:" in ctx
    assert "- 2024-06-14: done (Distance=5 km)" in ctx
    assert "- 2024-06-15: not done" in ctx
    assert (TODAY - timedelta(days=60)).isoformat() not in ctx


def test_context_habit_without_entries(db):
    habit = Habit(user_id=1, name="Yoga")
    db.add(habit)
    db.commit()
    assert "No entries in the last 30 days." in build_context(db, habit.id, today=TODAY)


def test_context_unknown_habit_raises(db):
    with pytest.raises(LookupError):
        build_context(db, 999, today=TODAY)


def test_build_messages_structure():
    history = [{"role": "user", "content": str(i)} for i in range(MAX_HISTORY + 5)]
    msgs = build_messages("CTX-MARKER", "hello", history, today=TODAY)
    assert msgs[0]["role"] == "system"
    system = msgs[0]["content"]
    assert SYSTEM_PROMPT in system and RESPONSE_STYLE_PROMPT in system
    assert "2024-06-15" in system and "CTX-MARKER" in system
    assert msgs[1:-1] == history[-MAX_HISTORY:]
    assert len(msgs) == MAX_HISTORY + 2
    assert msgs[-1] == {"role": "user", "content": "hello"}


def test_build_messages_short_history_kept():
    history = [{"role": "assistant", "content": "a"}]
    msgs = build_messages("c", "m", history, today=TODAY)
    assert msgs[1:-1] == history


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _reply(content):
    return FakeResponse(200, {"choices": [{"message": {"content": content}}]})


@pytest.fixture
def llm(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")

    def install(result):
        def fake_post(*args, **kwargs):
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(chat_service.httpx, "post", fake_post)

    return install


def test_call_llm_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", None)
    with pytest.raises(LLMError) as e:
        call_llm([])
    assert e.value.status_code == 503


@pytest.mark.parametrize(
    "result,status",
    [
        (httpx.TimeoutException("slow"), 504),
        (httpx.ConnectError("down"), 502),
        (FakeResponse(500, {}), 502),
        (FakeResponse(200, ValueError("bad json")), 502),
        (_reply(""), 502),
        (_reply("   "), 502),
        (_reply(None), 502),
    ],
)
def test_call_llm_errors(llm, result, status):
    llm(result)
    with pytest.raises(LLMError) as e:
        call_llm([{"role": "user", "content": "hi"}])
    assert e.value.status_code == status


def test_call_llm_success_trimmed(llm):
    llm(_reply("  Keep going!  \n"))
    assert call_llm([{"role": "user", "content": "hi"}]) == "Keep going!"
