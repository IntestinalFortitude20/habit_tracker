from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.habits import get_habit_or_404
from app.db.session import get_db
from app.models.models import Metric
from app.schemas.habit import MetricCreate, MetricRead, MetricUpdate

router = APIRouter(prefix="/api/habits/{habit_id}/metrics", tags=["metrics"])


def get_metric_or_404(db: Session, habit_id: int, metric_id: int) -> Metric:
    get_habit_or_404(db, habit_id)
    metric = db.query(Metric).filter(Metric.id == metric_id, Metric.habit_id == habit_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.post("", response_model=MetricRead, status_code=status.HTTP_201_CREATED)
def create_metric(habit_id: int, payload: MetricCreate, db: Session = Depends(get_db)):
    get_habit_or_404(db, habit_id)
    metric = Metric(habit_id=habit_id, **payload.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("", response_model=list[MetricRead])
def list_metrics(habit_id: int, db: Session = Depends(get_db)):
    get_habit_or_404(db, habit_id)
    return db.query(Metric).filter(Metric.habit_id == habit_id).order_by(Metric.id).all()


@router.get("/{metric_id}", response_model=MetricRead)
def get_metric(habit_id: int, metric_id: int, db: Session = Depends(get_db)):
    return get_metric_or_404(db, habit_id, metric_id)


@router.put("/{metric_id}", response_model=MetricRead)
def update_metric(habit_id: int, metric_id: int, payload: MetricUpdate, db: Session = Depends(get_db)):
    metric = get_metric_or_404(db, habit_id, metric_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is None and key != "unit":
            continue
        setattr(metric, key, value)
    db.commit()
    db.refresh(metric)
    return metric


@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric(habit_id: int, metric_id: int, db: Session = Depends(get_db)):
    metric = get_metric_or_404(db, habit_id, metric_id)
    db.delete(metric)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
