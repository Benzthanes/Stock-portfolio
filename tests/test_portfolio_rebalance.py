import unittest
from unittest.mock import patch

from src.portfolio import analyze_portfolio, generate_portfolio_markdown
from src.scoring import REBALANCE_WEIGHTS, compute_rebalance_score
from src.screener import evaluate_stock


class TestPortfolioDipOpportunities(unittest.TestCase):
    @patch("src.fx.fetch_usdthb", return_value=34.5)
    @patch("src.portfolio.fetch_screener_data")
    @patch("src.portfolio.fetch_batch_news", return_value={})
    @patch("src.portfolio.fetch_batch_catalysts", return_value={})
    def test_dip_opportunities_uses_actionable_and_grades(self, _cat, _news, mock_scan, _fx):
        # Good grade A stock with actionable setup
        row_good = {
            "ticker": "GOOD",
            "close": 100.0,
            "open": 98.0,
            "change": 2.0,
            "RSI": 35.0,
            "RSI[1]": 30.0,
            "EMA200": 98.0,
            "total_revenue_yoy_growth_ttm": 25.0,
            "net_income_yoy_growth_ttm": 30.0,
            "return_on_equity_fq": 25.0,
            "price_earnings_growth_ttm": 0.8,
            "debt_to_equity_fq": 0.5,
            "free_cash_flow_ttm": 1e9,
        }
        # Bad grade F stock with low RSI (should NOT be in dip_opportunities)
        row_bad = {
            "ticker": "BAD",
            "close": 50.0,
            "open": 49.0,
            "change": 1.0,
            "RSI": 25.0,
            "RSI[1]": 24.0,
            "EMA200": 60.0,
            "total_revenue_yoy_growth_ttm": -30.0,
            "net_income_yoy_growth_ttm": -50.0,
            "return_on_equity_fq": -20.0,
            "price_earnings_growth_ttm": -1.0,
            "debt_to_equity_fq": 5.0,
            "free_cash_flow_ttm": -1e8,
        }
        mock_scan.return_value = [row_good, row_bad]

        portfolio_data = {
            "portfolio_name": "Test",
            "base_currency": "USD",
            "holdings": [
                {"ticker": "GOOD", "exchange": "NASDAQ", "shares": 10, "avg_cost": 100.0},
                {"ticker": "BAD", "exchange": "NASDAQ", "shares": 10, "avg_cost": 50.0},
            ]
        }
        summary = analyze_portfolio(portfolio_data)
        dip_tickers = [p["ticker"] for p in summary["dip_opportunities"]]
        self.assertIn("GOOD", dip_tickers)
        self.assertNotIn("BAD", dip_tickers)

    @patch("src.fx.fetch_usdthb", return_value=34.5)
    @patch("src.portfolio.fetch_screener_data", return_value=[])
    @patch("src.portfolio.fetch_batch_news", return_value={})
    @patch("src.portfolio.fetch_batch_catalysts", return_value={})
    def test_analyze_portfolio_includes_fx_source(self, _cat, _news, _scan, _fx):
        summary = analyze_portfolio({"holdings": []})
        self.assertEqual(summary["fx_rate_usd_thb"], 34.5)
        self.assertEqual(summary["fx_source"], "live")


class TestDipTierCriteria(unittest.TestCase):
    def test_tier_strictly_uses_grade_and_entry_signal(self):
        # Grade A with entry signal -> ⭐⭐⭐ Actionable
        row_a_active = {
            "ticker": "ACT",
            "close": 100.0,
            "open": 98.0,
            "change": 2.0,
            "RSI": 35.0,
            "RSI[1]": 30.0,
            "EMA200": 98.0,
            "total_revenue_yoy_growth_ttm": 25.0,
            "net_income_yoy_growth_ttm": 30.0,
            "return_on_equity_fq": 25.0,
            "price_earnings_growth_ttm": 0.8,
            "debt_to_equity_fq": 0.5,
            "free_cash_flow_ttm": 1e9,
        }
        eval_active = evaluate_stock(row_a_active)
        self.assertEqual(eval_active["stock_score"]["grade"], "A+")
        self.assertTrue(eval_active["stock_score"]["timing"]["entry_signal"])
        self.assertEqual(eval_active["tier"], "⭐⭐⭐ Actionable Dip Buy 🎯")

        # Grade A WITHOUT entry signal -> ⭐ Watchlist (รอแท่งกลับตัว)
        row_a_wait = dict(row_a_active, RSI=30.0, **{"RSI[1]": 35.0})
        eval_wait = evaluate_stock(row_a_wait)
        self.assertFalse(eval_wait["stock_score"]["timing"]["entry_signal"])
        self.assertEqual(eval_wait["tier"], "⭐ Watchlist (รอแท่งกลับตัว)")


