import unittest
from pathlib import Path
import src.chart_data as cd
from src.chart_data import (
    INDICATOR_SCHEMA_VERSION,
    compute_ai_confluence_signals,
    compute_fibo_and_indicators,
)


class TestRemovedIndicators(unittest.TestCase):
    """Test suite verifying complete removal of 6 unbacked indicators."""

    def setUp(self):
        self.candles = [
            {
                "time": f"2026-01-{(i % 28) + 1:02d}",
                "open": 100.0 + i * 0.5,
                "high": 102.0 + i * 0.5,
                "low": 99.0 + i * 0.5,
                "close": 101.0 + i * 0.5,
                "volume": 1500000,
            }
            for i in range(40)
        ]

    def test_removed_functions_not_present_in_module(self):
        """The 6 indicator calculation functions must not exist in src.chart_data."""
        removed_fn_names = [
            "compute_waddah_attar_explosion",
            "compute_volume_flow_indicator",
            "compute_wavetrend_oscillator",
            "compute_ut_bot_alerts",
            "compute_hull_suite",
            "compute_lorentzian_classification",
        ]
        for fn_name in removed_fn_names:
            self.assertFalse(
                hasattr(cd, fn_name),
                f"Function {fn_name} should have been removed from src.chart_data",
            )

    def test_schema_version_incremented(self):
        """INDICATOR_SCHEMA_VERSION must be incremented to 16."""
        self.assertEqual(INDICATOR_SCHEMA_VERSION, 16)

    def test_payload_keys_removed_and_retained(self):
        """Removed keys must be absent in payload while retained indicators remain present."""
        data = compute_fibo_and_indicators(self.candles, ticker="TEST")

        removed_keys = ["wae", "vfi", "wavetrend", "ut_bot", "hull_suite", "lorentzian_ml"]
        for key in removed_keys:
            self.assertNotIn(key, data, f"Key '{key}' must not be present in chart payload")

        retained_keys = ["squeeze_momentum", "chandelier_exit"]
        for key in retained_keys:
            self.assertIn(key, data, f"Key '{key}' must remain present in chart payload")
            self.assertIsInstance(data[key], dict)

    def test_confluence_logic_action_and_scores_unaffected(self):
        """Confluence decision engine actions, types, and scores must remain identical."""
        base_kwargs = {
            "candles": self.candles,
            "fibo_levels": {"0.0": 125.0, "50.0": 110.0, "61.8": 107.0, "78.6": 103.0},
            "pattern": None,
            "poc_price": 105.0,
            "current_st_trend": "BULLISH",
            "current_rsi": 45.0,
            "current_macd_hist": 0.5,
            "atr_val": 2.0,
        }

        # 1. Grade A+ with entry signal -> ENTRY, score 5
        score_a_plus = {
            "total": 92.0,
            "grade": "A+",
            "stars": 5,
            "reasons": ["High Rev Growth"],
            "timing": {"entry_signal": True},
        }
        res_entry = compute_ai_confluence_signals(**base_kwargs, stock_score=score_a_plus)[-1]
        self.assertEqual(res_entry["action"], "เข้าเงื่อนไขจุดเข้า")
        self.assertEqual(res_entry["type"], "ENTRY")
        self.assertEqual(res_entry["score"], 5)

        # 2. Grade A without entry signal -> HOLD, score 4
        score_a = {
            "total": 78.0,
            "grade": "A",
            "stars": 4,
            "reasons": ["Solid Fundamentals"],
            "timing": {"entry_signal": False},
        }
        res_hold_a = compute_ai_confluence_signals(**base_kwargs, stock_score=score_a)[-1]
        self.assertEqual(res_hold_a["action"], "รอ")
        self.assertEqual(res_hold_a["type"], "HOLD")
        self.assertEqual(res_hold_a["score"], 4)

        # 3. Grade B -> HOLD, score 3
        score_b = {
            "total": 60.0,
            "grade": "B",
            "stars": 3,
            "reasons": ["Moderate Fundamentals"],
            "timing": {"entry_signal": False},
        }
        res_hold_b = compute_ai_confluence_signals(**base_kwargs, stock_score=score_b)[-1]
        self.assertEqual(res_hold_b["action"], "รอ")
        self.assertEqual(res_hold_b["type"], "HOLD")
        self.assertEqual(res_hold_b["score"], 3)

        # 4. Grade C -> WAIT, score 2
        score_c = {
            "total": 45.0,
            "grade": "C",
            "stars": 2,
            "reasons": ["Low Fundamentals"],
            "timing": {"entry_signal": False},
        }
        res_wait_c = compute_ai_confluence_signals(**base_kwargs, stock_score=score_c)[-1]
        self.assertEqual(res_wait_c["action"], "รอ")
        self.assertEqual(res_wait_c["type"], "WAIT")
        self.assertEqual(res_wait_c["score"], 2)

        # 5. Grade F -> AVOID, score 1
        score_f = {
            "total": 25.0,
            "grade": "F",
            "stars": 1,
            "reasons": ["Negative Earnings"],
            "timing": {"entry_signal": False},
        }
        res_avoid_f = compute_ai_confluence_signals(**base_kwargs, stock_score=score_f)[-1]
        self.assertEqual(res_avoid_f["action"], "เลี่ยง")
        self.assertEqual(res_avoid_f["type"], "AVOID")
        self.assertEqual(res_avoid_f["score"], 1)

        # 6. Earnings Guard -> EARNINGS_GUARD
        res_guard = compute_ai_confluence_signals(
            **base_kwargs,
            stock_score=score_a_plus,
            days_to_earnings=5.0,
        )[-1]
        self.assertEqual(res_guard["type"], "EARNINGS_GUARD")
        self.assertEqual(res_guard["action"], "พักสัญญาณ (งบออกใน 5 วัน)")

    def test_reasons_contain_no_removed_indicators(self):
        """Reasons produced by confluence decision engine must not mention removed indicators."""
        base_kwargs = {
            "candles": self.candles,
            "fibo_levels": {"0.0": 125.0, "50.0": 110.0, "61.8": 107.0, "78.6": 103.0},
            "pattern": None,
            "poc_price": 105.0,
            "current_st_trend": "BULLISH",
            "current_rsi": 45.0,
            "current_macd_hist": 0.5,
            "atr_val": 2.0,
            "squeeze_mom": {"squeeze_fired": True, "direction": "BULLISH", "momentum": 2.5},
            "chandelier_exit": {"direction": "LONG", "long_stop": 97.5},
        }
        signals = compute_ai_confluence_signals(**base_kwargs)
        all_reasons = " ".join(signals[-1]["reasons"])
        for banned in ["Lorentzian", "UT Bot", "Hull Suite", "WaveTrend", "WAE", "VFI"]:
            self.assertNotIn(banned, all_reasons, f"Forbidden term '{banned}' found in reasons")

    def test_templates_do_not_have_removed_indicators(self):
        """Template HTML and JS files must have removed indicator buttons and keys removed."""
        html_path = Path("src/templates/chart.html")
        html_content = html_path.read_text(encoding="utf-8")

        banned_dom_ids = [
            "tog_lorentzian",
            "tog_utbot",
            "tog_hull",
            "tog_osc_wae",
            "tog_osc_vfi",
            "tog_osc_wt",
        ]
        for dom_id in banned_dom_ids:
            self.assertNotIn(dom_id, html_content, f"DOM id '{dom_id}' should be removed from chart.html")

        # Retained toolbar buttons
        self.assertIn("tog_chand", html_content)
        self.assertIn("tog_osc_sqz", html_content)
        self.assertIn("tog_osc_rsi", html_content)

        js_path = Path("src/templates/chart.js")
        js_content = js_path.read_text(encoding="utf-8")
        # Ensure no removed indicators in subpane arrays
        self.assertNotIn("['rsi', 'sqz', 'wae', 'vfi', 'wt']", js_content)


if __name__ == "__main__":
    unittest.main()
