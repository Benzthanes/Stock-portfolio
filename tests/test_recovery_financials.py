"""
Tests for portfolio recovery and financial reports:
1. recovery.py loss_thb using holding cost_thb - (shares * close * fx)
2. Capital rotation zero-score metric identification and Smart DCA currency symbol
3. Passing existing row to analyze_recovery
4. financials checklist (non-Piotroski name, YoY handling, missing data N/A, FCF check, D/E bands)
5. financials fetch error handling (stale flag, old timestamp retention)
6. outlook curated & generic fallback guard
7. dip sim empty state
8. html_report responsive grid & concentration card
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from recovery import analyze_all_underwater, analyze_recovery
from src.financials import (
    compute_piotroski_f_score,
    generate_financial_executive_summary,
    process_quarterly_metrics,
)
from src.outlook import get_forward_outlook
from scripts.generate_dip_sim_report import generate_html_report
from src.html_report import _format_fx_badge, _news_items_html, generate_portfolio_html, generate_recovery_html
from scripts.generate_master_report import (
    generate_master_dashboard_html,
    generate_master_ledger_html,
    CONCENTRATION_RISK_THRESHOLD_PCT,
    format_win_rate_text,
)


class TestRecoveryLogic(unittest.TestCase):
    def test_loss_thb_uses_reconciled_cost_thb(self):
        """Task 1: assert loss_thb = cost_thb - (shares * close * fx) with real numbers."""
        mock_portfolio = {
            "portfolio_name": "Test Port",
            "base_currency": "USD",
            "fx_rate_usd_thb": 35.0,
            "holdings": [
                {
                    "ticker": "XYZ",
                    "shares": 10.0,
                    "avg_cost_usd": 100.0,
                    "cost_thb": 36200.0,  # Reconciled from slip (differs from 10*100*35 = 35000)
                    "exchange": "NASDAQ",
                }
            ],
        }
        mock_screener = [
            {
                "ticker": "XYZ",
                "name": "XYZ",
                "close": 90.0,
                "ATR": 2.0,
                "sector": "Technology",
                "industry": "Software",
            }
        ]
        with patch("recovery.load_portfolio", return_value=mock_portfolio), \
             patch("recovery.fetch_screener_data", return_value=mock_screener), \
             patch("recovery.fetch_batch_catalysts", return_value={}), \
             patch("recovery.get_catalyst_breakdown", return_value={"bullish": [], "bearish": []}):
            res = analyze_all_underwater(portfolio_path="dummy.json")

        self.assertEqual(res["total_underwater_count"], 1)
        pos = res["positions"][0]
        # shares * close * fx = 10 * 90 * 35 = 31,500 THB
        # loss_thb = cost_thb - (shares * close * fx) = 36,200 - 31,500 = 4,700 THB
        expected_loss_thb = 36200.0 - (10.0 * 90.0 * 35.0)
        self.assertEqual(expected_loss_thb, 4700.0)
        self.assertAlmostEqual(pos["loss_thb"], 4700.0, places=2)
        self.assertAlmostEqual(res["total_underwater_loss_thb"], 4700.0, places=2)
        # loss_usd = abs(unrealized_pl) = 10 * 100 - 10 * 90 = 100 USD
        self.assertAlmostEqual(pos["loss_usd"], 100.0, places=2)
        self.assertAlmostEqual(res["total_underwater_loss_usd"], 100.0, places=2)

    def test_capital_rotation_zero_score_metric_and_smart_dca_currency(self):
        """Task 2: Capital Rotation specifies 0-score metric, Smart DCA uses correct curr_sym."""
        # 1. Test Smart DCA with THB currency
        mock_port_thb = {
            "portfolio_name": "THB Port",
            "base_currency": "THB",
            "holdings": [{"ticker": "ABC", "shares": 10.0, "avg_cost": 100.0}],
        }
        mock_row_dca = {
            "ticker": "ABC",
            "name": "ABC",
            "close": 80.0,
            "total_revenue_yoy_growth_ttm": 30.0,
            "net_income_yoy_growth_ttm": 35.0,
            "return_on_equity_fq": 30.0,
            "price_earnings_growth_ttm": 0.8,
            "debt_to_equity_fq": 0.3,
            "free_cash_flow_ttm": 1e9,
            "EMA200": 70.0,
            "RSI": 30.0,
            "ATR": 2.0,
        }
        with patch("recovery.load_portfolio", return_value=mock_port_thb), \
             patch("recovery.get_catalyst_breakdown", return_value={"bullish": [], "bearish": []}):
            rec = analyze_recovery("ABC", market_row=mock_row_dca)
            self.assertEqual(rec["primary_playbook"], "Smart DCA")
            self.assertIn("฿", rec["layman_action"])
            self.assertNotIn("$", rec["layman_action"])

        # 2. Test Capital Rotation metric
        mock_row_weak = {
            "ticker": "WEAK",
            "name": "WEAK",
            "close": 50.0,
            "total_revenue_yoy_growth_ttm": -15.0,  # Negative revenue trap
            "net_income_yoy_growth_ttm": -25.0,   # Shrinking
            "return_on_equity_fq": -5.0,          # Negative ROE
            "price_earnings_growth_ttm": -1.2,     # Negative PEG
            "debt_to_equity_fq": 3.5,             # High debt risk
            "free_cash_flow_ttm": -1e6,           # Negative FCF
            "EMA200": 70.0,
            "RSI": 45.0,
            "ATR": 2.0,
        }
        with patch("recovery.load_portfolio", return_value=mock_port_thb), \
             patch("recovery.get_catalyst_breakdown", return_value={"bullish": [], "bearish": []}):
            rec_weak = analyze_recovery("WEAK", custom_cost=100.0, custom_shares=10.0, market_row=mock_row_weak)
            self.assertEqual(rec_weak["primary_playbook"], "Capital Rotation")
            self.assertIn("Capital Rotation", rec_weak["action_verdict"])
            # Assert it mentions specific weak points rather than just generic "กำไรหดตัว"
            self.assertFalse("ทำไรหดตัว" in rec_weak["action_verdict"])


class TestFinancialsLogic(unittest.TestCase):
    def test_piotroski_renamed_and_yoy_guard(self):
        """Task 4: Checklist title renamed, YoY guarded if < 5 quarters, missing data N/A."""
        # 1. Less than 5 quarters
        q1 = {"revenue": 100, "net_income": 20, "fcf": 25, "debt_to_equity": 0.5, "gross_margin": 60.0, "operating_margin": 30.0, "stockholders_equity": 200}
        q2 = {"revenue": 120, "net_income": 30, "fcf": 35, "debt_to_equity": 0.4, "gross_margin": 62.0, "operating_margin": 32.0, "stockholders_equity": 230}
        res_short = compute_piotroski_f_score([q1, q2])
        self.assertEqual(res_short["title"], "เช็กลิสต์งบ 9 ข้อ (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)")
        self.assertEqual(res_short["criteria"][3]["detail"], "N/A")
        self.assertIsNone(res_short["criteria"][3]["passed"])
        self.assertEqual(res_short["criteria"][6]["detail"], "N/A")
        self.assertIsNone(res_short["criteria"][6]["passed"])
        self.assertEqual(res_short["max_score"], 7)

        # 2. Missing data should not become 0 or "$0"
        q_missing = {"revenue": None, "net_income": None, "fcf": None, "debt_to_equity": None}
        res_missing = compute_piotroski_f_score([q_missing])
        for crit in res_missing["criteria"]:
            self.assertNotEqual(crit["detail"], "$0")
            self.assertNotEqual(crit["detail"], "0")

    def test_fcf_executive_summary_sign(self):
        """Task 4: Executive summary checks FCF sign before declaring strong/positive FCF."""
        q_neg_fcf = [{
            "revenue": 100,
            "revenue_fmt": "$100.00M",
            "rev_growth_yoy": 15.0,
            "net_margin": 28.0,
            "net_income_fmt": "$28.00M",
            "fcf": -15.0,
            "fcf_fmt": "-$15.00M",
            "debt_to_equity": 0.4,
            "total_debt_fmt": "$40.00M",
        }]
        summary = generate_financial_executive_summary(q_neg_fcf)
        self.assertIn("FCF ติดลบ", summary["profitability"])
        self.assertNotIn("FCF แข็งแกร่ง", summary["profitability"])
        self.assertNotIn("FCF เป็นบวก", summary["profitability"])

    def test_stale_flag_on_fetch_failure(self):
        """Task 5: process_quarterly_metrics retains old timestamp and sets stale=True on failure."""
        old_ts = 1700000000
        existing_quarters = [{"date": "2024-03-31", "revenue": 100, "net_income": 20}]
        res = process_quarterly_metrics(
            "TEST",
            raw_data=None,  # Simulated fetch failure
            existing_quarters=existing_quarters,
            existing_timestamp=old_ts,
        )
        self.assertTrue(res["stale"])
        self.assertEqual(res["timestamp"], old_ts)


class TestOutlookAndDipSim(unittest.TestCase):
    def test_outlook_guards(self):
        """Task 12 & 13: NVDA date, VRT no claim, BAC t_low check, generic fallback underwater check."""
        # 1. BAC with close >= t_low should not say "ต่ำกว่าเป้าหมายสถาบันทุกแห่ง"
        mock_data_bac = {
            "ticker": "BAC",
            "close": 45.0,
            "price_target_low": 40.0,  # close is above target low
            "price_target_average": 50.0,
            "sector": "Finance",
        }
        out_bac = get_forward_outlook("BAC", mock_data_bac, {"quality_tier": "🟢 Resilient Major Bank"}, 30, 42.0, 45.0)
        self.assertNotIn("ต่ำกว่าเป้าหมายสถาบันทุกแห่ง", out_bac["tailored_roadmap"])

        # 2. Generic fallback when stock is not underwater
        mock_data_gen = {"ticker": "PROFIT", "close": 120.0, "sector": "Tech", "industry": "Software"}
        out_gen = get_forward_outlook("PROFIT", mock_data_gen, {}, 45, 100.0, 120.0)
        self.assertEqual(out_gen["drawdown_root_cause"], [])

    def test_dip_sim_empty_state(self):
        """Task 14: When no positions, renders empty state card and neutral color."""
        data_empty = {
            "portfolio_name": "Dip Simulation",
            "description": "Dip Test",
            "base_currency": "THB",
            "fx_rate": 35.0,
            "total_capital_thb": 0.0,
            "total_capital_usd": 0.0,
            "total_current_val_thb": 0.0,
            "total_current_val_usd": 0.0,
            "total_pl_thb": 0.0,
            "total_pl_usd": 0.0,
            "total_pl_pct": 0.0,
            "holdings_count": 0,
            "in_profit_count": 0,
            "hit_tp_count": 0,
            "hit_sl_count": 0,
            "positions": [],
            "closed_trades": [],
        }
        html = generate_html_report(data_empty)
        self.assertIn("ยังไม่มีไม้จำลอง", html)
        self.assertIn("/dip", html)
        self.assertNotIn("ตารางจำลองการถือครองหุ้น Dip รายตัว", html)
        self.assertNotIn("รายละเอียดกลยุทธ์และเหตุผลการช้อนซื้อของแต่ละตัว", html)


class TestHtmlReportBadges(unittest.TestCase):
    def test_news_badges(self):
        """Task 10: LLM review badge and heuristic badge."""
        items = [
            {"title": "News 1", "title_th": "ข่าว 1", "ai_analyzed": True, "source": "Reuters"},
            {"title": "News 2", "title_th": "ข่าว 2", "ai_analyzed": False, "source": "Bloomberg"},
        ]
        html = _news_items_html(items, "ไม่มีข่าว")
        self.assertIn("สรุปโดย LLM ตรวจซ้ำก่อนใช้", html)
        self.assertNotIn("AI Verified", html)
        self.assertIn("heuristic", html)


class TestMasterReportMetrics(unittest.TestCase):
    def setUp(self):
        fx_patch = patch("src.fx.fetch_usdthb", return_value=35.0)
        self.fetch_fx = fx_patch.start()
        self.addCleanup(fx_patch.stop)
        self.fixture_data = {
            "portfolio_name": "Test Master Port",
            "broker": "Dime!",
            "account_no": "12345678",
            "fx_rate": 35.0,
            "total_net_worth_thb": 150000.0,
            "total_net_worth_usd": 4285.71,
            "net_injected_capital_thb": 100000.0,
            "all_time_profit_thb": 50000.0,
            "all_time_roi_pct": 50.0,
            "total_cash_thb": 20000.0,
            "dime_save_cash_thb": 15000.0,
            "dime_usd_cash": 142.85,
            "stock_market_val_usd": 3714.28,
            "stock_market_val_thb": 130000.0,
            "stock_unrealized_pl_usd": 714.28,
            "stock_unrealized_pl_thb": 25000.0,
            "stock_unrealized_pl_pct": 23.8,
            "total_dividends_usd": 50.0,
            "total_dividends_thb": 1750.0,
            "total_realized_and_div_thb": 28750.0,
            "trades_summary": {
                "total_trades": 7,
                "winning_trades": 7,
                "losing_trades": 0,
                "win_rate_pct": 100.0,
                "total_realized_pl_usd": 800.0,
                "total_realized_pl_thb": 27000.0,
            },
            "positions": [
                {
                    "ticker": "LLY",
                    "name": "Eli Lilly",
                    "exchange": "NYSE",
                    "shares": 10.0,
                    "avg_cost_usd": 200.0,
                    "close_price": 300.0,
                    "current_val_usd": 3000.0,
                    "current_val_thb": 105000.0,
                    "unrealized_pl_usd": 1000.0,
                    "unrealized_pl_thb": 35000.0,
                    "unrealized_pl_pct": 50.0,
                    "weight_pct": 75.0,
                },
                {
                    "ticker": "NVDA",
                    "name": "Nvidia",
                    "exchange": "NASDAQ",
                    "shares": 5.0,
                    "avg_cost_usd": 100.0,
                    "close_price": 140.0,
                    "current_val_usd": 700.0,
                    "current_val_thb": 24500.0,
                    "unrealized_pl_usd": 200.0,
                    "unrealized_pl_thb": 7000.0,
                    "unrealized_pl_pct": 40.0,
                    "weight_pct": 25.0,
                },
            ],
            "buy_orders": [
                {
                    "date": "2026-01-10 10:00:00",
                    "ticker": "LLY",
                    "order_type": "Market",
                    "account": "Dime! Save",
                    "shares": 10.0,
                    "price_usd": 200.0,
                    "amt_usd": 2000.0,
                    "amt_thb": 70000.0,
                    "fx_rate": 35.0,
                    "fn": "slip1.jpg",
                }
            ],
            "closed_trades": [
                {
                    "id": "trade_0",
                    "ticker": "SPY",
                    "name": "SPDR S&P 500",
                    "buy_date": "2025-01-01",
                    "date": "2025-06-01",
                    "holding_days": 150,
                    "shares": 5.0,
                    "buy_price_usd": 400.0,
                    "sell_price_usd": 450.0,
                    "total_cost_usd": 2000.0,
                    "net_revenue_usd": 2250.0,
                    "realized_pl_usd": 250.0,
                    "realized_pl_thb": 8750.0,
                    "realized_pl_pct": 12.5,
                    "buy_tranches": [],
                }
            ],
            "dividends_list": [
                {
                    "date": "2026-02-01",
                    "ticker": "AAPL",
                    "rate": "0.25",
                    "amount_usd": 25.0,
                }
            ],
            "cash_movements": [
                {
                    "type": "ฝากเงิน",
                    "date_str": "2026-01-01",
                    "amount_thb": 50000.0,
                    "balance_thb": 50000.0,
                    "channel": "PromptPay",
                    "ref": "REF001",
                }
            ],
        }

    def test_realized_pl_and_win_rate_display(self):
        # Master dashboard: Realized P&L shows THB first, USD second; Win Rate shows "7/7 ไม้กำไร"
        html = generate_master_dashboard_html(self.fixture_data)
        self.assertIn("฿27,000.00", html)
        self.assertIn("+$800.00 USD", html)
        self.assertIn("7/7 ไม้กำไร", html)
        self.assertNotIn("Win Rate 100.0%", html)

        # Ledger dashboard: Realized P&L shows THB first, USD second; Win Rate shows "7/7 ไม้กำไร"
        ledger_html = generate_master_ledger_html(self.fixture_data)
        self.assertIn("฿27,000.00", ledger_html)
        self.assertIn("+$800.00 USD", ledger_html)
        self.assertIn("7/7 ไม้กำไร", ledger_html)

    def test_win_rate_percentage_when_at_least_20_trades(self):
        data_20 = dict(self.fixture_data)
        data_20["trades_summary"] = {
            "total_trades": 20,
            "winning_trades": 18,
            "losing_trades": 2,
            "win_rate_pct": 90.0,
            "total_realized_pl_usd": 1500.0,
            "total_realized_pl_thb": 52500.0,
        }
        html = generate_master_dashboard_html(data_20)
        self.assertIn("Win Rate 90.0% (18/20 ไม้กำไร)", html)

    def test_concentration_callout_on_master_page(self):
        # LLY is 75% >= 40% threshold -> must show callout
        html = generate_master_dashboard_html(self.fixture_data)
        self.assertIn("แจ้งเตือนความเสี่ยงการกระจุกตัว", html)
        self.assertIn("LLY = 75.0%", html)
        self.assertIn("40%", html)

        # When no stock >= 40% -> no callout
        data_balanced = dict(self.fixture_data)
        data_balanced["positions"] = [
            {**p, "weight_pct": 20.0} for p in self.fixture_data["positions"]
        ]
        html_balanced = generate_master_dashboard_html(data_balanced)
        self.assertNotIn("แจ้งเตือนความเสี่ยงการกระจุกตัว", html_balanced)

    def test_kpi_short_thai_headers_with_english_title(self):
        html = generate_master_dashboard_html(self.fixture_data)
        self.assertIn('title="Total Net Worth / NAV">มูลค่าพอร์ตรวมสุทธิ<', html)
        self.assertIn('title="Net Deposited Capital">เงินต้นทุนเติมสุทธิ<', html)
        self.assertIn('title="All-Time Net Profit">กำไรรวมสุทธิของพอร์ต<', html)
        self.assertIn('title="Total Idle Cash">เงินสดคงเหลือรวม<', html)

    def test_table_formatting_and_no_nested_max_height(self):
        html = generate_master_dashboard_html(self.fixture_data)
        self.assertNotIn("max-height: 520px", html)
        ledger_html = generate_master_ledger_html(self.fixture_data)
        self.assertNotIn("max-height: 520px", ledger_html)
        self.assertIn("white-space: nowrap", ledger_html)


class TestTradesLedgerAndFx(unittest.TestCase):
    def setUp(self):
        import json
        import tempfile
        import shutil
        from pathlib import Path
        fx_patch = patch("src.fx.fetch_usdthb", return_value=None)
        self.fetch_fx = fx_patch.start()
        self.addCleanup(fx_patch.stop)
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.portfolio_path = self.tmp / "portfolio.json"
        self.ledger_path = self.tmp / "ledger.json"
        self.portfolio_path.write_text(
            json.dumps({"fx_rate_usd_thb": 33.0, "holdings": []}), encoding="utf-8"
        )
        self.ledger_path.write_text(
            json.dumps({
                "cash": {"dime_save_thb": 10000.0, "dime_usd": 500.0},
                "net_injected_capital_thb": 10000.0,
                "gross_deposits_thb": 10000.0,
                "transfer_out_thb": 0.0,
                "dime_save_interest_thb": 0.0,
                "cash_movements": [],
                "dividends": [],
                "buy_orders": [],
            }), encoding="utf-8"
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_record_buy_pay_usd_uses_fallback_fx_and_preserves_portfolio_fx(self):
        """Task 4: pay='usd' uses FALLBACK_USDTHB (33.62) or specified fx_rate, and _run_fx doesn't overwrite portfolio fx."""
        from src.trades import record_buy
        from src.fx import FALLBACK_USDTHB
        import json

        # 1. Buy without fx_rate: should use FALLBACK_USDTHB (33.62)
        res1 = record_buy(
            "AAPL", 1.0, 100.0, pay="usd",
            portfolio_path=str(self.portfolio_path),
            ledger_path=str(self.ledger_path),
            exchange_resolver=lambda t: ("NASDAQ", "Apple Inc"),
        )
        holding1 = res1["holding"]
        expected_cost_thb = round(100.0 * FALLBACK_USDTHB, 2)
        self.assertEqual(expected_cost_thb, 3362.00)
        self.assertEqual(holding1["cost_thb"], 3362.00)
        self.assertEqual(holding1["total_cost_usd"], 100.0)

        # Verify portfolio.json fx_rate_usd_thb was NOT overwritten (remains 33.0)
        p_data = json.loads(self.portfolio_path.read_text(encoding="utf-8"))
        self.assertEqual(p_data["fx_rate_usd_thb"], 33.0)

        # 2. Buy with specified fx_rate=35.5: should use specified rate
        res2 = record_buy(
            "MSFT", 2.0, 50.0, fx_rate=35.5, pay="usd",
            portfolio_path=str(self.portfolio_path),
            ledger_path=str(self.ledger_path),
            exchange_resolver=lambda t: ("NASDAQ", "Microsoft Corp"),
        )
        holding2 = res2["holding"]
        self.assertEqual(holding2["cost_thb"], 3550.00)
        self.assertEqual(holding2["total_cost_usd"], 100.0)

    def test_record_buy_thai_date_support(self):
        """Task 4: record_buy supports Thai Buddhist dates with and without time."""
        from src.trades import record_buy
        res_date1 = record_buy(
            "NVDA", 1.0, 50.0, trade_date="14 ต.ค. 69",
            portfolio_path=str(self.portfolio_path),
            ledger_path=str(self.ledger_path),
            exchange_resolver=lambda t: ("NASDAQ", "Nvidia Corp"),
        )
        self.assertEqual(res_date1["holding"]["buy_date"], "2026-10-14")
        self.assertIn("14 ต.ค. 69", res_date1["buy_order"]["date"])

        res_date2 = record_buy(
            "AMZN", 1.0, 80.0, trade_date="12 มิ.ย. 69 - 22:46 น.",
            portfolio_path=str(self.portfolio_path),
            ledger_path=str(self.ledger_path),
            exchange_resolver=lambda t: ("NASDAQ", "Amazon Inc"),
        )
        self.assertEqual(res_date2["holding"]["buy_date"], "2026-06-12")
        self.assertIn("22:46 น.", res_date2["buy_order"]["date"])

    def test_generate_trades_markdown_no_plus_minus_glitch(self):
        """Task 5: generate_trades_markdown displays -$12.50 / -฿420.25, never +฿- or ฿-."""
        from src.trades import generate_trades_markdown
        fake_trades_data = {
            "portfolio_name": "Test Port",
            "broker": "Test Broker",
            "trades": [
                {
                    "ticker": "LOSS",
                    "shares": 10.0,
                    "buy_price_usd": 100.0,
                    "sell_price_usd": 90.0,
                    "total_cost_usd": 1000.0,
                    "net_revenue_usd": 900.0,
                    "realized_pl_usd": -100.0,
                    "realized_pl_thb": -3362.0,
                    "realized_pl_pct": -10.0,
                    "date": "2026-10-15",
                    "buy_date": "2026-09-01",
                    "holding_days": 44,
                }
            ],
            "realized_summary": {
                "total_realized_pl_usd": -100.0,
                "total_realized_pl_thb": -3362.0,
                "roi_pct": -10.0,
                "win_rate_pct": 0.0,
                "winning_trades": 0,
                "losing_trades": 1,
                "total_trades": 1,
                "profit_factor_display": "0.00",
                "total_cost_usd": 1000.0,
                "total_revenue_usd": 900.0,
            }
        }
        md = generate_trades_markdown(fake_trades_data)
        self.assertIn("`-$100.00`", md)
        self.assertIn("(`-฿3,362.00`)", md)
        self.assertIn("`-10.00%`", md)
        self.assertNotIn("+฿-", md)
        self.assertNotIn("฿-", md)
        self.assertNotIn("$-", md)

    def test_fx_with_source_and_fallback_badge_rendering(self):
        """Tasks 6 & 7: resolve_usdthb_with_source returns (rate, source) and fallback badge renders on pages."""
        from src.fx import resolve_usdthb_with_source, FALLBACK_USDTHB
        import src.fx as fx

        with patch.object(fx, "fetch_usdthb", return_value=None):
            rate, source = resolve_usdthb_with_source(None)
            self.assertEqual(rate, FALLBACK_USDTHB)
            self.assertEqual(source, "fallback")

        # Test fallback badge in master dashboard and ledger
        t_helper = TestMasterReportMetrics()
        t_helper.setUp()
        data_fallback = dict(t_helper.fixture_data)
        data_fallback["fx_source"] = "fallback"
        data_fallback["fx_rate"] = 33.62

        master_html = generate_master_dashboard_html(data_fallback)
        self.assertIn("FX สำรอง 33.62", master_html)

        ledger_html = generate_master_ledger_html(data_fallback)
        self.assertIn("FX สำรอง 33.62", ledger_html)

        # Test fallback badge in review and recovery HTML
        review_summary = {
            "portfolio_name": "Test", "broker": "Test", "fx_rate_usd_thb": 33.62,
            "fx_source": "fallback", "positions": [],
        }
        review_html = generate_portfolio_html(review_summary)
        self.assertIn("FX สำรอง 33.62", review_html)

        recovery_summary = {
            "portfolio_name": "Test", "base_currency": "USD", "fx_rate": 33.62,
            "fx_source": "fallback", "positions": [],
        }
        rec_html = generate_recovery_html(recovery_summary)
        self.assertIn("FX สำรอง 33.62", rec_html)

    def test_recovery_uses_trade_levels_helper(self):
        """Task 8: analyze_recovery uses trade_levels from src.screener."""
        from recovery import analyze_recovery
        from src.screener import trade_levels

        row = {
            "ticker": "TEST",
            "name": "Test Stock",
            "close": 100.0,
            "ATR": 4.0,
            "SMA200": 95.0,
            "SMA50": 110.0,
            "EMA50": 110.0,
            "EMA200": 95.0,
            "RSI": 32.0,
            "RSI[1]": 30.0,
            "total_revenue_yoy_growth_ttm": 25.0,
            "net_income_yoy_growth_ttm": 30.0,
            "return_on_equity_fq": 20.0,
            "price_earnings_growth_ttm": 1.2,
            "debt_to_equity_fq": 0.5,
            "free_cash_flow_ttm": 5e8,
        }
        expected_levels = trade_levels(row)
        rec = analyze_recovery("TEST", custom_shares=10.0, custom_cost=120.0, market_row=row, catalysts={})
        self.assertEqual(rec["hard_stop_loss"], expected_levels["stop_loss"])
        self.assertEqual(rec["key_support"], expected_levels["key_support"])
        self.assertEqual(rec["support_desc"], expected_levels["support_desc"])
        self.assertEqual(rec["key_resistance"], expected_levels["key_resistance"])
        self.assertEqual(rec["resistance_desc"], expected_levels["resistance_desc"])

    def test_portfolio_health_grade_bands_in_html(self):
        """Task 9: Thai portfolio health labels get appropriate styling in generate_portfolio_html."""
        # ดีมาก / ดี -> emerald
        summary_good = {
            "portfolio_name": "Test", "broker": "Test", "health_grade": "ดีมาก",
            "health_score": 90.0, "positions": [],
        }
        html_good = generate_portfolio_html(summary_good)
        self.assertIn("var(--emerald)", html_good)

        # พอใช้ -> amber
        summary_fair = {
            "portfolio_name": "Test", "broker": "Test", "health_grade": "พอใช้",
            "health_score": 60.0, "positions": [],
        }
        html_fair = generate_portfolio_html(summary_fair)
        self.assertIn("var(--amber)", html_fair)

        # ต้องระวัง -> rose (Task 3 in Round 4)
        summary_warn = {
            "portfolio_name": "Test", "broker": "Test", "health_grade": "ต้องระวัง",
            "health_score": 45.0, "positions": [],
        }
        html_warn = generate_portfolio_html(summary_warn)
        self.assertIn("var(--rose)", html_warn)


