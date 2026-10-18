import unittest
from datetime import date, timedelta

from src.chart_data import compact_charts_for_page, compute_fibo_and_indicators
from src.screener import atr_stop_loss, evaluate_stock, filter_stocks


def _row(**kw):
    row = {"ticker": "TST", "exchange": "NYSE", "close": 100.0, "RSI": 30.0, "RSI|1W": 50.0, "SMA200": 90.0}
    row.update(kw)
    return row


class WilderAtrTest(unittest.TestCase):
    def test_atr14_uses_wilder_smoothing(self):
        spans = [1.0] * 14 + [8.0, 8.0]
        candles = [
            {"time": f"2024-01-{i + 1:02d}", "open": 100.0, "high": 100.0 + a, "low": 100.0 - a, "close": 100.0, "volume": 1000}
            for i, a in enumerate(spans)
        ]
        self.assertEqual(compute_fibo_and_indicators(candles)["atr14"]["value"], 3.93)


class SectorFilterTest(unittest.TestCase):
    def test_missing_sector_never_matches(self):
        rows = [_row(ticker="NONE", sector=None), _row(ticker="EMPTY", sector=""), _row(ticker="BANK", sector="Finance")]
        kept = filter_stocks(rows, rsi_max=100.0, sector_filter="Financials", weekly_rsi_min=None)
        self.assertEqual([s["ticker"] for s in kept], ["BANK"])

    def test_missing_weekly_rsi_is_excluded_when_filter_active(self):
        rows = [_row(ticker="NOWK", **{"RSI|1W": None}), _row(ticker="WK")]
        self.assertEqual([s["ticker"] for s in filter_stocks(rows, weekly_rsi_min=45.0)], ["WK"])


class StopLossTest(unittest.TestCase):
    def test_huge_atr_is_floored_at_half_price(self):
        self.assertEqual(atr_stop_loss(100.0, 80.0), 50.0)

    def test_normal_atr_and_fallback(self):
        self.assertEqual(atr_stop_loss(100.0, 2.0), 97.0)
        self.assertEqual(atr_stop_loss(100.0, None), 95.0)


class NameTest(unittest.TestCase):
    def test_null_description_falls_back_to_ticker(self):
        self.assertEqual(evaluate_stock(_row(description=None))["name"], "TST")


class CompactChartsTest(unittest.TestCase):
    def test_keeps_recent_daily_and_monthly_history(self):
        start = date(2020, 1, 1)
        candles = [
            {"time": (start + timedelta(days=i)).isoformat(), "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10}
            for i in range(1500)
        ]
        cache = {
            "AAA": {"full_history": True, "candles": candles, "ath": {"price": 2.0}},
            "OLD": {"candles": candles},
            "ZZZ": {"full_history": True, "candles": candles},
        }
        out = compact_charts_for_page(cache, ["AAA", "OLD"])
        self.assertEqual(list(out), ["AAA"])
        page = out["AAA"]["candles"]
        self.assertEqual(len(page), 7 + 1287)
        self.assertEqual(page[0], {"time": "2020-01-31", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 310})
        self.assertEqual(page[7]["time"], "2020-08-01")
        self.assertEqual(out["AAA"]["ath"], {"price": 2.0})
        self.assertEqual(len(cache["AAA"]["candles"]), 1500)


class EarningsHistoryTest(unittest.TestCase):
    def test_detect_earnings_history_calculates_correct_reaction(self):
        from src.chart_data import detect_earnings_history
        candles = [
            {"time": "2024-02-05", "open": 100.0, "high": 105.0, "low": 99.0, "close": 100.0, "volume": 1000},
            {"time": "2024-02-06", "open": 102.0, "high": 112.0, "low": 101.0, "close": 110.0, "volume": 3500},
            {"time": "2024-02-07", "open": 110.0, "high": 111.0, "low": 108.0, "close": 109.0, "volume": 1200},
        ]
        history = detect_earnings_history(candles)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["time"], "2024-02-06")
        self.assertEqual(history[0]["reaction_pct"], 10.0)
        self.assertIn("+10.0%", history[0]["text"])
        self.assertEqual(history[0]["color"], "#10b981")
        self.assertEqual(history[0]["position"], "belowBar")


class SuperInvestorsTest(unittest.TestCase):
    def test_lly_has_famous_whales(self):
        from src.chart_data import get_super_investors
        whales = get_super_investors("LLY")
        self.assertGreaterEqual(len(whales), 3)
        names = [w["name"] for w in whales]
        self.assertTrue(any("Ken Griffin" in n or "Lilly Endowment" in n for n in names))

    def test_fallback_whale_data(self):
        from src.chart_data import get_super_investors
        whales = get_super_investors("UNKNOWN_XYZ")
        self.assertGreaterEqual(len(whales), 1)
        self.assertEqual(whales[0]["fund"], "Passive & Index Whales")