class TestRebalanceWeightsConstants(unittest.TestCase):
    def test_rebalance_weights_contains_thresholds(self):
        self.assertIn("under_allocated_max_weight_pct", REBALANCE_WEIGHTS)
        self.assertEqual(REBALANCE_WEIGHTS["under_allocated_max_weight_pct"], 5.0)
        self.assertIn("upside_bonus_min_pct", REBALANCE_WEIGHTS)
        self.assertEqual(REBALANCE_WEIGHTS["upside_bonus_min_pct"], 15.0)

    def test_compute_rebalance_score_uses_weights(self):
        score_under = compute_rebalance_score(
            stars=4, in_value_zone=False, dist_ema200_pct=2.0, is_etf=False,
            weight_pct=4.9, target_upside_pct=10.0, fundamental_pct=80.0
        )
        score_over = compute_rebalance_score(
            stars=4, in_value_zone=False, dist_ema200_pct=2.0, is_etf=False,
            weight_pct=5.1, target_upside_pct=10.0, fundamental_pct=80.0
        )
        self.assertEqual(round(score_under - score_over, 2), REBALANCE_WEIGHTS["under_allocated"])


class TestPortfolioMarkdownFormatting(unittest.TestCase):
    def test_negative_pl_markdown_format(self):
        summary = {
            "broker": "InnovestX",
            "base_currency": "USD",
            "fx_rate_usd_thb": 35.0,
            "portfolio_name": "Test",
            "total_market_val_usd": 1000.0,
            "total_market_val_thb": 35000.0,
            "total_cost_usd": 1200.0,
            "total_cost_thb": 42000.0,
            "total_pl_usd": -200.0,
            "total_pl_thb": -7000.0,
            "total_pl_pct": -16.67,
            "total_daily_change_usd": -10.0,
            "total_daily_change_thb": -350.0,
            "total_daily_change_pct": -1.0,
            "health_score": 50.0,
            "health_grade": "ต้องระวัง",
            "health_status": "🟠 เปราะบาง",
            "health_grade_desc": "พอร์ตเริ่มมีความเสี่ยง",
            "hhi": 2000.0,
            "concentration_level": "Moderate",
            "sector_sorted": [],
            "top_buy_candidates": [],
            "forbidden_buys": [],
            "dip_opportunities": [],
            "positions": [],
            "priced_positions": [
                {
                    "ticker": "LOSER",
                    "name": "Loser Inc",
                    "business_summary": "Tech",
                    "rating": {"stars_str": "⭐"},
                    "stock_score": None,
                    "avg_cost_usd": 100.0,
                    "close_price": 80.0,
                    "key_support": 75.0,
                    "key_resistance": 90.0,
                    "current_val_usd": 800.0,
                    "current_val_thb": 28000.0,
                    "unrealized_pl_usd": -200.0,
                    "unrealized_pl_pct": -20.0,
                    "change_pct": -2.0,
                    "rsi": 28.0,
                    "dist_sma200_pct": -15.0,
                    "dist_ema200_pct": -15.0,
                    "in_value_zone": False,
                    "shares": 10,
                    "weight_pct": 100.0,
                }
            ]
        }
        md = generate_portfolio_markdown(summary)
        # Should format as -$200.00, NOT $-200.00
        self.assertIn("-$200.00", md)
        self.assertNotIn("$-200.00", md)


if __name__ == "__main__":
    unittest.main()
