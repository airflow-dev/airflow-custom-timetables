"""Holiday-calendar behaviour for BusinessDayOfMonth and MonthlyLastDayExceptWeekend.

Airflow is stubbed so these can run without an Airflow install. Requires:
  pip install holidays pendulum
"""

from __future__ import annotations

import sys
import types
import unittest


def _install_airflow_stubs() -> None:
    if "airflow.timetables.base" in sys.modules:
        return

    class Timetable:
        pass

    class DataInterval:
        def __init__(self, start, end):
            self.start = start
            self.end = end

    class DagRunInfo:
        @classmethod
        def interval(cls, start, end):
            info = cls()
            info.start = start
            info.end = end
            return info

    class TimeRestriction:
        def __init__(self, earliest=None, latest=None, catchup=True):
            self.earliest = earliest
            self.latest = latest
            self.catchup = catchup

    class CronDataIntervalTimetable:
        pass

    class AirflowPlugin:
        pass

    airflow = types.ModuleType("airflow")
    timetables = types.ModuleType("airflow.timetables")
    base = types.ModuleType("airflow.timetables.base")
    interval = types.ModuleType("airflow.timetables.interval")
    plugins = types.ModuleType("airflow.plugins_manager")

    base.Timetable = Timetable
    base.DataInterval = DataInterval
    base.DagRunInfo = DagRunInfo
    base.TimeRestriction = TimeRestriction
    interval.CronDataIntervalTimetable = CronDataIntervalTimetable
    plugins.AirflowPlugin = AirflowPlugin

    sys.modules["airflow"] = airflow
    sys.modules["airflow.timetables"] = timetables
    sys.modules["airflow.timetables.base"] = base
    sys.modules["airflow.timetables.interval"] = interval
    sys.modules["airflow.plugins_manager"] = plugins


_install_airflow_stubs()

from custom_timetables import BusinessDayOfMonth, MonthlyLastDayExceptWeekend  # noqa: E402


class TestBusinessDayOfMonthHolidays(unittest.TestCase):
    def test_weekends_only_keeps_new_years_weekday(self):
        # 1 Jan 2026 is Thursday. Without a calendar it is a business day.
        tt = BusinessDayOfMonth(n=1, hour=9, tz="Europe/London")
        day = tt._get_nth_business_day(2026, 1)
        self.assertEqual((day.year, day.month, day.day), (2026, 1, 1))

    def test_gb_eng_skips_new_years_day(self):
        # 1 Jan 2026 is New Year's Day (England). First working day is Friday 2 Jan.
        tt = BusinessDayOfMonth(
            n=1, hour=9, tz="Europe/London", country="GB", subdiv="ENG"
        )
        day = tt._get_nth_business_day(2026, 1)
        self.assertEqual((day.year, day.month, day.day), (2026, 1, 2))

    def test_us_last_business_day_skips_memorial_day(self):
        # 31 May 2021 was Monday Memorial Day. Last working day is Friday 28 May.
        tt = BusinessDayOfMonth(n=-1, hour=17, tz="America/New_York", country="US")
        day = tt._get_nth_business_day(2021, 5)
        self.assertEqual((day.year, day.month, day.day), (2021, 5, 28))

    def test_serialize_round_trip(self):
        tt = BusinessDayOfMonth(
            n=1, hour=9, tz="Europe/London", country="GB", subdiv="ENG", observed=False
        )
        again = BusinessDayOfMonth.deserialize(tt.serialize())
        self.assertEqual(again.country, "GB")
        self.assertEqual(again.subdiv, "ENG")
        self.assertEqual(again.observed, False)
        self.assertNotIn("_holiday_cache", again.serialize())

    def test_old_payload_has_no_country(self):
        tt = BusinessDayOfMonth.deserialize({"n": 1, "hour": 9, "tz": "Europe/London"})
        self.assertIsNone(tt.country)
        self.assertTrue(tt.observed)


class TestMonthlyLastDayExceptWeekendHolidays(unittest.TestCase):
    def test_weekend_only_walkback_unchanged(self):
        # Jan 2026 ends Saturday 31 → Friday 30. 30 Jan is not a GB holiday.
        tt = MonthlyLastDayExceptWeekend(hour=18, tz="Europe/London")
        day = tt._get_last_day(2026, 1)
        self.assertEqual((day.year, day.month, day.day), (2026, 1, 30))

    def test_us_memorial_day_month_end_walkback(self):
        # 31 May 2021 was Monday Memorial Day. Walk back to Friday 28 May.
        tt = MonthlyLastDayExceptWeekend(hour=18, tz="America/New_York", country="US")
        day = tt._get_last_day(2021, 5)
        self.assertEqual((day.year, day.month, day.day), (2021, 5, 28))

    def test_serialize_round_trip(self):
        tt = MonthlyLastDayExceptWeekend(hour=18, country="US", subdiv="NY")
        again = MonthlyLastDayExceptWeekend.deserialize(tt.serialize())
        self.assertEqual(again.country, "US")
        self.assertEqual(again.subdiv, "NY")
        self.assertTrue(again.observed)


if __name__ == "__main__":
    unittest.main()
