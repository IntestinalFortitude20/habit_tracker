import math
import json
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Entry, Goal, Habit, Metric, MetricValue, PlannedWorkout
from app.schemas.goal import GoalCreate, PlanDay
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
    race_type = goal.race_type or goal.goal_type
    plan = training.generate_plan(race_type, goal.experience_level, start, goal.target_date, goal.unit)
    db.add_all(PlannedWorkout(goal_id=goal.id, **w) for w in plan)
    return len(plan)


def _validate_metric(db: Session, habit: Habit, metric_id: int | None, required: bool) -> Metric | None:
    if metric_id is None:
        if required:
            raise HTTPException(status_code=422, detail="A metric is required for a metric target goal.")
        return None
    metric = db.query(Metric).filter(Metric.id == metric_id, Metric.habit_id == habit.id).first()
    if metric is None:
        raise HTTPException(status_code=422, detail=f"Metric {metric_id} does not belong to habit {habit.id}")
    if metric.type == "boolean":
        raise HTTPException(status_code=422, detail="Metric target goals require a numeric metric.")
    return metric


def _goal_record(db: Session, habit: Habit, payload: GoalCreate, start: date) -> tuple[Goal, dict | None]:
    is_running = payload.goal_type in ("running_plan", "5k", "10k", "half_marathon", "marathon")
    is_metric = payload.goal_type == "metric_target"
    if is_running:
        race_type = payload.race_type or (payload.goal_type if payload.goal_type != "running_plan" else None)
        if race_type not in training.goal_types():
            raise HTTPException(status_code=422, detail="Choose a valid running race distance.")
        if payload.target_date is None:
            raise HTTPException(status_code=422, detail="A target date is required for a running plan.")
        feas = feasibility_or_422(race_type, payload.experience_level, start, payload.target_date)
        metric = _validate_metric(db, habit, payload.metric_id, False)
        if metric is None:
            metric = Metric(habit_id=habit.id, name="Distance", type="count", unit=payload.unit)
            db.add(metric)
            db.flush()
        return Goal(
            habit_id=habit.id, metric_id=metric.id, goal_type="running_plan", race_type=race_type,
            distance=training.goal_distance(race_type, payload.unit), unit=payload.unit,
            experience_level=payload.experience_level, start_date=start, target_date=payload.target_date,
            end_date=payload.target_date,
        ), feas
    if payload.goal_type == "frequency":
        if payload.per_week is None and payload.per_month is None:
            raise HTTPException(status_code=422, detail="Set a weekly target, monthly target, or both.")
        if payload.target_date is not None and payload.target_date < date.today():
            raise HTTPException(status_code=422, detail="End date cannot be in the past.")
        return Goal(
            habit_id=habit.id, goal_type="frequency", distance=0, unit=payload.unit,
            experience_level=payload.experience_level, start_date=start,
            target_date=payload.target_date or date(9999, 12, 31), end_date=payload.target_date,
            per_week=payload.per_week, per_month=payload.per_month,
        ), None
    if is_metric:
        if payload.target_date is None:
            raise HTTPException(status_code=422, detail="An end date is required for a metric target goal.")
        if payload.target_date <= start:
            raise HTTPException(status_code=422, detail="End date must be after the start date.")
        if payload.target_date < date.today():
            raise HTTPException(status_code=422, detail="End date cannot be in the past.")
        if payload.target_value is None:
            raise HTTPException(status_code=422, detail="A target value is required.")
        if payload.plan_source is None:
            raise HTTPException(status_code=422, detail="Choose linear, AI coach, or manual plan mode.")
        metric = _validate_metric(db, habit, payload.metric_id, True)
        return Goal(
            habit_id=habit.id, metric_id=metric.id, goal_type="metric_target", distance=0,
            unit=metric.unit or "", experience_level=payload.experience_level, start_date=start,
            target_date=payload.target_date, end_date=payload.target_date,
            target_value=payload.target_value, start_value=payload.start_value or 0,
            plan_source=payload.plan_source,
        ), None
    raise HTTPException(status_code=422, detail="Choose a supported goal type.")


def _metric_plan(goal: Goal) -> list[dict]:
    start = goal.start_date
    end = goal.target_date
    days = max((end - start).days, 1)
    initial = goal.start_value or 0
    return [
        {
            "date": start + timedelta(days=i),
            "workout_type": "target",
            "target_distance": round(initial + (goal.target_value - initial) * i / days, 2),
            "target_duration_min": None,
            "phase": None,
            "notes": None,
        }
        for i in range(days + 1)
    ]


def _save_metric_plan(db: Session, goal: Goal, plan: list[PlanDay] | list[dict]) -> int:
    db.query(PlannedWorkout).filter(PlannedWorkout.goal_id == goal.id).delete()
    rows = []
    for day in plan:
        d = day.model_dump() if isinstance(day, PlanDay) else day
        rows.append(PlannedWorkout(
            goal_id=goal.id,
            date=d["date"],
            workout_type=d.get("workout_type") or "target",
            target_distance=d.get("target_value"),
            notes=d.get("notes"),
            phase=None,
            target_duration_min=None,
        ))
    db.add_all(rows)
    return len(rows)


