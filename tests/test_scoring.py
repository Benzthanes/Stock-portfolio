import unittest

from recovery import evaluate_fundamental_health
from src.portfolio import compute_stock_rating
from src.scoring import (
    FUNDAMENTAL_RULES,
    ROE_DISPLAY_RULES,
    format_roe_html,
    score_fundamentals,
    score_stock,
    score_timing,
)
from src.screener import evaluate_stock


class ScoreFundamentalsTest(unittest.TestCase):
    def test_googl_like_scores_full_marks(self):
        res = score_fundamentals("GOOGL", "Technology Services", 20.2, 111.3, 30.0, 0.16, 0.18, 7e10)
        self.assertEqual((res["points"], res["max_points"], res["pct"], res["coverage"], res["grade"]), (25.0, 25, 100.0, 1.0, "A+"))
        self.assertIn("Rev Growth +20% 🚀", res["reasons"])

    def test_abnb_like_expensive_peg_lands_at_b(self):
        res = score_fundamentals("ABNB", "Consumer Services", 14.2, 2.51, 30.0, 6.45, 0.32, 4e9)
        self.assertEqual({k: m["points"] for k, m in res["metrics"].items()},
                         {"rev_growth_yoy": 4, "net_inc_growth_yoy": 2, "roe": 5, "peg": 0, "debt_to_equity": 3, "fcf": 3})
        self.assertEqual((res["points"], res["pct"], res["grade"]), (17.0, 68.0, "B"))

    def test_finance_sector_ignores_debt_to_equity(self):
        res = score_fundamentals("BAC", "Finance", 5.0, 20.0, 10.0, 1.2, 2.35, 1e10)
        self.assertNotIn("debt_to_equity", res["metrics"])
        self.assertEqual((res["points"], res["max_points"], res["pct"], res["coverage"], res["grade"]), (14.0, 22, 63.6, 0.88, "B"))

    def test_low_coverage_caps_grade_at_b(self):
        res = score_fundamentals("NEW", "Technology Services", 25.0, None, None, None, None, None)
        self.assertEqual((res["pct"], res["coverage"], res["grade"]), (100.0, 0.2, "B"))

    def test_no_data_is_not_applicable_grade(self):
        res = score_fundamentals("NODATA", "Technology Services", None, None, None, None, None, None)
        self.assertEqual((res["applicable"], res["pct"], res["grade"]), (True, None, "N/A"))

    def test_etf_is_not_scored(self):
        res = score_fundamentals("VOO", "Miscellaneous", None, None, None, None, None, None)
        self.assertEqual((res["applicable"], res["pct"], res["grade"]), (False, None, "ETF"))

    def test_spcx_is_a_stock_not_an_etf(self):
        res = score_fundamentals("SPCX", "Electronic Technology", 30.0, 40.0, 20.0, 1.2, 0.5, 1e9)
        self.assertEqual((res["applicable"], res["points"], res["grade"]), (True, 23.0, "A+"))

    def test_every_band_table_covers_real_line_without_overlap(self):
        grid = [x / 100.0 for x in range(-100_000, 100_001, 7)]
        for metric, (_, bands) in FUNDAMENTAL_RULES.items():
            edges = {b.lo for b in bands if b.lo is not None} | {b.hi for b in bands if b.hi is not None}
            for v in grid + sorted(edges) + [-1e12, 1e12]:
                hits = [b for b in bands if (b.lo is None or v >= b.lo) and (b.hi is None or v < b.hi)]
                self.assertEqual(len(hits), 1, f"{metric} value {v} matched {len(hits)} bands")


class CallerIntegrationTest(unittest.TestCase):
    BASE = {"ticker": "TST", "exchange": "NYSE", "close": 100.0, "RSI": 30.0, "RSI|1W": 50.0, "SMA200": 90.0}
    GOOGL_FUNDAMENTALS = {
        "sector": "Technology Services",
        "total_revenue_yoy_growth_ttm": 20.2,
        "net_income_yoy_growth_ttm": 111.3,
        "return_on_equity_fq": 30.0,
        "price_earnings_growth_ttm": 0.16,
        "debt_to_equity_fq": 0.18,
        "free_cash_flow_ttm": 7e10,
    }

    def test_screener_adds_full_fundamental_bonus_and_tags(self):
        bare = evaluate_stock(self.BASE)
        rich = evaluate_stock({**self.BASE, **self.GOOGL_FUNDAMENTALS})
        self.assertEqual(round(rich["score_points"] - bare["score_points"], 1), 4.5)
        self.assertEqual(rich["fundamental"]["grade"], "A+")
        self.assertIn("Elite ROE (30%) 🏆", rich["signal_tags"])

    def test_recovery_quality_follows_grade(self):
        abnb = evaluate_fundamental_health({"ticker": "ABNB", "sector": "Consumer Services",
                                            "total_revenue_yoy_growth_ttm": 14.2, "net_income_yoy_growth_ttm": 2.51,
                                            "return_on_equity_fq": 30.0, "price_earnings_growth_ttm": 6.45,
                                            "debt_to_equity_fq": 0.32, "free_cash_flow_ttm": 4e9})
        self.assertEqual((abnb["grade"], abnb["quality_score"]), ("B", 2))
        self.assertEqual(abnb["quality_tier"], "🟡 Resilient / Stable (ธุรกิจประคองตัวได้)")
        weak = evaluate_fundamental_health({"ticker": "BAD", "total_revenue_yoy_growth_ttm": -10.0,
                                            "net_income_yoy_growth_ttm": -25.0, "return_on_equity_fq": -15.0})
        self.assertEqual((weak["grade"], weak["quality_score"], weak["quality_tier"]),
                         ("F", 1, "🔴 Profit Contraction (พื้นฐานอ่อนแอ)"))

    def test_stock_rating_lists_fundamental_risks(self):
        pos = {"ticker": "BAD", "dist_sma200_pct": 5.0, "rsi": 50.0, "unrealized_pl_pct": 0.0, "weight_pct": 5.0,
               "rev_growth_yoy": -10.0, "net_inc_growth_yoy": -25.0, "roe": -15.0, "debt_to_equity": 3.5}
        res = compute_stock_rating(pos)
        self.assertEqual((res["stars_count"], res["grade_code"], res["total"]), (2, "C", 40.0))
        self.assertIn("⚠️ High Debt Risk (D/E 3.50)", res["risk"])


