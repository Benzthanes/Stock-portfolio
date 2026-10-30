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


class ConfirmedEarningsReactionTest(unittest.TestCase):
    def test_bmo_reaction_on_same_calendar_day(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        candles = [
            {"time": "2024-04-23", "close": 100.0},
            {"time": "2024-04-24", "close": 112.5},
            {"time": "2024-04-25", "close": 115.0},
        ]
        res = calculate_confirmed_earnings_reaction(candles, ["2024-04-24"], timing="bmo")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["time"], "2024-04-24")
        self.assertEqual(res[0]["reaction_pct"], 12.5)
        self.assertIn("+12.5%", res[0]["text"])
        self.assertEqual(res[0]["position"], "belowBar")

    def test_amc_reaction_on_next_trading_session(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        candles = [
            {"time": "2026-08-03", "close": 125.65},  # Announcement date AMC
            {"time": "2026-08-04", "close": 162.66},  # Reaction trading session
            {"time": "2026-08-05", "close": 160.00},
        ]
        res = calculate_confirmed_earnings_reaction(candles, ["2026-08-03"], timing="amc")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["time"], "2026-08-04")
        self.assertEqual(res[0]["reaction_pct"], 29.5)
        self.assertIn("+29.5%", res[0]["text"])

    def test_amc_negative_reaction_drop(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        candles = [
            {"time": "2026-04-22", "close": 103.07},  # Announcement date AMC
            {"time": "2026-04-23", "close": 84.78},   # Reaction trading session
        ]
        res = calculate_confirmed_earnings_reaction(candles, ["2026-04-22"], timing="amc")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["time"], "2026-04-23")
        self.assertEqual(res[0]["reaction_pct"], -17.7)
        self.assertIn("-17.7%", res[0]["text"])
        self.assertEqual(res[0]["position"], "aboveBar")

    def test_amc_skips_when_next_candle_not_closed(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        candles = [
            {"time": "2026-10-27", "close": 100.0},
            {"time": "2026-10-28", "close": 105.0},  # Latest bar today, announced AMC tonight
        ]
        res = calculate_confirmed_earnings_reaction(candles, ["2026-10-28"], timing="amc")
        self.assertEqual(res, [])

    def test_ticker_pltr_default_timing_amc(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        candles = [
            {"time": "2026-08-03", "close": 125.65},  # PLTR announced AMC on 2026-08-03
            {"time": "2026-08-04", "close": 162.66},  # Next session reaction
        ]
        res = calculate_confirmed_earnings_reaction(candles, ["2026-08-03"], ticker="PLTR")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["time"], "2026-08-04")
        self.assertEqual(res[0]["reaction_pct"], 29.5)
        self.assertIn("+29.5%", res[0]["text"])

    def test_explicit_timing_overrides_ticker(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        candles = [
            {"time": "2026-08-02", "close": 123.00},
            {"time": "2026-08-03", "close": 125.65},  # Same-day reaction if forced BMO
            {"time": "2026-08-04", "close": 162.66},
        ]
        res = calculate_confirmed_earnings_reaction(candles, ["2026-08-03"], timing="bmo", ticker="PLTR")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["time"], "2026-08-03")
        self.assertEqual(res[0]["reaction_pct"], 2.2)

    def test_unknown_ticker_timing_reaction_none(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        candles = [
            {"time": "2026-05-10", "close": 50.0},
            {"time": "2026-05-11", "close": 55.0},
        ]
        res = calculate_confirmed_earnings_reaction(candles, ["2026-05-11"], ticker="UNKNOWN_TICKER_XYZ")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["time"], "2026-05-11")
        self.assertIsNone(res[0]["reaction_pct"])
        self.assertEqual(res[0]["text"], "🗓️ งบ")

    def test_vrt_nok_vst_timings_are_bmo(self):
        from src.earnings_calendar import get_earnings_timing
        self.assertEqual(get_earnings_timing("VRT"), "bmo")
        self.assertEqual(get_earnings_timing("NOK"), "bmo")
        self.assertEqual(get_earnings_timing("VST"), "bmo")

    def test_newly_added_earnings_timings(self):
        from src.earnings_calendar import get_earnings_timing
        self.assertEqual(get_earnings_timing("SKHY"), "bmo")
        self.assertEqual(get_earnings_timing("AAPL"), "amc")
        self.assertEqual(get_earnings_timing("MSFT"), "amc")
        self.assertEqual(get_earnings_timing("AMZN"), "amc")
        self.assertEqual(get_earnings_timing("JPM"), "bmo")
        self.assertEqual(get_earnings_timing("SPCX"), "amc")
        self.assertEqual(get_earnings_timing("PLTR"), "amc")

    def test_three_year_tickers_have_twelve_quarters(self):
        from src.earnings_calendar import get_confirmed_earnings_dates
        three_year_tickers = [
            "VRT", "NOK", "LLY", "GOOGL", "BAC", "ABNB", "APP",
            "MNST", "NOW", "PLTR", "VST", "SKHY", "NVDA", "AAPL",
            "MSFT", "AMZN", "JPM"
        ]
        for ticker in three_year_tickers:
            dates = get_confirmed_earnings_dates(ticker)
            self.assertEqual(
                len(dates), 12,
                f"Ticker {ticker} should have exactly 12 quarterly earnings dates, got {len(dates)}"
            )

    def test_spcx_has_post_ipo_earnings_only(self):
        from src.earnings_calendar import get_confirmed_earnings_dates
        dates = get_confirmed_earnings_dates("SPCX")
        self.assertEqual(len(dates), 2)
        for d in dates:
            self.assertGreater(d, "2026-06-12", f"SPCX earnings date {d} must be after IPO 2026-06-12")

    def test_added_missing_quarters_present(self):
        from src.earnings_calendar import get_confirmed_earnings_dates
        expected_added_dates = {
            "VRT": "2024-02-21",
            "LLY": "2024-02-06",
            "BAC": "2024-01-12",
            "NOW": "2024-01-24",
            "APP": "2024-02-14",
            "SKHY": "2024-01-25",
            "GOOGL": "2026-02-04",
            "ABNB": "2026-02-12",
            "MNST": "2026-02-26",
            "NVDA": "2026-11-17",
        }
        for ticker, expected_date in expected_added_dates.items():
            dates = get_confirmed_earnings_dates(ticker)
            self.assertIn(
                expected_date, dates,
                f"Ticker {ticker} should contain added confirmed date {expected_date}"
            )

    def test_reaction_for_newly_timed_tickers(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        # Test BMO reaction on same day (JPM)
        jpm_candles = [
            {"time": "2024-01-11", "close": 170.0},
            {"time": "2024-01-12", "close": 168.0},
        ]
        res_jpm = calculate_confirmed_earnings_reaction(jpm_candles, ["2024-01-12"], ticker="JPM")
        self.assertEqual(len(res_jpm), 1)
        self.assertEqual(res_jpm[0]["time"], "2024-01-12")
        self.assertEqual(res_jpm[0]["reaction_pct"], -1.2)

        # Test AMC reaction on next session (AAPL)
        aapl_candles = [
            {"time": "2024-10-31", "close": 225.0},
            {"time": "2024-11-01", "close": 222.0},
        ]
        res_aapl = calculate_confirmed_earnings_reaction(aapl_candles, ["2024-10-31"], ticker="AAPL")
        self.assertEqual(len(res_aapl), 1)
        self.assertEqual(res_aapl[0]["time"], "2024-11-01")
        self.assertEqual(res_aapl[0]["reaction_pct"], -1.3)

    def test_vst_dates_contains_2024_05_08_not_09(self):
        from src.earnings_calendar import get_confirmed_earnings_dates
        dates = get_confirmed_earnings_dates("VST")
        self.assertIn("2024-05-08", dates)
        self.assertNotIn("2024-05-09", dates)

    def test_vst_reaction_uses_bmo_same_session(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction
        candles = [
            {"time": "2024-05-07", "close": 80.0},
            {"time": "2024-05-08", "close": 88.0},  # VST announced BMO on 2024-05-08
            {"time": "2024-05-09", "close": 90.0},
        ]
        res = calculate_confirmed_earnings_reaction(candles, ["2024-05-08"], ticker="VST")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["time"], "2024-05-08")
        self.assertEqual(res[0]["reaction_pct"], 10.0)
        self.assertIn("+10.0%", res[0]["text"])


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
        import shutil
        import tempfile
        from pathlib import Path
        from unittest import mock
        from src import chart_data

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tmp_path = Path(tmp.name)
        tmp_cache = tmp_path / "candles_cache.json"

        # Copy existing cache to temp dir if it exists so tests have realistic fixtures without touching disk data/
        real_cache_path = chart_data.CACHE_PATH
        if real_cache_path.exists():
            shutil.copyfile(real_cache_path, tmp_cache)
        else:
            tmp_cache.write_text("{}", encoding="utf-8")

        for patcher in (
            mock.patch("src.chart_page.REPORTS_DIR", tmp_path),
            mock.patch.object(chart_data, "CACHE_PATH", tmp_cache),
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
        # Classical Chart Pattern Toggle & Start Marker
        self.assertIn("pat: false", html)
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

    def test_failed_pattern_appends_breakdown_point(self):
        from src.chart_data import detect_chart_patterns
        # Pad with initial bars so len >= 25
        pad = [55.0] * 15
        prices = pad + [
            55.0, 54.0, 53.0, 52.5, 52.0,  # t1
            53.0, 54.0, 54.5, 53.5, 52.8, 52.0,  # neck, t2
            53.2, 54.2, 54.8, 53.0, 49.0   # rebound, breakdown
        ]
        candles = [
            {"time": f"2024-01-{(i % 28) + 1:02d}", "open": p, "high": p + 0.2, "low": p - 0.2, "close": p, "volume": 1000}
            for i, p in enumerate(prices)
        ]
        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertEqual(pat.get("status"), "failed")
        kp_names = [kp["name"] for kp in pat.get("key_points", [])]
        self.assertTrue(any("Breakdown" in name for name in kp_names))


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
        self.assertTrue(any("ไม่ผ่าน backtest ไม่นับคะแนน" in r for r in corrective["reasons"]))

    def test_bullish_impulse_does_not_add_unbacked_score(self):
        baseline = self._score()
        impulse = self._score(elliott_wave={"detected": True, "type": "Bullish Impulse (1-2-3-4-5)", "current_wave": "Wave (5)", "target": 120.0})
        self.assertEqual(impulse["score"], baseline["score"])
        self.assertTrue(any("ไม่ผ่าน backtest ไม่นับคะแนน" in r for r in impulse["reasons"]))

    def test_new_cycle_breakout_does_not_add_unbacked_score(self):
        baseline = self._score()
        new_cycle = self._score(elliott_wave={"detected": True, "type": "New Cycle Wave (1) Breakout", "current_wave": "New Cycle (1)", "target": 150.0})
        self.assertEqual(new_cycle["score"], baseline["score"])
        self.assertTrue(any("ไม่ผ่าน backtest ไม่นับคะแนน" in r for r in new_cycle["reasons"]))

    def test_bearish_impulse_does_not_add_buy_score(self):
        baseline = self._score()
        bearish = self._score(elliott_wave={"detected": True, "type": "Bearish Impulse (1-2-3-4-5)", "current_wave": "Bear Wave (5)", "target": 70.0})
        self.assertEqual(bearish["score"], baseline["score"])
        self.assertTrue(any("ไม่ผ่าน backtest ไม่นับคะแนน" in r for r in bearish["reasons"]))

    def test_pivot_s1_does_not_add_unbacked_score(self):
        baseline = self._score()
        below = self._score(pivots={"r1": 200.0, "s1": 102.0})
        above = self._score(pivots={"r1": 200.0, "s1": 98.0})
        self.assertEqual(below["score"], baseline["score"])
        self.assertEqual(above["score"], baseline["score"])
        self.assertTrue(any("ไม่ผ่าน backtest ไม่นับคะแนน" in r for r in above["reasons"]))

    def test_luxalgo_elliott_wave_detection_and_fibo_grid(self):
        from src.chart_data import detect_elliott_wave
        # Construct synthetic candles exhibiting a 5-wave impulse: 100 -> 120 -> 110 -> 145 -> 130 -> 160
        candles = []
        prices = (
            [100.0 + i * 2.0 for i in range(11)] +      # W1: 100 to 120
            [120.0 - i * 1.0 for i in range(1, 11)] +   # W2: 120 to 110
            [110.0 + i * 3.5 for i in range(1, 11)] +   # W3: 110 to 145
            [145.0 - i * 1.5 for i in range(1, 11)] +   # W4: 145 to 130
            [130.0 + i * 3.0 for i in range(1, 11)]     # W5: 130 to 160
        )
        for i, p in enumerate(prices):
            candles.append({
                "time": f"2024-01-{(i % 28) + 1:02d}",
                "open": p - 0.5,
                "high": p + 1.0,
                "low": p - 1.0,
                "close": p,
                "volume": 1000 + i * 10
            })
        ew = detect_elliott_wave(candles)
        self.assertTrue(ew["detected"])
        self.assertIn("Impulse", ew["type"])
        self.assertIsNotNone(ew["fibo_pullback"])
        self.assertIn("fib_618", ew["fibo_pullback"])
        self.assertIn("fib_854", ew["fibo_pullback"])


class EarningsHistoryEdgeTest(unittest.TestCase):
    def test_short_leading_window_is_ignored(self):
        from src.chart_data import detect_earnings_history
        candles = [
            {"time": f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(130)
        ]
        # In backward slicing of 130 bars (62 + 62 + 6), the short stub of 6 bars is at the beginning (index 0..5)
        candles[0] = {**candles[0], "close": 120.0, "volume": 9000}
        self.assertEqual(detect_earnings_history(candles), [])

    def test_recent_earnings_spike_in_latest_window_is_detected(self):
        from src.chart_data import detect_earnings_history
        candles = [
            {"time": f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(130)
        ]
        # Spike on the latest bar is in the full trailing 62-day window and must be detected
        candles[-1] = {**candles[-1], "close": 120.0, "volume": 9000}
        history = detect_earnings_history(candles)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["time"], candles[-1]["time"])
        self.assertEqual(history[0]["reaction_pct"], 20.0)

    def test_pending_earnings_window_does_not_place_fake_marker(self):
        from src.chart_data import detect_earnings_history
        candles = [
            {"time": f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}
            for i in range(130)
        ]
        # Volume surge 10 days before upcoming earnings must NOT be falsely marked as earnings reaction
        candles[-10] = {**candles[-10], "close": 95.0, "volume": 9000}
        history = detect_earnings_history(candles, days_to_earnings=0.3)
        self.assertEqual(history, [])

    def test_etf_has_no_earnings_history(self):
        from src.chart_data import detect_earnings_history
        candles = [
            {"time": f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 9000}
            for i in range(130)
        ]
        self.assertEqual(detect_earnings_history(candles, is_etf=True), [])
        self.assertEqual(detect_earnings_history(candles, ticker="VOO"), [])
        self.assertEqual(detect_earnings_history(candles, ticker="QQQI"), [])

    def test_vrt_confirmed_earnings_calendar_excludes_false_volume_spikes(self):
        from src.chart_data import detect_earnings_history, load_candles_cache
        cache = load_candles_cache()
        if "VRT" in cache and cache["VRT"].get("candles"):
            candles = cache["VRT"]["candles"]
            history = detect_earnings_history(candles, ticker="VRT")
            times = [h["time"] for h in history]
            # 2026-10-15 was a false heuristic volume spike, not an earnings date
            self.assertNotIn("2026-10-15", times)
            # 2026-07-29 was actual Q2 earnings
            self.assertIn("2026-07-29", times)
            h_jul29 = next(h for h in history if h["time"] == "2026-07-29")
            self.assertEqual(h_jul29["reaction_pct"], -17.3)
            # 2026-02-11 was actual Q4 earnings (+24.5%)
            self.assertIn("2026-02-11", times)
            h_feb11 = next(h for h in history if h["time"] == "2026-02-11")
            self.assertEqual(h_feb11["reaction_pct"], 24.5)
            # 2026-10-28 has not closed in cached daily bars yet, so no premature marker
            if candles[-1]["time"] < "2026-10-28":
                self.assertNotIn("2026-10-28", times)

    def test_nok_confirmed_earnings_calendar(self):
        from src.chart_data import detect_earnings_history, load_candles_cache
        cache = load_candles_cache()
        if "NOK" in cache and cache["NOK"].get("candles"):
            candles = cache["NOK"]["candles"]
            history = detect_earnings_history(candles, ticker="NOK")
            times = [h["time"] for h in history]
            # 2026-10-22 was actual Q3 earnings (-14.8%)
            self.assertIn("2026-10-22", times)
            h_oct22 = next(h for h in history if h["time"] == "2026-10-22")
            self.assertEqual(h_oct22["reaction_pct"], -14.8)


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


class LuxAlgoSupportResistanceTest(unittest.TestCase):
    def test_luxalgo_sr_insufficient_bars(self):
        from src.chart_data import compute_luxalgo_support_resistance
        res = compute_luxalgo_support_resistance([])
        self.assertIsNone(res["resistance"])
        self.assertIsNone(res["support"])

    def test_luxalgo_sr_detects_levels_and_breaks(self):
        from src.chart_data import compute_luxalgo_support_resistance
        candles = []
        for i in range(50):
            candles.append({
                "time": f"2026-01-{(i%28)+1:02d}",
                "open": 100.0,
                "high": 105.0 if i == 20 else 102.0,
                "low": 95.0 if i == 30 else 98.0,
                "close": 100.0,
                "volume": 1000000
            })
        # Last candle breaks out above 105 with volume surge
        candles.append({
            "time": "2026-02-21",
            "open": 103.0,
            "high": 110.0,
            "low": 103.0,
            "close": 108.0,
            "volume": 5000000
        })
        res = compute_luxalgo_support_resistance(candles, left_bars=5, right_bars=5)
        self.assertIsNotNone(res["resistance"])
        self.assertIsNotNone(res["support"])
        self.assertTrue(len(res["recent_breaks"]) > 0)


class SmartMoneyConceptsTest(unittest.TestCase):
    def test_smc_insufficient_candles(self):
        from src.chart_data import compute_smart_money_concepts
        res = compute_smart_money_concepts([])
        self.assertEqual(res["unmitigated_fvgs"], [])
        self.assertEqual(res["order_blocks"], [])

    def test_smc_detects_bullish_fvg(self):
        from src.chart_data import compute_smart_money_concepts
        candles = []
        for i in range(25):
            candles.append({
                "time": f"2026-01-{(i%28)+1:02d}",
                "open": 100.0 + i,
                "high": 102.0 + i,
                "low": 99.0 + i,
                "close": 101.0 + i,
                "volume": 1000000
            })
        # Create a Bullish FVG: candle[22].low > candle[20].high
        candles[20] = {"time": "2026-01-21", "open": 120.0, "high": 122.0, "low": 119.0, "close": 121.0, "volume": 1000000}
        candles[21] = {"time": "2026-01-22", "open": 122.0, "high": 130.0, "low": 122.0, "close": 129.0, "volume": 3000000}
        candles[22] = {"time": "2026-01-23", "open": 129.0, "high": 132.0, "low": 125.0, "close": 131.0, "volume": 2000000}
        res = compute_smart_money_concepts(candles)
        self.assertIn("unmitigated_fvgs", res)
        bullish_fvgs = [f for f in res["unmitigated_fvgs"] if f["type"] == "BULLISH_FVG"]
        self.assertTrue(len(bullish_fvgs) > 0)


class SqueezeMomentumTest(unittest.TestCase):
    def test_insufficient_candles(self):
        from src.chart_data import compute_squeeze_momentum
        res = compute_squeeze_momentum([])
        self.assertEqual(res["status"], "NO_SQUEEZE")
        self.assertFalse(res["squeeze_on"])
        self.assertFalse(res["squeeze_fired"])
        self.assertEqual(res["momentum"], 0.0)
        self.assertEqual(res["histogram"], [])

    def test_squeeze_compression_and_structure(self):
        from src.chart_data import compute_squeeze_momentum
        # 30 tight range candles to induce volatility compression
        candles = []
        for i in range(35):
            candles.append({
                "time": f"2026-01-{(i%28)+1:02d}",
                "open": 100.0,
                "high": 100.2,
                "low": 99.8,
                "close": 100.0,
                "volume": 100000
            })
        res = compute_squeeze_momentum(candles)
        self.assertIn(res["status"], ["SQUEEZE_ON", "SQUEEZE_FIRED", "NORMAL"])
        self.assertIn("momentum", res)
        self.assertIn("direction", res)
        self.assertIn("histogram", res)
        self.assertTrue(len(res["histogram"]) > 0)
        entry = res["histogram"][-1]
        self.assertIn("time", entry)
        self.assertIn("value", entry)
        self.assertIn("color", entry)
        self.assertIn("sqz_on", entry)
        self.assertIn("sqz_off", entry)
        self.assertIn("dot_color", entry)


class ChandelierExitTest(unittest.TestCase):
    def test_insufficient_candles(self):
        from src.chart_data import compute_chandelier_exit
        res = compute_chandelier_exit([])
        self.assertEqual(res["status"], "NEUTRAL")
        self.assertEqual(res["direction"], "NEUTRAL")
        self.assertEqual(res["trailing_stop"], 0.0)
        self.assertEqual(res["series"], [])

    def test_chandelier_calculation(self):
        from src.chart_data import compute_chandelier_exit
        candles = []
        for i in range(40):
            candles.append({
                "time": f"2026-01-{(i%28)+1:02d}",
                "open": 100.0 + i,
                "high": 102.0 + i,
                "low": 99.0 + i,
                "close": 101.5 + i,
                "volume": 1000000
            })
        res = compute_chandelier_exit(candles)
        self.assertIn(res["status"], ["BUY_SIGNAL", "SELL_SIGNAL", "LONG", "SHORT"])
        self.assertIn(res["direction"], ["LONG", "SHORT"])
        self.assertGreater(res["trailing_stop"], 0.0)
        self.assertGreater(res["long_stop"], 0.0)
        self.assertGreater(res["short_stop"], 0.0)
        self.assertIn("series", res)
        self.assertTrue(len(res["series"]) > 0)


class CandleDateIntegrityTest(unittest.TestCase):
    def test_candle_timestamp_utc_determinism(self):
        import json
        from unittest.mock import patch
        from src.chart_data import fetch_ticker_candles

        fake_yahoo_response = {
            "chart": {
                "result": [{
                    "timestamp": [1793280600],
                    "indicators": {
                        "quote": [{
                            "open": [1332.73],
                            "high": [1408.38],
                            "low": [1330.00],
                            "close": [1381.14],
                            "volume": [1778906]
                        }]
                    }
                }]
            }
        }
        with patch("src.chart_data.http_get") as mock_get:
            mock_get.return_value = json.dumps(fake_yahoo_response).encode("utf-8")
            candles = fetch_ticker_candles("LLY")
            self.assertEqual(len(candles), 1)
            self.assertEqual(candles[0]["time"], "2026-10-29")
            self.assertEqual(candles[0]["close"], 1381.14)

    def test_confirmed_earnings_reaction_lly_exact_date(self):
        from src.earnings_calendar import calculate_confirmed_earnings_reaction, get_confirmed_earnings_dates
        dates = get_confirmed_earnings_dates("LLY")
        self.assertIn("2026-10-29", dates)
        mock_candles = [
            {"time": "2026-10-28", "open": 1268.55, "high": 1299.43, "low": 1260.34, "close": 1288.30, "volume": 2052000},
            {"time": "2026-10-29", "open": 1332.73, "high": 1408.38, "low": 1330.00, "close": 1381.14, "volume": 1778906},
        ]
        events = calculate_confirmed_earnings_reaction(mock_candles, dates, ticker="LLY")
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["time"], "2026-10-29")
        self.assertEqual(ev["reaction_pct"], 7.2)
        self.assertEqual(ev["text"], "🗓️ +7.2%")
        self.assertEqual(ev["position"], "belowBar")


if __name__ == "__main__":
    unittest.main()



