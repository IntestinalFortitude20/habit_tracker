from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.chat import router as chat_router
from app.api.entries import router as entries_router
from app.api.goals import router as goals_router, types_router as goal_types_router
from app.api.habits import router as habits_router
from app.api.metrics import router as metrics_router
from app.api.stats import router as stats_router
from app.api.templates import router as templates_router
from app.core.config import settings
from sqlalchemy import inspect, text

from app.db.session import Base, engine

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    goal_columns = {column["name"] for column in inspect(engine).get_columns("goals")}
    additions = {
        "race_type": "VARCHAR(30)",
        "end_date": "DATE",
        "target_value": "FLOAT",
        "start_value": "FLOAT",
        "per_week": "INTEGER",
        "per_month": "INTEGER",
        "plan_source": "VARCHAR(20)",
    }
    for name, sql_type in additions.items():
        if name not in goal_columns:
            connection.execute(text(f"ALTER TABLE goals ADD COLUMN {name} {sql_type}"))

    workout_columns = {column["name"] for column in inspect(engine).get_columns("planned_workouts")}
    if "edited" not in workout_columns:
        connection.execute(text("ALTER TABLE planned_workouts ADD COLUMN edited BOOLEAN NOT NULL DEFAULT 0"))

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(habits_router)
app.include_router(metrics_router)
app.include_router(entries_router)
app.include_router(stats_router)
app.include_router(chat_router)
app.include_router(goal_types_router)
app.include_router(goals_router)
app.include_router(templates_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
