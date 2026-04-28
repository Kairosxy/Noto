from datetime import datetime, timedelta, timezone

from services.sm2 import next_due


def _near(a: datetime, b: datetime, minutes: int = 2) -> bool:
    return abs((a - b).total_seconds()) < minutes * 60


def test_again_resets_ease():
    due, ease, reps = next_due("again", ease=3, reps=5, now=datetime(2026, 4, 27, tzinfo=timezone.utc))
    assert ease == 0
    assert reps == 6
    assert _near(due, datetime(2026, 4, 28, tzinfo=timezone.utc))


def test_hard_keeps_ease_and_3d():
    now = datetime(2026, 4, 27, tzinfo=timezone.utc)
    due, ease, reps = next_due("hard", ease=2, reps=1, now=now)
    assert ease == 2
    assert _near(due, now + timedelta(days=3))


def test_good_multiplies_by_ease_plus_1():
    now = datetime(2026, 4, 27, tzinfo=timezone.utc)
    due, ease, _ = next_due("good", ease=0, reps=0, now=now)
    assert ease == 1
    assert _near(due, now + timedelta(days=7))

    due, ease, _ = next_due("good", ease=2, reps=2, now=now)
    assert ease == 3
    assert _near(due, now + timedelta(days=21))


def test_easy_larger_interval():
    now = datetime(2026, 4, 27, tzinfo=timezone.utc)
    due, ease, _ = next_due("easy", ease=0, reps=0, now=now)
    assert ease == 2
    assert _near(due, now + timedelta(days=21))
