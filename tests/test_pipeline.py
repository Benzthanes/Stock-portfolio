import datetime
import json
import math
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from src import chart_data, http, news, screener


def _synth(n=70):
    out, d, i = [], datetime.date(2026, 7, 1), 0
    while len(out) < n:
        if d.weekday() < 5:
            base = 100 + 10 * math.sin(i / 6.0) + 0.3 * i
            out.append({
                "time": d.isoformat(),
                "open": round(base - 0.5, 2),
                "high": round(base + 1.5 + (i % 3) * 0.4, 2),
                "low": round(base - 1.5 - (i % 4) * 0.3, 2),
                "close": round(base + (0.6 if i % 2 else -0.4), 2),
                "volume": 1000 + 37 * i,
            })
            i += 1
        d += datetime.timedelta(days=1)
    return out


class SupertrendPivotGoldenTest(unittest.TestCase):
    def test_supertrend_matches_pine_rma_reference(self):
        candles = _synth()
        cases = {35: ("BEARISH", 109.55), 45: ("BULLISH", 110.49), 60: ("BULLISH", 112.73), 70: ("BEARISH", 121.08)}
        for k, (trend, value) in cases.items():
            with self.subTest(bars=k):
                st = chart_data.compute_fibo_and_indicators(candles[:k])["supertrend"]
                self.assertEqual(st, {"trend": trend, "last_value": value})

    def test_classic_pivots_use_previous_calendar_month(self):
        candles = _synth()
        self.assertEqual(candles[-1]["time"], "2026-10-06")
        pivots = chart_data.compute_fibo_and_indicators(candles)["pivots"]
        self.assertEqual(pivots, {"pivot": 114.78, "r1": 121.85, "s1": 103.15, "r2": 133.48, "s2": 96.08})

    def test_previous_month_wraps_year(self):
        candles = [
            {"time": "2025-12-30", "high": 12.0, "low": 9.0, "close": 11.0},
            {"time": "2025-12-31", "high": 13.0, "low": 10.0, "close": 12.5},
            {"time": "2026-01-02", "high": 50.0, "low": 1.0, "close": 20.0},
        ]
        self.assertEqual(chart_data._previous_month_hlc(candles), (13.0, 9.0, 12.5))


class AnchorTest(unittest.TestCase):
    def test_poc_vwap_and_macro_fibo_ignore_bars_before_anchor(self):
        old = [{"time": f"2000-01-{i % 28 + 1:02d}", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 10 ** 9} for i in range(300)]
        recent = [{"time": f"2026-{i // 28 % 12 + 1:02d}-{i % 28 + 1:02d}", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000} for i in range(chart_data.ANCHOR_BARS)]
        out = chart_data.compute_fibo_and_indicators(old + recent)
        self.assertEqual(out["vwap"], 100.0)
        self.assertEqual(out["fibo_macro"]["0.0"], 101.0)
        self.assertEqual(out["fibo_macro"]["100.0"], 99.0)
        self.assertEqual(out["volume_profile"]["poc"], 100.02)
        self.assertEqual(out["anchor_2y"], {"time": recent[0]["time"], "bars": chart_data.ANCHOR_BARS})
        self.assertEqual(out["atl"]["price"], 0.9)

    def test_pattern_win_rate_has_no_unsourced_percentage(self):
        src = Path(chart_data.__file__).read_text(encoding="utf-8")
        self.assertNotIn("Bulkowski", src)
        self.assertEqual(chart_data.PATTERN_WIN_RATE_NOTE, "ไม่มีสถิติยืนยัน (heuristic)")


