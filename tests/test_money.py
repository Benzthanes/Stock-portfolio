import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import src.fx as fx
import src.portfolio as portfolio
from src.portfolio import analyze_portfolio, cost_basis
from src.trades import calculate_trades_summary, parse_trade_date, record_buy, record_sell


def quote(ticker, close, change=0.0):
    return {"ticker": ticker, "name": ticker, "close": close, "change": change}


class MoneyCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.portfolio = self.tmp / "portfolio.json"
        self.trades = self.tmp / "trades.json"
        self.ledger = self.tmp / "ledger.json"
        fx_patch = mock.patch.object(fx, "fetch_usdthb", return_value=None)
        self.fetch_fx = fx_patch.start()
        self.addCleanup(fx_patch.stop)
        self.addCleanup(self._tmp.cleanup)

    def write_portfolio(self, holdings, fx_rate=33.0):
        self.portfolio.write_text(json.dumps({"base_currency": "USD", "fx_rate_usd_thb": fx_rate, "holdings": holdings}), encoding="utf-8")

    def holdings(self):
        return json.loads(self.portfolio.read_text(encoding="utf-8"))["holdings"]

    def sell(self, *args, **kw):
        return record_sell(*args, portfolio_path=str(self.portfolio), trades_path=str(self.trades),
                           ledger_path=str(self.ledger), **kw)

    def buy(self, *args, **kw):
        return record_buy(*args, portfolio_path=str(self.portfolio), ledger_path=str(self.ledger),
                          exchange_resolver=lambda t: ("NASDAQ", t), **kw)


@mock.patch.object(portfolio, "fetch_batch_news", lambda tickers, max_items=2: {})
@mock.patch.object(portfolio, "fetch_batch_catalysts", lambda tickers, max_items=4: {})
@mock.patch.object(portfolio, "get_forward_outlook", lambda **kw: {})
class AnalyzePortfolioTest(MoneyCase):
    HOLDINGS = [
        {"ticker": "AAA", "exchange": "NASDAQ", "shares": 10, "avg_cost_usd": 100.0, "total_cost_usd": 1000.0, "cost_thb": 33000.0},
        {"ticker": "BBB", "exchange": "NASDAQ", "shares": 5, "avg_cost_usd": 200.0, "total_cost_usd": 1000.0, "cost_thb": 34000.0},
        {"ticker": "CCC", "exchange": "NASDAQ", "shares": 2, "avg_cost_usd": 50.0, "total_cost_usd": 100.0, "cost_thb": 3300.0},
    ]

    def analyze(self):
        self.fetch_fx.return_value = 35.0
        rows = [quote("AAA", 110.0), quote("BBB", 190.0)]
        with mock.patch.object(portfolio, "fetch_screener_data", lambda syms: rows):
            return analyze_portfolio({"base_currency": "USD", "fx_rate_usd_thb": 33.62, "holdings": self.HOLDINGS})

    def test_live_fx_and_position_thb_pl_sums_to_total(self):
        s = self.analyze()
        pos = {p["ticker"]: p for p in s["positions"]}
        self.assertEqual(s["fx_rate_usd_thb"], 35.0)
        self.assertAlmostEqual(pos["AAA"]["unrealized_pl_thb"], 5500.0)
        self.assertAlmostEqual(pos["BBB"]["unrealized_pl_thb"], -750.0)
        self.assertAlmostEqual(pos["AAA"]["unrealized_pl_usd"], 100.0)
        self.assertAlmostEqual(s["total_pl_thb"], 4750.0)
        self.assertAlmostEqual(pos["AAA"]["unrealized_pl_thb"] + pos["BBB"]["unrealized_pl_thb"], s["total_pl_thb"])
        self.assertAlmostEqual(s["total_pl_usd"], 50.0)
        self.assertAlmostEqual(s["total_pl_pct"], 2.5)

    def test_missing_quote_is_flagged_and_excluded_from_totals_and_weights(self):
        s = self.analyze()
        ccc = next(p for p in s["positions"] if p["ticker"] == "CCC")
        self.assertTrue(ccc["price_missing"])
        self.assertIsNone(ccc["unrealized_pl_pct"])
        self.assertIsNone(ccc["close_price"])
        self.assertEqual(ccc["weight_pct"], 0.0)
        self.assertIn("⚠️ Data Missing", ccc["alerts"])
        self.assertEqual(s["price_missing_tickers"], ["CCC"])
        self.assertAlmostEqual(s["total_cost_usd"], 2000.0)
        self.assertAlmostEqual(s["unpriced_cost_thb"], 3300.0)
        weights = sorted(round(p["weight_pct"], 4) for p in s["positions"])
        self.assertEqual(weights, [0.0, 46.3415, 53.6585])
        self.assertIn("n/a", portfolio.generate_portfolio_markdown(s))


