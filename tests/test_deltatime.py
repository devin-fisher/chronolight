import pytest
from datetime import datetime, timedelta, timezone

from chronolight.core.ical.deltatime import *

UTC = timezone.utc


# -------------------------
# Helpers
# -------------------------

def dt(minutes_offset: int) -> datetime:
    """Create a deterministic datetime relative to a fixed point."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    return base + timedelta(minutes=minutes_offset)


# -------------------------
# is_all_day tests
# -------------------------

def test_is_all_day_date_only():
    start = dt(0).date()  # relies on is_date detecting date-like objects
    end = dt(60)

    assert is_all_day(start, end) is True


def test_is_all_day_multi_day_event():
    start = dt(0)
    end = dt(60 * 24 + 1)  # > 1 day

    assert is_all_day(start, end) is True


def test_is_all_day_normal_event():
    start = dt(0)
    end = dt(30)

    assert is_all_day(start, end) is False


def test_is_all_day_bad_input_safety():
    start = "not-a-date"
    end = dt(30)

    assert is_all_day(start, end) is False


# -------------------------
# is_near_or_not_after tests
# -------------------------

THRESHOLD = 10


def test_near_start_within_threshold():
    now = dt(-5)
    start = dt(0)
    end = dt(30)

    assert is_near_or_during(now, start, end, THRESHOLD) is True


def test_near_start_exact_boundary():
    now = dt(-10)
    start = dt(0)
    end = dt(30)

    assert is_near_or_during(now, start, end, THRESHOLD) is True


def test_outside_threshold_before_start():
    now = dt(-11)
    start = dt(0)
    end = dt(30)

    assert is_near_or_during(now, start, end, THRESHOLD) is False


def test_active_inside_event():
    now = dt(15)
    start = dt(0)
    end = dt(30)

    assert is_near_or_during(now, start, end, THRESHOLD) is True


def test_exact_start():
    now = dt(0)
    start = dt(0)
    end = dt(30)

    assert is_near_or_during(now, start, end, THRESHOLD) is True


def test_exact_end():
    now = dt(30)
    start = dt(0)
    end = dt(30)

    assert is_near_or_during(now, start, end, THRESHOLD) is True


def test_after_event():
    now = dt(31)
    start = dt(0)
    end = dt(30)

    assert is_near_or_during(now, start, end, THRESHOLD) is False


def test_all_day_event_excluded():
    now = dt(0)

    start = dt(0).date()  # triggers all-day logic
    end = dt(1440)

    assert is_near_or_during(now, start, end, THRESHOLD) is False