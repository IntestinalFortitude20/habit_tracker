from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.habits import get_habit_or_404
from app.db.session import get_db
from app.models.models import Entry
from app.schemas.habit import EntryCreate, EntryRead, EntryUpdate
from app.services.entries import replace_metric_values, validate_metric_values

router = APIRouter(prefix="/api/habits/{habit_id}/entries", tags=["entries"])


def get_entry_or_404(db: Session, habit_id: int, entry_id: int) -> Entry:
    get_habit_or_404(db, habit_id)
    entry = db.query(Entry).filter(Entry.id == entry_id, Entry.habit_id == habit_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


def find_by_date(db: Session, habit_id: int, d: date) -> Entry | None:
    return db.query(Entry).filter(Entry.habit_id == habit_id, Entry.date == d).first()


@router.post("", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(habit_id: int, payload: EntryCreate, db: Session = Depends(get_db)):
    """Upsert: if an entry already exists for this habit/date it is replaced."""
    get_habit_or_404(db, habit_id)
    validate_metric_values(db, habit_id, payload.metric_values)
    try:
        entry = find_by_date(db, habit_id, payload.date)
        if entry is None:
            entry = Entry(habit_id=habit_id, date=payload.date)
            db.add(entry)
        entry.completed = payload.completed
        replace_metric_values(entry, payload.metric_values)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(entry)
    return entry


@router.get("", response_model=list[EntryRead])
def list_entries(
    habit_id: int,
    order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int | None = Query(None, ge=1, le=1000),
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
):
    get_habit_or_404(db, habit_id)
    q = db.query(Entry).filter(Entry.habit_id == habit_id)
    if start:
        q = q.filter(Entry.date >= start)
    if end:
        q = q.filter(Entry.date <= end)
    q = q.order_by(Entry.date.asc() if order == "asc" else Entry.date.desc())
    if limit:
        q = q.limit(limit)
    return q.all()


@router.get("/{entry_id}", response_model=EntryRead)
def get_entry(habit_id: int, entry_id: int, db: Session = Depends(get_db)):
    return get_entry_or_404(db, habit_id, entry_id)


@router.put("/{entry_id}", response_model=EntryRead)
def update_entry(habit_id: int, entry_id: int, payload: EntryUpdate, db: Session = Depends(get_db)):
    entry = get_entry_or_404(db, habit_id, entry_id)
    if payload.metric_values is not None:
        validate_metric_values(db, habit_id, payload.metric_values)
    if payload.date is not None and payload.date != entry.date:
        other = find_by_date(db, habit_id, payload.date)
        if other:
            raise HTTPException(status_code=409, detail="An entry already exists for that date")
    try:
        if payload.date is not None:
            entry.date = payload.date
        if payload.completed is not None:
            entry.completed = payload.completed
        if payload.metric_values is not None:
            replace_metric_values(entry, payload.metric_values)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(habit_id: int, entry_id: int, db: Session = Depends(get_db)):
    entry = get_entry_or_404(db, habit_id, entry_id)
    db.delete(entry)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
