from collections import namedtuple

StateTuple = namedtuple("State", ["classification", "uid", "ignored_uids", "near_events"])

InputTuple = namedtuple("Input", ["ignore"])

EventTuple = namedtuple("Event", ["start", "end", "uid"])