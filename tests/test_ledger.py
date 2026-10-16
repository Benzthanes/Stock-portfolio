import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.trades import load_ledger, record_buy, record_deposit, record_dividend, record_sell, record_withdraw


def no_lookup(ticker):
    raise AssertionError(f"exchange lookup should not run for {ticker}")


class LedgerCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.portfolio = self.tmp / "portfolio.json"
        self.ledger = self.tmp / "ledger.json"
        self.trades = self.tmp / "trades.json"
        self.portfolio.write_text(json.dumps({"fx_rate_usd_thb": 33.0, "holdings": [
            {"ticker": "AAA", "exchange": "NASDAQ", "name": "Aaa Inc", "shares": 10.0,
             "avg_cost_usd": 40.0, "total_cost_usd": 400.0, "cost_thb": 13200.0, "buy_date": "2026-01-02"}]}), encoding="utf-8")
        shutil.copy(ROOT / "data" / "ledger.json", self.ledger)

    def tearDown(self):
        self._tmp.cleanup()

    def holding(self, ticker):
        holdings = json.loads(self.portfolio.read_text(encoding="utf-8"))["holdings"]
        return next(h for h in holdings if h["ticker"] == ticker)

    def buy(self, *args, **kw):
        kw.setdefault("portfolio_path", str(self.portfolio))
        kw.setdefault("ledger_path", str(self.ledger))
        kw.setdefault("exchange_resolver", no_lookup)
        return record_buy(*args, **kw)


class BuyTest(LedgerCase):
    def test_buy_into_existing_holding_averages_cost_and_deducts_thb(self):
        self.buy("AAA", 10, 50.0, fx_rate=34.0, trade_date="2026-10-15")
        h = self.holding("AAA")
        self.assertEqual((h["shares"], h["avg_cost_usd"], h["total_cost_usd"], h["cost_thb"]), (20.0, 45.0, 900.0, 30200.0))
        self.assertEqual(h["buy_date"], "2026-01-02")
        ledger = load_ledger(str(self.ledger))
        self.assertEqual(ledger["cash"], {"dime_save_thb": -17000.0, "dime_usd": 0.0})
        self.assertEqual(ledger["cash_movements"][-1], {
            "date_str": "15/10/2026", "type": "ชำระค่าซื้อหุ้น AAA", "amount_thb": -17000.0,
            "balance_thb": -17000.0, "channel": "Dime! Save", "ref": "trades.py buy"})
        self.assertEqual(ledger["buy_orders"], [{
            "fn": "CLI", "ticker": "AAA", "shares": 10.0, "price_usd": 50.0, "amt_usd": 500.0, "amt_thb": 17000.0,
            "fx_rate": 34.0, "date": "15 ต.ค. 69 - 12:00 น.", "order_type": "Market", "account": "Dime! Save (THB)"}])

    def test_buy_new_ticker_paid_in_usd_uses_resolver(self):
        from src.trades import save_ledger
        ledger = load_ledger(str(self.ledger))
        ledger["cash"]["dime_usd"] = 100.0
        save_ledger(ledger, str(self.ledger))
        res = self.buy("bbb", 2, 10.0, pay="usd", trade_date="2026-10-15", exchange_resolver=lambda t: ("NYSE", "Bbb Corp"))
        self.assertEqual(self.holding("BBB"), {"ticker": "BBB", "exchange": "NYSE", "name": "Bbb Corp", "shares": 2.0,
                                               "avg_cost_usd": 10.0, "total_cost_usd": 20.0, "cost_thb": 660.0,
                                               "buy_date": "2026-10-15"})
        self.assertEqual(load_ledger(str(self.ledger))["cash"], {"dime_save_thb": 0.0, "dime_usd": 80.0})
        self.assertEqual(res["warnings"], [])

    def test_buy_overspend_warns_without_blocking(self):
        res = self.buy("AAA", 10, 50.0, pay="usd", trade_date="2026-10-15")
        self.assertEqual(res["warnings"], ["Dime! USD cash is negative: $-500.00"])
        self.assertEqual(load_ledger(str(self.ledger))["cash"]["dime_usd"], -500.0)

    def test_buy_rejects_bad_input_and_dry_run_writes_nothing(self):
        with self.assertRaises(ValueError):
            self.buy("AAA", 0, 50.0)
        with self.assertRaises(ValueError):
            self.buy("AAA", 1, -1.0)
        before = (self.portfolio.read_text(encoding="utf-8"), self.ledger.read_text(encoding="utf-8"))
        res = self.buy("AAA", 10, 50.0, fx_rate=34.0, dry_run=True)
        self.assertEqual(res["holding"]["avg_cost_usd"], 45.0)
        self.assertEqual(before, (self.portfolio.read_text(encoding="utf-8"), self.ledger.read_text(encoding="utf-8")))


