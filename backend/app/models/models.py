from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="habits")
    metrics = relationship("Metric", back_populates="habit", cascade="all, delete-orphan")
    entries = relationship("Entry", back_populates="habit", cascade="all, delete-orphan")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # boolean | count | duration | rating
    unit = Column(String(50), nullable=True)

    habit = relationship("Habit", back_populates="metrics")
    values = relationship("MetricValue", back_populates="metric", cascade="all, delete-orphan")


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    completed = Column(Boolean, default=False, nullable=False)

    habit = relationship("Habit", back_populates="entries")
    metric_values = relationship("MetricValue", back_populates="entry", cascade="all, delete-orphan")


class MetricValue(Base):
    __tablename__ = "metric_values"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id"), nullable=False, index=True)
    value = Column(Float, nullable=False)

    entry = relationship("Entry", back_populates="metric_values")
    metric = relationship("Metric", back_populates="values")
