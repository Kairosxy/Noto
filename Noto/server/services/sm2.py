"""简版 SM-2：4 档间隔调度"""

from datetime import datetime, timedelta, timezone


def next_due(rating: str, ease: int, reps: int, now: datetime | None = None) -> tuple[datetime, int, int]:
    if now is None:
        now = datetime.now(timezone.utc)

    new_reps = reps + 1

    if rating == "again":
        return (now + timedelta(days=1), 0, new_reps)
    if rating == "hard":
        return (now + timedelta(days=3), ease, new_reps)
    if rating == "good":
        return (now + timedelta(days=7 * (ease + 1)), ease + 1, new_reps)
    if rating == "easy":
        return (now + timedelta(days=21 * (ease + 1)), ease + 2, new_reps)

    raise ValueError(f"未知 rating: {rating}")
