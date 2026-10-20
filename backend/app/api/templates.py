import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from app.schemas.habit import HabitTemplate

router = APIRouter(prefix="/api/templates", tags=["templates"])

TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "data" / "habit_templates.json"


@lru_cache(maxsize=1)
def load_templates() -> list[HabitTemplate]:
    with TEMPLATES_PATH.open(encoding="utf-8") as f:
        return [HabitTemplate(**t) for t in json.load(f)]


@router.get("", response_model=list[HabitTemplate])
def list_templates():
    return load_templates()
