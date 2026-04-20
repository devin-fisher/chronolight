try:
    from datetime import datetime, timedelta, timezone, date
except ImportError:
    from adafruit_datetime import datetime, timedelta, timezone, date


UTC = timezone.utc

# ---------- Time helpers ----------

TZ_OFFSETS = {
    "America/Los_Angeles": -8,
    "America/Denver": -7,
    "America/Chicago": -6,
    "America/New_York": -5,
    "America/Anchorage": -9,
    "Pacific/Honolulu": -10,
}

DST_EXEMPT = {
    "Pacific/Honolulu",
}
# ----- Parse

def parse_ics_line(line: str):
    """
    Parse a single ICS property line into a structured dict.

    Example input:
        DTSTART;TZID=America/Denver:20260414T090000

    Returns:
        {
            "name": "DTSTART",
            "params": {"TZID": "America/Denver"},
            "value": "20260414T090000"
        }
    """

    if ":" not in line:
        raise ValueError(f"Invalid ICS line: {line}")

    header, value = line.split(":", 1)

    # ----------------------------
    # Parse name + params
    # ----------------------------
    parts = header.split(";")

    name = parts[0].strip().upper()
    params = {}

    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.strip().upper()] = v.strip()

    return name, value.strip(), params


# ---- DST rules (US) ----
def _second_sunday_march(year):
    d = datetime(year, 3, 8)
    return d + timedelta(days=(6 - d.weekday()))

def _first_sunday_november(year):
    d = datetime(year, 11, 1)
    return d + timedelta(days=(6 - d.weekday()))

def _is_dst(dt):
    start = _second_sunday_march(dt.year).replace(hour=2)
    end = _first_sunday_november(dt.year).replace(hour=2)
    return start <= dt < end


# ---- Convert US local -> UTC ----
def _to_utc_us(dt, tzid):
    base = TZ_OFFSETS.get(tzid, -7)  # default: Denver

    if tzid in DST_EXEMPT:
        offset = base
    else:
        offset = base + (1 if _is_dst(dt) else 0)

    local_tz = timezone(timedelta(hours=offset))
    return (dt - local_tz.utcoffset(dt)).replace(tzinfo=UTC)


# ---- Main parser ----
def parse_datatime(val, default_tz, tzid=None):
    val = val.strip()

    # UTC case
    is_utc = False
    if val.endswith("Z"):
        is_utc = True
        val = val[:-1]

    year = int(val[0:4])
    month = int(val[4:6])
    day = int(val[6:8])

    if "T" in val:
        hour = int(val[9:11])
        minute = int(val[11:13])
        second = int(val[13:15])
    else:
        return date(year, month, day)
        # hour = minute = second = 0
        # is_utc = True # no time data

    dt = datetime(year, month, day, hour, minute, second)

    # ---- OUTPUT ALWAYS UTC ----

    if is_utc:
        return dt.replace(tzinfo=UTC)

    if tzid:
        return _to_utc_us(dt, tzid)

    # fallback: assume Denver
    return _to_utc_us(dt, default_tz)

# ---- Converters  ----

def normalize_dt(x):
    x = to_datetime(x)
    if hasattr(x, "tzinfo") and x.tzinfo is not None:
        x = x.replace(tzinfo=None)
    return x

def to_datetime(dt):
    if isinstance(dt, datetime):
        return dt
    if isinstance(dt, date):
        return datetime(dt.year, dt.month, dt.day)

    raise TypeError("expected date or datetime")


def to_date(dt):
    if type(dt) is date:
        return dt
    else:
        return dt.date()

def resolve_datetime(date_dt, time_dt):
    return datetime(
        date_dt.year,
        date_dt.month,
        date_dt.day,
        getattr(time_dt, "hour", 0),
        getattr(time_dt, "minute", 0),
        getattr(time_dt, "second", 0),
        tzinfo=getattr(time_dt, "tzinfo", timezone.utc),
    )

def is_date(dt):
    return type(dt) is date