class CashTest(LedgerCase):
    def test_deposit_raises_capital_and_cash(self):
        record_deposit(20000.0, trade_date="2026-10-15", ledger_path=str(self.ledger))
        ledger = load_ledger(str(self.ledger))
        self.assertEqual(ledger["net_injected_capital_thb"], 1265000.0)
        self.assertEqual(ledger["gross_deposits_thb"], 1315000.0)
        self.assertEqual(ledger["cash"]["dime_save_thb"], 20000.0)
        self.assertEqual(ledger["cash_movements"][-1]["balance_thb"], 20000.0)
        self.assertEqual(ledger["cash_movements"][-1]["channel"], "PROMPTPAY")

    def test_withdraw_reverses_deposit(self):
        record_deposit(500.0, ledger_path=str(self.ledger))
        record_withdraw(500.0, ledger_path=str(self.ledger))
        ledger = load_ledger(str(self.ledger))
        self.assertEqual(ledger["net_injected_capital_thb"], 1245000.0)
        self.assertEqual(ledger["transfer_out_thb"], 50500.0)
        self.assertEqual(ledger["cash"]["dime_save_thb"], 0.0)
        self.assertEqual(ledger["cash_movements"][-1]["amount_thb"], -500.0)

    def test_dividend_raises_dime_usd(self):
        record_dividend("VOO", 1.5, fx_rate=34.0, rate="1.8/หุ้น", trade_date="2026-10-15", ledger_path=str(self.ledger))
        ledger = load_ledger(str(self.ledger))
        self.assertEqual(ledger["cash"]["dime_usd"], 1.5)
        self.assertEqual(ledger["dividends"][0], {"date": "15 ต.ค. 69", "ticker": "VOO", "amount_usd": 1.5,
                                                  "rate": "1.8/หุ้น", "amount_thb": 51.0, "fx_rate": 34.0})
        self.assertEqual(len(ledger["dividends"]), 14)

    def test_sell_credits_proceeds_to_dime_usd(self):
        record_sell("AAA", 50.0, shares=4, fees=1.0, fx_rate=34.0, trade_date="2026-10-15",
                    portfolio_path=str(self.portfolio), trades_path=str(self.trades), ledger_path=str(self.ledger))
        self.assertEqual(load_ledger(str(self.ledger))["cash"]["dime_usd"], 199.0)


from src.trades import resolve_slip_relative_path, get_slip_modal_component
from scripts.generate_master_report import generate_master_ledger_html


class SlipViewerTest(unittest.TestCase):
    def test_resolve_slip_relative_path_existing(self):
        rel = resolve_slip_relative_path("IMG_5526.webp", from_reports_dir=True)
        self.assertEqual(rel, "../data/screenshots/IMG_5526.webp")

    def test_resolve_slip_relative_path_empty_and_special(self):
        self.assertEqual(resolve_slip_relative_path(None), "")
        self.assertEqual(resolve_slip_relative_path(""), "")
        self.assertEqual(resolve_slip_relative_path("-"), "")
        self.assertEqual(resolve_slip_relative_path("CLI"), "")

    def test_slip_modal_component_markup(self):
        modal_html = get_slip_modal_component()
        self.assertIn('id="slipModal"', modal_html)
        self.assertIn('function openSlipModal(', modal_html)
        self.assertIn('function closeSlipModal(', modal_html)
        self.assertIn('.slip-badge-btn', modal_html)

    def test_ledger_html_includes_slip_modal_and_buttons(self):
        sample_data = {
            "portfolio_name": "Test Port",
            "buy_orders": [{
                "fn": "IMG_5526.webp", "ticker": "SPCX", "shares": 6.0, "price_usd": 150.0,
                "amt_usd": 900.0, "amt_thb": 30000.0, "fx_rate": 33.62, "date": "12 มิ.ย. 69 - 22:46 น.",
                "order_type": "Market", "account": "Dime! USD"
            }],
            "closed_trades": [{
                "id": "TRD-1", "ticker": "SPCX", "shares": 6.0, "buy_price_usd": 150.0, "sell_price_usd": 200.0,
                "total_cost_usd": 900.0, "net_revenue_usd": 1200.0, "realized_pl_usd": 300.0,
                "realized_pl_thb": 10000.0, "realized_pl_pct": 33.33, "buy_date": "12 มิ.ย. 69",
                "date": "17 มิ.ย. 69", "buy_tranches": [{
                    "tranche": 1, "date": "12 มิ.ย. 69", "shares": 6.0, "price_usd": 150.0,
                    "amt_usd": 900.0, "amt_thb": 0.0, "file": "IMG_5526.webp", "note": "buy"
                }]
            }],
            "dividends_list": [],
            "cash_movements": [],
            "trades_summary": {"total_trades": 1, "winning_trades": 1, "win_rate_pct": 100.0, "total_realized_pl_thb": 10000.0},
            "fx_rate": 33.62
        }
        html = generate_master_ledger_html(sample_data)
        self.assertIn('id="slipModal"', html)
        self.assertIn('openSlipModal(&quot;../data/screenshots/IMG_5526.webp&quot;', html)


if __name__ == "__main__":
    unittest.main()