class CDCActionZoneTest(unittest.TestCase):
    def test_cdc_bullish_and_bearish_zones(self):
        from src.chart_data import compute_cdc_actionzone
        # Bullish upward candles
        candles_up = [
            {"time": f"2024-01-{i + 1:02d}", "open": 100.0 + i * 2, "high": 102.0 + i * 2, "low": 99.0 + i * 2, "close": 101.0 + i * 2, "volume": 1000}
            for i in range(40)
        ]
        res_up = compute_cdc_actionzone(candles_up)
        self.assertEqual(res_up["status"], "BULLISH")
        self.assertEqual(res_up["zone"], "green")
        self.assertEqual(res_up["badge_color"], "#22c55e")
        self.assertGreater(res_up["fast_ema12"], res_up["slow_ema26"])
        self.assertEqual(len(res_up["candle_colors"]), 40)

        # Bearish downward candles
        candles_down = [
            {"time": f"2024-02-{i + 1:02d}", "open": 200.0 - i * 3, "high": 201.0 - i * 3, "low": 195.0 - i * 3, "close": 196.0 - i * 3, "volume": 1000}
            for i in range(40)
        ]
        res_down = compute_cdc_actionzone(candles_down)
        self.assertEqual(res_down["status"], "BEARISH")
        self.assertEqual(res_down["zone"], "red")
        self.assertEqual(res_down["badge_color"], "#ef4444")
        self.assertLess(res_down["fast_ema12"], res_down["slow_ema26"])


class ChartPageGenerationTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from unittest import mock
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for patcher in (
            mock.patch("src.chart_page.REPORTS_DIR", Path(tmp.name)),
            mock.patch("src.news.fetch_batch_news", return_value={}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_generate_stock_chart_page_html_renders_cockpit_and_subpane(self):
        from src.chart_page import generate_stock_chart_page_html
        html = generate_stock_chart_page_html()
        self.assertGreater(len(html), 50000)
        self.assertIn("cockpit-grid", html)
        self.assertIn("rsi-subpane-wrap", html)
        self.assertIn("chart-botbar", html)
        self.assertIn("EMA 9", html)
        self.assertIn("EMA 200", html)
        self.assertIn("dca-results-card", html)
        self.assertIn("ai_narrative_text", html)

    def test_generate_stock_chart_page_html_renders_new_controls_and_whales(self):
        from src.chart_page import generate_stock_chart_page_html
        html = generate_stock_chart_page_html()
        # Toggle buttons
        self.assertIn('id="tog_pivots"', html)
        self.assertIn('id="tog_ew"', html)
        self.assertIn('id="tog_earn"', html)
        self.assertIn('id="tog_cdc"', html)
        # Cockpit sidebar cards
        self.assertIn('id="ew_sidebar_card"', html)
        self.assertIn('id="whales_sidebar_card"', html)
        self.assertIn('id="whales_sidebar_body"', html)
        self.assertIn('id="news_sidebar_card"', html)
        self.assertIn('id="news_sidebar_body"', html)
        # Flat toolbar - no collapsible drawer
        self.assertNotIn("adv-indicators-tray", html)
        self.assertNotIn("adv-toggle-btn", html)
        # JavaScript logic
        self.assertIn("updateElliottWaveSidebar", html)
        self.assertIn("updateWhalesSidebar", html)
        self.assertIn("updateNewsSidebar", html)
        self.assertIn("drawPivotPriceLines", html)
        self.assertIn("drawElliottWave", html)
        self.assertIn("earnings_history", html)
        # Indicator help modal & ? buttons
        self.assertIn('class="help-q"', html)
        self.assertIn('id="ind_modal"', html)
        self.assertIn("openIndicatorHelp", html)
        self.assertIn("closeIndicatorHelp", html)
        self.assertIn("INDICATOR_GUIDES", html)
        self.assertIn("CDC ActionZone", html)
        # 52W High and Low chips in Fibo strip
        self.assertIn('id="chip_w52_hi"', html)
        self.assertIn('id="chip_w52_lo"', html)
        self.assertIn('id="btn_fibo_mode"', html)
        # News Modal & Synthesis Popup
        self.assertIn('id="news_modal"', html)
        self.assertIn('id="nm_title_th"', html)
        self.assertIn('id="nm_summary"', html)
        self.assertIn('id="nm_impact"', html)
        self.assertIn('id="nm_action"', html)
        self.assertIn("openNewsModal", html)
        self.assertIn("closeNewsModal", html)
        # Elliott Wave Macro & Active Wave Engine
        self.assertIn("getActiveElliottWave", html)
        self.assertIn("current_wave_badge", str(html))
        # Classical Chart Pattern Auto-Enable & Start Marker
        self.assertIn("pat: true", html)
        self.assertIn('id="tog_pat"', html)
        self.assertIn('id="btn_toggle_pat_chart"', html)
        self.assertIn("🚩 จุดเริ่มแพทเทิร์น", html)

    def test_classical_pattern_key_points_and_start_role(self):
        from src.chart_data import detect_chart_patterns
        # Generate synthetic consolidation box candles
        candles = [
            {"time": f"2024-01-{(i % 28) + 1:02d}", "open": 100.0, "high": 105.0 if i == 10 else 102.0, "low": 95.0 if i == 20 else 98.0, "close": 100.0, "volume": 1000}
            for i in range(40)
        ]
        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertIn("key_points", pat)
        self.assertGreaterEqual(len(pat["key_points"]), 2)
        # Earliest key point has role: "start"
        self.assertEqual(pat["key_points"][0].get("role"), "start")


class ConfluenceScoringTest(unittest.TestCase):
    def _score(self, **kwargs):
        from src.chart_data import compute_ai_confluence_signals
        candles = [
            {"time": f"2024-01-{i + 1:02d}", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(30)
        ]
        base = dict(candles=candles, fibo_levels={}, pattern=None, poc_price=0.0, current_st_trend="BEARISH",
                    current_rsi=50.0, current_macd_hist=0.0, atr_val=1.0)
        base.update(kwargs)
        signals = compute_ai_confluence_signals(**base)
        current = signals[-1]
        return current

    def test_corrective_wave_does_not_add_buy_score(self):
        baseline = self._score()
        corrective = self._score(elliott_wave={"detected": True, "type": "Corrective Wave (A-B-C)", "current_wave": "Wave (C)", "target": 90.0})
        self.assertEqual(corrective["score"], baseline["score"])

    def test_bullish_impulse_adds_buy_score(self):
        baseline = self._score()
        impulse = self._score(elliott_wave={"detected": True, "type": "Bullish Impulse (1-2-3-4-5)", "current_wave": "Wave (5)", "target": 120.0})
        self.assertEqual(impulse["score"], baseline["score"] + 1)

    def test_pivot_s1_only_counts_when_price_holds_above_support(self):
        baseline = self._score()
        below = self._score(pivots={"r1": 200.0, "s1": 102.0})
        above = self._score(pivots={"r1": 200.0, "s1": 98.0})
        self.assertEqual(below["score"], baseline["score"])
        self.assertEqual(above["score"], baseline["score"] + 1)


class EarningsHistoryEdgeTest(unittest.TestCase):
    def test_short_trailing_window_is_ignored(self):
        from src.chart_data import detect_earnings_history
        candles = [
            {"time": f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(130)
        ]
        candles[-1] = {**candles[-1], "close": 120.0, "volume": 9000}
        self.assertEqual(detect_earnings_history(candles), [])


class SuperInvestorsAsOfTest(unittest.TestCase):
    def test_every_entry_carries_as_of_note(self):
        from src.chart_data import get_super_investors, SUPER_INVESTORS_AS_OF
        for ticker in ("LLY", "UNKNOWN_XYZ"):
            self.assertTrue(all(w["as_of"] == SUPER_INVESTORS_AS_OF for w in get_super_investors(ticker)))


class FallingKnifeShieldTest(unittest.TestCase):
    def test_red_plunge_day_is_not_actionable_and_gets_forming_base_tier(self):
        # A stock plunging -6.5% on a red candle
        data = _row(open=105.0, close=98.0, change=-6.6, RSI=30.0, RSI_prev=36.0, SMA200=90.0)
        eval_res = evaluate_stock(data)
        self.assertFalse(eval_res["is_actionable"])
        self.assertTrue(eval_res["is_plunge_day"])
        self.assertIn("รอสร้างฐาน", eval_res["tier"])
        self.assertIn("⚠️ Plunge Day (มีดยังหล่น)", eval_res["signal_tags"])

    def test_green_reversal_candle_is_actionable(self):
        # A stock rebounding with green candle and RSI hook up
        data = _row(open=95.0, close=98.0, change=1.5, RSI=34.0, **{"RSI[1]": 31.0, "SMA200": 90.0})
        eval_res = evaluate_stock(data)
        self.assertTrue(eval_res["is_actionable"])
        self.assertFalse(eval_res["is_plunge_day"])
        self.assertIn("Actionable", eval_res["tier"])
        self.assertIn("Green Reversal Candle 🕯️🟢", eval_res["signal_tags"])

    def test_stoch_rsi_floor_noise_is_filtered(self):
        # Stoch RSI pinned at 4 vs 3 should NOT trigger fresh_stoch_cross
        data = _row(**{"Stoch.RSI.K": 4.5, "Stoch.RSI.D": 3.0, "Stoch.RSI.K[1]": 2.5, "Stoch.RSI.D[1]": 3.0})
        eval_res = evaluate_stock(data)
        self.assertFalse(eval_res["fresh_stoch_cross"])

    def test_filter_stocks_require_reversal_excludes_falling_knives(self):
        knife = _row(ticker="KNIFE", open=100.0, close=93.0, change=-7.0, RSI=30.0)
        reversal = _row(ticker="REV", open=92.0, close=95.0, change=1.0, RSI=34.0, **{"RSI[1]": 31.0})
        filtered = filter_stocks([knife, reversal], rsi_max=40.0, require_reversal=True)
        self.assertEqual([s["ticker"] for s in filtered], ["REV"])


if __name__ == "__main__":
    unittest.main()

