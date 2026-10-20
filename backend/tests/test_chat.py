import json
import logging
import re

from datetime import date

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.services import chat as chat_service


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


def test_call_llm_logs_model_and_duration(monkeypatch, caplog):
    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "hello"}}]}

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "test-model")
    monkeypatch.setattr(chat_service.httpx, "post", lambda *args, **kwargs: Response())
    with caplog.at_level(logging.INFO, logger=chat_service.__name__):
        assert chat_service.call_llm([]) == "hello"

    assert re.search(r"model=test-model duration_seconds=\d+\.\d{3}", caplog.text)


def _fake_stream(monkeypatch, lines, status=200):
    class Resp:
        status_code = status

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def iter_lines(self):
            return iter(lines)

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(chat_service.httpx, "stream", lambda *a, **k: Resp())


def _chunk(text):
    return "data: " + json.dumps({"choices": [{"delta": {"content": text}}]})


def test_stream_llm_parses_sse(monkeypatch):
    _fake_stream(monkeypatch, [
        'data: {"choices":[{"delta":{"role":"assistant"}}]}', "", _chunk("Keep "), "", _chunk("going!"), "", "data: [DONE]",
    ])
    assert "".join(chat_service.stream_llm([])) == "Keep going!"


def test_stream_endpoint_events(monkeypatch):
    monkeypatch.setattr(chat_service, "stream_llm", lambda m: (t for t in ["Keep ", "going!"]))
    with TestClient(app) as c:
        r = c.post("/api/chat/stream", json={"message": "hi"})
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        tokens = [json.loads(l[6:])["token"] for l in r.text.splitlines() if l.startswith("data: {\"token")]
        assert "".join(tokens) == "Keep going!" and "event: done" in r.text


def test_stream_endpoint_errors(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", None)
    with TestClient(app) as c:
        assert c.post("/api/chat/stream", json={"message": "hi"}).status_code == 503

    def broken(messages):
        yield "partial"
        raise chat_service.LLMError(502, "boom")

    monkeypatch.setattr(chat_service, "stream_llm", broken)
    with TestClient(app) as c:
        r = c.post("/api/chat/stream", json={"message": "hi"})
        assert r.status_code == 200 and "event: error" in r.text and "boom" in r.text
