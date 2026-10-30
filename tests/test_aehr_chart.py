"""
Tests for AEHR integration in stock chart and metadata registry.
Asserts that AEHR is correctly tracked as a watched stock with Fibo support,
not counted as a portfolio holding or realized trade, and rendered with the 'จับตา' badge.
Honors FILTER_STOCK_DATA_DIR to guarantee data isolation.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.chart_page import (
    WATCHED_STOCKS,
    get_all_stocks_metadata,
)
from src.profiles import get_business_summary


class TestAehrChart(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_env = os.environ.get("FILTER_STOCK_DATA_DIR")
        os.environ["FILTER_STOCK_DATA_DIR"] = self.temp_dir

        # Isolated portfolio with LLY holding
        mock_port = {
            "portfolio_name": "Test Port",
            "holdings": [
                {
                    "ticker": "LLY",
                    "name": "Eli Lilly and Company",
                    "shares": 27.6477,
                    "avg_cost_usd": 750.0,
                    "close_price": 820.0,
                }
            ],
        }
        (Path(self.temp_dir) / "portfolio.json").write_text(json.dumps(mock_port), encoding="utf-8")

        # Isolated trades with PLTR closed trade
        mock_trades = {
            "trades": [
                {
                    "ticker": "PLTR",
                    "name": "Palantir Technologies Inc.",
                    "buy_price_usd": 25.0,
                    "sell_price_usd": 42.0,
                }
            ]
        }
        (Path(self.temp_dir) / "trades.json").write_text(json.dumps(mock_trades), encoding="utf-8")

    def tearDown(self):
        if self.old_env is not None:
            os.environ["FILTER_STOCK_DATA_DIR"] = self.old_env
        else:
            os.environ.pop("FILTER_STOCK_DATA_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_aehr_in_watched_stocks_registry(self):
        """Assert AEHR is in WATCHED_STOCKS table with valid metadata and Shay Boloor fibo support."""
        self.assertIn("AEHR", WATCHED_STOCKS)
        info = WATCHED_STOCKS["AEHR"]
        self.assertEqual(info["name"], "Aehr Test Systems")
        self.assertEqual(info["sector"], "Semiconductor Equipment")
        self.assertEqual(info["exchange"], "NASDAQ")
        self.assertEqual(info["fibo_support"], 57.0)

    def test_aehr_metadata_classification(self):
        """Assert AEHR in get_all_stocks_metadata() is NOT a holding, is watched, and has zero cost."""
        meta = get_all_stocks_metadata()
        self.assertIn("AEHR", meta)

        aehr_meta = meta["AEHR"]
        self.assertEqual(aehr_meta["ticker"], "AEHR")
        self.assertEqual(aehr_meta["name"], "Aehr Test Systems")
        self.assertEqual(aehr_meta["exchange"], "NASDAQ")
        self.assertIs(aehr_meta["is_holding"], False)
        self.assertIs(aehr_meta["is_watched"], True)
        self.assertEqual(aehr_meta["cost"], 0.0)
        self.assertEqual(aehr_meta["shares"], 0.0)
        self.assertEqual(aehr_meta["support"], 57.0)

        # Confirm holding and closed trades are correctly distinguished
        self.assertIn("LLY", meta)
        self.assertIs(meta["LLY"]["is_holding"], True)
        self.assertIs(meta["LLY"]["is_watched"], False)

        self.assertIn("PLTR", meta)
        self.assertIs(meta["PLTR"]["is_holding"], False)
        self.assertIs(meta["PLTR"]["is_watched"], False)

    def test_aehr_business_profile(self):
        """Assert business summary for AEHR describes semiconductor wafer-level burn-in."""
        summary = get_business_summary("AEHR")
        self.assertIn("ผู้ผลิตระบบทดสอบและเบิร์นอินระดับเวเฟอร์", summary)
        self.assertIn("Wafer-level Burn-in", summary)

    def test_aehr_sidebar_pill_rendering(self):
        """Assert pill for AEHR contains 'จับตา' badge and not 'ถืออยู่' or 'ขายแล้ว'."""
        meta = get_all_stocks_metadata()
        m = meta["AEHR"]

        # Replicate pill badge generation from chart_page
        is_holding = m.get("is_holding", False)
        is_watched = m.get("is_watched", False)
        if is_holding:
            badge_html = '<span class="sc-badge sc-badge-holding">ถืออยู่</span>'
        elif is_watched:
            badge_html = '<span class="sc-badge sc-badge-watch">จับตา</span>'
        else:
            badge_html = '<span class="sc-badge sc-badge-closed">ขายแล้ว</span>'

        self.assertEqual(badge_html, '<span class="sc-badge sc-badge-watch">จับตา</span>')
        self.assertNotIn("ถืออยู่", badge_html)
        self.assertNotIn("ขายแล้ว", badge_html)


if __name__ == "__main__":
    unittest.main()


class TestStockCountBadge(unittest.TestCase):
    def test_count_badges_are_filled_not_hardcoded(self):
        """Both stock-count badges take the real ticker count (it was hard-coded to 15)."""
        from src.chart_page import render_chart_template
        html = render_chart_template({"__STOCK_COUNT__": "16"})
        self.assertIn('id="floating_stock_badge">16<', html)
        self.assertIn('id="sidebar_stock_count">16<', html)
        self.assertNotIn("__STOCK_COUNT__", html)
