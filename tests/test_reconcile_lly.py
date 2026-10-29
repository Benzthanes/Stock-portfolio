import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.reconcile_cost_thb as rc


class ReconcileLLYTest(unittest.TestCase):
    """Test user decision for LLY: locked share count and cost_thb immunity for holdings."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        d = Path(self._tmp.name)

        # Portfolio with LLY (confirmed by user) and XYZ (mismatched shares)
        self.initial_portfolio = {
            "holdings": [
                {
                    "ticker": "LLY",
                    "exchange": "NYSE",
                    "name": "Eli Lilly and Company",
                    "shares": 27.6477631,
                    "avg_cost_usd": 1021.1077,
                    "total_cost_usd": 28231.34,
                    "cost_thb": 949137.8,
                },
                {
                    "ticker": "XYZ",
                    "exchange": "NASDAQ",
                    "name": "XYZ Corp",
                    "shares": 10.0,
                    "avg_cost_usd": 100.0,
                    "total_cost_usd": 1000.0,
                    "cost_thb": 33620.0,
                },
            ]
        }
        (d / "portfolio.json").write_text(json.dumps(self.initial_portfolio), encoding="utf-8")
        (d / "trades.json").write_text(json.dumps({"trades": []}), encoding="utf-8")
        (d / "ledger.json").write_text(json.dumps({"cash": {}, "buy_orders": []}), encoding="utf-8")
        self.dir = d

        # Slips: LLY total shares 27.7467 (differs from 27.6477631), XYZ total shares 15.0 (differs from 10.0)
        self.mock_slips = [
            {
                "fn": "slip_lly.png",
                "ticker": "LLY",
                "shares": 27.7467,
                "amt_usd": 0.0,
                "amt_thb": 960000.0,
                "date": "20 ต.ค. 69",
                "account": "Dime! Save (THB)",
            },
            {
                "fn": "slip_xyz.png",
                "ticker": "XYZ",
                "shares": 15.0,
                "amt_usd": 0.0,
                "amt_thb": 45000.0,
                "date": "22 ต.ค. 69",
                "account": "Dime! Save (THB)",
            },
        ]

        self.patches = [
            mock.patch.dict(os.environ, {"FILTER_STOCK_DATA_DIR": str(d)}),
            mock.patch.object(rc, "load_ocr_buy_orders", lambda: [dict(s) for s in self.mock_slips]),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self._tmp.cleanup()

    def test_plan_marks_lly_holding_as_locked(self):
        p = rc.plan(usd_fx=33.62)
        by_ticker = {r["ticker"]: r for r in p["holdings"]}

        # LLY holding must be locked and ok must be False
        self.assertIn("LLY", by_ticker)
        self.assertTrue(by_ticker["LLY"]["locked"])
        self.assertFalse(by_ticker["LLY"]["ok"])
        self.assertEqual(by_ticker["LLY"]["shares"], 27.6477631)
        self.assertEqual(by_ticker["LLY"]["slip_shares"], 27.7467)
        self.assertEqual(by_ticker["LLY"]["old"], 949137.8)
        self.assertEqual(by_ticker["LLY"]["new"], 960000.0)

        # XYZ is a normal mismatch: locked is False, ok is False
        self.assertIn("XYZ", by_ticker)
        self.assertFalse(by_ticker["XYZ"]["locked"])
        self.assertFalse(by_ticker["XYZ"]["ok"])
        self.assertEqual(by_ticker["XYZ"]["shares"], 10.0)
        self.assertEqual(by_ticker["XYZ"]["slip_shares"], 15.0)

    def test_print_plan_contains_locked_status_text(self):
        p = rc.plan(usd_fx=33.62)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc.print_plan(p, usd_fx=33.62)
        output_str = out.getvalue()

        self.assertIn("LOCKED (ผู้ใช้ยืนยันยอดพอร์ต)", output_str)
        self.assertIn("LLY", output_str)
        self.assertIn("SHARES MISMATCH (skipped unless --force)", output_str)
        self.assertIn("XYZ", output_str)

    def test_apply_without_force_changes_nothing(self):
        p = rc.plan(usd_fx=33.62)
        changed = rc.apply(p, force=False)
        self.assertEqual(changed, [])

        updated = json.loads((self.dir / "portfolio.json").read_text(encoding="utf-8"))["holdings"]
        by_ticker = {h["ticker"]: h for h in updated}
        self.assertEqual(by_ticker["LLY"]["cost_thb"], 949137.8)
        self.assertEqual(by_ticker["XYZ"]["cost_thb"], 33620.0)

    def test_apply_with_force_updates_mismatch_but_preserves_locked_lly(self):
        p = rc.plan(usd_fx=33.62)
        changed = rc.apply(p, force=True)

        # XYZ had a share mismatch and should be forced, but LLY is locked and must remain untouched
        self.assertIn("XYZ", changed)
        self.assertNotIn("LLY", changed)
        self.assertEqual(changed, ["XYZ"])

        updated = json.loads((self.dir / "portfolio.json").read_text(encoding="utf-8"))["holdings"]
        by_ticker = {h["ticker"]: h for h in updated}
        # LLY must remain exact initial value
        self.assertEqual(by_ticker["LLY"]["cost_thb"], 949137.8)
        self.assertEqual(by_ticker["LLY"]["shares"], 27.6477631)
        # XYZ must be updated to new cost
        self.assertEqual(by_ticker["XYZ"]["cost_thb"], 45000.0)

    def test_holding_lly_with_matching_slip_shares_not_overwritten_even_with_force(self):
        """Even if slip shares exactly match portfolio shares, LLY holding remains locked and unwritten."""
        matching_slips = [
            {
                "fn": "slip_lly_exact.png",
                "ticker": "LLY",
                "shares": 27.6477631,
                "amt_usd": 0.0,
                "amt_thb": 920000.0,
                "date": "20 ต.ค. 69",
                "account": "Dime! Save (THB)",
            }
        ]
        with mock.patch.object(rc, "load_ocr_buy_orders", lambda: [dict(s) for s in matching_slips]):
            p = rc.plan(usd_fx=33.62)
            by_ticker = {r["ticker"]: r for r in p["holdings"]}
            self.assertTrue(by_ticker["LLY"]["locked"])
            self.assertFalse(by_ticker["LLY"]["ok"])
            self.assertEqual(by_ticker["LLY"]["shares"], 27.6477631)
            self.assertEqual(by_ticker["LLY"]["slip_shares"], 27.6477631)
            self.assertEqual(by_ticker["LLY"]["new"], 920000.0)

            # Apply with force=True must not write LLY holding
            changed = rc.apply(p, force=True)
            self.assertNotIn("LLY", changed)

            updated = json.loads((self.dir / "portfolio.json").read_text(encoding="utf-8"))["holdings"]
            by_ticker_h = {h["ticker"]: h for h in updated}
            self.assertEqual(by_ticker_h["LLY"]["cost_thb"], 949137.8)
            self.assertEqual(by_ticker_h["LLY"]["shares"], 27.6477631)

    def test_closed_trade_lly_reconciled_normally_when_shares_match(self):
        """Closed trade of LLY with matching shares should reconcile normally (not locked)."""
        # Add a closed trade for LLY
        trade_entry = {
            "id": "TRD-20261025-LLY",
            "ticker": "LLY",
            "action": "SELL",
            "date": "2026-10-25",
            "shares": 5.0,
            "total_cost_usd": 5000.0,
            "cost_thb": 168100.0,
            "revenue_thb": 190000.0,
            "realized_pl_thb": 21900.0,
        }
        (self.dir / "trades.json").write_text(json.dumps({"trades": [trade_entry]}), encoding="utf-8")

        # Buy slips: 10 shares bought at 300,000 THB before sell date
        trade_slips = [
            {
                "fn": "slip_buy_lly.png",
                "ticker": "LLY",
                "shares": 10.0,
                "amt_usd": 0.0,
                "amt_thb": 300000.0,
                "date": "20 ต.ค. 69",
                "account": "Dime! Save (THB)",
            }
        ]
        with mock.patch.object(rc, "load_ocr_buy_orders", lambda: [dict(s) for s in trade_slips]):
            p = rc.plan(usd_fx=33.62)

            # Verify trade row
            self.assertEqual(len(p["trades"]), 1)
            t_row = p["trades"][0]
            self.assertEqual(t_row["id"], "TRD-20261025-LLY")
            self.assertEqual(t_row["ticker"], "LLY")
            self.assertEqual(t_row["shares"], 5.0)
            self.assertTrue(t_row["ok"])
            # Selling 5.0 of 10.0 shares -> half of 300,000 = 150,000.0 THB cost
            self.assertEqual(t_row["new"], 150000.0)
            # Realized P&L: 190,000 - 150,000 = 40,000.0 THB
            self.assertEqual(t_row["new_pl"], 40000.0)

            # Apply without force should reconcile the trade
            changed = rc.apply(p, force=False)
            self.assertIn("TRD-20261025-LLY", changed)
            self.assertNotIn("LLY", changed)  # holding remains untouched

            updated_trades = json.loads((self.dir / "trades.json").read_text(encoding="utf-8"))["trades"]
            self.assertEqual(updated_trades[0]["cost_thb"], 150000.0)
            self.assertEqual(updated_trades[0]["realized_pl_thb"], 40000.0)


if __name__ == "__main__":
    unittest.main()
