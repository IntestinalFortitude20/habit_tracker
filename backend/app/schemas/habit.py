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
    name: str
    type: MetricType
    unit: str | None = None


class MetricCreate(MetricBase):
    habit_id: int


class MetricRead(MetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
