"""
Unit tests for unified earnings calendar source, calendar day difference, and badge rendering.
Asserts concrete numeric values without network access.
"""

import unittest
from datetime import date
from unittest import mock
from zoneinfo import ZoneInfo
from src.earnings_calendar import get_next_earnings_info, get_confirmed_earnings_dates
from src.screener import evaluate_stock
from src.html_report import generate_portfolio_html
from src.outlook import get_forward_outlook
from src.chart_data import compute_ai_confluence_signals
from src.scoring import score_fundamentals, score_timing, score_stock, EARNINGS_GUARD_DAYS


class TestEarningsBadgeUnified(unittest.TestCase):
    def test_calendar_vs_today_exact_days(self):
        # 2026-11-05 vs 2026-10-29 must be exactly 7 calendar days
        today = date(2026, 10, 29)
        info_mnst = get_next_earnings_info("MNST", today=today)
        self.assertEqual(info_mnst["days_to_earnings"], 7)
        self.assertEqual(info_mnst["earnings_date_str"], "05 Nov 2026")
        self.assertTrue(info_mnst["is_earnings_near"])
        self.assertEqual(info_mnst["source"], "calendar")

    def test_tradingview_conflict_prefers_calendar(self):
        today = date(2026, 10, 29)
        # TradingView incorrectly reports 2026-10-29 (timestamp 1793275200) for MNST
        tv_bad_data = {
            "earnings_release_next_date": 1793275200,
            "earnings_release_date": 1786047000,
        }
        info = get_next_earnings_info("MNST", tv_data=tv_bad_data, today=today)
        self.assertEqual(info["days_to_earnings"], 7)
        self.assertEqual(info["earnings_date_str"], "05 Nov 2026")
        self.assertEqual(info["source"], "calendar")

    def test_abnb_exact_days_not_skewed(self):
        # ABNB calendar is 2026-11-05. Must be 7 days from 2026-10-29.
        today = date(2026, 10, 29)
        info = get_next_earnings_info("ABNB", today=today)
        self.assertEqual(info["days_to_earnings"], 7)
        self.assertEqual(info["earnings_date_str"], "05 Nov 2026")

    def test_app_exact_days_not_skewed(self):
        # APP calendar is 2026-11-04. Must be 6 days from 2026-10-29.
        today = date(2026, 10, 29)
        info = get_next_earnings_info("APP", today=today)
        self.assertEqual(info["days_to_earnings"], 6)
        self.assertEqual(info["earnings_date_str"], "04 Nov 2026")

    def test_lly_same_day_is_zero(self):
        # LLY calendar is 2026-10-29. Must be 0 days on 2026-10-29.
        today = date(2026, 10, 29)
        info = get_next_earnings_info("LLY", today=today)
        self.assertEqual(info["days_to_earnings"], 0)
        self.assertEqual(info["earnings_date_str"], "29 Oct 2026")
        self.assertTrue(info["is_earnings_near"])

    def test_unlisted_ticker_falls_back_to_tradingview(self):
        today = date(2026, 10, 29)
        # 1793912400 corresponds to 2026-11-05 in America/New_York (17:00 EDT)
        tv_data = {"earnings_release_next_date": 1793912400}
        info = get_next_earnings_info("UNKNOWN_CORP_XYZ", tv_data=tv_data, today=today)
        self.assertEqual(info["days_to_earnings"], 7)
        self.assertEqual(info["earnings_date_str"], "05 Nov 2026")
        self.assertEqual(info["source"], "tradingview")

    def test_etf_ticker_has_no_earnings(self):
        today = date(2026, 10, 29)
        tv_data = {"earnings_release_next_date": 1793912400}
        for etf in ["VOO", "QQQI", "SPY"]:
            info = get_next_earnings_info(etf, tv_data=tv_data, today=today)
            self.assertIsNone(info["days_to_earnings"])
            self.assertFalse(info["is_earnings_near"])
            self.assertIsNone(info["source"])

    def test_html_badge_rendering_day_zero_and_seven(self):
        # Test HTML report handles 0d as 'งบออกวันนี้' and 7d as 'งบออกใน 7 วัน'
        summary = {
            "account": {"total_market_val_usd": 1000.0, "total_cost_usd": 900.0, "cash_usd": 100.0},
            "fx_rate": 33.62,
            "positions": [
                {
                    "ticker": "MNST",
                    "name": "Monster Beverage Corp",
                    "exchange": "NASDAQ",
                    "shares": 10.0,
                    "avg_cost_usd": 40.0,
                    "close_price": 45.0,
                    "weight_pct": 50.0,
                    "days_to_earnings": 7,
                    "earnings_date": "05 Nov 2026",
                    "is_earnings_near": True,
                    "alerts": ["⚠️ Earnings in 7d"],
                },
                {
                    "ticker": "LLY",
                    "name": "Eli Lilly & Co",
                    "exchange": "NYSE",
                    "shares": 1.0,
                    "avg_cost_usd": 800.0,
                    "close_price": 900.0,
                    "weight_pct": 50.0,
                    "days_to_earnings": 0,
                    "earnings_date": "29 Oct 2026",
                    "is_earnings_near": True,
                    "alerts": ["⚠️ Earnings today"],
                },
            ],
        }
        html = generate_portfolio_html(summary)
        self.assertIn("⚠️ งบออกใน 7 วัน", html)
        self.assertIn("⚠️ งบออกวันนี้", html)
        self.assertNotIn("งบออกใน 0 วัน", html)

    def test_outlook_earnings_note(self):
        today_fo = get_forward_outlook("APP", {}, {}, days_to_earnings=0, avg_cost=100.0, close=100.0)
        self.assertIn("มีกำหนดงบออกวันนี้", today_fo["tailored_roadmap"])

        future_fo = get_forward_outlook("APP", {}, {}, days_to_earnings=7, avg_cost=100.0, close=100.0)
        self.assertIn("มีวันงบออกในอีก 7 วัน", future_fo["tailored_roadmap"])

        # Also test non-curated default fallback ticker
        generic_fo = get_forward_outlook("GENERIC_XYZ", {}, {}, days_to_earnings=5, avg_cost=100.0, close=100.0)
        self.assertIn("มีวันงบออกในอีก 5 วัน", generic_fo["tailored_roadmap"])

    def test_recovery_earnings_freeze_dca_text(self):
        # Pin "today" so the expected 7 and 0 days hold on any run date.
        import recovery
        real = recovery.get_next_earnings_info
        pinned = lambda t, tv_data=None, **kw: real(t, tv_data=tv_data, today=date(2026, 10, 29))
        with mock.patch.object(recovery, "get_next_earnings_info", side_effect=pinned):
            self._check_recovery_earnings_text(recovery.analyze_recovery)

    def _check_recovery_earnings_text(self, analyze_recovery):
        # Mock row with ticker MNST (7 days away)
        row_mnst = {
            "name": "MNST",
            "close": 40.0,
            "open": 40.0,
            "high": 42.0,
            "low": 39.0,
            "EMA200": 38.0,
            "SMA20": 41.0,
            "RSI": 45.0,
            "RSI[1]": 43.0,
            "total_revenue_yoy_growth_ttm": 15.0,
            "net_income_yoy_growth_ttm": 20.0,
            "return_on_equity_fq": 25.0,
            "debt_to_equity_fq": 0.1,
            "price_earnings_growth_ttm": 1.2,
            "free_cash_flow_ttm": 1e8,
        }
        res_mnst = analyze_recovery(
            "MNST",
            custom_cost=50.0,
            custom_shares=10.0,
            market_row=row_mnst,
            catalysts=[],
        )
        self.assertTrue(res_mnst["is_earnings_imminent"])
        self.assertEqual(res_mnst["days_to_earnings"], 7)
        self.assertIn("งบออกใน 7 วัน", res_mnst["action_verdict"])
        self.assertIn("งบจะออกในอีก 7 วัน", res_mnst["layman_action"])

        # Mock row with ticker LLY (0 days away)
        row_lly = dict(row_mnst, name="LLY")
        res_lly = analyze_recovery(
            "LLY",
            custom_cost=50.0,
            custom_shares=10.0,
            market_row=row_lly,
            catalysts=[],
        )
        self.assertTrue(res_lly["is_earnings_imminent"])
        self.assertEqual(res_lly["days_to_earnings"], 0)
        self.assertIn("งบออกวันนี้", res_lly["action_verdict"])
        self.assertIn("งบจะออกวันนี้", res_lly["layman_action"])

    def test_chart_data_guard_badge_wording(self):
        fund = score_fundamentals("MNST", "Consumer Non-Durables", 20.0, 30.0, 25.0, 1.2, 0.1, 1e8)
        timing = score_timing(5.0, 45.0, 42.0)

        candles = [
            {"time": f"2026-10-{i:02d}", "open": 50.0, "high": 52.0, "low": 49.0, "close": 51.0, "volume": 1000}
            for i in range(1, 29)
        ]
        base_kwargs = {
            "candles": candles,
            "fibo_levels": {"0.0": 55.0, "50.0": 50.0, "61.8": 48.0, "78.6": 45.0},
            "pattern": None,
            "poc_price": 50.0,
            "current_st_trend": "BULLISH",
            "current_rsi": 45.0,
            "current_macd_hist": 0.5,
            "atr_val": 1.5,
            "ticker": "MNST",
        }

        # 0 days to earnings (today)
        score_0 = score_stock(fund, timing, days_to_earnings=0)
        sigs_0 = compute_ai_confluence_signals(
            **base_kwargs,
            stock_score=score_0,
            days_to_earnings=0,
        )
        self.assertTrue(len(sigs_0) > 0)
        self.assertEqual(sigs_0[-1]["badge"], "🟠 พักสัญญาณ (งบออกวันนี้)")

        # 7 days to earnings
        score_7 = score_stock(fund, timing, days_to_earnings=7)
        sigs_7 = compute_ai_confluence_signals(
            **base_kwargs,
            stock_score=score_7,
            days_to_earnings=7,
        )
        self.assertTrue(len(sigs_7) > 0)
        self.assertEqual(sigs_7[-1]["badge"], "🟠 พักสัญญาณ (งบออกใน 7 วัน)")


if __name__ == "__main__":
    unittest.main()
