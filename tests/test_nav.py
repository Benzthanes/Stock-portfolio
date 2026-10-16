import re
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.nav import nav_bar_html

FIXED = datetime(2026, 10, 15, 9, 5)


class NavBarTest(unittest.TestCase):
    def test_links_all_reports_in_order(self):
        html = nav_bar_html("master", FIXED)
        self.assertEqual(
            re.findall(r'href="([^"]+)"', html),
            [
                "portfolio_master.html",
                "portfolio_review.html",
                "portfolio_recovery.html",
                "portfolio_dip_sim.html",
                "trades_ledger.html",
                "stock_chart.html",
                "portfolio_set_review.html",
                "portfolio_set_recovery.html",
            ],
        )

    def test_exactly_one_active_item_matches_page(self):
        html = nav_bar_html("ledger", FIXED)
        self.assertEqual(
            re.findall(r'<a href="([^"]+)" class="rnav-link active"', html),
            ["trades_ledger.html"],
        )
        self.assertEqual(html.count('aria-current="page"'), 1)

    def test_timestamp_format(self):
        self.assertIn("อัปเดต: 2026-10-15 09:05", nav_bar_html("chart", FIXED))
        self.assertRegex(nav_bar_html("chart"), r"อัปเดต: \d{4}-\d{2}-\d{2} \d{2}:\d{2}<")

    def test_thai_labels(self):
        html = nav_bar_html("review", FIXED)
        self.assertEqual(
            re.findall(r'class="rnav-link[^"]*"[^>]*>([^<]+)</a>', html),
            ["ภาพรวม", "สุขภาพพอร์ต", "แก้ดอย", "Dip จำลอง", "รายการซื้อขายทั้งหมด", "กราฟ", "หุ้นไทย สุขภาพพอร์ต", "หุ้นไทย แก้ดอย"],
        )

    def test_unknown_page_rejected(self):
        with self.assertRaises(ValueError):
            nav_bar_html("no_such_page", FIXED)


if __name__ == "__main__":
    unittest.main()
