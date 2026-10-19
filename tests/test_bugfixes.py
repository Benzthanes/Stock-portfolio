"""Regression tests for defects found in the 2026-10-19 review. Each test failed before its fix."""

import json
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import recovery
from src import ai_news, news, trades
from src.chart_data import _rma, _rsi_value, detect_earnings_history
from src.portfolio import top_pick_reason
from src.scoring import is_etf, score_fundamentals
from src.screener import evaluate_stock
from src.universe import get_tv_symbols, resolve_custom_tickers


class TradeDateTest(unittest.TestCase):
    def test_two_digit_slash_years(self):
        self.assertEqual(trades.parse_trade_date("12/06/26"), date(2026, 6, 12))
        self.assertEqual(trades.parse_trade_date("12/06/69"), date(2026, 6, 12))

    def test_invalid_dates_return_none(self):
        self.assertIsNone(trades.parse_trade_date("2026-13-01"))
        self.assertIsNone(trades.parse_trade_date("31/02/2026"))


class LedgerWriteTest(unittest.TestCase):
    def test_failed_swap_restores_earlier_files(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.json", Path(d) / "b"
            a.write_text("OLD", encoding="utf-8")
            b.mkdir()
            with self.assertRaises(OSError):
                trades._atomic_write_many([(a, "NEW"), (b, "NEW")])
            self.assertEqual(a.read_text(encoding="utf-8"), "OLD")

    def test_trade_ids_stay_unique_within_one_second(self):
        first = trades._unique_trade_id({"trades": []}, "ZZZ")
        second = trades._unique_trade_id({"trades": [{"id": first}]}, "ZZZ")
        self.assertNotEqual(first, second)
        self.assertEqual(second, first + "-2")

    def test_data_dir_follows_env_not_cwd(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"FILTER_STOCK_DATA_DIR": d}):
            self.assertEqual(trades.data_path("ledger.json"), Path(d) / "ledger.json")
        self.assertEqual(trades.data_path("ledger.json"), ROOT / "data" / "ledger.json")


class SellTest(unittest.TestCase):
    def sell(self, holding, **kw):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "portfolio.json"
            p.write_text(json.dumps({"fx_rate_usd_thb": 33.0, "holdings": [holding]}), encoding="utf-8")
            ledger = Path(d) / "ledger.json"
            ledger.write_text(json.dumps({"cash": {"dime_save_thb": 0.0, "dime_usd": 0.0}}), encoding="utf-8")
            return trades.record_sell(holding["ticker"], 50.0, fx_rate=33.0, portfolio_path=str(p),
                                      trades_path=str(Path(d) / "trades.json"), ledger_path=str(ledger), **kw)

    def test_zero_share_holding_cannot_be_sold(self):
        with self.assertRaises(ValueError):
            self.sell({"ticker": "ZZZ", "shares": 0, "avg_cost_usd": 10.0, "total_cost_usd": 0.0}, dry_run=True)

    def test_realized_cost_is_a_share_of_total_cost(self):
        res = self.sell({"ticker": "ZZZ", "shares": 3.0, "avg_cost_usd": 33.3333, "total_cost_usd": 100.0}, shares=3.0, dry_run=True)
        self.assertEqual(res["trade"]["total_cost_usd"], 100.0)


def gradeable_row(**extra):
    row = {"ticker": "GOOD", "close": 100.0, "SMA20": 105.0, "EMA200": 95.0, "ATR": 2.0,
           "total_revenue_yoy_growth_ttm": 30.0, "net_income_yoy_growth_ttm": 40.0, "return_on_equity_fq": 30.0,
           "price_earnings_growth_ttm": 0.8, "debt_to_equity_fq": 0.3, "free_cash_flow_ttm": 1e9}
    row.update(extra)
    return {k: v for k, v in row.items() if v is not None}


@mock.patch.object(recovery, "get_catalyst_breakdown", lambda t, max_items=4: {"bullish": [], "bearish": [], "all": []})
@mock.patch.object(recovery, "get_forward_outlook", lambda *a, **k: {})
class RecoveryVerdictTest(unittest.TestCase):
    def verdict(self, row, cost=150.0):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "portfolio.json"
            p.write_text(json.dumps({"base_currency": "USD", "holdings": [
                {"ticker": row["ticker"], "exchange": "NASDAQ", "shares": 10, "avg_cost_usd": cost, "total_cost_usd": cost * 10}]}),
                encoding="utf-8")
            with mock.patch.object(recovery, "fetch_screener_data", lambda syms: [row]):
                return recovery.analyze_recovery(row["ticker"], portfolio_path=str(p))["primary_playbook"]

    def test_missing_rsi_is_not_oversold(self):
        self.assertEqual(self.verdict(gradeable_row()), "Hold & Guard")
        self.assertEqual(self.verdict(gradeable_row(RSI=30.0)), "Smart DCA")

    def test_missing_ema200_blocks_smart_dca(self):
        self.assertEqual(self.verdict(gradeable_row(RSI=30.0, EMA200=None)), "Hold & Guard")

    def test_no_fundamentals_is_not_capital_rotation(self):
        row = {"ticker": "NEWCO", "close": 100.0, "RSI": 50.0, "RSI[1]": 49.0, "SMA20": 110.0, "EMA200": 98.0}
        self.assertEqual(self.verdict(row), "Hold & Guard")


