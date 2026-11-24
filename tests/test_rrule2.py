
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import chronolight.core.ical.rrule as subject


class TestParseRRule(unittest.TestCase):

    def test_empty_rule(self):
        self.assertEqual({}, subject.parse_rrule(None))
        self.assertEqual({}, subject.parse_rrule(""))

    def test_daily_rule(self):
        rule = subject.parse_rrule("FREQ=DAILY")

        self.assertEqual("DAILY", rule["FREQ"])

    def test_interval(self):
        rule = subject.parse_rrule("FREQ=WEEKLY;INTERVAL=2")

        self.assertEqual(2, rule["INTERVAL"])

    def test_count(self):
        rule = subject.parse_rrule("FREQ=DAILY;COUNT=10")

        self.assertEqual(10, rule["COUNT"])

    def test_byday(self):
        rule = subject.parse_rrule("FREQ=WEEKLY;BYDAY=MO,WE,FR")

        self.assertEqual(["MO", "WE", "FR"], rule["BYDAY"])

    def test_multiple_parameters(self):
        rule = subject.parse_rrule(
            "FREQ=WEEKLY;INTERVAL=2;COUNT=5;BYDAY=TU,TH"
        )

        self.assertEqual("WEEKLY", rule["FREQ"])
        self.assertEqual(2, rule["INTERVAL"])
        self.assertEqual(5, rule["COUNT"])
        self.assertEqual(["TU", "TH"], rule["BYDAY"])

    def test_until(self):
        rule = subject.parse_rrule(
            "FREQ=DAILY;UNTIL=20250210T180000Z"
        )

        self.assertIsNotNone(rule["UNTIL"])


class TestMatchesByDay(unittest.TestCase):

    def test_no_byday_matches_every_day(self):
        self.assertTrue(subject.matches_byday(date(2025, 2, 4), None))

    def test_matching_weekday(self):
        # Tuesday
        self.assertTrue(
            subject.matches_byday(date(2025, 2, 4), ["TU"])
        )

    def test_non_matching_weekday(self):
        self.assertFalse(
            subject.matches_byday(date(2025, 2, 4), ["MO"])
        )

    def test_multiple_weekdays(self):
        self.assertTrue(
            subject.matches_byday(date(2025, 2, 4), ["MO", "TU", "WE"])
        )

        self.assertFalse(
            subject.matches_byday(date(2025, 2, 4), ["MO", "WE"])
        )

    def test_all_weekdays(self):
        for weekday in subject.WEEKDAY:
            with self.subTest(weekday=weekday):
                self.assertTrue(
                    subject.matches_byday(
                        date(2025, 2, 4),
                        [weekday, "TU"]
                    )
                )

    def test_unsupported_ordinal_byday(self):
        self.assertFalse(
            subject.matches_byday(date(2025, 2, 2), ["1SU"])
        )

    def test_unsupported_value(self):
        self.assertFalse(
            subject.matches_byday(date(2025, 2, 4), ["XX"])
        )


class TestUnsupportedByDay(unittest.TestCase):

    def test_none(self):
        self.assertFalse(subject.has_unsupported_byday(None))

    def test_empty(self):
        self.assertFalse(subject.has_unsupported_byday([]))

    def test_simple_weekdays(self):
        self.assertFalse(
            subject.has_unsupported_byday(["MO", "TU", "WE"])
        )

    def test_all_weekdays(self):
        self.assertFalse(
            subject.has_unsupported_byday(
                ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            )
        )

    def test_ordinal_weekdays(self):
        self.assertTrue(
            subject.has_unsupported_byday(["1SU", "2SU"])
        )

    def test_mixed_supported_and_unsupported(self):
        self.assertTrue(
            subject.has_unsupported_byday(["MO", "1SU"])
        )


