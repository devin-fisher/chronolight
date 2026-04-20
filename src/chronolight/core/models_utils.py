from chronolight.core.classification import ScheduleClassification


def state_to_str(val):
    return f"State({ScheduleClassification.name(val.classification)}, {val.uid}, {val.ignored_uids})"