import unittest
from src.earnings_calendar import (
    CONFIRMED_EARNINGS_DATES,
    CONFIRMED_EARNINGS_TIMING,
    get_earnings_timing,
)
from src.portfolio import (
    CONCENTRATION_WARN_PCT,
    compute_financial_health,
    compute_stock_rating,
)
from src.scoring import (
    PORTFOLIO_HEALTH_BANDS,
    compute_rebalance_score,
    evaluate_portfolio_health,
)
from src.screener import (
    atr_stop_loss,
    evaluate_stock,
    filter_stocks,
    trade_levels,
)


class TestPortfolioConcentration(unittest.TestCase):
    def test_concentration_warn_pct_constant(self):
        self.assertEqual(CONCENTRATION_WARN_PCT, 40.0)


class TestEarningsTimingAndDates(unittest.TestCase):
    def test_unknown_ticker_timing_is_unknown(self):
        self.assertNotIn("UNKNOWN_XYZ", CONFIRMED_EARNINGS_TIMING)
        self.assertIsNone(get_earnings_timing("UNKNOWN_XYZ"))

    def test_skhy_confirmed_timing(self):
        self.assertEqual(get_earnings_timing("SKHY"), "bmo")

    def test_vst_confirmed_date_and_timing(self):
        vst_dates = CONFIRMED_EARNINGS_DATES.get("VST", [])
        self.assertIn("2024-05-08", vst_dates)
        self.assertNotIn("2024-05-09", vst_dates)
        self.assertEqual(get_earnings_timing("VST"), "bmo")

    def test_vrt_and_nok_timing(self):
        self.assertEqual(get_earnings_timing("VRT"), "bmo")
        self.assertEqual(get_earnings_timing("NOK"), "bmo")


class TestTradeLevels(unittest.TestCase):
    def test_trade_levels_with_full_data(self):
        row = {
            "close": 100.0,
            "ATR": 2.0,
            "SMA200": 95.0,
            "SMA50": 110.0,
            "BB.lower": 92.0,
            "BB.upper": 108.0,
        }
        res = trade_levels(row)
        self.assertEqual(res["atr"], 2.0)
        self.assertEqual(res["stop_loss"], 97.0)
        self.assertEqual(res["take_profit"], 110.0)
        self.assertEqual(res["key_support"], 95.0)
        self.assertEqual(res["support_desc"], "เส้น 200 วัน (SMA 200)")
        self.assertEqual(res["key_resistance"], 110.0)
        self.assertEqual(res["resistance_desc"], "เส้น 50 วัน (Mean Reversion)")
        self.assertEqual(res["risk"], 3.0)
        self.assertEqual(res["reward"], 10.0)
        self.assertEqual(res["rr_ratio"], 3.3)

    def test_trade_levels_missing_atr_returns_none(self):
        row = {"close": 100.0, "SMA200": 90.0}
        res = trade_levels(row)
        self.assertIsNone(res["atr"])
        self.assertEqual(res["stop_loss"], 95.0)  # fallback 5%

    def test_stop_loss_is_never_negative(self):
        # Huge ATR and low price
        sl = atr_stop_loss(1.0, 50.0)
        self.assertGreaterEqual(sl, 0.0)
        res = trade_levels({"close": 0.5, "ATR": 100.0})
        self.assertGreaterEqual(res["stop_loss"], 0.0)

    def test_zero_or_negative_close(self):
        res = trade_levels({"close": 0.0})
        self.assertIsNone(res["stop_loss"])
        self.assertIsNone(res["atr"])


class TestPortfolioHealthBands(unittest.TestCase):
    def test_portfolio_health_bands_order_and_labels(self):
        self.assertEqual(len(PORTFOLIO_HEALTH_BANDS), 5)
        grades = [b.grade for b in PORTFOLIO_HEALTH_BANDS]
        self.assertEqual(grades, ["ดีมาก", "ดี", "พอใช้", "ต้องระวัง", "เสี่ยง"])

    def test_evaluate_portfolio_health(self):
        self.assertEqual(evaluate_portfolio_health(90.0).grade, "ดีมาก")
        self.assertEqual(evaluate_portfolio_health(85.0).grade, "ดีมาก")
        self.assertEqual(evaluate_portfolio_health(80.0).grade, "ดี")
        self.assertEqual(evaluate_portfolio_health(70.0).grade, "ดี")
        self.assertEqual(evaluate_portfolio_health(60.0).grade, "พอใช้")
        self.assertEqual(evaluate_portfolio_health(55.0).grade, "พอใช้")
        self.assertEqual(evaluate_portfolio_health(45.0).grade, "ต้องระวัง")
        self.assertEqual(evaluate_portfolio_health(40.0).grade, "ต้องระวัง")
        self.assertEqual(evaluate_portfolio_health(35.0).grade, "เสี่ยง")
        self.assertEqual(evaluate_portfolio_health(0.0).grade, "เสี่ยง")


class TestRebalanceScore(unittest.TestCase):
    def test_compute_rebalance_score(self):
        score_above = compute_rebalance_score(
            stars=5,
            in_value_zone=True,
            dist_ema200_pct=2.5,
            is_etf=False,
            weight_pct=4.0,
            target_upside_pct=20.0,
            fundamental_pct=90.0,
        )
        score_below = compute_rebalance_score(
            stars=5,
            in_value_zone=True,
            dist_ema200_pct=-5.0,
            is_etf=False,
            weight_pct=4.0,
            target_upside_pct=20.0,
            fundamental_pct=90.0,
        )
        self.assertGreater(score_above, score_below)
        self.assertEqual(round(score_above - score_below, 2), 2.0)