class TestIsOccurrenceDate(unittest.TestCase):

    def setUp(self):
        # Tuesday, February 4, 2025
        self.start = datetime(2025, 2, 4, 18, tzinfo=timezone.utc)

    def matches(self, candidate, freq, interval=1, byday=None):
        return subject.is_occurrence_date(
            candidate,
            self.start,
            freq,
            interval,
            byday
        )

    # DTSTART

    def test_start_date_is_occurrence(self):
        self.assertTrue(
            self.matches(date(2025, 2, 4), "DAILY")
        )

    def test_date_before_start(self):
        self.assertFalse(
            self.matches(date(2025, 2, 3), "DAILY")
        )

    # DAILY

    def test_daily(self):
        self.assertTrue(
            self.matches(date(2025, 2, 5), "DAILY")
        )

    def test_daily_interval_two(self):
        self.assertTrue(
            self.matches(date(2025, 2, 6), "DAILY", interval=2)
        )

        self.assertFalse(
            self.matches(date(2025, 2, 5), "DAILY", interval=2)
        )

        self.assertTrue(
            self.matches(date(2025, 2, 8), "DAILY", interval=2)
        )

    def test_daily_interval_three(self):
        self.assertTrue(
            self.matches(date(2025, 2, 7), "DAILY", interval=3)
        )

        self.assertFalse(
            self.matches(date(2025, 2, 8), "DAILY", interval=3)
        )

    # WEEKLY

    def test_weekly_same_weekday(self):
        self.assertTrue(
            self.matches(date(2025, 2, 11), "WEEKLY", byday=["TU"])
        )

    def test_weekly_different_weekday(self):
        self.assertFalse(
            self.matches(date(2025, 2, 12), "WEEKLY", byday=["TU"])
        )

    def test_weekly_multiple_weekdays(self):
        self.assertTrue(
            self.matches(date(2025, 2, 6), "WEEKLY", byday=["TU", "TH"])
        )

        self.assertFalse(
            self.matches(date(2025, 2, 7), "WEEKLY", byday=["TU", "TH"])
        )

    def test_weekly_interval_two(self):
        self.assertTrue(
            self.matches(
                date(2025, 2, 18),
                "WEEKLY",
                interval=2,
                byday=["TU"]
            )
        )

        self.assertFalse(
            self.matches(
                date(2025, 2, 11),
                "WEEKLY",
                interval=2,
                byday=["TU"]
            )
        )

    def test_weekly_interval_three(self):
        self.assertTrue(
            self.matches(
                date(2025, 2, 25),
                "WEEKLY",
                interval=3,
                byday=["TU"]
            )
        )

    # MONTHLY

    def test_monthly_same_day(self):
        self.assertTrue(
            self.matches(date(2025, 3, 4), "MONTHLY")
        )

    def test_monthly_different_day(self):
        self.assertFalse(
            self.matches(date(2025, 3, 5), "MONTHLY")
        )

    def test_monthly_interval_two(self):
        self.assertTrue(
            self.matches(date(2025, 4, 4), "MONTHLY", interval=2)
        )

        self.assertFalse(
            self.matches(date(2025, 3, 4), "MONTHLY", interval=2)
        )

    def test_monthly_interval_three(self):
        self.assertTrue(
            self.matches(date(2025, 5, 4), "MONTHLY", interval=3)
        )

    def test_monthly_byday(self):
        # First Tuesday in March 2025
        self.assertTrue(
            self.matches(date(2025, 3, 4), "MONTHLY", byday=["TU"])
        )

        self.assertFalse(
            self.matches(date(2025, 3, 5), "MONTHLY", byday=["TU"])
        )

    # Unsupported

    def test_unsupported_frequency(self):
        self.assertFalse(
            self.matches(date(2025, 2, 5), "YEARLY")
        )

    def test_unsupported_ordinal_byday(self):
        self.assertFalse(
            self.matches(
                date(2025, 2, 2),
                "WEEKLY",
                byday=["1SU"]
            )
        )

    # Input normalization

    def test_datetime_candidate(self):
        self.assertTrue(
            self.matches(
                datetime(2025, 2, 6, 12, tzinfo=timezone.utc),
                "WEEKLY",
                byday=["TU", "TH"]
            )
        )


