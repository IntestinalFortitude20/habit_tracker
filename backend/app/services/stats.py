from datetime import date, timedelta
from typing import Iterable


def compute_stats(
    entries: Iterable[tuple[date, bool]], today: date | None = None, rest_days: Iterable[date] = ()
) -> dict:
    """Compute streak and completion stats from (date, completed) pairs.

    Current streak rule: count consecutive completed days ending today; if today
    is not completed (missing or not done), the streak ending yesterday still counts.
    Completion rates are completed days in the trailing window (including today)
    divided by the window size.

    Planned rest days (``rest_days``) never break a streak: a rest day without a
    completed entry is skipped (it neither adds to nor resets the streak).
    """
    today = today or date.today()
    logged = {}
    for d, completed in entries:
        logged[d] = logged.get(d, False) or completed
    done = {d for d, c in logged.items() if c}
    rest = set(rest_days) - done

    longest = run = 0
    prev = None
    for d in sorted(done):
        connected = prev is not None and all(
            prev + timedelta(days=i) in rest for i in range(1, (d - prev).days)
        )
        run = run + 1 if connected else 1
        longest = max(longest, run)
        prev = d

    cursor = today if today in done else today - timedelta(days=1)
    current = 0
    while cursor in done or cursor in rest:
        current += cursor in done
        cursor -= timedelta(days=1)

    def rate(days: int) -> float:
        start = today - timedelta(days=days - 1)
        return round(sum(1 for d in done if start <= d <= today) / days, 4)

    return {
        "current_streak": current,
        "longest_streak": longest,
        "completion_rate_7d": rate(7),
        "completion_rate_30d": rate(30),
        "total_completed_days": len(done),
        "total_logged_days": len(logged),
    }
