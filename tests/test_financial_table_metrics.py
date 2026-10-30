import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHART_JS_PATH = ROOT / "src" / "templates" / "chart.js"
CHART_CSS_PATH = ROOT / "src" / "templates" / "chart.css"


class TestFinancialTableMetrics(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CHART_JS_PATH.exists(), "src/templates/chart.js must exist")
        self.assertTrue(CHART_CSS_PATH.exists(), "src/templates/chart.css must exist")
        self.js_code = CHART_JS_PATH.read_text(encoding="utf-8")
        self.css_code = CHART_CSS_PATH.read_text(encoding="utf-8")

    def test_financial_metrics_schema_has_14_rows(self):
        self.assertIn("FINANCIAL_METRICS_SCHEMA", self.js_code)
        match = re.search(
            r"const\s+FINANCIAL_METRICS_SCHEMA\s*=\s*\[([\s\S]*?)\];",
            self.js_code,
        )
        self.assertIsNotNone(match, "FINANCIAL_METRICS_SCHEMA array must be found in chart.js")
        schema_body = match.group(1)

        keys = re.findall(r"key:\s*'([^']+)'", schema_body)
        short_ens = re.findall(r"short_en:\s*'([^']+)'", schema_body)
        help_ths = re.findall(r"help_th:\s*'([^']+)'", schema_body)

        expected_keys = [
            "revenue",
            "rev_growth_qoq",
            "rev_growth_yoy",
            "gross_profit",
            "gross_margin",
            "operating_income",
            "net_income",
            "net_margin",
            "eps",
            "fcf",
            "total_debt",
            "stockholders_equity",
            "debt_to_equity",
            "pe_quarterly",
        ]
        expected_short_ens = [
            "Revenue",
            "Rev QoQ",
            "Rev YoY",
            "GP",
            "GM %",
            "Op Income",
            "NI",
            "NM %",
            "EPS",
            "FCF",
            "Debt",
            "Equity",
            "D/E",
            "P/E",
        ]

        self.assertEqual(len(keys), 14, f"Expected 14 keys in schema, got {len(keys)}")
        self.assertEqual(keys, expected_keys, "Schema keys must match the exact 14 expected financial rows")
        self.assertEqual(len(short_ens), 14, f"Expected 14 short_en in schema, got {len(short_ens)}")
        self.assertEqual(short_ens, expected_short_ens, "Schema short_en must match expected abbreviations")
        self.assertEqual(len(help_ths), 14, f"Expected 14 help_th explanations, got {len(help_ths)}")

        for key, help_text in zip(keys, help_ths):
            self.assertTrue(
                help_text.strip().endswith("."),
                f"help_th for {key} must end with a period: {help_text}",
            )
            self.assertNotIn("—", help_text, f"help_th for {key} must not contain long dash: {help_text}")
            self.assertNotIn("–", help_text, f"help_th for {key} must not contain en dash: {help_text}")

    def test_obsolete_mobile_list_removed(self):
        self.assertNotIn("finMobileSelectQuarter", self.js_code, "finMobileSelectQuarter must be removed")
        self.assertNotIn(".finm-list", self.js_code, ".finm-list must be removed from chart.js")
        self.assertNotIn(".finm-chips", self.js_code, ".finm-chips must be removed from chart.js")
        self.assertNotIn(".finm-list", self.css_code, ".finm-list must be removed from chart.css")
        self.assertNotIn(".finm-chips", self.css_code, ".finm-chips must be removed from chart.css")

    def test_popover_and_mobile_table_registered(self):
        self.assertIn("window.toggleFinHelp = toggleFinHelp;", self.js_code)
        self.assertIn("window.closeFinHelp = closeFinHelp;", self.js_code)
        self.assertIn("window.finMobileView = finMobileView;", self.js_code)
        self.assertIn("window.FINANCIAL_METRICS_SCHEMA = FINANCIAL_METRICS_SCHEMA;", self.js_code)

    def test_css_sticky_header_solid_background(self):
        self.assertIn(".fin-table td.fin-row-header,", self.css_code)
        self.assertIn(".fin-table .fin-row-sub td.fin-row-header,", self.css_code)
        self.assertIn("background: #0c1427 !important;", self.css_code)
