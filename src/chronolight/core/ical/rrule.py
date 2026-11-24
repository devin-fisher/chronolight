from chronolight.core.ical.deltatime import day_offset
from chronolight.core.ical.duration import find_end, resolve_duration

from chronolight.core.ical.datetime import parse_datatime, to_date, resolve_datetime, normalize_dt, UTC

# ----------------------------
# RRULE parsing
# ----------------------------

WEEKDAY = {
    "MO": 0, "TU": 1, "WE": 2,
    "TH": 3, "FR": 4, "SA": 5, "SU": 6
}


def parse_rrule(rrule_str):
    if not rrule_str:
        return {}

    rule = {}
    for part in rrule_str.split(";"):
        k, v = part.split("=")

        if k == "BYDAY":
            rule[k] = v.split(",")
        elif k in ("COUNT", "INTERVAL"):
            rule[k] = int(v)
        elif k == "UNTIL":
            rule["UNTIL"] = to_date(
                parse_datatime(v, UTC)
            )
        else:
            rule[k] = v

    return rule


# ----------------------------
# Helpers
# ----------------------------

def matches_byday(now, byday):
    if not byday:
        return True

    for d in byday:
        if d not in WEEKDAY:
            print("WARN: unsupported BYDAY:", d)
            return False  # or skip it depending on your preference

    return now.weekday() in [WEEKDAY[d] for d in byday]



def week_index(dtstart, now):
    dtstart = to_date(dtstart)
    now = to_date(now)

    return (now - dtstart).days // 7


def month_index(dtstart, dt):
    return (dt.year - dtstart.year) * 12 + (dt.month - dtstart.month)


# ----------------------------
# Core evaluator
# ----------------------------

def recurring_event(now, dtstart, dtend, duration, rrule_val, _rrule_params):
    """
    Returns (start, end) if event is happening today (from now), else None.
    """
    now = to_date(now)

    rule = parse_rrule(rrule_val)

    until = rule.get("UNTIL")
    count = rule.get("COUNT")

    if until is not None and until and now > until:
        return None

    freq = rule.get("FREQ")
    interval = int(rule.get("INTERVAL", 1))
    byday = rule.get("BYDAY")

    if not is_occurrence_date(now, dtstart, freq, interval, byday):
        return None

    if not within_count(now, dtstart, freq, interval, byday,
                        int(count) if count is not None else None):
        return None

    duration = resolve_duration(dtstart, dtend, duration)

    start = resolve_datetime(now, dtstart)
    end = find_end(start, None, duration)

    return start, end


def within_count(now, dtstart, freq, interval, byday, count):
    if count is None:
        return True

    occurrences = 0
    days = (now - dtstart.date()).days

    for offset in range(days + 1):
        # candidate = dtstart.date() + timedelta(days=offset)
        candidate = day_offset(dtstart, offset)

        if is_occurrence_date(candidate, dtstart, freq, interval, byday):
            occurrences += 1

            if occurrences > count:
                return False

    return True

def has_unsupported_byday(byday):
    if not byday:
        return False

    return any(
        value not in {"MO", "TU", "WE", "TH", "FR", "SA", "SU"}
        for value in byday
    )

def is_occurrence_date(candidate, dtstart, freq, interval, byday):
    start_date = to_date(dtstart)
    candidate = to_date(candidate)

    if has_unsupported_byday(byday):
        return False

    if candidate < start_date:
        return False

    # DTSTART is the first occurrence.
    if candidate == start_date:
        return True

    if freq == "DAILY":
        days = (candidate - start_date).days
        return days % interval == 0

    elif freq == "WEEKLY":
        weeks = week_index(dtstart, candidate)

        return (
            weeks % interval == 0
            and matches_byday(candidate, byday)
        )

    elif freq == "MONTHLY":
        months = month_index(dtstart, candidate)

        if months % interval != 0:
            return False

        if byday:
            return matches_byday(candidate, byday)

        return candidate.day == start_date.day

    return False