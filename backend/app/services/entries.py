from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Entry, Metric, MetricValue
from app.schemas.habit import MetricValueIn


def validate_metric_values(db: Session, habit_id: int, values: list[MetricValueIn]) -> None:
    ids = [v.metric_id for v in values]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Duplicate metric_id in metric_values")
    if not ids:
        return
    found = {
        m.id for m in db.query(Metric.id).filter(Metric.habit_id == habit_id, Metric.id.in_(ids)).all()
    }
    missing = set(ids) - found
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Metric(s) {sorted(missing)} do not belong to habit {habit_id}",
        )


def replace_metric_values(entry: Entry, values: list[MetricValueIn]) -> None:
    entry.metric_values.clear()
    for v in values:
        entry.metric_values.append(MetricValue(metric_id=v.metric_id, value=v.value))
