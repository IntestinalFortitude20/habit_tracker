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
# .venv\\Scripts\\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs on `http://127.0.0.1:8000`

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`

## ✅ Current MVP Endpoints

- `GET /health`
- `POST /api/habits`
- `GET /api/habits`

## 🛣️ Roadmap

### Phase 1: Core Tracking
- [x] Scaffold backend + frontend
- [ ] Add CRUD for habits
- [ ] Add metrics per habit
- [ ] Add daily entries + metric values
- [ ] Compute current + longest streak

### Phase 2: Visualization
- [ ] Habit list with streak cards
- [ ] Habit detail page
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
