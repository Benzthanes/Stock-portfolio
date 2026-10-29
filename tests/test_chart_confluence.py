import unittest
from src.chart_data import compute_ai_confluence_signals, compute_fibo_and_indicators
from src.scoring import EARNINGS_GUARD_DAYS, FundamentalScore, score_fundamentals, score_stock, score_timing


class ChartConfluenceTest(unittest.TestCase):
    def setUp(self):
        # 40 synthetic daily candles
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

    def _base_kwargs(self, **kwargs):
        base = {
            "candles": self.candles,
            "fibo_levels": {"0.0": 125.0, "50.0": 110.0, "61.8": 107.0, "78.6": 103.0},
            "pattern": None,
            "poc_price": 105.0,
            "current_st_trend": "BULLISH",
            "current_rsi": 45.0,
            "current_macd_hist": 0.5,
            "atr_val": 2.0,
        }
        base.update(kwargs)
        return base

    def test_grade_f_stock_never_gets_buy_or_dca_action(self):
        """Grade F stocks must NEVER receive buy-oriented actions regardless of technical indicators."""
        f_score = {
            "total": 35.0,
            "grade": "F",
            "stars": 1,
            "pillars": {"fundamental": 30.0, "timing": 40.0},
            "coverage": 0.9,
            "earnings_guard": False,
            "reasons": ["⚠️ Neg Rev Trap (-15.0%)", "⚠️ High Debt Risk (D/E 3.50)"],
            "timing": {"entry_signal": False},
        }

        # Pass every unbacked bullish indicator simultaneously
        signals = compute_ai_confluence_signals(
            **self._base_kwargs(
                stock_score=f_score,
                squeeze_mom={"squeeze_fired": True, "direction": "BULLISH", "momentum": 2.5},
                chandelier_exit={"direction": "LONG", "long_stop": 97.5},
                cdc_zone="green",
                elliott_wave={"detected": True, "type": "Bullish Impulse (1-2-3-4-5)", "current_wave": "Wave (5)", "target": 130.0},
                pivots={"r1": 100.0, "s1": 95.0},
                luxalgo_sr={"current_signal": {"time": self.candles[-1]["time"], "type": "BREAKOUT_VOL", "desc": "Volume Breakout"}},
                smc={"unmitigated_fvgs": [{"type": "BULLISH_FVG", "bottom": 100.0, "top": 105.0}]},
            )
        )

        latest = signals[-1]
        self.assertEqual(latest["action"], "เลี่ยง")
        self.assertEqual(latest["type"], "AVOID")
        self.assertEqual(latest["score"], 1)
        self.assertNotIn("BUY", latest["action"])
        self.assertNotIn("DCA", latest["action"])
        self.assertEqual(latest["marker_color"], "#f43f5e")

    def test_unbacked_indicators_do_not_add_points(self):
        """Unbacked technical indicators must NOT add points to confluence score."""
        baseline_signals = compute_ai_confluence_signals(**self._base_kwargs())
        baseline = baseline_signals[-1]

        signals = compute_ai_confluence_signals(
            **self._base_kwargs(
                squeeze_mom={"squeeze_fired": True, "direction": "BULLISH", "momentum": 2.5},
                chandelier_exit={"direction": "LONG", "long_stop": 97.5},
                cdc_zone="green",
                elliott_wave={"detected": True, "type": "Bullish Impulse (1-2-3-4-5)", "current_wave": "Wave (5)", "target": 130.0},
                pivots={"r1": 100.0, "s1": 95.0},
                smc={"unmitigated_fvgs": [{"type": "BULLISH_FVG", "bottom": 100.0, "top": 105.0}]},
            )
        )
        latest = signals[-1]

        self.assertEqual(latest["score"], baseline["score"])
        # Check reasons have unbacked tag
        unbacked_reasons = [r for r in latest["reasons"] if "ไม่ผ่าน backtest ไม่นับคะแนน" in r]
        self.assertGreaterEqual(len(unbacked_reasons), 3)

    def test_earnings_guard_activates_and_suspends_action(self):
        """Within 14 days of earnings, action must be suspended with exact days left."""
        a_score = {
            "total": 92.0,
            "grade": "A+",
            "stars": 5,
            "pillars": {"fundamental": 95.0, "timing": 88.0},
            "coverage": 1.0,
            "earnings_guard": True,
            "reasons": ["Rev Growth +30% 🚀"],
            "timing": {"entry_signal": True},
        }

        signals = compute_ai_confluence_signals(
            **self._base_kwargs(
                stock_score=a_score,
                days_to_earnings=6.0,
            )
        )
        latest = signals[-1]

        self.assertEqual(latest["action"], "พักสัญญาณ (งบออกใน 6 วัน)")
        self.assertEqual(latest["type"], "EARNINGS_GUARD")
        self.assertTrue(latest["earnings_guard"])
        self.assertEqual(latest["guard_days"], 6)
        self.assertEqual(latest["marker_color"], "#fb923c")

    def test_grade_a_with_rsi_hook_gets_entry_action(self):
        """High-grade stocks with RSI hook entry signal get entry condition action."""
        a_score = {
            "total": 88.0,
            "grade": "A+",
            "stars": 5,
            "pillars": {"fundamental": 90.0, "timing": 85.0},
            "coverage": 1.0,
            "earnings_guard": False,
            "reasons": ["Rev Growth +25% 🚀", "RSI Hook ยกหัวจากต่ำกว่า 40 ⤴"],
            "timing": {"entry_signal": True},
        }

        signals = compute_ai_confluence_signals(
            **self._base_kwargs(
                stock_score=a_score,
                days_to_earnings=45.0,
            )
        )
        latest = signals[-1]

        self.assertEqual(latest["action"], "เข้าเงื่อนไขจุดเข้า")
        self.assertEqual(latest["type"], "ENTRY")
        self.assertEqual(latest["score"], 5)
        self.assertEqual(latest["marker_color"], "#10b981")

    def test_grade_a_without_rsi_hook_waits(self):
        """High-grade stocks without RSI hook entry signal get hold/wait action."""
        a_score = {
            "total": 80.0,
            "grade": "A",
            "stars": 4,
            "pillars": {"fundamental": 85.0, "timing": 70.0},
            "coverage": 1.0,
            "earnings_guard": False,
            "reasons": ["Rev Growth +18%"],
            "timing": {"entry_signal": False},
        }

        signals = compute_ai_confluence_signals(
            **self._base_kwargs(
                stock_score=a_score,
                days_to_earnings=45.0,
            )
        )
        latest = signals[-1]

        self.assertEqual(latest["action"], "รอ")
        self.assertEqual(latest["type"], "HOLD")
        self.assertEqual(latest["score"], 4)

    def test_removed_indicators_not_in_reasons(self):
        """Removed unbacked indicators must not appear in confluence reasons."""
        signals = compute_ai_confluence_signals(**self._base_kwargs())
        latest = signals[-1]
        for name in ["Lorentzian", "UT Bot", "Hull Suite", "WaveTrend", "WAE", "VFI"]:
            reasons_with_name = [r for r in latest["reasons"] if name in r]
            self.assertEqual(len(reasons_with_name), 0)

    def test_historical_swing_markers_placed_at_confirmation_bar(self):
        """Swing trough markers must be timestamped at bar i+3 where they are causally confirmed."""
        # Create a trough at index 20
        candles = [
            {"time": f"2025-{(i // 25) + 1:02d}-{(i % 25) + 1:02d}", "open": 100.0, "high": 102.0, "low": 98.0, "close": 100.0, "volume": 1000}
            for i in range(50)
        ]
        # Low at index 20
        candles[20] = {"time": candles[20]["time"], "open": 90.0, "high": 91.0, "low": 80.0, "close": 85.0, "volume": 5000}
        # Bar 20 is confirmed at bar 23 (i+3)
        signals = compute_ai_confluence_signals(
            candles=candles,
            fibo_levels={"0.0": 105.0, "50.0": 85.0, "61.8": 80.0, "78.6": 75.0},
            pattern=None,
            poc_price=100.0,
            current_st_trend="BULLISH",
            current_rsi=35.0,
            current_macd_hist=0.0,
            atr_val=2.0,
        )
        historical = [s for s in signals if not s.get("is_latest")]
        if historical:
            # First historical signal should NOT be at candle[20]["time"]
            self.assertNotEqual(historical[0]["time"], candles[20]["time"])
            self.assertEqual(historical[0]["time"], candles[23]["time"])
            self.assertEqual(historical[0]["price"], candles[23]["close"])

    def test_grade_f_stock_has_no_historical_rule_entry_or_dca(self):
        """Grade F stocks must NEVER emit RULE_ENTRY or RULE_DCA historical signals."""
        candles = [
            {"time": f"2025-{(i // 25) + 1:02d}-{(i % 25) + 1:02d}", "open": 100.0, "high": 102.0, "low": 98.0, "close": 100.0, "volume": 1000}
            for i in range(50)
        ]
        candles[20] = {"time": candles[20]["time"], "open": 90.0, "high": 91.0, "low": 80.0, "close": 85.0, "volume": 5000}
        f_score = {
            "total": 35.0,
            "grade": "F",
            "stars": 1,
            "pillars": {"fundamental": 30.0, "timing": 40.0},
            "coverage": 0.9,
            "earnings_guard": False,
            "reasons": ["⚠️ Neg Rev Trap"],
            "timing": {"entry_signal": False},
        }
        signals = compute_ai_confluence_signals(
            candles=candles,
            fibo_levels={"0.0": 105.0, "50.0": 85.0, "61.8": 80.0, "78.6": 75.0},
            pattern=None,
            poc_price=100.0,
            current_st_trend="BULLISH",
            current_rsi=35.0,
            current_macd_hist=0.0,
            atr_val=2.0,
            stock_score=f_score,
        )
        historical_types = [s.get("type") for s in signals if not s.get("is_latest")]
        self.assertNotIn("RULE_ENTRY", historical_types)
        self.assertNotIn("RULE_DCA", historical_types)
        self.assertNotIn("BUY", [s.get("action") for s in signals])
        self.assertNotIn("STRONG BUY", historical_types)

    def test_no_strong_buy_string_in_output(self):
        """No output of compute_ai_confluence_signals should contain 'STRONG BUY' or '🚀'."""
        signals = compute_ai_confluence_signals(**self._base_kwargs())
        for s in signals:
            self.assertNotIn("STRONG BUY", s.get("type", ""))
            self.assertNotIn("STRONG BUY", s.get("action", ""))
            self.assertNotIn("STRONG BUY", s.get("badge", ""))
            self.assertNotIn("STRONG BUY", s.get("summary", ""))
            self.assertNotIn("🚀", s.get("badge", ""))

    def test_grade_f_and_c_with_high_rsi_stay_avoid_and_wait(self):
        """Grade F with RSI > 70 gets AVOID (not TRIM); Grade C gets WAIT (not TRIM)."""
        f_score = {"total": 20.0, "grade": "F", "stars": 1, "pillars": {}, "coverage": 1.0, "earnings_guard": False, "reasons": []}
        c_score = {"total": 45.0, "grade": "C", "stars": 2, "pillars": {}, "coverage": 1.0, "earnings_guard": False, "reasons": []}

        # Grade F with RSI = 78.0
        sig_f = compute_ai_confluence_signals(**self._base_kwargs(stock_score=f_score, current_rsi=78.0))[-1]
        self.assertEqual(sig_f["type"], "AVOID")
        self.assertEqual(sig_f["action"], "เลี่ยง")
        self.assertIn("RSI", sig_f["summary"])

        # Grade C with RSI = 78.0
        sig_c = compute_ai_confluence_signals(**self._base_kwargs(stock_score=c_score, current_rsi=78.0))[-1]
        self.assertEqual(sig_c["type"], "WAIT")
        self.assertEqual(sig_c["action"], "รอ")
        self.assertIn("RSI", sig_c["summary"])

    def test_grade_b_with_high_rsi_gets_trim(self):
        """Grade B with RSI > 70 gets TRIM."""
        b_score = {"total": 60.0, "grade": "B", "stars": 3, "pillars": {}, "coverage": 1.0, "earnings_guard": False, "reasons": []}
        sig_b = compute_ai_confluence_signals(**self._base_kwargs(stock_score=b_score, current_rsi=75.0))[-1]
        self.assertEqual(sig_b["type"], "TRIM")
        self.assertEqual(sig_b["action"], "แบ่งทำกำไร / รอ")

    def test_guard_days_threshold_and_levels_informational(self):
        """current_signal must have guard_days_threshold == 14 and levels_informational flag."""
        # AVOID signal
        f_score = {"total": 20.0, "grade": "F", "stars": 1, "pillars": {}, "coverage": 1.0, "earnings_guard": False, "reasons": []}
        sig_avoid = compute_ai_confluence_signals(**self._base_kwargs(stock_score=f_score))[-1]
        self.assertEqual(sig_avoid["guard_days_threshold"], 14)
        self.assertTrue(sig_avoid["levels_informational"])

        # EARNINGS_GUARD signal
        a_score = {"total": 90.0, "grade": "A+", "stars": 5, "pillars": {}, "coverage": 1.0, "earnings_guard": True, "reasons": []}
        sig_guard = compute_ai_confluence_signals(**self._base_kwargs(stock_score=a_score, days_to_earnings=5.0))[-1]
        self.assertEqual(sig_guard["guard_days_threshold"], 14)
        self.assertTrue(sig_guard["levels_informational"])

        # ENTRY signal
        sig_entry = compute_ai_confluence_signals(**self._base_kwargs(stock_score={**a_score, "earnings_guard": False, "timing": {"entry_signal": True}}))[-1]
        self.assertFalse(sig_entry["levels_informational"])


if __name__ == "__main__":
    unittest.main()
