# Habit Tracker

A modern habit tracker app built with **FastAPI + React + TypeScript**.

The app supports flexible habit metrics (streaks, counts, duration, ratings), visual progress tracking, and planned AI/ML features for coaching and predictions.

## 🚀 Goals

- Track daily habits and goals
- Support custom metrics per habit
- Show streaks and trend charts
- Add AI chat assistance (via LLM API)
- Add ML-based risk prediction (e.g., missed-day likelihood)

## 🧱 Tech Stack

- **Frontend:** React + TypeScript + Vite
- **Backend:** FastAPI + SQLAlchemy + Pydantic
- **Database:** SQLite (dev), PostgreSQL (prod)
- **Visualization:** (planned) chart + heatmap components
- **AI:** (planned) LLM integration through backend endpoint
- **ML:** (planned) scikit-learn predictive model

## 📁 Project Structure

```text
habit_tracker/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ db/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  └─ main.py
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ components/
│  │  ├─ pages/
│  │  ├─ hooks/
│  │  ├─ types/
│  │  └─ App.tsx
│  └─ package.json
└─ README.md
```

## 🧩 Data Model (MVP)

- **User**: account owner
- **Habit**: top-level habit or goal
- **Metric**: flexible metric definition per habit
- **Entry**: daily log record for habit
- **MetricValue**: metric values attached to an entry

### Entities

- `User(id, email, hashed_password, created_at)`
- `Habit(id, user_id, name, description, created_at, archived)`
- `Metric(id, habit_id, name, type, unit)`
  - `type`: `boolean | count | duration | rating`
- `Entry(id, habit_id, date, completed)`
- `MetricValue(id, entry_id, metric_id, value)`

> **Design note:** streaks are computed from `Entry.date` + `completed`, not stored.

## 🖥️ Local Development

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs on `http://127.0.0.1:8000` (desktop) and `http://<your-lan-ip>:8000` (LAN devices)

### 2) Frontend

```bash
cd frontend
npm install
npm run dev -- --host
```

Frontend runs on `http://localhost:5173` (desktop) and `http://<your-lan-ip>:5173` (LAN devices)

### 3) LAN Test Checklist

- Ensure phone + computer are on the same Wi-Fi network
- Open backend health from phone: `http://<your-lan-ip>:8000/health`
- Open frontend from phone: `http://<your-lan-ip>:5173`
- If unreachable, allow inbound firewall access to ports `8000` and `5173`

## ✅ Current MVP Endpoints

- `GET /health`
- `POST /api/habits`
- `GET /api/habits`

## ✅ Phase 1 Features

- Metrics per habit (`boolean`, `count`, `duration`, `rating`, optional unit): add, edit, delete
- Daily entry logging with completed flag + per-metric values
- Stats: current streak, longest streak, 7d/30d completion rates

### API summary

| Method | Path | Notes |
| --- | --- | --- |
| POST/GET | `/api/habits/{id}/metrics` | create / list |
| GET/PUT/DELETE | `/api/habits/{id}/metrics/{metric_id}` | |
| POST/GET | `/api/habits/{id}/entries` | POST **upserts** by date; GET supports `order=asc\|desc`, `limit` |
| GET/PUT/DELETE | `/api/habits/{id}/entries/{entry_id}` | |
| GET | `/api/habits/{id}/stats` | streaks, rates, totals |

Metric values must reference metrics of the same habit (422 otherwise); unknown habit/metric/entry returns 404.
Current streak = consecutive completed days ending today, or ending yesterday if today isn't completed yet.
Rates = completed days in the trailing 7/30 days (incl. today) divided by 7/30. No DB migration is needed (existing tables are used).

### Using the screens

- `/habits`: create habits; click one to open it (shows its current streak).
- `/habits/:habitId`: view stats, manage metrics, log an entry for a date (inputs are generated from the metrics), and review/delete recent entries. Works from phone via the LAN setup above.

### Tests

```bash
cd backend && pip install -r requirements.txt -r requirements-dev.txt && python -m pytest
```

## 🛣️ Roadmap

### Phase 1: Core Tracking
- [x] Scaffold backend + frontend
- [x] Add CRUD for habits (create/list/get)
- [x] Add metrics per habit
- [x] Add daily entries + metric values
- [x] Compute current + longest streak

### Phase 2: Visualization
- [x] Habit list with streak summary
- [x] Habit detail page
- [ ] Contribution-style heatmap
- [ ] Metric trend charts

### Phase 3: AI Assistant
- [ ] `POST /api/chat` endpoint
- [ ] Context injection (habit summaries)
- [ ] Tool-calling for logging/update actions

### Phase 4: ML Features
- [ ] Feature engineering pipeline
- [ ] Missed-day risk classifier
- [ ] Weekly trend forecasting
- [ ] Surface predictions in UI + AI prompts

## 📌 Resume Framing

Emphasize:
- Full-stack architecture (FastAPI + React + TS)
- Flexible schema design for extensible metrics
- Production-aware API design and deployment path
- AI feature integration (LLM + tool use)
- Practical ML component with measurable user value

## 📄 License

MIT
