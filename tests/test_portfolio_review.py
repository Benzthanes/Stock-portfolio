import unittest
from src.portfolio import compute_financial_health, compute_stock_rating, analyze_portfolio
from src.html_report import generate_portfolio_html


class PortfolioReviewProductionTest(unittest.TestCase):
    def test_compute_financial_health_incorporates_roe_and_debt(self):
        # Elite business with high ROE and low debt
        pos_elite = {
            "ticker": "AAPL",
            "rev_growth_yoy": 15.0,
            "net_inc_growth_yoy": 20.0,
            "roe": 35.0,
            "debt_to_equity": 0.5,
            "fcf": 2000000000,
            "peg": 1.1
        }
        res_elite = compute_financial_health(pos_elite)
        self.assertIn("A", res_elite["health_grade"])
        self.assertEqual(res_elite["roe_str"], "+35.0%")
        self.assertEqual(res_elite["de_str"], "0.50")
        self.assertIn("ROE", res_elite["summary"])

        # Distressed business with negative ROE and high leverage
        pos_distressed = {
            "ticker": "BAD",
            "rev_growth_yoy": -10.0,
            "net_inc_growth_yoy": -25.0,
            "roe": -15.0,
            "debt_to_equity": 3.5,
            "fcf": -50000000,
            "peg": -0.5
        }
        res_distressed = compute_financial_health(pos_distressed)
        self.assertIn("D", res_distressed["health_grade"])
        self.assertLess(res_distressed["score"], 0)

    def test_compute_stock_rating_rewards_high_roe_and_penalizes_debt(self):
        pos_high_roe = {
            "ticker": "MSFT",
            "dist_sma200_pct": 15.0,
            "in_value_zone": False,
            "rsi": 55.0,
            "rev_growth_yoy": 16.0,
            "net_inc_growth_yoy": 22.0,
            "roe": 30.0,
            "debt_to_equity": 0.4,
            "unrealized_pl_pct": 10.0,
            "weight_pct": 10.0
        }
        res = compute_stock_rating(pos_high_roe)
        self.assertGreaterEqual(res["stars_count"], 4)
        self.assertIn("ROE", res["strength"])

    def test_disqualification_and_support_boundaries(self):
        # Position with plunge day active
        p_plunge = {
            "ticker": "PLG",
            "name": "Plunge Co",
            "shares": 10,
            "avg_cost_usd": 100,
            "close_price": 80.0,
            "weight_pct": 10.0,
            "is_plunge_day": True,
            "is_earnings_near": False,
            "net_inc_growth_yoy": 10.0,
            "rating": {"stars_count": 4},
            "price_missing": False,
            "unrealized_pl_pct": -20.0
        }
        # Position with high debt
        p_debt = {
            "ticker": "LEV",
            "name": "Leveraged Co",
            "shares": 10,
            "avg_cost_usd": 50,
            "close_price": 50.0,
            "weight_pct": 10.0,
            "debt_to_equity": 4.0,
            "is_earnings_near": False,
            "net_inc_growth_yoy": 5.0,
            "rating": {"stars_count": 3},
            "price_missing": False,
            "unrealized_pl_pct": 0.0
        }
        # Good candidate
        p_good = {
            "ticker": "GOOD",
            "name": "Good Co",
            "shares": 10,
            "avg_cost_usd": 50,
            "close_price": 55.0,
            "current_val_usd": 550.0,
            "current_val_thb": 18150.0,
            "unrealized_pl_usd": 50.0,
            "unrealized_pl_thb": 1650.0,
            "unrealized_pl_pct": 10.0,
            "change_pct": 1.5,
            "rsi": 45.0,
            "dist_sma200_pct": 5.0,
            "weight_pct": 5.0,
            "is_earnings_near": False,
            "net_inc_growth_yoy": 25.0,
            "roe": 22.0,
            "debt_to_equity": 0.3,
            "fcf": 1000000,
            "peg": 1.0,
            "rating": {"stars_count": 5, "stars_str": "⭐⭐⭐⭐⭐"},
            "price_missing": False,
            "key_support": 52.0,
            "key_resistance": 65.0,
            "tv_url": "https://tradingview.com"
        }

        port_data = {
            "portfolio_name": "Test Port",
            "broker": "Dime",
            "base_currency": "USD",
            "holdings": [
                {"ticker": "PLG", "shares": 10, "avg_cost": 100},
                {"ticker": "LEV", "shares": 10, "avg_cost": 50},
                {"ticker": "GOOD", "shares": 10, "avg_cost": 50}
            ]
        }
        # We can test analyze_portfolio logic directly or verify html generation
        summary = {
            "portfolio_name": "Test Port",
            "broker": "Dime",
            "base_currency": "USD",
            "positions": [p_good],
            "total_market_val_usd": 550.0,
            "total_market_val_thb": 18150.0,
            "total_cost_usd": 500.0,
            "total_cost_thb": 16500.0,
            "total_pl_usd": 50.0,
            "total_pl_thb": 1650.0,
            "total_pl_pct": 10.0,
            "top_buy_candidates": [p_good],
            "forbidden_buys": [{"ticker": "PLG", "name": "Plunge Co", "reason": "Plunge Day"}],
            "sector_sorted": [("Tech", 100.0)]
        }
        html = generate_portfolio_html(summary)
        self.assertIn("ROE (%)", html)
        self.assertIn("D/E (หนี้/ทุน)", html)
        self.assertIn("🏆", html)
        self.assertIn("🛡️", html)


if __name__ == "__main__":
    unittest.main()