class ScreenerTest(unittest.TestCase):
    def test_missing_average_volume_is_not_a_spike(self):
        res = evaluate_stock({"ticker": "IPO", "close": 10.0, "volume": 5_000_000, "average_volume_30d_calc": None})
        self.assertEqual(res["vol_ratio"], 1.0)

    def test_value_zone_matches_scoring_band(self):
        res = evaluate_stock({"ticker": "V", "close": 108.0, "EMA200": 100.0, "SMA200": 100.0})
        self.assertTrue(res["in_value_zone"])
        self.assertEqual(res["stock_score"]["timing"]["metrics"]["ema200_dist"]["points"], 6)

    def test_zero_revenue_growth_is_data_not_an_etf(self):
        self.assertFalse(is_etf("BRK", "Miscellaneous", 0.0))
        self.assertEqual(score_fundamentals("BRK", "Miscellaneous", 0.0, None, 20.0, None, None, None)["grade"], "B")

    def test_top_pick_below_200_day_line_does_not_claim_uptrend(self):
        pick = {"ticker": "X", "dist_sma200_pct": -23.0, "target_upside_pct": 15.0,
                "fundamental": score_fundamentals("X", None, 30, 40, 30, 0.8, 0.3, 1e9)}
        self.assertNotIn("เหนือเส้น 200 วัน", top_pick_reason(pick, str))


class NewsTest(unittest.TestCase):
    def test_sentiment_phrases(self):
        cases = {
            "Apple cuts dividend by 50%": "bearish",
            "Intel narrows loss, shares jump": "bullish",
            "Analyst cuts price target on Nike": "bearish",
            "Stock slips 6% after guidance": "bearish",
            "Q3 profit misses estimates": "bearish",
            "Should you buy Nvidia stock now?": "neutral",
            "Lilly beats estimates": "bullish",
        }
        self.assertEqual({t: news.classify_sentiment(t) for t in cases}, cases)

    def test_minus_zero_offset_is_utc(self):
        self.assertEqual(news._format_relative_time("Fri, 16 Oct 2026 23:30:00 -0000"), "16 Oct 2026")
        self.assertEqual(news._format_relative_time("Fri, 16 Oct 2026 23:30:00 GMT"), "16 Oct 2026")

    def test_latest_means_newest(self):
        now = datetime.now(timezone.utc)
        items = "".join(
            f"<item><title>Story {age} - Src</title><link>https://x/{age}</link><pubDate>{format_datetime(now - timedelta(days=age))}</pubDate></item>"
            for age in (4, 0, 3, 1))
        rss = f"<rss><channel>{items}</channel></rss>".encode()
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(news, "http_get", lambda *a, **k: rss), \
                mock.patch.object(news, "CACHE_FILE", Path(d) / "c.json"), \
                mock.patch.object(news, "_enrich_articles", lambda arts, t: None):
            arts, ok = news.fetch_stock_news_with_status("ZZZ", max_items=2)
        self.assertTrue(ok)
        self.assertEqual([a["title"] for a in arts], ["Story 0", "Story 1"])


class AiNewsTest(unittest.TestCase):
    def test_same_title_with_new_link_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(ai_news, "AI_CACHE_FILE", Path(d) / "ai.json"), \
                mock.patch.object(ai_news, "DATA_DIR", Path(d)):
            for link in ("https://a1", "https://a2", ""):
                ai_news.merge_ai_articles("LLY", [{"title": "Lilly beats", "link": link}])
            self.assertEqual(len(ai_news.load_ai_news_cache()["LLY"]["articles"]), 1)


class UniverseTest(unittest.TestCase):
    def test_one_alphabet_listing(self):
        symbols = get_tv_symbols("all")
        self.assertEqual([s for s in symbols if "GOOG" in s], ["NASDAQ:GOOGL"])
        self.assertEqual(len(symbols), len(set(symbols)))

    def test_unknown_etf_tries_amex(self):
        self.assertIn("AMEX:VOO", resolve_custom_tickers(["VOO"]))


class IndicatorTest(unittest.TestCase):
    def test_rsi_without_losses_is_100(self):
        self.assertEqual(_rsi_value(0.0, 0.0), 100.0)
        self.assertEqual(_rsi_value(1.0, 1.0), 50.0)

    def test_rma_is_wilder_smoothing(self):
        self.assertEqual(_rma([1.0, 2.0, 3.0, 4.0], 2), [1.0, 1.5, 2.25, 3.125])

    def test_zero_volume_makes_no_earnings_markers(self):
        start = date(2024, 1, 1)
        candles = [{"time": (start + timedelta(days=i)).isoformat(), "open": 10, "high": 10, "low": 10, "close": 10, "volume": 0}
                   for i in range(200)]
        self.assertEqual(detect_earnings_history(candles), [])


if __name__ == "__main__":
    unittest.main()
