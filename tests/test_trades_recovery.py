import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent

import recovery
from src.trades import record_sell

LLY = {
    "ticker": "LLY",
    "exchange": "NYSE",
    "name": "Eli Lilly and Company",
    "shares": 27.6477631,
    "avg_cost_usd": 1021.1077,
    "total_cost_usd": 28231.34,
    "cost_thb": 949137.8,
}


def quote(ticker, close, target=None):
    return {"name": ticker, "ticker": ticker, "close": close, "ATR": 5.0, "price_target_average": target,
            "price_target_low": target, "price_target_high": target}


def no_news(ticker, max_items=4):
    return {"ticker": ticker, "bullish": [], "bearish": [], "all": []}


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        (self.tmp / "data").mkdir()
        (self.tmp / "reports").mkdir()
        os.chdir(self.tmp)
        self._env = mock.patch.dict(os.environ, {"FILTER_STOCK_DATA_DIR": str(self.tmp / "data")})
        self._env.start()
        fx_patch = mock.patch("src.fx.fetch_usdthb", return_value=35.0)
        self.fetch_fx = fx_patch.start()
        self.addCleanup(fx_patch.stop)

    def tearDown(self):
        self._env.stop()
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def write_portfolio(self, holdings):
        path = self.tmp / "data" / "portfolio.json"
        path.write_text(json.dumps({"base_currency": "USD", "fx_rate_usd_thb": 33.62, "holdings": holdings}), encoding="utf-8")
        return path

    def read_holdings(self):
        return json.loads((self.tmp / "data" / "portfolio.json").read_text(encoding="utf-8"))["holdings"]


