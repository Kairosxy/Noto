"""简版 SM-2：4 档间隔调度"""

from datetime import datetime, timedelta, timezone

# rating -> (days_fn(ease), new_ease_fn(ease))
_RULES = {
    "again": (lambda _ease: 1,                 lambda _ease: 0),
    "hard":  (lambda _ease: 3,                 lambda ease: ease),
    "good":  (lambda ease: 7 * (ease + 1),     lambda ease: ease + 1),
    "easy":  (lambda ease: 21 * (ease + 1),    lambda ease: ease + 2),
}


def next_due(rating: str, ease: int, reps: int, now: datetime | None = None) -> tuple[datetime, int, int]:
    if now is None:
        now = datetime.now(timezone.utc)
    rule = _RULES.get(rating)
    if rule is None:
        raise ValueError(f"未知 rating: {rating}")
    days_fn, ease_fn = rule
    return (now + timedelta(days=days_fn(ease)), ease_fn(ease), reps + 1)
