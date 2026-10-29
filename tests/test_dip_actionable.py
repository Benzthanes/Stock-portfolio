import unittest
from src.screener import evaluate_stock

class TestDipActionableEvaluation(unittest.TestCase):
    def test_evaluate_stock_no_has_reversal_confirmation_key(self):
        """Verify has_reversal_confirmation is removed from evaluate_stock return dict."""
        stock_data = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "close": 150.0,
            "open": 148.0,
            "change": 1.35,
            "RSI": 32.0,
            "RSI[1]": 30.0,
            "EMA200": 145.0,
            "SMA200": 145.0,
            "total_revenue_yoy_growth_ttm": 12.0,
            "net_income_yoy_growth_ttm": 15.0,
            "return_on_equity_fq": 25.0,
            "free_cash_flow_ttm": 1000000000.0,
        }
        res = evaluate_stock(stock_data)
        self.assertNotIn("has_reversal_confirmation", res)
        self.assertIn("is_actionable", res)
        self.assertIsInstance(res["is_actionable"], bool)
        self.assertEqual(res["ticker"], "AAPL")
        self.assertEqual(res["close"], 150.0)

    def test_evaluate_stock_actionable_behavior_values(self):
        """Assert exact boolean values for actionable dip setups."""
        # Setup 1: High grade stock with RSI hook up (entry_signal = True) and positive candle -> actionable = True
        stock_a = {
            "ticker": "MSFT",
            "close": 200.0,
            "open": 195.0,
            "change": 2.56,
            "RSI": 34.0,
            "RSI[1]": 31.0,
            "EMA200": 190.0, # distance 5.26% -> Value Zone
            "SMA200": 190.0,
            "total_revenue_yoy_growth_ttm": 16.0,
            "net_income_yoy_growth_ttm": 18.0,
            "return_on_equity_fq": 22.0,
            "free_cash_flow_ttm": 5000000000.0,
        }
        res_a = evaluate_stock(stock_a)
        self.assertTrue(res_a["is_actionable"])
        self.assertFalse(res_a["is_plunge_day"])
        self.assertEqual(res_a["tier"], "⭐⭐⭐ Actionable Dip Buy 🎯")

        # Setup 2: Same stock on an active plunge day (-3.5%) -> actionable = False
        stock_b = dict(stock_a)
        stock_b["change"] = -3.5
        stock_b["open"] = 205.0
        res_b = evaluate_stock(stock_b)
        self.assertTrue(res_b["is_plunge_day"])
        self.assertFalse(res_b["is_actionable"])
        self.assertEqual(res_b["tier"], "👀 รอสร้างฐาน (Forming Base - วันทิ้งตัว)")

if __name__ == "__main__":
    unittest.main()