class RecordSellTest(TempDirCase):
    def test_partial_sell_keeps_original_cost_thb_proportionally(self):
        self.write_portfolio([dict(LLY)])
        record_sell("LLY", 1100.0, shares=1, fx_rate=36.5, trade_date="2026-10-15",
                    portfolio_path="data/portfolio.json", trades_path="data/trades.json")
        lly = self.read_holdings()[0]
        self.assertEqual(lly["cost_thb"], 914808.16)
        self.assertEqual(lly["shares"], 26.6477631)

    def test_cli_rejects_zero_negative_and_excess_shares(self):
        self.write_portfolio([dict(LLY)])
        for shares, msg in [("0", "must be greater than 0"), ("-1", "must be greater than 0"), ("30", "only 27.6477631 held")]:
            r = subprocess.run([sys.executable, str(ROOT / "trades.py"), "sell", "-t", "LLY", "-p", "1100", "-s", shares],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, shares)
            self.assertIn(msg, r.stderr)
        self.assertEqual(self.read_holdings()[0]["shares"], 27.6477631)
        self.assertFalse((self.tmp / "data" / "trades.json").exists())

    def test_cli_omitted_shares_sells_all(self):
        self.write_portfolio([dict(LLY)])
        r = subprocess.run([sys.executable, str(ROOT / "trades.py"), "sell", "-t", "LLY", "-p", "1100", "-d", "2026-10-15"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.read_holdings(), [])

    def test_buy_date_and_holding_days_copied_from_holding(self):
        self.write_portfolio([dict(LLY, buy_date="2026-10-01")])
        res = record_sell("LLY", 1100.0, shares=1, trade_date="2026-10-15",
                          portfolio_path="data/portfolio.json", trades_path="data/trades.json")
        self.assertEqual(res["trade"]["buy_date"], "2026-10-01")
        self.assertEqual(res["trade"]["holding_days"], 14)


@mock.patch.object(recovery, "get_catalyst_breakdown", no_news)
@mock.patch.object(recovery, "fetch_batch_catalysts", lambda tickers, max_items=4: {})
class RecoveryTest(TempDirCase):
    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["recovery.py", *argv]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                recovery.main()
                code = 0
            except SystemExit as e:
                code = e.code
        return code, out.getvalue(), err.getvalue()

    def test_single_ticker_does_not_overwrite_portfolio_dashboard(self):
        self.write_portfolio([])
        dashboard = self.tmp / "reports" / "portfolio_recovery.html"
        dashboard.write_text("<html>dashboard</html>", encoding="utf-8")
        with mock.patch.object(recovery, "fetch_screener_data", lambda syms: [quote("VOO", 400.0)]):
            code, out, err = self.run_main("VOO", "--cost", "450")
        self.assertEqual(code, 0, err)
        self.assertEqual(dashboard.read_text(encoding="utf-8"), "<html>dashboard</html>")
        self.assertTrue((self.tmp / "reports" / "recovery_VOO.md").exists())

    def test_shares_zero_gives_clear_error(self):
        self.write_portfolio([])
        with mock.patch.object(recovery, "fetch_screener_data", lambda syms: [quote("VOO", 400.0)]):
            code, out, err = self.run_main("VOO", "--cost", "450", "--shares", "0", "--json")
        self.assertEqual(code, 1)
        self.assertIn("Shares must be greater than 0", err)

    def test_missing_quote_is_skipped_with_warning(self):
        self.write_portfolio([
            {"ticker": "AAA", "exchange": "NASDAQ", "shares": 10, "avg_cost_usd": 100.0, "total_cost_usd": 1000.0},
            {"ticker": "BBB", "exchange": "NASDAQ", "shares": 10, "avg_cost_usd": 100.0, "total_cost_usd": 1000.0},
        ])
        with mock.patch.object(recovery, "fetch_screener_data",
                               lambda syms: [quote("AAA", 80.0)] if len(syms) > 1 or "AAA" in syms[0] else []):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                summary = recovery.analyze_all_underwater("data/portfolio.json")
        self.assertEqual([p["ticker"] for p in summary["positions"]], ["AAA"])
        self.assertIn("Warning: skipping BBB", err.getvalue())

    def test_hold_recommendation_follows_target_vs_cost(self):
        self.write_portfolio([{"ticker": "AAA", "exchange": "NASDAQ", "shares": 10, "avg_cost_usd": 100.0, "total_cost_usd": 1000.0}])
        cases = [(90.0, "แต่ราคาเป้าหมายสถาบันยังต่ำกว่าต้นทุนเดิมของคุณ"),
                 (120.0, "ราคาเป้าหมายสถาบันอยู่สูงกว่าต้นทุนเดิมของคุณ"),
                 (None, "ยังไม่มีข้อมูลราคาเป้าหมายสถาบันเทียบต้นทุนของคุณ")]
        for target, phrase in cases:
            with mock.patch.object(recovery, "fetch_screener_data", lambda syms, t=target: [quote("AAA", 80.0, t)]):
                report = recovery.generate_portfolio_recovery_report(recovery.analyze_all_underwater("data/portfolio.json"))
            self.assertIn(f"ทางเลือกที่ 1 (ถือรอเฉยๆ) {phrase}", report)


class MasterOutputTest(TempDirCase):
    def test_master_summary_uses_real_trades_and_dividends(self):
        import scripts.generate_master_report as gmr
        data = {
            "portfolio_name": "P", "total_net_worth_thb": 1.0, "total_net_worth_usd": 1.0, "net_injected_capital_thb": 1.0,
            "all_time_profit_thb": 1.0, "all_time_roi_pct": 1.0, "total_cash_thb": 1.0, "dime_save_cash_thb": 1.0,
            "dime_usd_cash": 1.0, "positions": [], "stock_market_val_usd": 1.0, "stock_market_val_thb": 1.0,
            "trades_summary": {"total_realized_pl_usd": -12.5, "total_realized_pl_thb": -420.25, "win_rate_pct": 66.7, "total_trades": 3, "winning_trades": 2},
            "total_dividends_usd": 3.0, "total_dividends_thb": 100.86, "dividends_list": [{}, {}],
        }
        out = io.StringIO()
        with mock.patch.object(gmr, "generate_master_dashboard_data", return_value=data), \
             mock.patch.object(gmr, "generate_master_dashboard_html", return_value="<html/>"), \
             contextlib.redirect_stdout(out):
            gmr.main()
        text = out.getvalue()
        self.assertIn("Realized Trades P&L  : -$12.50 (-฿420.25) | 2/3 ไม้กำไร", text)
        self.assertIn("Total Dividends Recv : +$3.00 (+฿100.86) | 2 payments", text)


if __name__ == "__main__":
    unittest.main()
