import os
import json

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
        assert c.post(f"/api/habits/{h}/goal/regenerate", json={}).status_code == 409
        assert c.post(f"/api/habits/{h}/goal/regenerate", json={"confirm": True}).status_code == 200
        assert c.delete(f"/api/habits/{h}/goal").status_code == 204
        assert c.get(f"/api/habits/{h}/goal").status_code == 404


def test_frequency_and_metric_goal_progress_and_plan_edits():
    with TestClient(app) as c:
        habit_id = c.post("/api/habits", json={"user_id": 1, "name": "strength"}).json()["id"]
        frequency = c.post(f"/api/habits/{habit_id}/goal", json={
            "goal_type": "frequency", "per_week": 4, "per_month": 15,
        })
        assert frequency.status_code == 201
        assert frequency.json()["goal"]["end_date"] is None
        for offset in (0, 1):
            c.post(f"/api/habits/{habit_id}/entries", json={
                "date": (date.today() - timedelta(days=offset)).isoformat(), "completed": True,
            })
        progress = c.get(f"/api/habits/{habit_id}/goal/progress").json()
        assert progress["week_completed"] == 2
        assert progress["week_target"] == 4
        assert progress["month_completed"] == 2
        assert progress["month_target"] == 15

        metric_id = c.post(f"/api/habits/{habit_id}/metrics", json={
            "name": "Reps", "type": "count", "unit": "reps",
        }).json()["id"]
        c.delete(f"/api/habits/{habit_id}/goal")
        target = date.today() + timedelta(days=4)
        created = c.post(f"/api/habits/{habit_id}/goal", json={
            "goal_type": "metric_target",
            "metric_id": metric_id,
            "target_value": 40,
            "start_value": 10,
            "target_date": target.isoformat(),
            "plan_source": "linear",
        })
        assert created.status_code == 201
        today = date.today().isoformat()
        plan = c.get(f"/api/habits/{habit_id}/goal/plan?start={today}&end={today}").json()
        assert plan[0]["target_value"] == 10
        changed = c.put(f"/api/habits/{habit_id}/goal/plan/{today}", json={
            "target_value": 12, "workout_type": "deload",
        })
        assert changed.status_code == 200
        assert changed.json()["target_value"] == 12
        assert changed.json()["workout_type"] == "deload"
        assert c.get(f"/api/habits/{habit_id}/goal/progress").json()["goal"]["plan_source"] == "linear"


def test_goal_validation_rejects_invalid_metric_and_missing_frequency_target():
    with TestClient(app) as c:
        habit_id = c.post("/api/habits", json={"user_id": 1, "name": "habit"}).json()["id"]
        other_habit_id = c.post("/api/habits", json={"user_id": 1, "name": "other"}).json()["id"]
        metric_id = c.post(f"/api/habits/{other_habit_id}/metrics", json={
            "name": "Reps", "type": "count", "unit": "reps",
        }).json()["id"]
        missing_frequency = c.post(f"/api/habits/{habit_id}/goal", json={"goal_type": "frequency"})
        assert missing_frequency.status_code == 422
        invalid_metric = c.post(f"/api/habits/{habit_id}/goal", json={
            "goal_type": "metric_target", "metric_id": metric_id, "target_value": 20,
            "target_date": (date.today() + timedelta(days=10)).isoformat(), "plan_source": "linear",
        })
        assert invalid_metric.status_code == 422


def test_ai_plan_is_draft_until_accepted(monkeypatch):
    from app.services import chat

    with TestClient(app) as c:
        habit_id = c.post("/api/habits", json={"user_id": 1, "name": "lifting"}).json()["id"]
        metric_id = c.post(f"/api/habits/{habit_id}/metrics", json={
            "name": "Reps", "type": "count", "unit": "reps",
        }).json()["id"]
        start = date.today()
        end = start + timedelta(days=2)
        days = [
            {"date": (start + timedelta(days=offset)).isoformat(), "target_value": 10 + offset * 5,
             "workout_type": "target", "notes": None}
            for offset in range(3)
        ]
        monkeypatch.setattr(chat, "call_llm", lambda messages: json.dumps({"days": days}))
        payload = {
            "goal_type": "metric_target", "metric_id": metric_id, "target_value": 20,
            "target_date": end.isoformat(), "plan_source": "ai",
        }
        draft = c.post(f"/api/habits/{habit_id}/goal/draft", json=payload)
        assert draft.status_code == 200
        assert len(draft.json()["plan"]) == 3
        assert c.get(f"/api/habits/{habit_id}/goal").status_code == 404
        accepted = c.post(f"/api/habits/{habit_id}/goal/accept", json={
            "goal": payload, "plan": draft.json()["plan"],
        })
        assert accepted.status_code == 201
        assert accepted.json()["goal"]["plan_source"] == "ai"


def _running_goal(c, name):
    h = c.post("/api/habits", json={"user_id": 1, "name": name}).json()["id"]
    today = date.today()
    target = today + timedelta(days=30 * 7)
    r = c.post(f"/api/habits/{h}/goal", json={"goal_type": "marathon", "target_date": target.isoformat()})
    assert r.status_code == 201
    return h, r.json()["goal"], today


