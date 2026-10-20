import math
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Entry, Goal, Habit, Metric, MetricValue, PlannedWorkout
from app.schemas.goal import GoalCreate
from app.services import training

ON_TRACK_THRESHOLD = 0.7
REGENERATE_THRESHOLD = 0.5
ADHERENCE_WINDOW_DAYS = 28
MIN_DUE_FOR_REGENERATE = 4


def get_active_goal(db: Session, habit_id: int) -> Goal | None:
    return (
        db.query(Goal)
        .filter(Goal.habit_id == habit_id, Goal.status == "active")
        .order_by(Goal.id.desc())
        .first()
    )


def rest_dates(db: Session, habit_id: int) -> set[date]:
    """Planned rest days of the active goal; these never break a streak."""
    goal = get_active_goal(db, habit_id)
    if goal is None:
        return set()
    rows = db.query(PlannedWorkout.date).filter(
        PlannedWorkout.goal_id == goal.id, PlannedWorkout.workout_type == "rest"
    ).all()
    return {r.date for r in rows}


def feasibility_or_422(goal_type: str, level: str, start: date, target: date) -> dict:
    if target <= start:
        raise HTTPException(status_code=422, detail={"message": "Target date must be after the start date."})
    result = training.check_feasibility(goal_type, level, start, target)
    if not result["feasible"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": result["message"],
                "earliest_date": result["earliest_date"].isoformat(),
                "latest_date": result["latest_date"].isoformat(),
            },
        )
    return result


def _store_plan(db: Session, goal: Goal, start: date) -> int:
    plan = training.generate_plan(goal.goal_type, goal.experience_level, start, goal.target_date, goal.unit)
    db.add_all(PlannedWorkout(goal_id=goal.id, **w) for w in plan)
    return len(plan)


def create_goal(db: Session, habit: Habit, payload: GoalCreate) -> tuple[Goal, dict, int]:
    start = payload.start_date or date.today()
    feas = feasibility_or_422(payload.goal_type, payload.experience_level, start, payload.target_date)
    metric_id = payload.metric_id
    if metric_id is not None:
        if not db.query(Metric.id).filter(Metric.id == metric_id, Metric.habit_id == habit.id).first():
            raise HTTPException(status_code=422, detail=f"Metric {metric_id} does not belong to habit {habit.id}")
    try:
        for old in db.query(Goal).filter(Goal.habit_id == habit.id, Goal.status == "active").all():
            old.status = "cancelled"
        if metric_id is None:
            metric = Metric(habit_id=habit.id, name="Distance", type="count", unit=payload.unit)
            db.add(metric)
            db.flush()
            metric_id = metric.id
        goal = Goal(
            habit_id=habit.id,
            metric_id=metric_id,
            goal_type=payload.goal_type,
            distance=training.goal_distance(payload.goal_type, payload.unit),
            unit=payload.unit,
            experience_level=payload.experience_level,
            start_date=start,
            target_date=payload.target_date,
        )
        db.add(goal)
        db.flush()
        count = _store_plan(db, goal, start)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(goal)
    return goal, feas, count


def regenerate_plan(db: Session, goal: Goal, target: date | None, level: str | None, today: date | None = None) -> tuple[dict, int]:
    """Re-plan the remaining days (today onward). Past workouts and entries are kept; missed work is not caught up."""
    today = today or date.today()
    new_target = target or goal.target_date
    new_level = level or goal.experience_level
    start = max(today, goal.start_date)
    feas = feasibility_or_422(goal.goal_type, new_level, start, new_target)
    try:
        db.query(PlannedWorkout).filter(PlannedWorkout.goal_id == goal.id, PlannedWorkout.date >= start).delete()
        goal.target_date = new_target
        goal.experience_level = new_level
        count = _store_plan(db, goal, start)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return feas, count


def _entry_lookup(db: Session, goal: Goal, start: date, end: date) -> dict[date, tuple[Entry, float | None]]:
    entries = db.query(Entry).filter(Entry.habit_id == goal.habit_id, Entry.date >= start, Entry.date <= end).all()
    out = {}
    for e in entries:
        actual = None
        for mv in e.metric_values:
            if mv.metric_id == goal.metric_id:
                actual = mv.value
        out[e.date] = (e, actual)
    return out


