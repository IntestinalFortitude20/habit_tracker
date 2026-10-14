from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.habits import router as habits_router
from app.core.config import settings
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(habits_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
