import datetime as dt
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MetricType = Literal["boolean", "count", "duration", "rating"]


class HabitBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    archived: bool = False


class HabitCreate(HabitBase):
    user_id: int


class HabitRead(HabitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime


class MetricBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: MetricType
    unit: str | None = Field(default=None, max_length=50)


class MetricCreate(MetricBase):
    pass


class MetricUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: MetricType | None = None
    unit: str | None = Field(default=None, max_length=50)


class MetricRead(MetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int


class MetricValueIn(BaseModel):
    metric_id: int
    value: float


class MetricValueRead(MetricValueIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class EntryCreate(BaseModel):
    date: dt.date
    completed: bool = False
    metric_values: list[MetricValueIn] = []


class EntryUpdate(BaseModel):
    date: dt.date | None = None
    completed: bool | None = None
    metric_values: list[MetricValueIn] | None = None


class EntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    date: dt.date
    completed: bool
    metric_values: list[MetricValueRead] = []


class HabitStats(BaseModel):
    current_streak: int
    longest_streak: int
    completion_rate_7d: float
    completion_rate_30d: float
    total_completed_days: int
    total_logged_days: int
