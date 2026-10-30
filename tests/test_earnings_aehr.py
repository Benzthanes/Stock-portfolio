"""
Unit tests for AEHR confirmed earnings calendar integration.
Asserts concrete dates, announcement timing ('amc'), next earnings calculation,
and price reaction calculation without network access.
Honors FILTER_STOCK_DATA_DIR to guarantee data isolation.
"""

import os
import shutil
import tempfile
import unittest
from datetime import date

from src.earnings_calendar import (
    get_confirmed_earnings_dates,
    get_earnings_timing,
    get_next_earnings_info,
    calculate_confirmed_earnings_reaction,
)


class TestEarningsAehr(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_env = os.environ.get("FILTER_STOCK_DATA_DIR")
        os.environ["FILTER_STOCK_DATA_DIR"] = self.temp_dir

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        if self.old_env is not None:
            os.environ["FILTER_STOCK_DATA_DIR"] = self.old_env
        else:
            os.environ.pop("FILTER_STOCK_DATA_DIR", None)

    def test_aehr_confirmed_dates_exact(self):
        expected_dates = [
            "2024-01-09", "2024-04-09", "2024-07-16", "2024-10-10",
            "2025-01-13", "2025-04-08", "2025-07-08", "2025-10-06",
            "2026-01-08", "2026-04-07", "2026-07-14", "2026-11-02",
        ]
        dates = get_confirmed_earnings_dates("AEHR")
        self.assertEqual(dates, expected_dates)
        self.assertEqual(len(dates), 12)

    def test_aehr_earnings_timing_amc(self):
        timing = get_earnings_timing("AEHR")
        self.assertEqual(timing, "amc")

    def test_aehr_next_earnings_info_near(self):
        # As of 2026-10-30, next earnings is 2026-11-02 (3 calendar days away)
        today = date(2026, 10, 30)
        info = get_next_earnings_info("AEHR", today=today)
        self.assertEqual(info["days_to_earnings"], 3)
        self.assertEqual(info["earnings_date_str"], "02 Nov 2026")
        self.assertTrue(info["is_earnings_near"])
        self.assertEqual(info["source"], "calendar")
        self.assertEqual(info["earnings_iso"], "2026-11-02")

    def test_aehr_earnings_reaction_amc(self):
        # AMC: reaction on idx + 1 vs idx
        candles = [
            {"time": "2026-07-13", "open": 20.0, "high": 21.0, "low": 19.5, "close": 20.0},
            {"time": "2026-07-14", "open": 20.0, "high": 20.5, "low": 19.8, "close": 20.0},  # Earnings AMC
            {"time": "2026-07-15", "open": 24.0, "high": 25.0, "low": 23.5, "close": 24.0},  # Reaction day (+20%)
        ]
        events = calculate_confirmed_earnings_reaction(
            candles=candles,
            dates=["2026-07-14"],
            ticker="AEHR",
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["time"], "2026-07-15")
        self.assertEqual(events[0]["reaction_pct"], 20.0)
        self.assertEqual(events[0]["text"], "🗓️ +20.0%")
        self.assertEqual(events[0]["position"], "belowBar")


if __name__ == "__main__":
    unittest.main()
