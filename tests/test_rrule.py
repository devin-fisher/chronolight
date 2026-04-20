import pytest
from datetime import datetime, date, timedelta

from chronolight.core.ical.rrule import recurring_event


# import your module here
# from your_module import recurring_event


# ----------------------------
# Helpers
# ----------------------------

def at(y, m, d, hh=0, mm=0):
    return datetime(y, m, d, hh, mm)


# ----------------------------
# DAILY tests
# ----------------------------

def test_daily_basic_match():
    dtstart = at(2026, 4, 10, 9, 0)
    now = at(2026, 4, 12, 9, 30)

    rrule = "FREQ=DAILY;INTERVAL=1"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is not None


def test_daily_interval_skip():
    dtstart = at(2026, 4, 10, 9, 0)
    now = at(2026, 4, 11, 9, 30)

    rrule = "FREQ=DAILY;INTERVAL=2"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is None


# ----------------------------
# WEEKLY tests
# ----------------------------

def test_weekly_byday_match():
    # Monday start
    dtstart = at(2026, 4, 6, 9, 0)  # Monday
    now = at(2026, 4, 8, 9, 30)     # Wednesday

    rrule = "FREQ=WEEKLY;BYDAY=WE"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is not None


def test_weekly_byday_no_match():
    dtstart = at(2026, 4, 6, 9, 0)
    now = at(2026, 4, 8, 9, 30)

    rrule = "FREQ=WEEKLY;BYDAY=MO"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is None


def test_weekly_interval_skip():
    dtstart = at(2026, 4, 6, 9, 0)
    now = at(2026, 4, 20, 9, 30)  # 2 weeks later

    rrule = "FREQ=WEEKLY;INTERVAL=3;BYDAY=MO"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is None


# ----------------------------
# MONTHLY tests
# ----------------------------

def test_monthly_same_day_match():
    dtstart = at(2026, 1, 15, 9, 0)
    now = at(2026, 4, 15, 9, 30)

    rrule = "FREQ=MONTHLY"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is not None


def test_monthly_wrong_day():
    dtstart = at(2026, 1, 15, 9, 0)
    now = at(2026, 4, 14, 9, 30)

    rrule = "FREQ=MONTHLY"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is None


# ----------------------------
# Duration tests
# ----------------------------

def test_default_duration_one_hour():
    dtstart = at(2026, 4, 17, 9, 0)
    now = at(2026, 4, 17, 9, 30)

    rrule = "FREQ=DAILY"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is not None

    start, end = res
    assert end - start == timedelta(hours=1)


def test_explicit_duration():
    dtstart = at(2026, 4, 17, 9, 0)
    now = at(2026, 4, 17, 9, 30)

    rrule = "FREQ=DAILY"
    duration = timedelta(minutes=15)

    res = recurring_event(now, dtstart, None, duration, rrule, None)
    assert res is not None

    start, end = res
    assert end - start == duration


# ----------------------------
# Edge: not active yet / past
# ----------------------------

def test_event_not_started_yet():
    dtstart = at(2026, 4, 20, 9, 0)
    now = at(2026, 4, 17, 9, 30)

    rrule = "FREQ=DAILY"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is None


def test_until_cutoff_blocks_future():
    dtstart = at(2026, 4, 10, 9, 0)
    now = at(2026, 4, 20, 9, 30)

    rrule = "FREQ=DAILY;UNTIL=20260415T000000"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is None

def test_until_allows_before_cutoff():
    dtstart = at(2026, 4, 10, 9, 0)
    now = at(2026, 4, 14, 9, 30)

    rrule = "FREQ=DAILY;UNTIL=20260415T000000"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is not None

def test_until_boundary_exact():
    dtstart = at(2026, 4, 10, 9, 0)
    now = at(2026, 4, 15, 9, 30)

    rrule = "FREQ=DAILY;UNTIL=20260415T000000"

    res = recurring_event(now, dtstart, None, None, rrule, None)

    # depending on interpretation, usually UNTIL is inclusive date-boundary,
    assert res is not None

def test_until_weekly():
    dtstart = at(2026, 4, 6, 9, 0)  # Monday
    now = at(2026, 4, 20, 9, 30)

    rrule = "FREQ=WEEKLY;BYDAY=MO;UNTIL=20260413T000000"

    res = recurring_event(now, dtstart, None, None, rrule, None)
    assert res is None