class StockScoreTest(unittest.TestCase):
    def test_value_zone_and_entry_signal(self):
        t = score_timing(4.0, 38.0, 35.0)
        self.assertEqual((t["points"], t["pct"], t["entry_signal"]), (6.0, 100.0, True))
        self.assertEqual(score_timing(-12.0, 55.0, 60.0)["points"], 0.0)
        self.assertFalse(score_timing(4.0, 45.0, 42.0)["entry_signal"])

    def test_combined_grade_weights_fundamental_and_timing(self):
        abnb = score_fundamentals("ABNB", None, 14.2, 2.51, 30.0, 6.45, 0.32, 4e9)
        s = score_stock(abnb, score_timing(15.0, 55.0, 50.0), days_to_earnings=10)
        self.assertEqual((s["total"], s["grade"], s["stars"], s["earnings_guard"]), (60.8, "B", 3, True))
        self.assertEqual(s["pillars"], {"fundamental": 68.0, "timing": 50.0})

    def test_etf_keeps_fixed_stars(self):
        s = score_stock(score_fundamentals("VOO", None, None, None, None, None, None, None), score_timing(8.0, 50, 49))
        self.assertEqual((s["grade"], s["stars"], s["total"]), ("ETF", 4, 100.0))


class ROEDisplayRulesTest(unittest.TestCase):
    def test_roe_display_rules_table_structure(self):
        self.assertEqual(len(ROE_DISPLAY_RULES), 3)
        self.assertEqual(ROE_DISPLAY_RULES[0].min_val, 20.0)
        self.assertFalse(ROE_DISPLAY_RULES[0].strict_gt)
        self.assertEqual(ROE_DISPLAY_RULES[0].css_class, "text-emerald fw-bold")
        self.assertEqual(ROE_DISPLAY_RULES[0].suffix, " 🏆")

        self.assertEqual(ROE_DISPLAY_RULES[1].min_val, 0.0)
        self.assertTrue(ROE_DISPLAY_RULES[1].strict_gt)
        self.assertEqual(ROE_DISPLAY_RULES[1].css_class, "text-emerald")
        self.assertEqual(ROE_DISPLAY_RULES[1].suffix, "")

        self.assertIsNone(ROE_DISPLAY_RULES[2].min_val)
        self.assertEqual(ROE_DISPLAY_RULES[2].css_class, "text-rose fw-bold")
        self.assertEqual(ROE_DISPLAY_RULES[2].suffix, " 🔻")

    def test_roe_html_formatting_exact_outputs(self):
        # Elite ROE: >= 20.0
        self.assertEqual(format_roe_html(20.0), "<span class='text-emerald fw-bold'>+20.0% 🏆</span>")
        self.assertEqual(format_roe_html(28.5), "<span class='text-emerald fw-bold'>+28.5% 🏆</span>")

        # Positive ROE: > 0 and < 20.0
        self.assertEqual(format_roe_html(19.9), "<span class='text-emerald'>+19.9%</span>")
        self.assertEqual(format_roe_html(15.0), "<span class='text-emerald'>+15.0%</span>")
        self.assertEqual(format_roe_html(0.1), "<span class='text-emerald'>+0.1%</span>")

        # Zero or Negative ROE: <= 0
        self.assertEqual(format_roe_html(0.0), "<span class='text-rose fw-bold'>+0.0% 🔻</span>")
        self.assertEqual(format_roe_html(-5.2), "<span class='text-rose fw-bold'>-5.2% 🔻</span>")

        # Missing ROE: None
        self.assertEqual(format_roe_html(None), "-")


if __name__ == "__main__":
    unittest.main()
