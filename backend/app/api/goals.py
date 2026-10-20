from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.habits import get_habit_or_404
from app.db.session import get_db
from app.models.models import Goal
from app.schemas.goal import (
    Feasibility,
    GoalCreate,
    GoalCreated,
    GoalProgress,
    GoalRead,
    GoalRegenerate,
    GoalType,
    Level,
    WorkoutRead,
)
from app.services import goals as goal_service
from app.services import training

types_router = APIRouter(prefix="/api/goal-types", tags=["goals"])
router = APIRouter(prefix="/api/habits/{habit_id}/goal", tags=["goals"])


@types_router.get("")
def list_goal_types():
    data = training.goal_types()
    return {
        "goal_types": [
            {
                "id": k,
                "label": v["label"],
                "distance_miles": v["distance_miles"],
                "min_weeks": {lvl: p["min_weeks"] for lvl, p in v["levels"].items()},
            }
            for k, v in data.items()
        ],
        "disclaimer": training.DISCLAIMER,
    }


def active_goal_or_404(db: Session, habit_id: int) -> Goal:
    get_habit_or_404(db, habit_id)
    goal = goal_service.get_active_goal(db, habit_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="No active goal for this habit")
    return goal


@router.get("/feasibility", response_model=Feasibility)
def check_feasibility(
    habit_id: int,
    goal_type: GoalType,
    target_date: date,
    experience_level: Level = "beginner",
    start_date: date | None = None,
    db: Session = Depends(get_db),
):
    get_habit_or_404(db, habit_id)
    start = start_date or date.today()
    if target_date <= start:
        raise HTTPException(status_code=422, detail={"message": "Target date must be after the start date."})
    return training.check_feasibility(goal_type, experience_level, start, target_date)


@router.post("", response_model=GoalCreated, status_code=status.HTTP_201_CREATED)
def create_goal(habit_id: int, payload: GoalCreate, db: Session = Depends(get_db)):
    habit = get_habit_or_404(db, habit_id)
    goal, feas, count = goal_service.create_goal(db, habit, payload)
    return {"goal": goal, "feasibility": feas, "workouts_created": count}


@router.get("", response_model=GoalRead)
def get_goal(habit_id: int, db: Session = Depends(get_db)):
    return active_goal_or_404(db, habit_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def cancel_goal(habit_id: int, db: Session = Depends(get_db)):
    goal = active_goal_or_404(db, habit_id)
    goal.status = "cancelled"
    db.commit()


@router.get("/plan", response_model=list[WorkoutRead])
def get_plan(habit_id: int, start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
    goal = active_goal_or_404(db, habit_id)
    return goal_service.list_workouts(db, goal, start, end)


@router.get("/progress", response_model=GoalProgress)
def get_progress(habit_id: int, db: Session = Depends(get_db)):
    goal = active_goal_or_404(db, habit_id)
    return goal_service.compute_progress(db, goal)


@router.post("/regenerate", response_model=GoalCreated)
def regenerate(habit_id: int, payload: GoalRegenerate | None = None, db: Session = Depends(get_db)):
    goal = active_goal_or_404(db, habit_id)
    payload = payload or GoalRegenerate()
    feas, count = goal_service.regenerate_plan(db, goal, payload.target_date, payload.experience_level)
    db.refresh(goal)
    return {"goal": goal, "feasibility": feas, "workouts_created": count}
