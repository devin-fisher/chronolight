from chronolight.core.ical.datetime import parse_datatime
from chronolight.core.ical.deltatime import is_near_or_during
from chronolight.core.ical.duration import parse_duration, find_end
from chronolight.core.ical.rrule import recurring_event

from chronolight.core.classification import ScheduleClassification
from chronolight.core.models import EventTuple


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

def add_if_near(now, dtstart, dtend, duration, uid, events):
    # Calculate end from duration if end is None
    dtend = find_end(dtstart, dtend, duration)

    if is_near_or_during(now, dtstart, dtend, 90):
        events.append(EventTuple(dtstart, dtend, uid))


def find_near_events(now, lines, default_tz):
    in_event = False
    dtstart = dtend = duration = uid = rrule = None
    events = []

    it = iter(lines)
    try:
        preview_line = next(it)
    except StopIteration:
        preview_line = None

    # for raw in lines:
    while preview_line is not None:
        try:
            raw = next(it)
        except StopIteration:
            raw = None

        if raw is not None:
            if raw.startswith(" ") or raw.startswith("\t"):
                preview_line = preview_line + raw[1:]
                continue
            else:
                line = preview_line
                preview_line = raw
        else:
            line = preview_line
            preview_line = None

        if line.startswith("#"):
            continue

        if not line.strip():
            continue

        field, value, params = parse_ics_line(line)

        # Event boundaries
        if field == "BEGIN" and value == "VEVENT":
            in_event = True
            dtstart = dtend = duration = uid = rrule = None

        elif field == "END" and value == "VEVENT":
            if dtstart:
                add_if_near(now, dtstart, dtend, duration, uid, events)
                if rrule:
                    event = recurring_event(now, dtstart, dtend, duration, rrule, {})
                    if event:
                        add_if_near(now, event[0], event[1], None, uid, events)

            in_event = False

        elif in_event:
            if field == "DTSTART":
                dtstart = parse_datatime(value, default_tz, params.get("TZID", None))
            elif field == "DTEND":
                dtend = parse_datatime(value, default_tz, params.get("TZID", None))
            elif field == "DURATION":
                duration = parse_duration(value, params)
            elif field == "UID":
                uid = value
            elif field == "RRULE":
                rrule = value

    return events