class CostBasisTest(unittest.TestCase):
    def test_uses_base_currency_keys_only(self):
        h = {"shares": 10, "avg_cost_usd": 3.0, "avg_cost_thb": 100.0, "total_cost_thb": 1000.0}
        self.assertEqual(cost_basis(h, "THB"), (100.0, 1000.0))
        self.assertEqual(cost_basis(h, "USD"), (3.0, 30.0))


class SellTest(MoneyCase):
    def test_partial_sell_conserves_cost_thb_and_books_fx_gain(self):
        self.write_portfolio([{"ticker": "AAA", "exchange": "NASDAQ", "shares": 10.0, "avg_cost_usd": 100.0,
                               "total_cost_usd": 1000.0, "cost_thb": 33000.0}])
        t = self.sell("AAA", 100.0, shares=5, fx_rate=35.0, trade_date="2026-10-15")["trade"]
        self.assertEqual(t["cost_thb"], 16500.0)
        self.assertEqual(t["revenue_thb"], 17500.0)
        self.assertEqual(t["realized_pl_usd"], 0.0)
        self.assertEqual(t["realized_pl_thb"], 1000.0)
        self.assertEqual(t["fx_rate"], 35.0)
        self.assertEqual(self.holdings()[0]["cost_thb"], 16500.0)

    def test_uneven_split_still_sums_to_original_cost(self):
        self.write_portfolio([{"ticker": "AAA", "exchange": "NASDAQ", "shares": 7.0, "avg_cost_usd": 10.0,
                               "total_cost_usd": 70.0, "cost_thb": 1000.01}])
        t = self.sell("AAA", 12.0, shares=3, fx_rate=34.0, trade_date="2026-10-15")["trade"]
        self.assertEqual(t["cost_thb"], 428.58)
        self.assertEqual(self.holdings()[0]["cost_thb"], 571.43)

    def test_live_fx_is_used_and_persisted_when_no_rate_given(self):
        self.fetch_fx.return_value = 35.0
        self.write_portfolio([{"ticker": "AAA", "exchange": "NASDAQ", "shares": 10.0, "avg_cost_usd": 100.0,
                               "total_cost_usd": 1000.0, "cost_thb": 33000.0}])
        t = self.sell("AAA", 100.0, shares=5, trade_date="2026-10-15")["trade"]
        self.assertEqual(t["fx_rate"], 35.0)
        self.assertEqual(json.loads(self.portfolio.read_text(encoding="utf-8"))["fx_rate_usd_thb"], 35.0)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["ledger.json", "portfolio.json", "trades.json"])

    def test_thai_buy_date_gives_holding_days_and_iso_sell_date(self):
        self.write_portfolio([{"ticker": "AAA", "exchange": "NASDAQ", "shares": 1.0, "avg_cost_usd": 10.0,
                               "total_cost_usd": 10.0, "cost_thb": 330.0, "buy_date": "12 มิ.ย. 69 - 22:46 น."}])
        t = self.sell("AAA", 11.0, fx_rate=33.0, trade_date="17 มิ.ย. 69")["trade"]
        self.assertEqual(t["date"], "2026-06-17")
        self.assertEqual(t["holding_days"], 5)

    def test_unparseable_buy_date_gives_none(self):
        self.write_portfolio([{"ticker": "AAA", "exchange": "NASDAQ", "shares": 1.0, "avg_cost_usd": 10.0,
                               "total_cost_usd": 10.0, "cost_thb": 330.0, "buy_date": "sometime"}])
        t = self.sell("AAA", 11.0, fx_rate=33.0, trade_date="2026-06-17")["trade"]
        self.assertIsNone(t["holding_days"])

    def test_negative_price_and_fees_rejected(self):
        self.write_portfolio([{"ticker": "AAA", "exchange": "NASDAQ", "shares": 1.0, "avg_cost_usd": 10.0, "total_cost_usd": 10.0}])
        with self.assertRaisesRegex(ValueError, "ราคาต้องมากกว่า 0 / Price must be greater than 0"):
            self.sell("AAA", -1.0, fx_rate=33.0)
        with self.assertRaisesRegex(ValueError, "Fees must be 0 or more"):
            self.sell("AAA", 10.0, fees=-1.0, fx_rate=33.0)
        self.assertFalse(self.trades.exists())


