import unittest

from scripts.check_reports import check


def chart(signals, last="2026-10-29"):
    return {"candles": [{"time": last, "close": 100.0}], "ai_signals": signals}


def sig(**kw):
    base = {"time": "2026-10-29", "type": "HOLD", "price": 100.0, "stop_loss": 97.0, "target": 105.0, "earnings_guard": False, "guard_days": None}
    base.update(kw)
    return base


class CheckReportsTest(unittest.TestCase):
    def test_clean_reports_have_no_problems(self):
        charts = {"AAA": chart([sig()]), "BBB": chart([sig(type="EARNINGS_GUARD", earnings_guard=True, guard_days=6)])}
        positions = [{"ticker": "AAA", "days_to_earnings": 103}, {"ticker": "BBB", "days_to_earnings": 6}]
        self.assertEqual(check(charts, positions, "2026-10-30"), [])

    def test_short_side_levels_are_flagged(self):
        problems = check({"LLY": chart([sig(type="TRIM", price=1381.14, stop_loss=1444.92, target=1296.1)])}, [], "2026-10-30")
        self.assertEqual(problems, ["LLY 2026-10-29 TRIM: stop 1444.92 / price 1381.14 / target 1296.1 not long-side"])

    def test_guard_without_days_is_flagged(self):
        problems = check({"LLY": chart([sig(earnings_guard=True, guard_days=None)])}, [], "2026-10-30")
        self.assertEqual(problems, ["LLY: earnings guard on but guard_days is None"])

    def test_stale_guard_after_report_date_is_flagged(self):
        charts = {"LLY": chart([sig(type="EARNINGS_GUARD", earnings_guard=True, guard_days=0)])}
        problems = check(charts, [{"ticker": "LLY", "days_to_earnings": 103}], "2026-10-30")
        self.assertEqual(problems, ["LLY: chart guard True but account_summary days_to_earnings is 103"])

    def test_guard_days_mismatch_is_flagged(self):
        charts = {"ABNB": chart([sig(type="EARNINGS_GUARD", earnings_guard=True, guard_days=7)])}
        problems = check(charts, [{"ticker": "ABNB", "days_to_earnings": 6}], "2026-10-30")
        self.assertEqual(problems, ["ABNB: chart guard_days 7 but account_summary days_to_earnings is 6"])

    def test_weekend_and_future_candles_are_flagged(self):
        self.assertEqual(check({"AAA": chart([sig()], last="2026-10-31")}, [], "2026-11-02"), ["AAA: last candle 2026-10-31 falls on a weekend"])
        self.assertEqual(check({"AAA": chart([sig()], last="2026-10-30")}, [], "2026-10-29"), ["AAA: last candle 2026-10-30 is after the US market date 2026-10-29"])


if __name__ == "__main__":
    unittest.main()
