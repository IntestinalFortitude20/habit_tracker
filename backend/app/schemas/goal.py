import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GoalType = Literal["5k", "10k", "half_marathon", "marathon", "running_plan", "frequency", "metric_target"]
Level = Literal["beginner", "intermediate", "advanced"]
Unit = Literal["mi", "km"]


class GoalCreate(BaseModel):
    goal_type: GoalType
    target_date: dt.date | None = None
    experience_level: Level = "beginner"
    start_date: dt.date | None = None
    unit: Unit = "mi"
    metric_id: int | None = None
    race_type: Literal["5k", "10k", "half_marathon", "marathon"] | None = None
    target_value: float | None = Field(default=None, gt=0)
    start_value: float | None = Field(default=None, ge=0)
    per_week: int | None = Field(default=None, gt=0, le=31)
    per_month: int | None = Field(default=None, gt=0, le=31)
    plan_source: Literal["linear", "ai", "manual"] | None = None


class GoalRegenerate(BaseModel):
    target_date: dt.date | None = None
    experience_level: Level | None = None


class PlanDay(BaseModel):
    date: dt.date
    target_value: float | None = Field(default=None, ge=0)
    workout_type: Literal["target", "rest", "deload"] = "target"
    notes: str | None = None


class GoalAccept(BaseModel):
    goal: GoalCreate
    plan: list[PlanDay] = []


class PlanDayUpdate(BaseModel):
    target_value: float | None = Field(default=None, ge=0)
    workout_type: Literal["target", "rest", "deload"] | None = None
    notes: str | None = None


class PlanAdjustment(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    metric_id: int | None
    goal_type: str
    race_type: str | None = None
    distance: float
    unit: str
    experience_level: str
    start_date: dt.date
    target_date: dt.date
    end_date: dt.date | None = None
    target_value: float | None = None
    start_value: float | None = None
    per_week: int | None = None
    per_month: int | None = None
    plan_source: str | None = None
    status: str


class GoalCreated(BaseModel):
    goal: GoalRead
    feasibility: "Feasibility | None" = None
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
    target_value: float | None = None
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
    current_week: WeekSummary | None = None
    weeks: list[WeekSummary] = []
    week_completed: int | None = None
    week_target: int | None = None
    month_completed: int | None = None
    month_target: int | None = None
    metric_progress: float | None = None


GoalCreated.model_rebuild()