def create_goal(db: Session, habit: Habit, payload: GoalCreate, plan: list[PlanDay] | None = None) -> tuple[Goal, dict | None, int]:
    start = payload.start_date or date.today()
    if payload.plan_source == "ai":
        raise HTTPException(status_code=422, detail="Review and accept an AI draft before saving the goal.")
    if payload.plan_source == "manual" and not plan:
        raise HTTPException(status_code=422, detail="Add at least one target day to the manual plan.")
    goal, feas = _goal_record(db, habit, payload, start)
    if goal.goal_type == "metric_target" and plan:
        allowed = {start + timedelta(days=i) for i in range((goal.target_date - start).days + 1)}
        if any(day.date not in allowed for day in plan) or len({day.date for day in plan}) != len(plan):
            raise HTTPException(status_code=422, detail="Plan days must be unique and within the goal dates.")
        if payload.plan_source == "manual" and not any(day.target_value is not None for day in plan):
            raise HTTPException(status_code=422, detail="A manual plan must include at least one target.")
    try:
        for old in db.query(Goal).filter(Goal.habit_id == habit.id, Goal.status == "active").all():
            old.status = "cancelled"
        db.add(goal)
        db.flush()
        if goal.goal_type == "running_plan":
            count = _store_plan(db, goal, start)
        elif goal.goal_type == "metric_target":
            count = _save_metric_plan(db, goal, plan if plan is not None else _metric_plan(goal))
        else:
            count = 0
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(goal)
    return goal, feas, count


def update_plan_day(db: Session, goal: Goal, day: date, updates: dict) -> dict:
    if goal.goal_type != "metric_target":
        raise HTTPException(status_code=422, detail="Only metric target plan days can be edited.")
    workout = db.query(PlannedWorkout).filter(
        PlannedWorkout.goal_id == goal.id, PlannedWorkout.date == day
    ).first()
    if workout is None:
        raise HTTPException(status_code=404, detail="No planned target exists for this date.")
    for field, value in updates.items():
        setattr(workout, "target_distance" if field == "target_value" else field, value)
    db.commit()
    return workout_view(workout, _entry_lookup(db, goal, day, day).get(day), date.today())


def regenerate_plan(db: Session, goal: Goal, target: date | None, level: str | None, today: date | None = None) -> tuple[dict, int]:
    """Re-plan the remaining days (today onward). Past workouts and entries are kept; missed work is not caught up."""
    if goal.goal_type != "running_plan":
        raise HTTPException(status_code=422, detail="Only running plans can be regenerated this way.")
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


def draft_metric_plan(db: Session, habit: Habit, payload: GoalCreate) -> list[dict]:
    if payload.goal_type != "metric_target" or payload.plan_source != "ai":
        raise HTTPException(status_code=422, detail="AI drafts require an AI-coached metric target.")
    start = payload.start_date or date.today()
    goal, _ = _goal_record(db, habit, payload, start)
    metric = db.query(Metric).filter(Metric.id == goal.metric_id).first()
    history = (
        db.query(Entry)
        .filter(Entry.habit_id == habit.id, Entry.date >= start - timedelta(days=90), Entry.date < start)
        .order_by(Entry.date)
        .all()
    )
    recent = [
        {"date": entry.date.isoformat(), "value": mv.value}
        for entry in history
        for mv in entry.metric_values
        if mv.metric_id == goal.metric_id
    ]
    from app.services.chat import call_llm

    prompt = (
        "Create a safe, general training plan as JSON only: "
        '{"days":[{"date":"YYYY-MM-DD","target_value":number|null,"workout_type":"target|rest|deload","notes":string|null}]}. '
        "Use a realistic progression, include easier or rest days when appropriate, and cover each date from start through end. "
        "This is general guidance, not medical advice. Do not invent history. "
        f"Habit: {habit.name}. Metric: {metric.name if metric else 'metric'} "
        f"({metric.unit if metric and metric.unit else ''}). Start value: {goal.start_value:g}; "
        f"target: {goal.target_value:g}; start date: {start.isoformat()}; end date: {goal.target_date.isoformat()}. "
        f"Recent history: {json.dumps(recent)}"
    )
    try:
        response = call_llm([{"role": "user", "content": prompt}])
        parsed = json.loads(response)
        days = [PlanDay.model_validate(item) for item in parsed["days"]]
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The coach could not create a valid plan draft. Please try again.") from exc
    expected_dates = {start + timedelta(days=i) for i in range((goal.target_date - start).days + 1)}
    by_date = {day.date: day for day in days}
    if set(by_date) != expected_dates:
        raise HTTPException(status_code=502, detail="The coach returned an incomplete plan draft. Please try again.")
    return [day.model_dump() for day in sorted(by_date.values(), key=lambda item: item.date)]


