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
    dtstart = normalize_dt(dtstart)
    now = normalize_dt(now)

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

    until = rule.get("UNTIL", None)

    if until is not None and until and now > until:
        return None

    freq = rule.get("FREQ")
    interval = rule.get("INTERVAL", 1)
    byday = rule.get("BYDAY")

    # Resolve duration once
    duration = resolve_duration(dtstart, dtend, duration)

    # ----------------------------
    # DAILY
    # ----------------------------
    if freq == "DAILY":
        days = (now - dtstart.date()).days
        if days < 0 or days % interval != 0:
            return None

    # ----------------------------
    # WEEKLY
    # ----------------------------
    elif freq == "WEEKLY":
        weeks = week_index(dtstart, now)
        if weeks < 0 or weeks % interval != 0:
            return None

        if not matches_byday(now, byday):
            return None

    # ----------------------------
    # MONTHLY
    # ----------------------------
    elif freq == "MONTHLY":
        months = month_index(dtstart, now)
        if months < 0 or months % interval != 0:
            return None

        # simplified: same day-of-month unless BYDAY is used
        if byday:
            if not matches_byday(now, byday):
                return None
        else:
            if now.day != dtstart.day:
                return None

    else:
        return None  # unsupported FREQ

    # ----------------------------
    # Build occurrence for "now"
    # ----------------------------

    start = resolve_datetime(now, dtstart)
    end = find_end(start, None, duration)

    return start, end