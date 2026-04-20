try:
    from datetime import timedelta
except ImportError:
    from adafruit_datetime import timedelta

from chronolight.core.ical.datetime import is_date


# -------------------------
# Time window helpers
# -------------------------

def within(now, start, end):
    """True if now is within the start and end period"""
    return start <= now <= end

def within_start_minutes(now, start, minutes: int) -> bool:
    """True if start is within n `minutes` of now."""
    return timedelta(0) <= (start - now) <= timedelta(minutes=minutes)


def within_minutes_after(now, start, minutes: int) -> bool:
    """True if now is within n `minutes` after start."""
    threshold = timedelta(minutes=minutes)
    delta = now - start
    return timedelta(0) <= delta <= threshold


# -------------------------
# Period classification helper
# -------------------------

def is_all_day(start, end) -> bool:
    """
    Returns True if event should be treated as all-day or invalid for timing logic.
    """
    if is_date(start):
        return True

    # guard against malformed data
    try:
        return (end - start).days >= 1
    except Exception:
        return False


# -------------------------
# Near helper
# -------------------------

def is_near_or_during(now, start, end, threshold_minutes: int) -> bool:
    """
    True if:
    - event is near start (within threshold)
    OR
    - now is inside event window
    """
    if is_all_day(start, end):
        return False

    near_start = within_start_minutes(now, start, threshold_minutes)
    in_event = within(now, start, end)

    return near_start or in_event