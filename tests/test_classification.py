import unittest
from datetime import datetime, timezone

from chronolight.core.classification import ScheduleClassification
from chronolight.core.models import EventTuple


# ---------------------------------------------------------
# Test clock (single place to control time)
# ---------------------------------------------------------

def now():
    return datetime(2025, 2, 4, 18, 30, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------
# Helper event factory
# ---------------------------------------------------------

# class FakeEvent:
#     def __init__(self, start, end, uid="x"):
#         self.start = start
#         self.end = end
#         self.uid = uid


# ---------------------------------------------------------
# classify_event tests
# ---------------------------------------------------------

class TestClassifyEvent(unittest.TestCase):

    def setUp(self):
        self.c = ScheduleClassification()

    def test_all_day_returns_idle(self):
        start = datetime(2025, 2, 4, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 2, 5, 0, 0, 0, tzinfo=timezone.utc)

        state = self.c.classify_event(now(), start, end)
        self.assertEqual(state, ScheduleClassification.IDLE)


    def test_event_started(self):
        start = datetime(2025, 2, 4, 18, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc)

        state = self.c.classify_event(now(), start, end)
        self.assertIn(state, [
            ScheduleClassification.STARTED,
            ScheduleClassification.STARTING
        ])


    def test_event_upcoming(self):
        start = datetime(2025, 2, 4, 18, 40, 0, tzinfo=timezone.utc)
        end = datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc)

        state = self.c.classify_event(now(), start, end)
        self.assertIn(state, [
            ScheduleClassification.UPCOMING,
            ScheduleClassification.SOON,
            ScheduleClassification.IDLE
        ])


    def test_event_far_future(self):
        start = datetime(2025, 2, 5, 18, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 2, 5, 19, 0, 0, tzinfo=timezone.utc)

        state = self.c.classify_event(now(), start, end)
        self.assertEqual(state, ScheduleClassification.IDLE)


# ---------------------------------------------------------
# classify_events tests (IMPORTANT LOGIC)
# ---------------------------------------------------------

class TestClassifyEvents(unittest.TestCase):

    def setUp(self):
        self.c = ScheduleClassification()

    def test_empty_events(self):
        state, uid = ScheduleClassification.classify_events(
            self.c, now(), []
        )

        self.assertEqual(state, ScheduleClassification.IDLE)
        self.assertIsNone(uid)


    def test_single_event(self):
        events = [
            EventTuple(
                datetime(2025, 2, 4, 18, 0, 0, tzinfo=timezone.utc),
                datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc),
                uid="a",
            )
        ]

        state, uid = ScheduleClassification.classify_events(
            self.c, now(), events
        )

        self.assertEqual(uid, "a")
        self.assertIn(state, [
            ScheduleClassification.STARTED,
            ScheduleClassification.STARTING,
            ScheduleClassification.SOON,
            ScheduleClassification.UPCOMING,
        ])


    def test_most_urgent_event_wins(self):
        events = [
            EventTuple(
                datetime(2025, 2, 5, 18, 0, 0, tzinfo=timezone.utc),
                datetime(2025, 2, 5, 19, 0, 0, tzinfo=timezone.utc),
                uid="future",
            ),
            EventTuple(
                datetime(2025, 2, 4, 18, 10, 0, tzinfo=timezone.utc),
                datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc),
                uid="current",
            ),
        ]

        state, uid = ScheduleClassification.classify_events(
            self.c, now(), events
        )

        # should pick the more urgent event (current)
        self.assertEqual(uid, "current")


    def test_all_day_event_is_ignored(self):
        events = [
            EventTuple(
                datetime(2025, 2, 4, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2025, 2, 5, 0, 0, 0, tzinfo=timezone.utc),
                uid="allday",
            )
        ]

        state, uid = ScheduleClassification.classify_events(
            self.c, now(), events
        )

        self.assertEqual(state, ScheduleClassification.IDLE)


    def test_mixed_events_priority(self):
        events = [
            EventTuple(
                datetime(2025, 2, 6, 18, 0, 0, tzinfo=timezone.utc),
                datetime(2025, 2, 6, 19, 0, 0, tzinfo=timezone.utc),
                uid="far",
            ),
            EventTuple(
                datetime(2025, 2, 4, 18, 20, 0, tzinfo=timezone.utc),
                datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc),
                uid="near",
            ),
        ]

        state, uid = ScheduleClassification.classify_events(
            self.c, now(), events
        )

        self.assertEqual(uid, "near")


