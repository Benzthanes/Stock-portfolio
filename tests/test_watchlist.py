"""
Tests for Watchlist Engine & Fibonacci Support Analysis (src/watchlist.py).
Asserts classification boundaries, data integrity, and fallback rendering when network is unreachable.
"""

import json
import os
import shutil
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from src.watchlist import (
    SOURCE_AUTHOR,
    SOURCE_UPDATED,
    WATCHLIST_STOCKS,
    analyze_watchlist,
    classify_support_distance,
    generate_watchlist_html,
    generate_watchlist_page,
)


class TestWatchlist(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_env = os.environ.get("FILTER_STOCK_DATA_DIR")
        os.environ["FILTER_STOCK_DATA_DIR"] = self.temp_dir

        # Setup mock portfolio.json in temp_dir
        mock_port = {
            "portfolio_name": "Test Port",
            "holdings": [
                {"ticker": "GOOGL", "shares": 10},
                {"ticker": "VRT", "shares": 5},
            ],
        }
        (Path(self.temp_dir) / "portfolio.json").write_text(json.dumps(mock_port), encoding="utf-8")

    def tearDown(self):
        if self.old_env is not None:
            os.environ["FILTER_STOCK_DATA_DIR"] = self.old_env
        else:
            os.environ.pop("FILTER_STOCK_DATA_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_watchlist_stocks_data_integrity(self):
        """Assert 48 image stocks (4 per group) plus SPCX added by the user."""
        self.assertEqual(len(WATCHLIST_STOCKS), 49)
        self.assertEqual(SOURCE_AUTHOR, "Shay Boloor")
        self.assertEqual(SOURCE_UPDATED, "2026-10-17")

        groups = {}
        for s in WATCHLIST_STOCKS:
            g = s["group"]
            groups.setdefault(g, []).append(s)
            self.assertGreater(s["support"], 0)
            self.assertTrue(s["ticker"].isupper())

        self.assertEqual(len(groups), 12)
        for g, stocks in groups.items():
            from_image = [x for x in stocks if not x.get("source")]
            self.assertEqual(len(from_image), 4, f"Group {g} should have exactly 4 image stocks")

        # Spot check specific values from shay_fibo_support_2026-10-17.md
        stock_map = {s["ticker"]: s for s in WATCHLIST_STOCKS}
        self.assertEqual(stock_map["RKLB"]["support"], 50.0)
        self.assertEqual(stock_map["OKLO"]["support"], 27.0)
        self.assertEqual(stock_map["AEHR"]["support"], 57.0)
        self.assertEqual(stock_map["SPCX"]["support"], 115.0)
        self.assertEqual(stock_map["SPCX"]["group"], "Space")
        self.assertEqual([x["ticker"] for x in WATCHLIST_STOCKS if x.get("source")], ["SPCX"])
        self.assertEqual(stock_map["GEV"]["support"], 678.0)
        self.assertEqual(stock_map["LITE"]["support"], 765.0)
        self.assertEqual(stock_map["NOW"]["support"], 124.0)

    def test_classify_support_distance_exact_values(self):
        """Assert exact classification for -0.7%, +4.5%, +7.4%, boundaries, and None."""
        # 1. Negative diff (-0.7%) -> Group A (ต่ำกว่าแนวรับ)
        code_a, label_a = classify_support_distance(-0.7)
        self.assertEqual(code_a, "A")
        self.assertEqual(label_a, "(ก) ต่ำกว่าแนวรับ")

        # 2. 0 to 5% diff (+4.5%) -> Group B (0-5% เหนือแนวรับ)
        code_b, label_b = classify_support_distance(4.5)
        self.assertEqual(code_b, "B")
        self.assertEqual(label_b, "(ข) 0-5% เหนือแนวรับ")

        # 3. > 5% diff (+7.4%) -> Group C (เกิน 5%)
        code_c, label_c = classify_support_distance(7.4)
        self.assertEqual(code_c, "C")
        self.assertEqual(label_c, "(ค) เกิน 5%")

        # Boundary checks
        self.assertEqual(classify_support_distance(-0.0001)[0], "A")
        self.assertEqual(classify_support_distance(0.0)[0], "B")
        self.assertEqual(classify_support_distance(5.0)[0], "B")
        self.assertEqual(classify_support_distance(5.0001)[0], "C")
        self.assertEqual(classify_support_distance(None)[0], "unknown")

    def test_analyze_watchlist_with_mocked_quotes(self):
        """Assert % diff calculation, status assignment, portfolio tagging, and sorting."""
        # Mock quotes for a few sample stocks
        mock_quotes = {
            # OKLO: support 27.0, price 26.811 -> diff -0.189 (-0.7%)
            "OKLO": {"close": 26.811, "premarket_close": None, "postmarket_close": None, "exchange": "NYSE", "description": "Oklo Inc"},
            # ON: support 72.0, price 75.24 -> diff +3.24 (+4.5%)
            "ON": {"close": 75.24, "premarket_close": None, "postmarket_close": None, "exchange": "NASDAQ", "description": "ON Semiconductor"},
            # AEHR: support 57.0, price 61.218 -> diff +4.218 (+7.4%)
            "AEHR": {"close": 61.218, "premarket_close": None, "postmarket_close": None, "exchange": "NASDAQ", "description": "Aehr Test Systems"},
            # GOOGL: in portfolio
            "GOOGL": {"close": 283.82, "premarket_close": 281.85, "postmarket_close": None, "exchange": "NASDAQ", "description": "Alphabet Inc"},
        }

        result = analyze_watchlist(price_data=mock_quotes)
        self.assertEqual(result["total_count"], 49)
        self.assertEqual(result["portfolio_count"], 2)  # GOOGL and VRT in portfolio.json

        item_map = {it["ticker"]: it for it in result["items"]}

        # Check OKLO (-0.7%)
        oklo = item_map["OKLO"]
        self.assertEqual(oklo["status_code"], "A")
        self.assertAlmostEqual(oklo["pct_diff"], -0.7, places=1)

        # Check ON (+4.5%)
        on_item = item_map["ON"]
        self.assertEqual(on_item["status_code"], "B")
        self.assertAlmostEqual(on_item["pct_diff"], 4.5, places=1)

        # Check AEHR (+7.4%)
        aehr = item_map["AEHR"]
        self.assertEqual(aehr["status_code"], "C")
        self.assertAlmostEqual(aehr["pct_diff"], 7.4, places=1)

        # Check GOOGL (in portfolio and premarket priority)
        googl = item_map["GOOGL"]
        self.assertTrue(googl["in_portfolio"])
        self.assertEqual(googl["effective_price"], 281.85)
        self.assertEqual(googl["price_type"], "Premarket")

        # Check sorting: lowest pct_diff comes first
        valid_items = [it for it in result["items"] if it["pct_diff"] is not None]
        for i in range(len(valid_items) - 1):
            self.assertLessEqual(valid_items[i]["pct_diff"], valid_items[i + 1]["pct_diff"])

    @patch("urllib.request.urlopen")
    def test_page_generation_when_http_fetch_fails(self, mock_urlopen):
        """When network fetch fails, generate_watchlist_page must succeed and show alert banner."""
        mock_urlopen.side_effect = urllib.error.URLError("Network access blocked in tests")

        reports_temp = Path(self.temp_dir) / "reports"
        reports_temp.mkdir(parents=True, exist_ok=True)

        out_path = generate_watchlist_page(reports_dir=reports_temp)
        self.assertTrue(out_path.exists())
        self.assertTrue(out_path.is_file())

        content = out_path.read_text(encoding="utf-8")
        # Assert alert banner is present
        self.assertIn("ไม่สามารถดึงราคาล่าสุดจาก TradingView Scanner API ได้", content)
        # Assert disclaimer box is present
        self.assertIn("ข้อจำกัดและคำเตือนสำคัญ (Risk Disclaimer)", content)
        self.assertIn("แนวรับ Fibo จากภาพยังไม่ผ่าน backtest", content)
        self.assertIn("สภาพคล่องช่วง Premarket ต่ำ", content)
        # Assert nav bar is present
        self.assertIn('aria-label="รายงาน"', content)
        self.assertIn("หุ้นที่สนใจ", content)
        # Assert all 49 tickers are in the generated table
        for s in WATCHLIST_STOCKS:
            self.assertIn(f">{s['ticker']}<", content)


if __name__ == "__main__":
    unittest.main()
