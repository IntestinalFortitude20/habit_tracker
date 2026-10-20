from fastapi.testclient import TestClient

from app.main import app


def test_list_templates():
    with TestClient(app) as c:
        r = c.get("/api/templates")
        assert r.status_code == 200
        data = r.json()
        ids = {t["id"] for t in data}
        assert {"flossing", "exercise", "distance-running", "quit-smoking", "deep-work-coding"} <= ids
        assert len(ids) == len(data)
        smoking = next(t for t in data if t["id"] == "quit-smoking")
        assert "Not medical advice" in smoking["description"]
        for t in data:
            assert t["metrics"] and t["cue"] and t["tiny_version"]


def test_create_habit_from_template_values():
    with TestClient(app) as c:
        t = c.get("/api/templates").json()[0]
        h = c.post("/api/habits", json={"user_id": 1, "name": t["name"], "description": t["description"]}).json()
        for m in t["metrics"]:
            assert c.post(f"/api/habits/{h['id']}/metrics", json=m).status_code == 201
        assert len(c.get(f"/api/habits/{h['id']}/metrics").json()) == len(t["metrics"])