class TestWithinCount(unittest.TestCase):

    def setUp(self):
        self.start = datetime(2025, 2, 4, 18, tzinfo=timezone.utc)

    def count(self, candidate, freq, count, interval=1, byday=None):
        return subject.within_count(
            candidate,
            self.start,
            freq,
            interval,
            byday,
            count
        )

    def test_none_count_is_unlimited(self):
        self.assertTrue(
            self.count(date(2025, 3, 4), "DAILY", None)
        )

    def test_daily_count_first_occurrence(self):
        self.assertTrue(
            self.count(date(2025, 2, 4), "DAILY", 1)
        )

    def test_daily_count_last_occurrence(self):
        self.assertTrue(
            self.count(date(2025, 2, 6), "DAILY", 3)
        )

    def test_daily_count_exceeded(self):
        self.assertFalse(
            self.count(date(2025, 2, 7), "DAILY", 3)
        )

    def test_daily_count_with_interval(self):
        self.assertTrue(
            self.count(date(2025, 2, 8), "DAILY", 3, interval=2)
        )

        self.assertFalse(
            self.count(date(2025, 2, 10), "DAILY", 3, interval=2)
        )

    def test_weekly_count(self):
        self.assertTrue(
            self.count(
                date(2025, 2, 18),
                "WEEKLY",
                3,
                byday=["TU"]
            )
        )

        self.assertFalse(
            self.count(
                date(2025, 2, 25),
                "WEEKLY",
                3,
                byday=["TU"]
            )
        )

    def test_weekly_count_with_interval(self):
        self.assertTrue(
            self.count(
                date(2025, 2, 18),
                "WEEKLY",
                2,
                interval=2,
                byday=["TU"]
            )
        )

        self.assertFalse(
            self.count(
                date(2025, 3, 4),
                "WEEKLY",
                2,
                interval=2,
                byday=["TU"]
            )
        )

    def test_monthly_count(self):
        self.assertTrue(
            self.count(date(2025, 4, 4), "MONTHLY", 3)
        )

        self.assertFalse(
            self.count(date(2025, 5, 4), "MONTHLY", 3)
        )

    def test_count_one_does_not_allow_next_occurrence(self):
        self.assertFalse(
            self.count(date(2025, 2, 5), "DAILY", 1)
        )


class TestRecurringEvent(unittest.TestCase):

    def setUp(self):
        self.start = datetime(2025, 2, 4, 18, tzinfo=timezone.utc)
        self.end = datetime(2025, 2, 4, 19, tzinfo=timezone.utc)

        self.duration = timedelta(hours=1)

    def evaluate(self, now, rule):
        with (
            patch.object(subject, "resolve_duration", return_value=self.duration),
            patch.object(subject, "resolve_datetime", return_value="START"),
            patch.object(subject, "find_end", return_value="END"),
        ):
            return subject.recurring_event(
                now,
                self.start,
                self.end,
                self.duration,
                rule,
                {}
            )

    def test_matching_daily_event(self):
        result = self.evaluate(
            date(2025, 2, 5),
            "FREQ=DAILY"
        )

        self.assertEqual(("START", "END"), result)

    def test_non_matching_event(self):
        result = self.evaluate(
            date(2025, 2, 5),
            "FREQ=WEEKLY;BYDAY=TU"
        )

        self.assertIsNone(result)

    def test_daily_count_allows_occurrence(self):
        result = self.evaluate(
            date(2025, 2, 6),
            "FREQ=DAILY;COUNT=3"
        )

        self.assertEqual(("START", "END"), result)

    def test_daily_count_rejects_occurrence(self):
        result = self.evaluate(
            date(2025, 2, 7),
            "FREQ=DAILY;COUNT=3"
        )

        self.assertIsNone(result)

    def test_weekly_count_allows_occurrence(self):
        result = self.evaluate(
            date(2025, 2, 18),
            "FREQ=WEEKLY;BYDAY=TU;COUNT=3"
        )

        self.assertEqual(("START", "END"), result)

    def test_weekly_count_rejects_occurrence(self):
        result = self.evaluate(
            date(2025, 2, 25),
            "FREQ=WEEKLY;BYDAY=TU;COUNT=3"
        )

        self.assertIsNone(result)

    def test_until_allows_occurrence_on_until_date(self):
        result = self.evaluate(
            date(2025, 2, 10),
            "FREQ=DAILY;UNTIL=20250210T180000Z"
        )

        self.assertEqual(("START", "END"), result)

    def test_until_rejects_occurrence_after_until(self):
        result = self.evaluate(
            date(2025, 2, 11),
            "FREQ=DAILY;UNTIL=20250210T180000Z"
        )

        self.assertIsNone(result)

    def test_unsupported_byday_does_not_expand(self):
        result = self.evaluate(
            date(2025, 2, 9),
            "FREQ=WEEKLY;BYDAY=1SU,2SU,3SU,4SU,5SU"
        )

        self.assertIsNone(result)

    def test_unsupported_frequency(self):
        result = self.evaluate(
            date(2025, 2, 5),
            "FREQ=YEARLY"
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
