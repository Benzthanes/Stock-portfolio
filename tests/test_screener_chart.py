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


if __name__ == "__main__":
    unittest.main()
