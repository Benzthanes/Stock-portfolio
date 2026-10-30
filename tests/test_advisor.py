import json
import os
import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from src import advisor
from src.advisor import TRIGGERS, generate_advisor_html, generate_advisor_page, lly_weight_pct, trigger_status

FIXED = datetime(2026, 10, 30, 22, 30)
PRICES = {"LLY": 1431.86, "SMH": 524.25, "GPIQ": 54.61, "AEHR": 54.60, "CHPY": 56.89}


class TriggerStatusTest(unittest.TestCase):
    def test_above_not_reached_reports_gap(self):
        self.assertEqual(trigger_status("above", 570.6, 524.25), {"hit": False, "gap_pct": 8.8})

    def test_above_reached(self):
        self.assertEqual(trigger_status("above", 519.0, 524.25), {"hit": True, "gap_pct": 0.0})

    def test_below_reached_and_not(self):
        self.assertEqual(trigger_status("below", 55.5, 54.61), {"hit": True, "gap_pct": 0.0})
        self.assertEqual(trigger_status("below", 467.0, 524.25), {"hit": False, "gap_pct": -10.9})

    def test_missing_price(self):
        self.assertEqual(trigger_status("above", 57.0, None), {"hit": None, "gap_pct": None})


class AdvisorPageTest(unittest.TestCase):
    def test_trigger_rows_show_live_status(self):
        html = generate_advisor_html(PRICES, 78.0, FIXED)
        rows = re.findall(r'<tr data-kind="(\w+)" data-level="([\d.]+)" data-ticker="(\w+)">.*?</tr>', html, re.S)
        self.assertEqual(len(rows), len(TRIGGERS))
        smh_rows = re.findall(r'data-ticker="SMH">.*?<td class="st-cell">(.*?)</td></tr>', html, re.S)
        self.assertEqual(len(smh_rows), 4)
        self.assertIn("ถึงแล้ว", smh_rows[0])      # 524.25 >= 519
        self.assertIn("อีก -3.7%", smh_rows[1])    # 505 vs 524.25
        self.assertIn("อีก +8.8%", smh_rows[2])
        self.assertIn("อีก -10.9%", smh_rows[3])

    def test_nav_marks_advisor_active(self):
        html = generate_advisor_html(PRICES, 78.0, FIXED)
        self.assertIn('href="advisor.html" class="rnav-link active"', html)

    def test_lly_weight_bar_uses_value(self):
        html = generate_advisor_html(PRICES, 63.4, FIXED)
        self.assertIn("<b>63.4%</b>", html)
        self.assertIn('class="prog-fill" style="width:63.4%"', html)

    def test_no_prices_shows_alert(self):
        html = generate_advisor_html({}, None, FIXED)
        self.assertIn("ดึงราคาจาก TradingView ไม่ได้", html)
        self.assertIn("ไม่มีราคา", html)

    def test_lly_weight_from_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = {"stock_market_val_usd": 50000.0,
                       "positions": [{"ticker": "LLY", "current_val_usd": 39000.0}, {"ticker": "VOO", "current_val_usd": 11000.0}]}
            Path(tmp, "account_summary.json").write_text(json.dumps(summary), encoding="utf-8")
            with mock.patch.dict(os.environ, {"FILTER_STOCK_DATA_DIR": tmp}):
                self.assertEqual(lly_weight_pct(), 78.0)

    def test_page_written_without_network(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"FILTER_STOCK_DATA_DIR": tmp}):
            out = generate_advisor_page(Path(tmp), prices={})
            self.assertEqual(out.name, "advisor.html")
            self.assertIn("คำแนะนำพอร์ต", out.read_text(encoding="utf-8"))

    def test_symbols_cover_every_trigger_and_asked_ticker(self):
        tickers = {t["ticker"] for t in TRIGGERS} | {a["ticker"] for a in advisor.ASKED}
        self.assertEqual(tickers - set(advisor.SYMBOLS), set())


if __name__ == "__main__":
    unittest.main()