def workout_view(w: PlannedWorkout, entry_info: tuple[Entry, float | None] | None, today: date) -> dict:
    entry, actual = entry_info if entry_info else (None, None)
    if w.workout_type == "rest":
        status = "rest"
    elif entry is not None and entry.completed:
        status = "completed"
    elif w.date < today:
        status = "missed"
    elif w.date == today:
        status = "today"
    else:
        status = "upcoming"
    diff = pct = None
    if actual is not None and w.target_distance:
        diff = round(actual - w.target_distance, 2)
        pct = round(actual / w.target_distance * 100, 1)
    return {
        "date": w.date,
        "workout_type": w.workout_type,
        "target_distance": w.target_distance,
        "target_duration_min": w.target_duration_min,
        "phase": w.phase,
        "notes": w.notes,
        "status": status,
        "entry_id": entry.id if entry else None,
        "actual_distance": actual,
        "difference": diff,
        "percent_of_target": pct,
    }


def list_workouts(db: Session, goal: Goal, start: date | None, end: date | None, today: date | None = None) -> list[dict]:
    today = today or date.today()
    q = db.query(PlannedWorkout).filter(PlannedWorkout.goal_id == goal.id)
    if start:
        q = q.filter(PlannedWorkout.date >= start)
    if end:
        q = q.filter(PlannedWorkout.date <= end)
    rows = q.order_by(PlannedWorkout.date).all()
    if not rows:
        return []
    lookup = _entry_lookup(db, goal, rows[0].date, rows[-1].date)
    return [workout_view(w, lookup.get(w.date), today) for w in rows]


def _week_summary(week_start: date, items: list[dict], today: date) -> dict:
    runs = [i for i in items if i["status"] != "rest"]
    due = [i for i in runs if i["status"] in ("completed", "missed")]
    done = [i for i in runs if i["status"] == "completed"]
    return {
        "week_start": week_start,
        "planned_distance": round(sum(i["target_distance"] or 0 for i in runs), 1),
        "completed_distance": round(sum(i["actual_distance"] or 0 for i in done), 1),
        "planned_workouts": len(runs),
        "completed_workouts": len(done),
        "adherence": round(len(done) / len(due), 2) if due else None,
    }


def compute_progress(db: Session, goal: Goal, today: date | None = None) -> dict:
    today = today or date.today()
    items = list_workouts(db, goal, None, None, today)
    by_week: dict[date, list[dict]] = {}
    for i in items:
        ws = i["date"] - timedelta(days=i["date"].weekday())
        by_week.setdefault(ws, []).append(i)
    weeks = [_week_summary(ws, v, today) for ws, v in sorted(by_week.items())]
    this_monday = today - timedelta(days=today.weekday())
    current = next((w for w in weeks if w["week_start"] == this_monday), None) or _week_summary(this_monday, [], today)

    window_start = today - timedelta(days=ADHERENCE_WINDOW_DAYS)
    recent = [
        i for i in items
        if i["status"] in ("completed", "missed") and window_start <= i["date"] <= today
    ]
    adherence = round(sum(1 for i in recent if i["status"] == "completed") / len(recent), 2) if recent else None
    days_remaining = max((goal.target_date - today).days, 0)
    finished = today > goal.target_date
    on_track = adherence is None or adherence >= ON_TRACK_THRESHOLD
    suggest = (
        not finished
        and adherence is not None
        and len(recent) >= MIN_DUE_FOR_REGENERATE
        and adherence < REGENERATE_THRESHOLD
    )
    label = "finished" if finished else ("on track" if on_track else "behind")
    return {
        "goal": goal,
        "weeks_remaining": math.ceil(days_remaining / 7),
        "days_remaining": days_remaining,
        "adherence": adherence,
        "on_track": on_track,
        "status_label": label,
        "suggest_regenerate": suggest,
        "current_week": current,
        "weeks": weeks,
    }


def goal_context_lines(db: Session, habit_id: int, today: date) -> list[str]:
    goal = get_active_goal(db, habit_id)
    if goal is None:
        return []
    label = training.goal_types()[goal.goal_type]["label"]
    prog = compute_progress(db, goal, today)
    lines = [
        f"Goal: {label} ({goal.distance:g} {goal.unit}) on {goal.target_date.isoformat()}, "
        f"{goal.experience_level} level, {prog['weeks_remaining']} week(s) remaining, status: {prog['status_label']}."
    ]
    if prog["adherence"] is not None:
        lines.append(f"Plan adherence over the last {ADHERENCE_WINDOW_DAYS} days: {round(prog['adherence'] * 100)}%.")
    todays = list_workouts(db, goal, today, today, today)
    if todays:
        w = todays[0]
        target = f"{w['target_distance']:g} {goal.unit}" if w["target_distance"] else (
            f"{w['target_duration_min']:g} min" if w["target_duration_min"] else "no distance target"
        )
        lines.append(f"Today's planned workout: {w['workout_type']} ({target}), status: {w['status']}.")
    return lines
