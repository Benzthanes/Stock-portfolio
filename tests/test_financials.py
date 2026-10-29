import os
import tempfile
import unittest
from pathlib import Path
from src.financials import (
    fmt_currency,
    get_quarter_label,
    process_quarterly_metrics,
    load_financials_cache,
    save_financials_cache,
    get_all_financials_payload,
    compute_piotroski_f_score,
    generate_financial_executive_summary,
)


class TestFinancials(unittest.TestCase):
    def test_fmt_currency(self):
        self.assertEqual(fmt_currency(None), "-")
        self.assertEqual(fmt_currency(0), "$0.00")
        self.assertEqual(fmt_currency(109417000000.0), "$109.42B")
        self.assertEqual(fmt_currency(-2500000000.0), "-$2.50B")
        self.assertEqual(fmt_currency(45000000.0), "$45.00M")
        self.assertEqual(fmt_currency(1500.0), "$1.5K")

    def test_get_quarter_label(self):
        self.assertEqual(get_quarter_label("2026-06-30"), "Q2'26")
        self.assertEqual(get_quarter_label("2025-12-31"), "Q4'25")
        self.assertEqual(get_quarter_label("2026-03-31"), "Q1'26")
        self.assertEqual(get_quarter_label("2025-09-30"), "Q3'25")

    def test_process_quarterly_metrics_calculations(self):
        # 5 quarters of mock data to verify QoQ, YoY, Margins, and D/E
        mock_raw = {
            "timeseries": {
                "result": [
                    {
                        "meta": {"type": ["quarterlyTotalRevenue"]},
                        "quarterlyTotalRevenue": [
                            {"asOfDate": "2025-06-30", "reportedValue": {"raw": 100.0}},
                            {"asOfDate": "2025-09-30", "reportedValue": {"raw": 110.0}},
                            {"asOfDate": "2025-12-31", "reportedValue": {"raw": 120.0}},
                            {"asOfDate": "2026-03-31", "reportedValue": {"raw": 130.0}},
                            {"asOfDate": "2026-06-30", "reportedValue": {"raw": 125.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["quarterlyNetIncome"]},
                        "quarterlyNetIncome": [
                            {"asOfDate": "2025-06-30", "reportedValue": {"raw": 20.0}},
                            {"asOfDate": "2025-09-30", "reportedValue": {"raw": 22.0}},
                            {"asOfDate": "2025-12-31", "reportedValue": {"raw": 24.0}},
                            {"asOfDate": "2026-03-31", "reportedValue": {"raw": 26.0}},
                            {"asOfDate": "2026-06-30", "reportedValue": {"raw": 25.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["quarterlyGrossProfit"]},
                        "quarterlyGrossProfit": [
                            {"asOfDate": "2026-06-30", "reportedValue": {"raw": 50.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["quarterlyDilutedEPS"]},
                        "quarterlyDilutedEPS": [
                            {"asOfDate": "2026-06-30", "reportedValue": {"raw": 2.50}},
                        ],
                    },
                    {
                        "meta": {"type": ["quarterlyTotalDebt"]},
                        "quarterlyTotalDebt": [
                            {"asOfDate": "2026-06-30", "reportedValue": {"raw": 60.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["quarterlyStockholdersEquity"]},
                        "quarterlyStockholdersEquity": [
                            {"asOfDate": "2026-06-30", "reportedValue": {"raw": 80.0}},
                        ],
                    },
                    {
                        "meta": {"type": ["quarterlyFreeCashFlow"]},
                        "quarterlyFreeCashFlow": [
                            {"asOfDate": "2026-06-30", "reportedValue": {"raw": 30.0}},
                        ],
                    },
                ]
            }
        }

        candles = [{"time": "2026-06-30", "close": 200.0}]
        res = process_quarterly_metrics("TEST", mock_raw, candles=candles)

        self.assertTrue(res["has_data"])
        self.assertEqual(res["quarters_count"], 5)
        self.assertEqual(res["latest_quarter"], "Q2'26")

        quarters = res["quarters"]
        latest = quarters[-1]

        # Margin: 25 / 125 = 20.0%
        self.assertEqual(latest["net_margin"], 20.0)
        # Gross Margin: 50 / 125 = 40.0%
        self.assertEqual(latest["gross_margin"], 40.0)
        # D/E: 60 / 80 = 0.75
        self.assertEqual(latest["debt_to_equity"], 0.75)
        # QoQ Revenue: (125 - 130) / 130 * 100 = -3.85%
        self.assertEqual(latest["rev_growth_qoq"], -3.85)
        # YoY Revenue: (125 - 100) / 100 * 100 = 25.0%
        self.assertEqual(latest["rev_growth_yoy"], 25.0)
        # Quarterly P/E: 200 / (2.5 * 4) = 20.0
        self.assertEqual(latest["pe_quarterly"], 20.0)

    def test_cache_save_and_load_isolated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_cache = {
                "AAPL": {"ticker": "AAPL", "has_data": True, "quarters": [{"date": "2026-06-30", "revenue": 100}]}
            }
            save_financials_cache(test_cache, data_dir=tmp_path)
            loaded = load_financials_cache(data_dir=tmp_path)
            self.assertEqual(loaded["AAPL"]["quarters"][0]["revenue"], 100)

    def test_piotroski_f_score(self):
        # Empty quarters
        empty_res = compute_piotroski_f_score([])
        self.assertIsNone(empty_res["score"])
        self.assertEqual(empty_res["max_score"], 9)

        # High-health quarters with full 5 quarters for YoY
        q1 = {
            "revenue": 100,
            "net_income": 20,
            "gross_margin": 55.0,
            "operating_margin": 30.0,
            "debt_to_equity": 0.5,
            "stockholders_equity": 200,
            "fcf": 25,
        }
        q2 = {
            "revenue": 120,
            "net_income": 30,
            "gross_margin": 60.0,
            "operating_margin": 35.0,
            "debt_to_equity": 0.4,
            "stockholders_equity": 230,
            "fcf": 35,
        }
        res = compute_piotroski_f_score([q1, q1, q1, q1, q2])
        self.assertIsNotNone(res["score"])
        self.assertGreaterEqual(res["score"], 8)
        self.assertEqual(res["max_score"], 9)
        self.assertEqual(len(res["criteria"]), 9)
        self.assertIn("Elite", res["label"])
        self.assertEqual(res["title"], "เช็กลิสต์งบ 9 ข้อ (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)")

        # Short quarters (< 5) should show N/A for YoY without failing
        res_short = compute_piotroski_f_score([q1, q2])
        self.assertEqual(res_short["max_score"], 7)
        self.assertEqual(res_short["score"], 7)
        self.assertEqual(res_short["evaluable_count"], 7)
        self.assertIsNone(res_short["criteria"][3]["passed"])
        self.assertEqual(res_short["criteria"][3]["detail"], "N/A")
        self.assertIsNone(res_short["criteria"][6]["passed"])
        self.assertEqual(res_short["criteria"][6]["detail"], "N/A")

        # Insufficient criteria (< 5 evaluable) should label "ข้อมูลไม่พอ"
        q_sparse = {"revenue": 100}  # Only 1 or 2 evaluable
        res_sparse = compute_piotroski_f_score([q_sparse])
        self.assertLess(res_sparse["evaluable_count"], 5)
        self.assertEqual(res_sparse["label"], "ข้อมูลไม่พอ")
        self.assertIn("title", res_sparse)
        self.assertEqual(res_sparse["title"], "เช็กลิสต์งบ 9 ข้อ (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)")

    def test_process_quarterly_metrics_stale_timestamp(self):
        # When raw_data is None (stale), if existing_timestamp is None, timestamp should be 0, not now
        res_none_ts = process_quarterly_metrics("TEST", None, existing_timestamp=None)
        self.assertTrue(res_none_ts["stale"])
        self.assertEqual(res_none_ts["timestamp"], 0)

        # When existing_timestamp is provided, preserve it exactly
        res_with_ts = process_quarterly_metrics("TEST", None, existing_timestamp=1700000000)
        self.assertTrue(res_with_ts["stale"])
        self.assertEqual(res_with_ts["timestamp"], 1700000000)

    def test_generate_financial_executive_summary(self):
        quarters = [
            {
                "revenue": 100,
                "revenue_fmt": "$100.00M",
                "rev_growth_yoy": 25.5,
                "net_margin": 30.0,
                "net_income_fmt": "$30.00M",
                "debt_to_equity": 0.5,
                "total_debt_fmt": "$50.00M",
                "fcf": 35,
                "fcf_fmt": "$35.00M",
            }
        ]
        summary = generate_financial_executive_summary(quarters)
        self.assertIn("เติบโต", summary["growth"])
        self.assertIn("FCF แข็งแกร่ง", summary["profitability"])
        self.assertIn("ปลอดภัยสูงมาก", summary["debt"])

        # Test negative FCF and negative equity
        quarters_neg = [
            {
                "revenue": 100,
                "revenue_fmt": "$100.00M",
                "rev_growth_yoy": -5.0,
                "net_margin": 26.0,
                "net_income_fmt": "$26.00M",
                "debt_to_equity": -0.5,
                "total_debt_fmt": "$80.00M",
                "fcf": -20,
                "fcf_fmt": "-$20.00M",
            }
        ]
        summary_neg = generate_financial_executive_summary(quarters_neg)
        self.assertIn("FCF ติดลบ", summary_neg["profitability"])
        self.assertNotIn("FCF แข็งแกร่ง", summary_neg["profitability"])
        self.assertIn("Negative Equity", summary_neg["debt"])


if __name__ == "__main__":
    unittest.main()

