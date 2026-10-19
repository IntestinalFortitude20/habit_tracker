import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict

GoalType = Literal["5k", "10k", "half_marathon", "marathon"]
Level = Literal["beginner", "intermediate", "advanced"]
Unit = Literal["mi", "km"]


class GoalCreate(BaseModel):
    goal_type: GoalType
    target_date: dt.date
    experience_level: Level = "beginner"
    start_date: dt.date | None = None
    unit: Unit = "mi"
    metric_id: int | None = None


class GoalRegenerate(BaseModel):
    target_date: dt.date | None = None
    experience_level: Level | None = None


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    metric_id: int | None
    goal_type: str
    distance: float
    unit: str
    experience_level: str
    start_date: dt.date
    target_date: dt.date
    status: str


class GoalCreated(BaseModel):
    goal: GoalRead
    feasibility: "Feasibility"
    workouts_created: int


class Feasibility(BaseModel):
    feasible: bool
    message: str
    weeks_available: int
    min_weeks: int
    earliest_date: dt.date
    latest_date: dt.date
    base_weeks: int
    disclaimer: str


class WorkoutRead(BaseModel):
    date: dt.date
    workout_type: str
    target_distance: float | None
    target_duration_min: float | None
    phase: str | None
    notes: str | None
    status: str  # rest | completed | missed | today | upcoming
    entry_id: int | None = None
    actual_distance: float | None = None
    difference: float | None = None  # actual - target (negative = shortfall)
    percent_of_target: float | None = None


class WeekSummary(BaseModel):
    week_start: dt.date
    planned_distance: float
    completed_distance: float
    planned_workouts: int
    completed_workouts: int
    adherence: float | None


class GoalProgress(BaseModel):
    goal: GoalRead
    weeks_remaining: int
    days_remaining: int
    adherence: float | None
    on_track: bool
    status_label: str
    suggest_regenerate: bool
    current_week: WeekSummary
    weeks: list[WeekSummary]


GoalCreated.model_rebuild()
