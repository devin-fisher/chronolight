from chronolight.core.ical.deltatime import (
    within_start_minutes,
    within_minutes_after,
    within,
    is_all_day,
)

class Colors:
    OFF = (0, 0, 0)

    IDLE = (0, 64, 0)

    UPCOMING = (255, 100, 0)

    SOON = (255, 100, 0)

    STARTING = (255, 0, 0)

    STARTED = (255, 0, 0)


class ScheduleClassification:
    """
    Lightweight state machine for meeting lifecycle classification.

    States:
        IDLE      : no relevant event
        UPCOMING  : event is in the future
        SOON      : event is approaching
        STARTING  : immediate start window
        STARTED   : event is currently active

    Designed for:
    - CircuitPython compatibility
    - integer-based states (no Enum dependency)
    - deterministic testing
    """

    # -------------------------------------------------
    # State constants
    # -------------------------------------------------
    IDLE: int = 0
    UPCOMING: int = 1
    SOON: int = 2
    STARTING: int = 3
    STARTED: int = 4

    # -------------------------------------------------
    # Initialization
    # -------------------------------------------------
    def __init__(
        self,
        starting_threshold: int = 3,
        upcoming_threshold: int = 15,
        soon_threshold: int = 2,
    ) -> None:
        self.starting_threshold: int = starting_threshold
        self.upcoming_threshold: int = upcoming_threshold
        self.soon_threshold: int = soon_threshold

    # -------------------------------------------------
    # Utility
    # -------------------------------------------------
    @staticmethod
    def name(value: int) -> str:
        names: dict[int, str] = {
            ScheduleClassification.IDLE: "IDLE",
            ScheduleClassification.UPCOMING: "UPCOMING",
            ScheduleClassification.SOON: "SOON",
            ScheduleClassification.STARTING: "STARTING",
            ScheduleClassification.STARTED: "STARTED",
        }
        return names.get(value, "UNKNOWN")

    # -------------------------------------------------
    # Core classification
    # -------------------------------------------------
    def classify_event(
        self,
        now,
        start,
        end,
    ) -> int:
        """
        Classify a single event relative to `now`.

        Args:
            now: current datetime
            start: event start datetime
            end: event end datetime

        Returns:
            int: classification state
        """

        # All-day events are ignored for active classification
        if is_all_day(start, end):
            return ScheduleClassification.IDLE

        # Currently active event
        if within(now, start, end):
            if within_minutes_after(now, start, self.starting_threshold):
                return ScheduleClassification.STARTING
            return ScheduleClassification.STARTED

        # Future windows
        if within_start_minutes(now, start, self.soon_threshold):
            return ScheduleClassification.SOON

        if within_start_minutes(now, start, self.upcoming_threshold):
            return ScheduleClassification.UPCOMING

        return ScheduleClassification.IDLE

    # -------------------------------------------------
    # Aggregate classification
    # -------------------------------------------------
    @staticmethod
    def classify_events(
        classifier: "ScheduleClassification",
        now,
        events,
        ignored_uids=None
    ):
        """
        Determine the most important event state.

        Args:
            classifier: ScheduleClassification instance
            now: current datetime
            events: iterable of events with .start, .end, .uid
            ignored_uids: uid that should be ignored in clasification

        Returns:
            (state, uid) of highest priority event, or (IDLE, None)
        """

        def _classify(event):
            if event.uid in ignored_uids:
                return ScheduleClassification.IDLE

            return classifier.classify_event(now, event.start, event.end)

        if ignored_uids is None:
            ignored_uids = []

        if not events:
            return ScheduleClassification.IDLE, None

        most_important_event = max(
            events,
            key=_classify,
        )

        if most_important_event.uid in ignored_uids:
            return ScheduleClassification.IDLE, None

        state: int = classifier.classify_event(
            now,
            most_important_event.start,
            most_important_event.end,
        )

        return state, most_important_event.uid