from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.habits import get_habit_or_404
from app.db.session import get_db
from app.models.models import Entry
from app.schemas.habit import HabitStats
from app.services.stats import compute_stats

router = APIRouter(prefix="/api/habits/{habit_id}/stats", tags=["stats"])


@router.get("", response_model=HabitStats)
def get_stats(habit_id: int, db: Session = Depends(get_db)):
    get_habit_or_404(db, habit_id)
    rows = db.query(Entry.date, Entry.completed).filter(Entry.habit_id == habit_id).all()
    return compute_stats([(r.date, r.completed) for r in rows])