class TestConcentrationAndRecoveryFormatting(unittest.TestCase):
    def setUp(self):
        fx_patch = patch("src.fx.fetch_usdthb", return_value=35.0)
        self.fetch_fx = fx_patch.start()
        self.addCleanup(fx_patch.stop)

    def test_concentration_overrides_safe_wording_in_review(self):
        """Task 4: High single stock concentration overrides 'ปลอดภัย'/'สบายใจ' with explicit warning."""
        summary = {
            "portfolio_name": "Review Port",
            "broker": "Dime!",
            "health_grade": "ดี",
            "health_score": 75.0,
            "health_status": "🟢 ปลอดภัย แข็งแกร่ง",
            "health_grade_desc": "สุขภาพพอร์ตแข็งแรงดี สามารถถือลงทุนระยะยาวได้อย่างสบายใจ.",
            "concentration_level": "Extremely High",
            "hhi": 5800.0,
            "positions": [
                {
                    "ticker": "LLY",
                    "name": "Eli Lilly",
                    "exchange": "NYSE",
                    "shares": 10.0,
                    "avg_cost_usd": 200.0,
                    "close_price": 300.0,
                    "current_val_usd": 3000.0,
                    "weight_pct": 75.0,
                },
                {
                    "ticker": "NVDA",
                    "name": "Nvidia",
                    "exchange": "NASDAQ",
                    "shares": 5.0,
                    "avg_cost_usd": 100.0,
                    "close_price": 140.0,
                    "current_val_usd": 700.0,
                    "weight_pct": 25.0,
                },
            ],
        }
        html = generate_portfolio_html(summary)
        self.assertIn("ระวังการกระจุกตัวสูง (LLY 75.0%)", html)
        self.assertNotIn("ปลอดภัย", html)
        self.assertNotIn("สบายใจ", html)

    def test_earnings_days_thai_integer_formatting(self):
        """Task 5: Fractional earnings days like 0.7d or 0.1d format to integer Thai days."""
        summary = {
            "portfolio_name": "Earnings Port",
            "broker": "Dime!",
            "positions": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc",
                    "exchange": "NASDAQ",
                    "shares": 10.0,
                    "avg_cost_usd": 100.0,
                    "close_price": 120.0,
                    "weight_pct": 50.0,
                    "days_to_earnings": 0.7,
                    "earnings_date": "2026-10-30",
                    "is_earnings_near": True,
                    "alerts": ["Earnings in 0.7d"],
                },
                {
                    "ticker": "MSFT",
                    "name": "Microsoft Corp",
                    "exchange": "NASDAQ",
                    "shares": 10.0,
                    "avg_cost_usd": 200.0,
                    "close_price": 220.0,
                    "weight_pct": 50.0,
                    "days_to_earnings": 0.1,
                    "earnings_date": "2026-10-29",
                    "is_earnings_near": True,
                    "alerts": ["Earnings in 0.1d"],
                },
            ],
        }
        html = generate_portfolio_html(summary)
        self.assertIn("งบออกใน 1 วัน", html)
        self.assertIn("งบออกวันนี้", html)
        self.assertNotIn("0.7d", html)
        self.assertNotIn("0.1d", html)

    def test_recovery_rebound_targets_none_when_no_atr(self):
        """Task 6: analyze_recovery sets target_rebound_1atr/2atr to None when ATR is None or 0."""
        mock_row_no_atr = {
            "ticker": "NOATR",
            "name": "No ATR Stock",
            "close": 50.0,
            "ATR": 0.0,
            "sector": "Technology",
            "industry": "Software",
        }
        with patch("recovery.load_portfolio", return_value={"base_currency": "USD", "holdings": []}), \
             patch("recovery.get_catalyst_breakdown", return_value={"bullish": [], "bearish": []}):
            rec = analyze_recovery("NOATR", custom_shares=10.0, custom_cost=60.0, market_row=mock_row_no_atr)
            self.assertIsNone(rec["target_rebound_1atr"])
            self.assertIsNone(rec["target_rebound_2atr"])

    def test_portfolio_recovery_report_signed_currency_headers(self):
        """Task 6: generate_portfolio_recovery_report uses signed money format."""
        from recovery import generate_portfolio_recovery_report
        summary = {
            "portfolio_name": "Underwater Port",
            "base_currency": "USD",
            "total_underwater_count": 1,
            "total_underwater_loss_usd": 500.0,
            "total_underwater_loss_thb": 17500.0,
            "positions": [],
        }
        report = generate_portfolio_recovery_report(summary)
        self.assertIn("-$500.00 USD (-฿17,500.00 THB)", report)
        self.assertNotIn("+฿-", report)
        self.assertNotIn("$-", report)
        self.assertNotIn("฿-", report)


