"""
Unit tests for Daily Wealth Timeline Engine (src/wealth_timeline.py).
Asserts exact behavior, timeline continuity, datetime parsing, and valuation math.
"""

import unittest
from datetime import datetime
from src.wealth_timeline import (
    parse_wealth_datetime,
    dt_tuple_to_ymd,
    calculate_daily_wealth_timeline
)


class TestWealthTimeline(unittest.TestCase):

    def test_parse_wealth_datetime(self):
        # Thai format
        t1 = parse_wealth_datetime("14 ต.ค. 69 - 21:03 น.")
        self.assertEqual(t1, (2026, 10, 14, 21, 3, 0))

        # Thai date without time
        t2 = parse_wealth_datetime("17 มิ.ย. 69")
        self.assertEqual(t2, (2026, 6, 17, 12, 0, 0))

        # Slash format
        t3 = parse_wealth_datetime("02/02/2026")
        self.assertEqual(t3, (2026, 2, 2, 12, 0, 0))

        # Slash format with time
        t4 = parse_wealth_datetime("07/10/2026 23:30 น.")
        self.assertEqual(t4, (2026, 10, 7, 23, 30, 0))

        # ISO format
        t5 = parse_wealth_datetime("2026-08-15")
        self.assertEqual(t5, (2026, 8, 15, 12, 0, 0))

        # Empty
        self.assertEqual(parse_wealth_datetime(""), (0, 0, 0, 0, 0, 0))
        self.assertEqual(parse_wealth_datetime(None), (0, 0, 0, 0, 0, 0))

    def test_dt_tuple_to_ymd(self):
        self.assertEqual(dt_tuple_to_ymd((2026, 2, 2, 12, 0, 0)), "2026-02-02")
        self.assertEqual(dt_tuple_to_ymd((2026, 10, 19, 0, 0, 0)), "2026-10-19")

    def test_synthetic_timeline_math(self):
        synthetic_summary = {
            "fx_rate": 30.0,
            "buy_orders": [
                {
                    "ticker": "TEST",
                    "shares": 10.0,
                    "price_usd": 100.0,
                    "amt_usd": 1000.0,
                    "amt_thb": 30000.0,
                    "date": "2026-02-02",
                    "account": "Dime! Save (THB)"
                }
            ],
            "closed_trades": [],
            "cash_movements": [
                {
                    "date_str": "01/02/2026",
                    "type": "ฝากเงิน (โอนเข้า Dime! Save)",
                    "amount_thb": 100000.0,
                    "balance_thb": 100000.0
                },
                {
                    "date_str": "02/02/2026",
                    "type": "ชำระค่าซื้อหุ้น TEST",
                    "amount_thb": -30000.0,
                    "balance_thb": 70000.0
                }
            ],
            "dividends_list": []
        }

        synthetic_candles = {
            "TEST": {
                "candles": [
                    {"time": "2026-02-02", "close": 100.0},
                    {"time": "2026-02-03", "close": 110.0},
                ]
            }
        }

        res = calculate_daily_wealth_timeline(
            synthetic_summary,
            candles_cache=synthetic_candles,
            live_override=False
        )
        timeline = res["timeline"]
        self.assertGreaterEqual(len(timeline), 2)

        # Day 1: 2026-02-01
        p0 = timeline[0]
        self.assertEqual(p0["time"], "2026-02-01")
        self.assertEqual(p0["capital_thb"], 100000.0)
        self.assertEqual(p0["cash_thb"], 100000.0)
        self.assertEqual(p0["stock_thb"], 0.0)
        self.assertEqual(p0["nav_thb"], 100000.0)
        self.assertEqual(p0["profit_thb"], 0.0)

        # Day 2: 2026-02-02 (Bought 10 shares @ 100 = 1,000 USD * 30 = 30,000 THB)
        p1 = timeline[1]
        self.assertEqual(p1["time"], "2026-02-02")
        self.assertEqual(p1["capital_thb"], 100000.0)
        self.assertEqual(p1["cash_thb"], 70000.0)
        self.assertEqual(p1["stock_thb"], 30000.0)
        self.assertEqual(p1["nav_thb"], 100000.0)

        # Day 3: 2026-02-03 (Price rose to 110 USD -> 1,100 USD * 30 = 33,000 THB)
        p2 = timeline[2]
        self.assertEqual(p2["time"], "2026-02-03")
        self.assertEqual(p2["stock_thb"], 33000.0)
        self.assertEqual(p2["cash_thb"], 70000.0)
        self.assertEqual(p2["nav_thb"], 103000.0)
        self.assertEqual(p2["profit_thb"], 3000.0)
        self.assertEqual(p2["roi_pct"], 3.0)

    def test_real_account_data_timeline(self):
        import json
        from pathlib import Path
        summary_path = Path(__file__).resolve().parent.parent / "data" / "account_summary.json"
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            return

        res = calculate_daily_wealth_timeline(data, live_override=True)

        summary = res["summary"]
        timeline = res["timeline"]

        self.assertEqual(summary["start_date"], "2026-02-02")
        self.assertGreaterEqual(summary["total_days"], 250)
        self.assertEqual(summary["current_capital_thb"], 1245000.0)
        self.assertGreater(summary["current_nav_thb"], 1400000.0)
        self.assertGreater(summary["ath_nav_thb"], summary["current_capital_thb"])

        # Check continuity of points
        for pt in timeline:
            self.assertIn("time", pt)
            self.assertIn("nav_thb", pt)
            self.assertIn("capital_thb", pt)
            self.assertIn("profit_thb", pt)
            self.assertIn("roi_pct", pt)
            self.assertGreater(pt["nav_thb"], 0.0)
            self.assertGreater(pt["capital_thb"], 0.0)


if __name__ == "__main__":
    unittest.main()