def adjust_metric_plan(db: Session, goal: Goal, prompt: str, today: date | None = None) -> int:
    if goal.goal_type != "metric_target":
        raise HTTPException(status_code=422, detail="Only metric target plans can be adjusted by the coach.")
    today = today or date.today()
    remaining = (
        db.query(PlannedWorkout)
        .filter(PlannedWorkout.goal_id == goal.id, PlannedWorkout.date >= today)
        .order_by(PlannedWorkout.date)
        .all()
    )
    from app.services.chat import call_llm

    try:
        response = call_llm([{
            "role": "user",
            "content": (
                "Adjust this remaining metric plan according to the user's request. Return JSON only with a days array "
                'of {"date":"YYYY-MM-DD","target_value":number|null,"workout_type":"target|rest|deload","notes":string|null}. '
                "Keep the dates exactly as given. General guidance, not medical advice. "
                f"Request: {prompt}. Plan: {json.dumps([{'date': w.date.isoformat(), 'target_value': w.target_distance, 'workout_type': w.workout_type, 'notes': w.notes} for w in remaining])}"
            ),
        }])
        days = [PlanDay.model_validate(item) for item in json.loads(response)["days"]]
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The coach could not adjust the plan. Please try again.") from exc
    expected = {w.date for w in remaining}
    if {day.date for day in days} != expected:
        raise HTTPException(status_code=502, detail="The coach returned an invalid adjusted plan. Please try again.")
    _save_metric_plan(db, goal, [*[
        PlanDay(date=w.date, target_value=w.target_distance, workout_type=w.workout_type, notes=w.notes)
        for w in db.query(PlannedWorkout).filter(PlannedWorkout.goal_id == goal.id, PlannedWorkout.date < today)
    ], *days])
    db.commit()
    return len(days)


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
        "target_value": w.target_distance,
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
    if goal.goal_type == "frequency":
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        entries = db.query(Entry).filter(
            Entry.habit_id == goal.habit_id,
            Entry.completed.is_(True),
            Entry.date >= min(week_start, month_start),
            Entry.date <= today,
        ).all()
        week_count = sum(week_start <= e.date <= today for e in entries)
        month_count = sum(month_start <= e.date <= today for e in entries)
        targets_met = (
            (goal.per_week is None or week_count >= goal.per_week)
            and (goal.per_month is None or month_count >= goal.per_month)
        )
        finished = goal.end_date is not None and today > goal.end_date
        return {
            "goal": goal,
            "weeks_remaining": max(math.ceil(((goal.end_date or today) - today).days / 7), 0),
            "days_remaining": max(((goal.end_date or today) - today).days, 0),
            "adherence": None,
            "on_track": targets_met,
            "status_label": "finished" if finished else ("on track" if targets_met else "in progress"),
            "suggest_regenerate": False,
            "current_week": None,
            "weeks": [],
            "week_completed": week_count,
            "week_target": goal.per_week,
            "month_completed": month_count,
            "month_target": goal.per_month,
        }
    if goal.goal_type == "metric_target":
        plans = list_workouts(db, goal, today, today, today)
        entries = db.query(Entry).filter(
            Entry.habit_id == goal.habit_id, Entry.date >= goal.start_date, Entry.date <= today
        ).all()
        actuals = [
            mv.value
            for entry in entries
            for mv in entry.metric_values
            if mv.metric_id == goal.metric_id
        ]
        actual = actuals[-1] if actuals else goal.start_value or 0
        daily_target = plans[0]["target_value"] if plans else goal.target_value
        on_track = actual >= (daily_target or 0)
        finished = today > goal.target_date
        return {
            "goal": goal,
            "weeks_remaining": max(math.ceil((goal.target_date - today).days / 7), 0),
            "days_remaining": max((goal.target_date - today).days, 0),
            "adherence": None,
            "on_track": on_track,
            "status_label": "finished" if finished else ("on track" if on_track else "behind"),
            "suggest_regenerate": False,
            "current_week": None,
            "weeks": [],
            "metric_progress": round(actual / goal.target_value * 100, 1) if goal.target_value else None,
        }
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
    prog = compute_progress(db, goal, today)
    if goal.goal_type == "frequency":
        targets = []
        if goal.per_week is not None:
            targets.append(f"{prog['week_completed']} of {goal.per_week} this week")
        if goal.per_month is not None:
            targets.append(f"{prog['month_completed']} of {goal.per_month} this month")
        return [f"Goal: frequency — {', '.join(targets)}."]
    if goal.goal_type == "metric_target":
        metric = db.query(Metric).filter(Metric.id == goal.metric_id).first()
        label = metric.name if metric else "metric"
        return [
            f"Goal: reach {goal.target_value:g} {goal.unit} {label} by {goal.target_date.isoformat()}, "
            f"status: {prog['status_label']}."
        ]
    race_type = goal.race_type or goal.goal_type
    label = training.goal_types()[race_type]["label"]
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
