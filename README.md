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

### Prerequisites

- Python 3.10+
- Node.js 18+ (with npm)
- [Ollama](https://ollama.com/download) (for the local AI coach)

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env       # Windows: copy .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs on `http://127.0.0.1:8000` (desktop) and `http://<your-lan-ip>:8000` (LAN devices).
The `.env` file must live in `backend/` and is read at startup (restart after editing). It is git-ignored; never commit it.

### 2) Frontend

```bash
cd frontend
npm install
npm run dev -- --host
```

Frontend runs on `http://localhost:5173` (desktop) and `http://<your-lan-ip>:5173` (LAN devices)

### 3) AI chat setup (Ollama)

The AI coach calls an OpenAI-compatible chat completions API **from the backend only**; keys are never sent to the browser.

1. Install Ollama from https://ollama.com/download.
2. Pull the model: `ollama pull llama3.2:3b`
3. Confirm it is installed: `ollama list`
4. Verify Ollama is running: open `http://127.0.0.1:11434` (should say "Ollama is running"), or `curl http://127.0.0.1:11434`. If not, run `ollama serve`.
5. Make sure `backend/.env` (copied from `backend/.env.example`) contains:
   ```env
   LLM_API_KEY=ollama
   LLM_BASE_URL=http://127.0.0.1:11434/v1
   LLM_MODEL=llama3.2:3b
   ```
   `LLM_API_KEY` is only a placeholder for local Ollama (it is not checked, but must be non-empty). To use OpenAI or another provider, set a real key, its `LLM_BASE_URL` and `LLM_MODEL`.
6. Restart the backend.

Without a key, `POST /api/chat` returns `503` with a setup hint. Upstream errors map to `502`, timeouts to `504`.

Using the chat: tap the floating **chat bubble button** (bottom-right, "Open AI coach chat") on a habit page (scoped to that habit's metrics, stats and last 30 days of entries) or on the home page (general chat across all habits). Enter sends, Shift+Enter adds a newline; history lives only in the open panel.

**Mobile modals:** modals no longer autofocus inputs (so the keyboard only opens when you tap a field), sit toward the top on small screens, resize with the visual viewport, and scroll the focused field into view.

### Restart checklist

1. Start Ollama (`ollama serve`, or the desktop app) and check `http://127.0.0.1:11434`.
2. Start the backend: `cd backend && source .venv/bin/activate && python -m uvicorn app.main:app --reload --port 8000`
3. Start the frontend: `cd frontend && npm run dev`
4. Health checks: `http://127.0.0.1:8000/health` returns OK, `ollama list` shows `llama3.2:3b`.
5. Open `http://localhost:5173`, click the chat bubble and send a message to test the AI coach.

### Troubleshooting

- **Ollama not running / connection refused (502):** start it with `ollama serve` and check `http://127.0.0.1:11434`.
- **503 setup hint:** `LLM_API_KEY` is empty or `.env` is in the wrong place. It must be `backend/.env`, not the repo root or `frontend/`.
- **Changed `.env` but nothing changed:** restart the backend; settings are read at startup.
- **404 / upstream errors from the model:** `LLM_BASE_URL` must end in `/v1` (`http://127.0.0.1:11434/v1`). Also check `LLM_MODEL` matches `ollama list`.
- **Slow first reply:** the model loads on first use; see [docs/performance.md](docs/performance.md) (once available) for performance notes.

### 4) LAN Test Checklist

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
| POST/GET | `/api/habits/{id}/entries` | POST **upserts** by date; GET supports `order=asc\|desc`, `limit`, `start`, `end` (inclusive `YYYY-MM-DD` date range) |
| GET/PUT/DELETE | `/api/habits/{id}/entries/{entry_id}` | |
| GET | `/api/habits/{id}/stats` | streaks, rates, totals |

Metric values must reference metrics of the same habit (422 otherwise); unknown habit/metric/entry returns 404.
Current streak = consecutive completed days ending today, or ending yesterday if today isn't completed yet.
Rates = completed days in the trailing 7/30 days (incl. today) divided by 7/30. No DB migration is needed (existing tables are used).

### Using the screens

- `/habits`: habits are shown as a responsive grid of cards (title, description, current streak); click a card to open it. A floating "+" button (bottom-right) opens a modal to create a habit (name required, description optional). Empty state points to the button. Shared styling lives in `frontend/src/styles.css` (design tokens) with reusable `Button`, `Card`, `Fab` and `Modal` components; modals close via ESC, backdrop or the close button.
- `/habits/:habitId`: calendar-first habit page showing streak/stat cards (current, longest, 7d/30d rates) and the date view, with two actions: **Log entry** and **⚙ Settings**. Works from phone via the LAN setup above.
  - **Calendar** (default): month grid, navigable with ‹ ›. Click a day to see its completed status and metric values; **Edit entry** opens the Log entry modal prefilled for that date.
  - **Settings modal**: list, add (name, type, unit), edit (name, unit) and delete metrics.
  - **Log entry modal**: date picker (defaults to today), completed toggle and one input per metric. Picking a date that already has an entry prefills it and saving updates it. Stats and date views refresh after saving; success/error messages are shown in the modal.
  - **Heatmap**: a "Show heatmap" toggle appears only once the habit has at least one entry. It always covers 30 days inclusive, ending at the latest entry date (`start = end - 29 days`); days without entries (including days before the first entry) are neutral gray. Contribution days use 3 green intensity levels, based on the first `count` metric if one exists, otherwise on the completed flag. Clicking a day opens the same day details/edit flow.

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
- [x] `POST /api/chat` endpoint
- [x] Context injection (habit summaries)
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
