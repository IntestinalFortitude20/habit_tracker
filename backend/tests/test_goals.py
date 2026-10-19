import os

os.environ["DATABASE_URL"] = "sqlite:///./test_goals.db"

from datetime import date, timedelta  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.stats import compute_stats  # noqa: E402
from app.services.training import check_feasibility, generate_plan  # noqa: E402

T = date(2025, 1, 10)


def test_feasibility_rejects_and_suggests_earliest():
    r = check_feasibility("marathon", "beginner", T, T + timedelta(days=7))
    assert not r["feasible"] and r["earliest_date"] == T + timedelta(days=20 * 7 - 1)
    assert check_feasibility("marathon", "beginner", T, T + timedelta(days=52 * 7))["feasible"]


def test_plan_covers_every_day_and_ends_on_race():
    target = T + timedelta(days=40 * 7 + 3)
    plan = generate_plan("marathon", "beginner", T, target)
    assert [w["date"] for w in plan] == [T + timedelta(days=i) for i in range((target - T).days + 1)]
    assert plan[-1]["workout_type"] == "race" and plan[-1]["target_distance"] == 26.2
    assert plan[-2]["workout_type"] == "rest"
    assert max(w["target_distance"] or 0 for w in plan[:-1]) <= 20
    assert {w["phase"] for w in plan} >= {"base", "build", "taper", "recovery"}


def test_rest_days_do_not_break_streak():
    entries = [(T - timedelta(days=3), True), (T - timedelta(days=1), True), (T, True)]
    rest = [T - timedelta(days=2)]
    assert compute_stats(entries, today=T)["current_streak"] == 2
    s = compute_stats(entries, today=T, rest_days=rest)
    assert s["current_streak"] == 3 and s["longest_streak"] == 3


def test_goal_api_flow():
    with TestClient(app) as c:
        h = c.post("/api/habits", json={"user_id": 1, "name": "run"}).json()["id"]
        today = date.today()
        bad = c.post(f"/api/habits/{h}/goal", json={"goal_type": "marathon", "target_date": (today + timedelta(days=7)).isoformat()})
        assert bad.status_code == 422
        detail = bad.json()["detail"]
        assert detail["earliest_date"] == (today + timedelta(days=20 * 7 - 1)).isoformat()
        assert c.get(f"/api/habits/{h}/goal").status_code == 404

        target = today + timedelta(days=30 * 7)
        ok = c.post(f"/api/habits/{h}/goal", json={"goal_type": "marathon", "target_date": target.isoformat()})
        assert ok.status_code == 201
        assert ok.json()["workouts_created"] == (target - today).days + 1
        goal = ok.json()["goal"]
        assert goal["metric_id"]

        plan = c.get(f"/api/habits/{h}/goal/plan?start={today}&end={today + timedelta(days=13)}").json()
        assert len(plan) == 14
        run = next(w for w in plan if w["target_distance"])
        assert c.get(f"/api/goal-types").status_code == 200
        c.post(f"/api/habits/{h}/entries", json={
            "date": run["date"], "completed": True,
            "metric_values": [{"metric_id": goal["metric_id"], "value": run["target_distance"] / 2}]})
        after = c.get(f"/api/habits/{h}/goal/plan?start={run['date']}&end={run['date']}").json()[0]
        assert after["percent_of_target"] == 50.0 and after["difference"] < 0
        prog = c.get(f"/api/habits/{h}/goal/progress").json()
        assert prog["weeks_remaining"] == 30 and prog["on_track"]
        assert c.post(f"/api/habits/{h}/goal/regenerate", json={}).status_code == 200
        assert c.delete(f"/api/habits/{h}/goal").status_code == 204
        assert c.get(f"/api/habits/{h}/goal").status_code == 404
