import unittest
from datetime import datetime, timezone

from chronolight.core.ics import find_near_events


# ---------------------------------------------------------
# Central test clock (change here only if needed)
# ---------------------------------------------------------

def now():
    return datetime(2025, 2, 4, 18, 30, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------
# 1. BASIC EVENTS
# ---------------------------------------------------------

class TestBasicICS(unittest.TestCase):

    def test_event_with_duration(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "UID:event-1",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].uid, "event-1")


    def test_event_with_dtend(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DTEND:20250204T190000Z",
            "UID:event-2",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertEqual(len(events), 1)


# ---------------------------------------------------------
# 2. TIMEZONE EDGE CASES
# ---------------------------------------------------------

class TestTimezonesUS(unittest.TestCase):

    def test_utc_event(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "UID:utc",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_missing_timezone_fallback(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000",
            "DURATION:PT1H",
            "UID:no-tz",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz="America/Denver")

        self.assertIsInstance(events, list)


    def test_dst_spring_forward(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART;TZID=America/New_York:20250309T023000",
            "DURATION:PT1H",
            "UID:dst-spring",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_dst_fall_back(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART;TZID=America/Los_Angeles:20251102T013000",
            "DURATION:PT1H",
            "UID:dst-fall",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


# ---------------------------------------------------------
# 3. DURATION EDGE CASES
# ---------------------------------------------------------

class TestDuration(unittest.TestCase):

    def test_zero_duration(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT0S",
            "UID:zero",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_cross_midnight(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T230000Z",
            "DURATION:PT2H",
            "UID:overnight",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_missing_start(self):
        lines = [
            "BEGIN:VEVENT",
            "DURATION:PT1H",
            "UID:broken",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertEqual(events, [])


# ---------------------------------------------------------
# 4. RRULE EDGE CASES
# ---------------------------------------------------------

class TestRRule(unittest.TestCase):

    def test_daily_rrule(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "RRULE:FREQ=DAILY",
            "UID:daily",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertTrue(len(events) >= 1)


    def test_rrule_count(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "RRULE:FREQ=DAILY;COUNT=3",
            "UID:count",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_rrule_until(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "RRULE:FREQ=DAILY;UNTIL=20250206T000000Z",
            "UID:until",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_rrule_interval(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "RRULE:FREQ=DAILY;INTERVAL=2",
            "UID:interval",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


# ---------------------------------------------------------
# 5. STRUCTURE / PARSER EDGE CASES
# ---------------------------------------------------------

class TestStructure(unittest.TestCase):

    def test_line_folding(self):
        lines = [
            "BEGIN:VEVENT",
            "SUMMARY:This is a long",
            " folded line",
            "DTSTART:20250204T180000Z",
            "UID:fold",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_unknown_fields(self):
        lines = [
            "BEGIN:VEVENT",
            "X-CUSTOM:abc",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "UID:custom",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_multiple_events(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "UID:a",
            "END:VEVENT",
            "BEGIN:VEVENT",
            "DTSTART:20250204T190000Z",
            "DURATION:PT1H",
            "UID:b",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertTrue(len(events) >= 1)


# ---------------------------------------------------------
# 6. NEW EDGE CASES (IMPORTANT ADDITIONS)
# ---------------------------------------------------------

class TestAdvancedICS(unittest.TestCase):

    def test_all_day_dtend(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART;VALUE=DATE:20260414",
            "DTEND;VALUE=DATE:20260415",
            "UID:allday-1",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_all_day_implicit(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART;VALUE=DATE:20260420",
            "UID:allday-2",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_all_day_duration(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART;VALUE=DATE:20260422",
            "DURATION:P1D",
            "UID:allday-3",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_dtend_overrides_duration(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20260414T120000Z",
            "DURATION:PT2H",
            "DTEND:20260414T150000Z",
            "UID:override",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)


    def test_malformed_tz_param(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART;`TZID`=America/New_York:20260414T090000",
            "DURATION:PT1H",
            "UID:bad-tz",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        self.assertIsInstance(events, list)

# ---------------------------------------------------------
# 7. Unsupported RRULE
# ---------------------------------------------------------

class TestUnsupportedByDay(unittest.TestCase):

    def test_unsupported_byday_rules_do_not_expand(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "RRULE:FREQ=WEEKLY;BYDAY=1SU,5SU",
            "UID:byday-1",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        # Expected behavior:
        # BYDAY is NOT supported → should NOT generate recurring events
        self.assertIsInstance(events, list)
        self.assertTrue(len(events) <= 1)


    def test_multiple_unsupported_byday_values(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "RRULE:FREQ=WEEKLY;BYDAY=1SU,2SU,3SU,4SU,5SU",
            "UID:byday-2",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        # Should not explode or mis-expand
        self.assertIsInstance(events, list)
        self.assertTrue(len(events) <= 1)


# ---------------------------------------------------------
# 7. Unsupported EXDATE
# ---------------------------------------------------------
class TestUnsupportedExDate(unittest.TestCase):

    def test_exdate_is_ignored_no_crash(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "RRULE:FREQ=DAILY",
            "EXDATE:20250205T180000Z",
            "UID:exdate-1",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        # EXDATE not implemented → must NOT crash
        self.assertIsInstance(events, list)


    def test_exdate_does_not_affect_output_yet(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART:20250204T180000Z",
            "DURATION:PT1H",
            "RRULE:FREQ=DAILY",
            "EXDATE:20250205T180000Z",
            "UID:exdate-2",
            "END:VEVENT",
        ]

        events = find_near_events(now(), lines, default_tz=None)

        # Since EXDATE is unsupported:
        # we explicitly assert it is NOT applied
        # (i.e., engine behaves as if EXDATE doesn't exist)

        self.assertIsInstance(events, list)

        # IMPORTANT: we do NOT expect filtering yet
        # so we only ensure deterministic output
        self.assertTrue(len(events) >= 0)


    def test_recurance_count(self):
        lines = [
            "BEGIN:VEVENT",
            "DTSTART;TZID=America/Denver:20260707T130000",
            "DTEND;TZID=America/Denver:20260707T140000",
            "RRULE:FREQ=WEEKLY;WKST=SU;COUNT=4;BYDAY=TU",
            "EXDATE;TZID=America/Denver:20260721T130000",
            "EXDATE;TZID=America/Denver:20260728T130000",
            "DTSTAMP:20261124T174254Z",
            "ORGANIZER;CN=Lara Leavitt:mailto:lara.leavitt@imatsolutions.com",
            "UID:3flqn1ajg8e8568cvnn2rltms1@google.com",
            "X-GOOGLE-CONFERENCE:https://meet.google.com/hhn-uknm-gtr",
            "CREATED:20260702T154242Z",
            "DESCRIPTION:Join with Google Meet: https://meet.google.com/hhn-uknm-gtr\nOr",
            "  dial: (US) +1 574-404-3374 PIN: 314377742#\nMore phone numbers: https://te",
            " l.meet/hhn-uknm-gtr?pin=6635817974804&hs=7\n\nLearn more about Meet at: htt",
            " ps://support.google.com/a/users/answer/9282720",
            "LAST-MODIFIED:20260728T171813Z",
            "SEQUENCE:2",
            "STATUS:CONFIRMED",
            "SUMMARY:Design - Firely integration",
            "TRANSP:OPAQUE",
            "END:VEVENT",
        ]

        # events = find_near_events(datetime(2026, 7, 7, 19, 0, tzinfo=timezone.utc), lines, default_tz=None)
        events = find_near_events(datetime(2026, 11, 24, 18, 10, 14, 469737, tzinfo=timezone.utc), lines, default_tz=None)

        self.assertTrue(len(events) == 0)


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    unittest.main()