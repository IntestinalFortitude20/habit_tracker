import os

os.environ["DATABASE_URL"] = "sqlite:///./test_chat.db"

from datetime import date  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.services import chat as chat_service  # noqa: E402


def _make_habit(c):
    h = c.post("/api/habits", json={"user_id": 1, "name": "Running", "description": "Morning runs"}).json()
    m = c.post(f"/api/habits/{h['id']}/metrics", json={"name": "Distance", "type": "count", "unit": "km"}).json()
    c.post(f"/api/habits/{h['id']}/entries", json={"date": date.today().isoformat(), "completed": True, "metric_values": [{"metric_id": m["id"], "value": 5}]})
    return h


def test_context_for_habit_and_general():
    with TestClient(app) as c:
        h = _make_habit(c)
        db = SessionLocal()
        try:
            ctx = chat_service.build_context(db, h["id"])
            assert "Running" in ctx and "Morning runs" in ctx and "current streak" in ctx
            assert "Distance" in ctx
            general = chat_service.build_context(db, None)
            assert "Running" in general and "streak" in general
        finally:
            db.close()


def test_missing_key_returns_503(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", None)
    with TestClient(app) as c:
        r = c.post("/api/chat", json={"message": "hi"})
        assert r.status_code == 503 and "LLM_API_KEY" in r.json()["detail"]


def test_chat_with_mocked_llm(monkeypatch):
    captured = {}

    def fake(messages):
        captured["messages"] = messages
        return "Keep going!"

    monkeypatch.setattr(chat_service, "call_llm", fake)
    with TestClient(app) as c:
        h = _make_habit(c)
        history = [{"role": "user", "content": str(i)} for i in range(15)]
        r = c.post("/api/chat", json={"message": "hi", "habit_id": h["id"], "history": history})
        assert r.status_code == 200 and r.json() == {"reply": "Keep going!"}
        assert len(captured["messages"]) == 12  # system + 10 history + user
        assert c.post("/api/chat", json={"message": "hi", "habit_id": 99999}).status_code == 404
        assert c.post("/api/chat", json={"message": "x" * 2001}).status_code == 422
