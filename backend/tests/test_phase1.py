from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.services.stats import compute_stats

T = date(2025, 1, 10)


def d(n):
    return T - timedelta(days=n)


def test_streak_ending_today():
    s = compute_stats([(d(0), True), (d(1), True), (d(3), True)], today=T)
    assert s["current_streak"] == 2 and s["longest_streak"] == 2


def test_streak_ongoing_from_yesterday():
    assert compute_stats([(d(1), True), (d(2), True)], today=T)["current_streak"] == 2


def test_streak_broken_and_longest():
    s = compute_stats([(d(2), True), (d(5), True), (d(6), True), (d(7), True), (d(4), False)], today=T)
    assert s["current_streak"] == 0 and s["longest_streak"] == 3
    assert s["total_logged_days"] == 5 and s["total_completed_days"] == 4


def test_rates():
    s = compute_stats([(d(i), True) for i in range(7)], today=T)
    assert s["completion_rate_7d"] == 1.0 and s["completion_rate_30d"] == round(7 / 30, 4)


def test_api_flow():
    with TestClient(app) as c:
        h = c.post("/api/habits", json={"user_id": 1, "name": "x"}).json()["id"]
        h2 = c.post("/api/habits", json={"user_id": 1, "name": "y"}).json()["id"]
        m = c.post(f"/api/habits/{h}/metrics", json={"name": "reps", "type": "count"}).json()["id"]
        m2 = c.post(f"/api/habits/{h2}/metrics", json={"name": "r", "type": "count"}).json()["id"]
        assert c.get(f"/api/habits/{h2}/metrics/{m}").status_code == 404
        assert c.post(f"/api/habits/999/metrics", json={"name": "r", "type": "count"}).status_code == 404
        today = date.today().isoformat()
        bad = c.post(f"/api/habits/{h}/entries", json={"date": today, "completed": True,
                     "metric_values": [{"metric_id": m2, "value": 1}]})
        assert bad.status_code == 422
        ok = c.post(f"/api/habits/{h}/entries", json={"date": today, "completed": True,
                    "metric_values": [{"metric_id": m, "value": 50}]})
        assert ok.status_code == 201
        again = c.post(f"/api/habits/{h}/entries", json={"date": today, "completed": True,
                       "metric_values": [{"metric_id": m, "value": 60}]}).json()
        assert again["id"] == ok.json()["id"] and again["metric_values"][0]["value"] == 60
        assert len(c.get(f"/api/habits/{h}/entries?limit=5").json()) == 1
        assert c.get(f"/api/habits/{h}/stats").json()["current_streak"] == 1
        assert c.delete(f"/api/habits/{h}/metrics/{m}").status_code == 204
        assert c.delete(f"/api/habits/{h}/entries/{ok.json()['id']}").status_code == 204


def test_entries_date_range():
    with TestClient(app) as c:
        h = c.post("/api/habits", json={"user_id": 1, "name": "range"}).json()["id"]
        for d in ("2024-01-01", "2024-01-15", "2024-02-01"):
            c.post(f"/api/habits/{h}/entries", json={"date": d, "completed": True, "metric_values": []})
        r = c.get(f"/api/habits/{h}/entries?start=2024-01-01&end=2024-01-31&order=asc").json()
        assert [e["date"] for e in r] == ["2024-01-01", "2024-01-15"]
        assert len(c.get(f"/api/habits/{h}/entries?start=2024-01-10").json()) == 2


def test_delete_habit_removes_related_rows():
    from app.db.session import SessionLocal
    from app.models.models import Entry, Habit, Metric, MetricValue

    with TestClient(app) as c:
        h = c.post("/api/habits", json={"user_id": 1, "name": "Del"}).json()
        m = c.post(f"/api/habits/{h['id']}/metrics", json={"name": "Reps", "type": "count"}).json()
        c.post(f"/api/habits/{h['id']}/entries", json={"date": "2025-01-01", "completed": True, "metric_values": [{"metric_id": m["id"], "value": 3}]})
        assert c.delete(f"/api/habits/{h['id']}").status_code == 204
        assert c.get(f"/api/habits/{h['id']}").status_code == 404
        db = SessionLocal()
        try:
            assert db.query(Metric).filter(Metric.habit_id == h["id"]).count() == 0
            assert db.query(Entry).filter(Entry.habit_id == h["id"]).count() == 0
            assert db.query(MetricValue).filter(MetricValue.metric_id == m["id"]).count() == 0
            assert db.query(Habit).filter(Habit.id == h["id"]).count() == 0
        finally:
            db.close()


def test_delete_unknown_habit_404():
    with TestClient(app) as c:
        assert c.delete("/api/habits/999999").status_code == 404
