from collections import namedtuple

# -------------------------------------------------
# State constants
# -------------------------------------------------
IDLE: int = 0
UPCOMING: int = 1
SOON: int = 2
STARTING: int = 3
STARTED: int = 4

StateTuple = namedtuple("State", ["classification", "uid", "descr", "ignored_uids", "near_events"])

InputTuple = namedtuple("Input", ["ignore"])

EventTuple = namedtuple("Event", ["start", "end", "uid", "summary", "cal_name"])

IgnoreTuple = namedtuple("Ignore", ["uid", "timestamp"])