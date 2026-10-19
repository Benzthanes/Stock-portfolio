import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scripts.reconcile_cost_thb as rc

SLIPS = [
    {"fn": "a", "ticker": "AAA", "shares": 10.0, "amt_usd": 300.0, "amt_thb": 0.0, "date": "1 ต.ค. 69", "account": "Dime! USD"},
    {"fn": "b", "ticker": "AAA", "shares": 10.0, "amt_usd": 296.0, "amt_thb": 10000.0, "date": "5 ต.ค 69 - 20:33 น", "account": "Dime! Save (THB)"},
    {"fn": "c", "ticker": "BBB", "shares": 5.0, "amt_usd": 100.0, "amt_thb": 3400.0, "date": "2 ต.ค. 69", "account": "Dime! Save (THB)"},
]


class ReconcileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        d = Path(self._tmp.name)
        (d / "portfolio.json").write_text(json.dumps({"holdings": [
            {"ticker": "AAA", "shares": 15.0, "total_cost_usd": 447.0, "cost_thb": 15028.14},
            {"ticker": "BBB", "shares": 4.0, "total_cost_usd": 80.0, "cost_thb": 2689.6},
        ]}), encoding="utf-8")
        (d / "trades.json").write_text(json.dumps({"trades": [
            {"id": "T1", "ticker": "AAA", "action": "SELL", "date": "2026-10-10", "shares": 5.0,
             "total_cost_usd": 149.0, "cost_thb": 5009.38, "revenue_thb": 6000.0, "realized_pl_thb": 990.62},
        ]}), encoding="utf-8")
        (d / "ledger.json").write_text(json.dumps({"cash": {}, "buy_orders": []}), encoding="utf-8")
        self.dir = d
        self.patches = [mock.patch.dict(os.environ, {"FILTER_STOCK_DATA_DIR": str(d)}),
                        mock.patch.object(rc, "load_ocr_buy_orders", lambda: [dict(s) for s in SLIPS])]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self._tmp.cleanup()

    def run_script(self, *argv):
        with mock.patch.object(sys, "argv", ["reconcile_cost_thb.py", *argv]), contextlib.redirect_stdout(io.StringIO()):
            rc.main()
        return (json.loads((self.dir / "portfolio.json").read_text())["holdings"],
                json.loads((self.dir / "trades.json").read_text())["trades"])

    def test_dry_run_writes_nothing(self):
        before = (self.dir / "portfolio.json").read_text()
        self.run_script()
        self.assertEqual((self.dir / "portfolio.json").read_text(), before)

    def test_thb_slips_replace_fallback_cost_and_sells_take_their_share(self):
        holdings, trades = self.run_script("--apply")
        # AAA: 300 USD x 33.62 + 10,000 THB for 20 shares; selling 5 removes a quarter of each part.
        self.assertEqual(holdings[0]["cost_thb"], round((300 * 33.62 + 10000) * 0.75, 2))
        self.assertEqual(trades[0]["cost_thb"], round((300 * 33.62 + 10000) * 0.25, 2))
        self.assertEqual(trades[0]["realized_pl_thb"], round(6000.0 - trades[0]["cost_thb"], 2))

    def test_share_mismatch_is_skipped(self):
        holdings, _ = self.run_script("--apply")
        self.assertEqual(holdings[1]["cost_thb"], 2689.6)

    def test_second_run_changes_nothing(self):
        first = self.run_script("--apply")
        self.assertEqual(self.run_script("--apply"), first)
