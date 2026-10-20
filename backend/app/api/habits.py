from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Habit
from app.schemas.habit import HabitCreate, HabitRead

router = APIRouter(prefix="/api/habits", tags=["habits"])


def get_habit_or_404(db: Session, habit_id: int) -> Habit:
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(payload: HabitCreate, db: Session = Depends(get_db)):
    habit = Habit(**payload.model_dump())
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.get("", response_model=list[HabitRead])
def list_habits(db: Session = Depends(get_db)):
    return db.query(Habit).order_by(Habit.created_at.desc()).all()


@router.get("/{habit_id}", response_model=HabitRead)
def get_habit(habit_id: int, db: Session = Depends(get_db)):
    return get_habit_or_404(db, habit_id)


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = get_habit_or_404(db, habit_id)
    db.delete(habit)
    db.commit()