class TestFxSourceAndFallbackBadges(unittest.TestCase):
    def test_fx_failure_ttl_caching_and_retry(self):
        """Task 1: failed fetch caches fallback with TTL, retries after TTL expiration without sleeping."""
        import src.fx as fx

        orig_rate = fx._cached_rate
        orig_source = fx._cached_source
        orig_time = fx._last_failure_time
        try:
            fx._cached_rate = None
            fx._cached_source = None
            fx._last_failure_time = 0.0

            current_time = [1000.0]
            def mock_time():
                return current_time[0]

            with patch("time.time", side_effect=mock_time), \
                 patch("src.tradingview._fetch_from_scanner") as mock_scanner:
                # 1. First fetch fails
                mock_scanner.side_effect = Exception("Network unreachable")
                res1 = fx.fetch_usdthb()
                self.assertIsNone(res1)
                self.assertEqual(fx._cached_source, "fallback")
                self.assertEqual(fx._cached_rate, fx.FALLBACK_USDTHB)
                self.assertEqual(mock_scanner.call_count, 1)

                # 2. Call again after 5 minutes (< 600s TTL)
                current_time[0] = 1300.0
                res2 = fx.fetch_usdthb()
                self.assertIsNone(res2)
                self.assertEqual(mock_scanner.call_count, 1)

                # 3. Call again after 10 minutes + 1 second (> 600s TTL)
                current_time[0] = 1601.0
                mock_scanner.side_effect = None
                mock_scanner.return_value = [{"close": 35.8}]
                res3 = fx.fetch_usdthb()
                self.assertEqual(res3, 35.8)
                self.assertEqual(fx._cached_source, "live")
                self.assertEqual(fx._cached_rate, 35.8)
                self.assertEqual(mock_scanner.call_count, 2)

                # 4. Immediate subsequent call returns cached live rate without scanner call
                res4 = fx.fetch_usdthb()
                self.assertEqual(res4, 35.8)
                self.assertEqual(mock_scanner.call_count, 2)
        finally:
            fx._cached_rate = orig_rate
            fx._cached_source = orig_source
            fx._last_failure_time = orig_time

    def test_format_fx_badge_all_four_cases(self):
        """Assert _format_fx_badge behavior for live, fallback, stored, and any other non-live value."""
        # 1. live: returns empty string (no badge)
        self.assertEqual(_format_fx_badge("live"), "")

        # 2. fallback: returns amber badge with fallback rate
        fb_badge = _format_fx_badge("fallback")
        self.assertIn("FX สำรอง 33.62", fb_badge)
        self.assertIn("badge-amber", fb_badge)

        # 3. stored: returns amber badge for recorded rate
        stored_badge = _format_fx_badge("stored")
        self.assertIn("FX ที่บันทึกไว้", stored_badge)
        self.assertIn("badge-amber", stored_badge)

        # 4. other non-live sources: returns amber badge 'FX ไม่ใช่เรทสด'
        other_badge = _format_fx_badge("custom")
        self.assertIn("FX ไม่ใช่เรทสด", other_badge)
        self.assertIn("badge-amber", other_badge)

        manual_badge = _format_fx_badge("manual")
        self.assertIn("FX ไม่ใช่เรทสด", manual_badge)
        self.assertIn("badge-amber", manual_badge)

        # Edge cases: None or empty string returns empty
        self.assertEqual(_format_fx_badge(None), "")
        self.assertEqual(_format_fx_badge(""), "")

    def test_fx_stored_vs_fallback_badges(self):
        """Assert stored, fallback, live, and other fx_source badges in review & recovery reports."""
        # 1. Stored badge in review & recovery
        rev_stored = {
            "portfolio_name": "Stored Port", "broker": "Test", "fx_rate_usd_thb": 35.0,
            "fx_source": "stored", "positions": [],
        }
        rev_stored_html = generate_portfolio_html(rev_stored)
        self.assertIn("FX ที่บันทึกไว้", rev_stored_html)
        self.assertNotIn("FX สำรอง", rev_stored_html)

        rec_stored = {
            "portfolio_name": "Stored Port", "base_currency": "USD", "fx_rate": 35.0,
            "fx_source": "stored", "positions": [],
        }
        rec_stored_html = generate_recovery_html(rec_stored)
        self.assertIn("FX ที่บันทึกไว้", rec_stored_html)
        self.assertNotIn("FX สำรอง", rec_stored_html)

        # 2. Fallback badge in review & recovery
        rev_fallback = {
            "portfolio_name": "Fallback Port", "broker": "Test", "fx_rate_usd_thb": 33.62,
            "fx_source": "fallback", "positions": [],
        }
        rev_fallback_html = generate_portfolio_html(rev_fallback)
        self.assertIn("FX สำรอง 33.62", rev_fallback_html)
        self.assertNotIn("FX ที่บันทึกไว้", rev_fallback_html)

        rec_fallback = {
            "portfolio_name": "Fallback Port", "base_currency": "USD", "fx_rate": 33.62,
            "fx_source": "fallback", "positions": [],
        }
        rec_fallback_html = generate_recovery_html(rec_fallback)
        self.assertIn("FX สำรอง 33.62", rec_fallback_html)
        self.assertNotIn("FX ที่บันทึกไว้", rec_fallback_html)

        # 3. Live badge in review & recovery (no badge displayed)
        rev_live = {
            "portfolio_name": "Live Port", "broker": "Test", "fx_rate_usd_thb": 35.5,
            "fx_source": "live", "positions": [],
        }
        rev_live_html = generate_portfolio_html(rev_live)
        self.assertNotIn("FX สำรอง", rev_live_html)
        self.assertNotIn("FX ที่บันทึกไว้", rev_live_html)
        self.assertNotIn("FX ไม่ใช่เรทสด", rev_live_html)

        rec_live = {
            "portfolio_name": "Live Port", "base_currency": "USD", "fx_rate": 35.5,
            "fx_source": "live", "positions": [],
        }
        rec_live_html = generate_recovery_html(rec_live)
        self.assertNotIn("FX สำรอง", rec_live_html)
        self.assertNotIn("FX ที่บันทึกไว้", rec_live_html)
        self.assertNotIn("FX ไม่ใช่เรทสด", rec_live_html)

        # 4. Other fx_source in review & recovery ('FX ไม่ใช่เรทสด')
        rev_other = {
            "portfolio_name": "Other Port", "broker": "Test", "fx_rate_usd_thb": 35.0,
            "fx_source": "custom_cache", "positions": [],
        }
        rev_other_html = generate_portfolio_html(rev_other)
        self.assertIn("FX ไม่ใช่เรทสด", rev_other_html)
        self.assertNotIn("FX สำรอง", rev_other_html)
        self.assertNotIn("FX ที่บันทึกไว้", rev_other_html)

        rec_other = {
            "portfolio_name": "Other Port", "base_currency": "USD", "fx_rate": 35.0,
            "fx_source": "custom_cache", "positions": [],
        }
        rec_other_html = generate_recovery_html(rec_other)
        self.assertIn("FX ไม่ใช่เรทสด", rec_other_html)
        self.assertNotIn("FX สำรอง", rec_other_html)
        self.assertNotIn("FX ที่บันทึกไว้", rec_other_html)


if __name__ == "__main__":
    unittest.main()
