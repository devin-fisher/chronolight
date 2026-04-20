from chronolight.core.ical.datetime import is_date

try:
    from datetime import timedelta
except ImportError:
    from adafruit_datetime import timedelta

def parse_duration(dur_value, dur_params):
    """
    Parse an ICS duration string (simplified P[nD]T[nH][nM]) into timedelta.
    Examples:
        "P1DT2H30M" → 1 day, 2 hours, 30 minutes
    Returns:
        datetime.timedelta
    """
    days = hours = minutes = 0
    num = ""

    for c in dur_value:
        if c == "P":
            continue
        elif c == "T":
            continue
        elif c.isdigit():
            num += c
        else:
            if c == "D":
                days = int(num)
            elif c == "H":
                hours = int(num)
            elif c == "M":
                minutes = int(num)
            num = ""

    return timedelta(days=days, hours=hours, minutes=minutes)

def resolve_duration(dtstart, dtend=None, duration=None):
    """
    ICS-style duration resolution with sane defaults.
    """
    if is_date(dtstart):
        return timedelta(days=1)

    if dtend:
        return dtend - dtstart

    if duration:
        return duration

    # Default timed event
    return timedelta(hours=1)

def find_end(start, end, duration):
    if not end:
        if not duration:
            if is_date(start):
                duration = timedelta(days=1)
            else:
                duration = timedelta(hours=1)

        end = start + duration
    return end