class TestDipTierAndGuards(unittest.TestCase):
    BASE_STOCK = {
        "ticker": "GOOD",
        "open": 100.0,
        "close": 102.0,
        "change": 2.0,
        "RSI": 35.0,
        "RSI[1]": 30.0,
        "SMA200": 98.0,
        "EMA200": 98.0,
        "RSI|1W": 50.0,
        "total_revenue_yoy_growth_ttm": 25.0,
        "net_income_yoy_growth_ttm": 30.0,
        "return_on_equity_fq": 25.0,
        "price_earnings_growth_ttm": 0.8,
        "debt_to_equity_fq": 0.5,
        "free_cash_flow_ttm": 1e9,
    }

    def test_actionable_dip_buy_for_top_stock_with_hook(self):
        res = evaluate_stock(self.BASE_STOCK)
        self.assertEqual(res["tier"], "⭐⭐⭐ Actionable Dip Buy 🎯")
        self.assertTrue(res["is_actionable"])
        self.assertFalse(res["is_plunge_day"])

    def test_plunge_guard_forces_forming_base_tier(self):
        plunging = dict(self.BASE_STOCK, change=-5.0, close=95.0, open=100.0)
        res = evaluate_stock(plunging)
        self.assertEqual(res["tier"], "👀 รอสร้างฐาน (Forming Base - วันทิ้งตัว)")
        self.assertFalse(res["is_actionable"])
        self.assertTrue(res["is_plunge_day"])

    def test_earnings_guard_forces_earnings_tier(self):
        import time
        now_ts = int(time.time())
        near_earnings = dict(self.BASE_STOCK, earnings_release_next_date=now_ts + 5 * 86400)
        res = evaluate_stock(near_earnings)
        self.assertEqual(res["tier"], "⚠️ รอพ้นวันงบ (Earnings Guard)")
        self.assertFalse(res["is_actionable"])
        self.assertTrue(res["is_earnings_near"])

    def test_no_entry_signal_goes_to_watchlist_reversal(self):
        # RSI not hooking up (rsi < rsi_prev)
        no_hook = dict(self.BASE_STOCK, RSI=32.0, **{"RSI[1]": 35.0})
        res = evaluate_stock(no_hook)
        self.assertEqual(res["tier"], "⭐ Watchlist (รอแท่งกลับตัว)")
        self.assertFalse(res["is_actionable"])

    def test_unbacked_indicators_do_not_affect_tier(self):
        # High ADX should NOT change tier or deduct arbitrary points
        high_adx = dict(self.BASE_STOCK, ADX=45.0)
        res = evaluate_stock(high_adx)
        self.assertEqual(res["tier"], "⭐⭐⭐ Actionable Dip Buy 🎯")
        self.assertIn("⚠️ High ADX Falling Knife", res["signal_tags"])

    def test_filter_stocks_falling_knife_checks_plunge_day_not_adx(self):
        high_adx_calm = dict(self.BASE_STOCK, ticker="CALM", ADX=45.0, change=1.0)
        plunge_stock = dict(self.BASE_STOCK, ticker="PLUNGE", change=-6.0, open=100.0, close=94.0)
        filtered = filter_stocks([high_adx_calm, plunge_stock], rsi_max=50.0, exclude_falling_knife=True)
        tickers = [s["ticker"] for s in filtered]
        self.assertIn("CALM", tickers)
        self.assertNotIn("PLUNGE", tickers)


class TestEtfNarrative(unittest.TestCase):
    def test_voo_narrative(self):
        res = compute_financial_health({"ticker": "VOO"})
        self.assertEqual(res["peg_verdict"], "N/A (กระจาย 500 บ.)")
        self.assertIn("500 บริษัท", res["summary"])

    def test_qqqi_narrative(self):
        res = compute_financial_health({"ticker": "QQQI"})
        self.assertEqual(res["peg_verdict"], "N/A (Covered Call)")
        self.assertIn("Covered Call", res["summary"])
        self.assertNotIn("500 บริษัท", res["summary"])

    def test_qqq_narrative(self):
        res = compute_financial_health({"ticker": "QQQ"})
        self.assertEqual(res["peg_verdict"], "N/A (กระจาย 100 บ.)")
        self.assertIn("100 บริษัท", res["summary"])


class TestTrendDescSign(unittest.TestCase):
    def test_trend_desc_negative_and_positive(self):
        rev_neg = compute_stock_rating({"ticker": "TST", "dist_sma200_pct": -5.0})
        self.assertIn("ต่ำกว่าเส้น 200 วัน 5.0%", rev_neg["summary"])
        self.assertNotIn("ยืนเหนือเส้น 200 วัน -5.0%", rev_neg["summary"])

        rev_pos = compute_stock_rating({"ticker": "TST", "dist_sma200_pct": 5.0})
        self.assertIn("ยืนเหนือเส้น 200 วัน +5.0%", rev_pos["summary"])


if __name__ == "__main__":
    unittest.main()
