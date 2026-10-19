"""Pure training-plan logic: feasibility checks and day-by-day plan generation."""
import json
import math
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

KM_PER_MILE = 1.609344
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "training_plans.json"
DISCLAIMER = "This is general training guidance, not medical advice. Consult a doctor before starting a new training program."
UNITS = ("mi", "km")
LEVELS = ("beginner", "intermediate", "advanced")


@lru_cache(maxsize=1)
def load_data() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def goal_types() -> dict:
    return load_data()["goals"]


def _convert(miles: float, unit: str) -> float:
    return miles * KM_PER_MILE if unit == "km" else miles


def _round_half(x: float) -> float:
    return round(x * 2) / 2


def goal_distance(goal_type: str, unit: str) -> float:
    return round(_convert(goal_types()[goal_type]["distance_miles"], unit), 1)


def check_feasibility(goal_type: str, level: str, start: date, target: date) -> dict:
    params = goal_types()[goal_type]["levels"][level]
    min_weeks = params["min_weeks"]
    max_weeks = load_data()["max_weeks"]
    days = (target - start).days + 1
    weeks = max(days, 0) // 7
    earliest = start + timedelta(days=min_weeks * 7 - 1)
    latest = start + timedelta(days=max_weeks * 7 - 1)
    label = goal_types()[goal_type]["label"]
    feasible, message = True, "This date looks realistic."
    if weeks < min_weeks:
        feasible = False
        message = (
            f"{label} needs at least {min_weeks} weeks of structured training for a {level} runner; "
            f"only {weeks} week(s) are available. The earliest realistic date is {earliest.isoformat()}."
        )
    elif weeks > max_weeks:
        feasible = False
        message = f"Plans longer than {max_weeks} weeks are not supported. Choose a date on or before {latest.isoformat()}."
    elif weeks > min_weeks:
        message = f"{weeks - min_weeks} extra week(s) will be used as a base-building phase."
    return {
        "feasible": feasible,
        "message": message,
        "weeks_available": weeks,
        "min_weeks": min_weeks,
        "earliest_date": earliest,
        "latest_date": latest,
        "base_weeks": max(weeks - min_weeks, 0) if feasible else 0,
        "disclaimer": DISCLAIMER,
    }


def _weekly_miles(k: int, n_blocks: int, params: dict, taper: int) -> tuple[float, str]:
    """Weekly mileage (miles) for the block k weeks before race week (k=0 is race week)."""
    if k < taper:
        i = taper - 1 - k  # 0 = first taper week
        factor = 0.8 - 0.4 * i / (taper - 1) if taper > 1 else 0.6
        return params["peak_weekly"] * factor, "taper"
    i = n_blocks - 1 - k  # chronological week index from plan start
    build = params["min_weeks"] - taper
    build_start = n_blocks - taper - build  # index of first build week (>= 0 when feasible)
    b = i - build_start
    start_w, peak = params["start_weekly"], params["peak_weekly"]
    if b < 0:
        miles, phase = start_w, "base"
    else:
        miles = start_w + (peak - start_w) * (b / (build - 1) if build > 1 else 1)
        phase = "build"
    if i % 4 == 3 and b != build - 1:
        return miles * 0.75, "recovery"
    return miles, phase


def generate_plan(goal_type: str, level: str, start: date, target: date, unit: str = "mi") -> list[dict]:
    """One workout dict per calendar day from start to target (inclusive), planned backward from race day."""
    info = goal_types()[goal_type]
    params = info["levels"][level]
    schedule = load_data()["schedules"][level]
    taper = info["taper_weeks"]
    total_days = (target - start).days + 1
    n_blocks = math.ceil(total_days / 7)
    peak_long = _convert(params["peak_long"], unit)
    plan = []
    for offset in range(total_days):
        d = start + timedelta(days=offset)
        days_before = (target - d).days
        k = days_before // 7
        if days_before == 0:
            plan.append({"date": d, "workout_type": "race", "target_distance": goal_distance(goal_type, unit),
                         "target_duration_min": None, "phase": "race",
                         "notes": f"Race day: {info['label']}. Start easy and enjoy it."})
            continue
        miles, phase = _weekly_miles(k, n_blocks, params, taper)
        slot = schedule[str(d.weekday())]
        wtype = slot["type"]
        if wtype == "long" and k == 0:
            wtype = "easy"
        if days_before == 1:
            wtype = "rest"
        if wtype == "rest":
            plan.append({"date": d, "workout_type": "rest", "target_distance": None, "target_duration_min": None,
                         "phase": phase, "notes": "Rest day."})
        elif wtype == "cross_training":
            plan.append({"date": d, "workout_type": wtype, "target_distance": None,
                         "target_duration_min": slot.get("duration_min", 30), "phase": phase,
                         "notes": "Low-impact cross-training (cycling, swimming, strength)."})
        else:
            dist = _convert(miles, unit) * slot.get("share", 0.15)
            if wtype == "long":
                dist = min(dist, peak_long)
            dist = max(_round_half(dist), 1.0)
            plan.append({"date": d, "workout_type": wtype, "target_distance": dist, "target_duration_min": None,
                         "phase": phase, "notes": f"{wtype.capitalize()} run, {phase} phase."})
    return plan