class BuyTest(MoneyCase):
    def test_fees_are_added_to_cost(self):
        self.write_portfolio([])
        r = self.buy("SPCX", 6, 150.0, fx_rate=33.0, fees=1.44, trade_date="2026-10-15")
        h = self.holdings()[0]
        self.assertEqual((h["total_cost_usd"], h["avg_cost_usd"], h["cost_thb"]), (901.44, 150.24, 29747.52))
        self.assertEqual((r["buy_order"]["amt_usd"], r["buy_order"]["fees_usd"], r["buy_order"]["fx_rate"]), (901.44, 1.44, 33.0))

    def test_negative_price_raises(self):
        self.write_portfolio([])
        with self.assertRaisesRegex(ValueError, "Price must be greater than 0"):
            self.buy("AAA", 1, -5.0, fx_rate=33.0)
        with self.assertRaisesRegex(ValueError, "Fees must be 0 or more"):
            self.buy("AAA", 1, 5.0, fx_rate=33.0, fees=-0.5)


class DateParseTest(unittest.TestCase):
    def test_formats_in_trades_json(self):
        cases = {"12 มิ.ย. 69 - 22:46 น.": "2026-06-12", "17 มิ.ย. 69": "2026-06-17", "16 - 17 มี.ค. 69": "2026-03-16",
                 "1 มิ.ย. - 15 ก.ค. 69": "2026-06-01", "2026-10-01": "2026-10-01", "1 ธ.ค. - 5 ม.ค. 70": "2026-12-01"}
        for text, iso in cases.items():
            self.assertEqual(parse_trade_date(text).isoformat(), iso, text)
        self.assertIsNone(parse_trade_date("not a date"))


class SummaryTest(unittest.TestCase):
    def test_win_rate_ignores_breakeven_and_profit_factor(self):
        trades = [{"realized_pl_usd": v} for v in (10.0, -5.0, 0.0, 0.0)]
        s = calculate_trades_summary({"trades": trades})
        self.assertEqual((s["win_rate_pct"], s["breakeven_trades"], s["profit_factor"]), (50.0, 2, 2.0))

    def test_no_losses_gives_json_safe_profit_factor(self):
        s = calculate_trades_summary({"trades": [{"realized_pl_usd": 10.0}, {"realized_pl_usd": 0.0}]})
        self.assertEqual(s["win_rate_pct"], 100.0)
        self.assertIsNone(s["profit_factor"])
        self.assertEqual(s["profit_factor_display"], "∞")
        self.assertNotIn("Infinity", json.dumps(s))


if __name__ == "__main__":
    unittest.main()
