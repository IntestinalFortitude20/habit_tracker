from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.entries import router as entries_router
from app.api.goals import router as goals_router, types_router as goal_types_router
from app.api.habits import router as habits_router
from app.api.metrics import router as metrics_router
from app.api.stats import router as stats_router
from app.core.config import settings
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

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


@app.get("/health")
def health_check():
    return {"status": "ok"}