class CandleCacheTest(unittest.TestCase):
    def test_save_is_atomic_and_strips_candle_colors(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candles_cache.json"
            entry = {"candles": [1], "cdc_actionzone": {"zone": "green", "candle_colors": [{"time": "x"}]}}
            with mock.patch.object(chart_data, "CACHE_PATH", path):
                chart_data.save_candles_cache({"AAA": entry})
            self.assertEqual(json.loads(path.read_text()), {"AAA": {"candles": [1], "cdc_actionzone": {"zone": "green"}}})
            self.assertEqual(entry["cdc_actionzone"]["candle_colors"], [{"time": "x"}])
            self.assertEqual([p.name for p in Path(d).iterdir()], ["candles_cache.json"])

    def test_failed_refresh_keeps_old_entry_and_marks_stale(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candles_cache.json"
            path.write_text(json.dumps({"AAA": {"candles": [{"close": 1}], "timestamp": 0, "full_history": True, "schema_version": 1}}))
            with mock.patch.object(chart_data, "CACHE_PATH", path), \
                    mock.patch.object(chart_data, "fetch_ticker_candles", side_effect=http.HttpError("u", "boom")), \
                    mock.patch("sys.stderr") as err:
                out = chart_data.get_all_charts_payload(["AAA"])
            self.assertTrue(out["AAA"]["stale"])
            self.assertEqual(out["AAA"]["candles"], [{"close": 1}])
            self.assertTrue(json.loads(path.read_text())["AAA"]["stale"])
            self.assertIn("AAA", "".join(c.args[0] for c in err.write.call_args_list))

    def test_fresh_entry_is_recomputed_when_market_day_changes(self):
        """Earnings guard depends on the day, so a 6-hour-fresh entry from yesterday must be recomputed."""
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candles_cache.json"
            candles = [{"time": f"2026-01-{i % 28 + 1:02d}", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 10} for i in range(40)]
            entry = {"candles": candles, "timestamp": time.time(), "full_history": True,
                     "schema_version": chart_data.INDICATOR_SCHEMA_VERSION, "earnings_hash": chart_data.EARNINGS_CALENDAR_HASH,
                     "market_date": "2026-10-29", "marker": "old"}
            path.write_text(json.dumps({"AAA": entry}))
            with mock.patch.object(chart_data, "CACHE_PATH", path), \
                    mock.patch.object(chart_data, "_market_today", return_value="2026-10-29"), \
                    mock.patch.object(chart_data, "fetch_ticker_candles") as fetch:
                same_day = chart_data.get_all_charts_payload(["AAA"])
            self.assertEqual(same_day["AAA"].get("marker"), "old")
            with mock.patch.object(chart_data, "CACHE_PATH", path), \
                    mock.patch.object(chart_data, "_market_today", return_value="2026-10-30"), \
                    mock.patch.object(chart_data, "fetch_ticker_candles") as fetch:
                next_day = chart_data.get_all_charts_payload(["AAA"])
            fetch.assert_not_called()
            self.assertNotIn("marker", next_day["AAA"])
            self.assertEqual(next_day["AAA"]["market_date"], "2026-10-30")
            self.assertEqual(len(next_day["AAA"]["candles"]), 40)


class HttpRetryTest(unittest.TestCase):
    def _resp(self, body):
        r = mock.MagicMock()
        r.__enter__.return_value.read.return_value = body
        return r

    def test_retries_5xx_then_succeeds(self):
        err = urllib.error.HTTPError("u", 503, "busy", {}, None)
        with mock.patch("src.http.urllib.request.urlopen", side_effect=[err, err, self._resp(b"ok")]) as u, \
                mock.patch("src.http._sleep") as sleep:
            self.assertEqual(http.http_get("https://ex.com"), b"ok")
        self.assertEqual(u.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertGreaterEqual(sleep.call_args_list[1].args[0], 1.0)

    def test_404_is_not_retried(self):
        err = urllib.error.HTTPError("u", 404, "nf", {}, None)
        with mock.patch("src.http.urllib.request.urlopen", side_effect=err) as u, mock.patch("src.http._sleep"):
            with self.assertRaises(http.HttpError) as cm:
                http.http_get("https://ex.com")
        self.assertEqual(cm.exception.status, 404)
        self.assertEqual(u.call_count, 1)

    def test_post_json(self):
        with mock.patch("src.http.urllib.request.urlopen", return_value=self._resp(b'{"a": 1}')) as u:
            self.assertEqual(http.http_post_json("https://ex.com", {"q": 1}), {"a": 1})
        req = u.call_args.args[0]
        self.assertEqual((req.get_method(), req.data), ("POST", b'{"q": 1}'))


class SentimentHeuristicTest(unittest.TestCase):
    def test_ai_is_not_bullish_by_default(self):
        self.assertEqual(news.classify_sentiment("Microsoft expands AI datacenter push"), "neutral")
        self.assertEqual(news.classify_sentiment("AI bubble fears hit chip stocks"), "bearish")
        self.assertEqual(news.classify_sentiment("SEC charges executive"), "bearish")
        self.assertEqual(news.classify_sentiment("Retailer cuts guidance on weak demand"), "bearish")


class NewsStatusTest(unittest.TestCase):
    def test_fetch_failure_is_flagged(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(news, "CACHE_FILE", Path(d) / "c.json"), \
                mock.patch.object(news, "http_get", side_effect=http.HttpError("u", "down")), \
                mock.patch("sys.stderr"):
            self.assertEqual(news.fetch_stock_news_with_status("ZZZ"), ([], False))
            self.assertFalse(news.get_catalyst_breakdown("ZZZ")["fetch_ok"])

    def test_empty_feed_is_ok(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(news, "CACHE_FILE", Path(d) / "c.json"), \
                mock.patch.object(news, "http_get", return_value=b"<rss><channel></channel></rss>"):
            self.assertEqual(news.fetch_stock_news_with_status("ZZZ"), ([], True))


class ScreenerMissingDataTest(unittest.TestCase):
    def _report(self, cat, **row):
        s = {"ticker": "TST", "name": "Test Co", "close": 100.0, "change_pct": 0.0, "rsi": 30.0, "rsi_hook_up": False,
             "stoch_k": None, "stoch_d": None, "rev_growth_yoy": None, "peg": None, "tier": "A", "signal_tags": [],
             "tv_url": "u", "is_earnings_near": False, "atr": None}
        s.update(row)
        with mock.patch.object(screener, "fetch_batch_catalysts", return_value={"TST": cat}):
            return screener.generate_markdown_report([s], 1, 35.0, True, None)

    def test_fetch_failure_never_claims_market_correction(self):
        out = self._report({"bullish": [], "bearish": [], "all": [], "fetch_ok": False})
        self.assertIn("ดึงข่าวไม่สำเร็จ", out)
        self.assertNotIn("market correction", out)
        self.assertNotIn("ปรับฐานตามตลาด.\n", out)
        self.assertNotIn("มั่นคง", out.split("👶")[1].split("---")[0])
        self.assertIn("ไม่มีข้อมูลการเติบโตของรายได้ (-)", out)
        self.assertIn("ไม่มีข้อมูลความผันผวน (-)", out)

    def test_empty_news_is_not_called_a_correction(self):
        out = self._report({"bullish": [], "bearish": [], "all": [], "fetch_ok": True}, atr=2.0, sector="Finance")
        self.assertNotIn("ดึงข่าวไม่สำเร็จ", out)
        self.assertIn("ไม่พบข่าวด้านลบในพาดหัวล่าสุดที่ดึงมาได้", out)


class ChartTemplateTest(unittest.TestCase):
    def test_templates_have_no_fstring_braces_or_leftover_markers(self):
        from src import chart_page
        html = chart_page.render_chart_template({m: "X" for m in ("__NAV_BAR__", "__PILLS_HTML__", "__DEFAULT_TICKER__", "__SORTED_TICKERS_JSON__", "__INIT_TICKER__")})
        self.assertNotIn("{{", html)
        self.assertNotIn("__CHART_", html)
        self.assertNotIn("__NAV_BAR__", html)
        self.assertIn("🔎 วิเคราะห์จากคีย์เวิร์ด", html)
        self.assertIn('id="st_stale_badge"', html)
        self.assertIn("Rule-based Confluence", html)
        self.assertNotIn("AI Confluence", html)


if __name__ == "__main__":
    unittest.main()
