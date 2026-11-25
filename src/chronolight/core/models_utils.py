import json

from chronolight.core.models import IDLE, UPCOMING, SOON, STARTING, STARTED


def name(value: int) -> str:
    names: dict[int, str] = {
        IDLE: "IDLE",
        UPCOMING: "UPCOMING",
        SOON: "SOON",
        STARTING: "STARTING",
        STARTED: "STARTED",
    }
    return names.get(value, "UNKNOWN")

def state_to_str(val):
    return f"State({name(val.classification)}, {val.uid}, {val.descr}, {[(item.uid, str(item.timestamp)) for item in val.ignored_uids]}, {[event_to_str(event) for event in val.near_events]})"

def state_to_json(val):
    rtn = dict()
    rtn['classification'] = name(val.classification)
    rtn['uid'] =  str(val.uid) if val.uid is not None else ""
    rtn['descr'] = str(val.descr) if val.descr is not None else ""
    rtn['near_events'] = [
        event_to_str(event) for event in val.near_events
    ]

    return json.dumps(rtn)

def event_to_str(val):
    return f"{val.start.astimezone():%-I:%M %p} -- {val.end.astimezone():%-I:%M %p}: {val.summary} ({val.cal_name})"