def _plan_day(c, h, day):
    return c.get(f"/api/habits/{h}/goal/plan?start={day}&end={day}").json()[0]


def test_convert_to_rest_and_back_marks_edited_and_keeps_streak():
    with TestClient(app) as c:
        h, goal, today = _running_goal(c, "rest-convert")
        run = next(w for w in c.get(f"/api/habits/{h}/goal/plan?start={today + timedelta(days=1)}&end={today + timedelta(days=14)}").json() if w["target_distance"])
        day = run["date"]
        assert run["edited"] is False
        edit = c.put(f"/api/habits/{h}/goal/plan/{day}", json={"target_distance": 3.5}).json()
        assert edit["target_distance"] == 3.5 and edit["edited"] is True
        rest = c.put(f"/api/habits/{h}/goal/plan/{day}", json={"workout_type": "rest", "notes": "sore knee"}).json()
        assert rest["status"] == "rest" and rest["notes"] == "sore knee" and rest["target_distance"] is None
        d = date.fromisoformat(day)
        from app.db.session import SessionLocal
        from app.services.goals import rest_dates
        with SessionLocal() as db:
            assert d in rest_dates(db, h)
        back = c.put(f"/api/habits/{h}/goal/plan/{day}", json={"workout_type": "workout"}).json()
        assert back["status"] != "rest" and back["target_distance"] == run["target_distance"]
        default_note = c.put(f"/api/habits/{h}/goal/plan/{day}", json={"workout_type": "rest"}).json()
        assert default_note["notes"] == "Rest day (changed by you)"


def test_past_day_converted_to_rest_keeps_streak_and_entry():
    with TestClient(app) as c:
        h = c.post("/api/habits", json={"user_id": 1, "name": "past-edit"}).json()["id"]
        today = date.today()
        r = c.post(f"/api/habits/{h}/goal", json={
            "goal_type": "marathon", "start_date": (today - timedelta(days=10)).isoformat(),
            "target_date": (today + timedelta(days=30 * 7)).isoformat()})
        assert r.status_code == 201
        past = [w for w in c.get(f"/api/habits/{h}/goal/plan?start={today - timedelta(days=6)}&end={today - timedelta(days=1)}").json()
                if w["workout_type"] != "rest"]
        day = past[0]["date"]
        d = date.fromisoformat(day)
        for offset in (d - timedelta(days=1), d + timedelta(days=1)):
            c.post(f"/api/habits/{h}/entries", json={"date": offset.isoformat(), "completed": True})
        c.post(f"/api/habits/{h}/entries", json={"date": day, "completed": True})
        denied = c.put(f"/api/habits/{h}/goal/plan/{day}", json={"workout_type": "rest"})
        assert denied.status_code == 409 and denied.json()["detail"]["requires_confirmation"]
        ok = c.put(f"/api/habits/{h}/goal/plan/{day}", json={"workout_type": "rest", "confirm": True}).json()
        assert ok["status"] == "rest" and ok["entry_id"] is not None and ok["edited"]
        stats = c.get(f"/api/habits/{h}/stats").json()
        assert stats["longest_streak"] >= 3


def test_past_day_edit_requires_confirmation_service():
    from app.db.session import SessionLocal
    from app.services import goals as svc
    import pytest
    from fastapi import HTTPException

    with TestClient(app) as c:
        h, goal, today = _running_goal(c, "past-svc")
        db = SessionLocal()
        try:
            g = svc.get_active_goal(db, h)
            later = today + timedelta(days=10)
            run = next(w for w in svc.list_workouts(db, g, today + timedelta(days=1), later) if w["status"] != "rest")
            future_today = date.fromisoformat(run["date"].isoformat()) + timedelta(days=3)
            with pytest.raises(HTTPException) as exc:
                svc.update_plan_day(db, g, run["date"], {"workout_type": "rest"}, today=future_today)
            assert exc.value.status_code == 409
            out = svc.update_plan_day(db, g, run["date"], {"workout_type": "rest", "confirm": True}, today=future_today)
            assert out["status"] == "rest" and out["edited"]
        finally:
            db.close()


def test_regenerate_preserve_edits_on_and_off():
    with TestClient(app) as c:
        h, goal, today = _running_goal(c, "regen")
        run = next(w for w in c.get(f"/api/habits/{h}/goal/plan?start={today + timedelta(days=1)}&end={today + timedelta(days=14)}").json() if w["target_distance"])
        day = run["date"]
        c.put(f"/api/habits/{h}/goal/plan/{day}", json={"target_distance": 9.5})
        total = len(c.get(f"/api/habits/{h}/goal/plan").json())
        kept = c.post(f"/api/habits/{h}/goal/regenerate", json={"confirm": True, "preserve_edits": True})
        assert kept.status_code == 200
        after = _plan_day(c, h, day)
        assert after["target_distance"] == 9.5 and after["edited"] is True
        assert len(c.get(f"/api/habits/{h}/goal/plan").json()) == total
        c.post(f"/api/habits/{h}/goal/regenerate", json={"confirm": True, "preserve_edits": False})
        reset = _plan_day(c, h, day)
        assert reset["target_distance"] == run["target_distance"] and reset["edited"] is False
        assert len(c.get(f"/api/habits/{h}/goal/plan").json()) == total