class TestClassificationEdgeCases(unittest.TestCase):

    def setUp(self):
        self.c = ScheduleClassification()

    # -------------------------------------------------
    # 1. BOUNDARY CONDITIONS (OFF BY ONE MINUTE STYLE BUGS)
    # -------------------------------------------------

    def test_exact_start_boundary(self):
        now_dt = datetime(2025, 2, 4, 18, 0, 0, tzinfo=timezone.utc)

        start = datetime(2025, 2, 4, 18, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc)

        state = self.c.classify_event(now_dt, start, end)

        self.assertIn(state, [
            ScheduleClassification.STARTED,
            ScheduleClassification.STARTING,
        ])


    def test_exact_end_boundary(self):
        now_dt = datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc)

        start = datetime(2025, 2, 4, 18, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc)

        state = self.c.classify_event(now_dt, start, end)

        self.assertEqual(state, ScheduleClassification.STARTED)


    # -------------------------------------------------
    # 2. ZERO / INVALID DURATION EDGE CASES
    # -------------------------------------------------

    def test_zero_duration_event(self):
        start = datetime(2025, 2, 4, 18, 0, 0, tzinfo=timezone.utc)
        end = start

        state = self.c.classify_event(now(), start, end)

        self.assertEqual(state, ScheduleClassification.IDLE)


    def test_end_before_start(self):
        start = datetime(2025, 2, 4, 19, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 2, 4, 18, 0, 0, tzinfo=timezone.utc)

        state = self.c.classify_event(now(), start, end)

        # should fail safely, not crash or misclassify
        self.assertIn(state, [
            ScheduleClassification.IDLE,
            ScheduleClassification.UPCOMING,
        ])


    # -------------------------------------------------
    # 3. OVERLAPPING EVENTS (PRIORITY COLLISIONS)
    # -------------------------------------------------

    def test_identical_priority_events(self):
        events = [
            EventTuple(
                datetime(2025, 2, 4, 18, 20, tzinfo=timezone.utc),
                datetime(2025, 2, 4, 19, 0, tzinfo=timezone.utc),
                uid="a",
            ),
            EventTuple(
                datetime(2025, 2, 4, 18, 20, tzinfo=timezone.utc),
                datetime(2025, 2, 4, 19, 0, tzinfo=timezone.utc),
                uid="b",
            ),
        ]

        state, uid = ScheduleClassification.classify_events(self.c, now(), events)

        # deterministic but arbitrary winner allowed
        self.assertIn(uid, ["a", "b"])


    # -------------------------------------------------
    # 4. VERY SHORT WINDOWS (THRESHOLD BREAKERS)
    # -------------------------------------------------

    def test_one_minute_event(self):
        start = datetime(2025, 2, 4, 18, 29, tzinfo=timezone.utc)
        end = datetime(2025, 2, 4, 18, 30, tzinfo=timezone.utc)

        state = self.c.classify_event(now(), start, end)

        self.assertIn(state, [
            ScheduleClassification.STARTED,
            ScheduleClassification.STARTING,
        ])


    # -------------------------------------------------
    # 5. THRESHOLD EDGE CASES
    # -------------------------------------------------

    def test_upcoming_vs_soon_boundary(self):
        start = datetime(2025, 2, 4, 18, 31, tzinfo=timezone.utc)

        state = self.c.classify_event(now(), start, start)

        self.assertIn(state, [
            ScheduleClassification.SOON,
            ScheduleClassification.UPCOMING,
            ScheduleClassification.IDLE,
        ])


    # -------------------------------------------------
    # 6. MULTI-EVENT STABILITY UNDER NOISE
    # -------------------------------------------------

    def test_many_events_noise_stability(self):
        events = []

        # noisy far-future events
        for i in range(20):
            events.append(EventTuple(
                datetime(2025, 2, 10, 18, i % 60, tzinfo=timezone.utc),
                datetime(2025, 2, 10, 19, 0, tzinfo=timezone.utc),
                uid=f"f{i}",
            ))

        # one near event
        events.append(EventTuple(
            datetime(2025, 2, 4, 18, 25, tzinfo=timezone.utc),
            datetime(2025, 2, 4, 19, 0, tzinfo=timezone.utc),
            uid="near",
        ))

        state, uid = ScheduleClassification.classify_events(self.c, now(), events)

        self.assertEqual(uid, "near")

# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    unittest.main()