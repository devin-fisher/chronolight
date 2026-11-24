import json

from chronolight.core.classification import ScheduleClassification


def state_to_str(val):
    return f"State({ScheduleClassification.name(val.classification)}, {val.uid}, {[(item.uid, str(item.timestamp)) for item in val.ignored_uids]})"

def state_to_json(val):
    rtn = dict()
    rtn['classification'] = ScheduleClassification.name(val.classification)
    rtn['uid'] =  str(val.uid) if val.uid is not None else ""
    rtn['near_events'] = [
        f"{event.start.astimezone():%-I:%M %p} -- {event.end.astimezone():%-I:%M %p}: {event.summary} ({event.cal_name})"
        for event in val.near_events
    ]

    return json.dumps(rtn)