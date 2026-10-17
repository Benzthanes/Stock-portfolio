import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import fmt
from src.html_report import generate_portfolio_html, generate_recovery_html
from src.nav import nav_bar_html
from src.outlook import CURATED_AS_OF, get_forward_outlook
from scripts.generate_master_report import (
    dividend_thb, generate_master_dashboard_html, generate_master_ledger_html,
)
from scripts import generate_dip_sim_report as dip

EVIL = '<b>Evil "Co"</b>'
EVIL_ESCAPED = "&lt;b&gt;Evil &quot;Co&quot;&lt;/b&gt;"


def _position(ticker="EVL", **over):
    p = {
        "ticker": ticker, "name": EVIL, "exchange": "NASDAQ", "sector": EVIL, "industry": "Software",
        "business_summary": EVIL, "weight_pct": 50.0, "shares": 10.0,
        "avg_cost_usd": 100.0, "avg_cost_thb": 3300.0, "close_price": 64.36,
        "current_val_usd": 643.62, "current_val_thb": 21639.0,
        "unrealized_pl_usd": -356.38, "unrealized_pl_thb": -11982.0, "unrealized_pl_pct": -35.64,
        "change_pct": -4.2, "rsi": 28.0, "dist_sma200_pct": -12.5, "in_value_zone": False,
        "key_support": 60.0, "key_resistance": 80.0, "stop_loss": 55.0, "take_profit": 90.0,
        "price_target_average": 90.0, "price_target_low": 70.0, "price_target_high": 120.0,
        "target_upside_pct": 39.8, "rec_buy": 10, "rec_hold": 3, "rec_sell": 1,
        "rev_growth_yoy": None, "net_inc_growth_yoy": -4.2, "pe": None, "peg": None,
        "tv_url": "https://www.tradingview.com/chart/?symbol=NASDAQ:EVL", "alerts": [],
        "rating": {"stars_str": "⭐⭐", "action": "hold"}, "financial_health": {},
        "forward_outlook": get_forward_outlook(ticker, {"sector": EVIL, "industry": EVIL}, {}),
    }
    p.update(over)
    return p


def _missing_position():
    return _position(
        "MISS", price_missing=True, close_price=None, current_val_usd=None, current_val_thb=None,
        unrealized_pl_usd=None, unrealized_pl_thb=None, unrealized_pl_pct=None, weight_pct=0.0,
        key_support=None, key_resistance=None, stop_loss=None, take_profit=None,
        target_upside_pct=None, dist_sma200_pct=None, rsi=None,
    )


def _review_summary(base_currency="USD"):
    loser = _position()
    return {
        "portfolio_name": EVIL, "broker": "Dime", "fx_rate_usd_thb": 33.0, "base_currency": base_currency,
        "total_market_val_usd": 643.62, "total_market_val_thb": 21239.46,
        "total_cost_usd": 1000.0, "total_cost_thb": 33000.0,
        "total_pl_usd": -356.38, "total_pl_thb": -11760.54, "total_pl_pct": -35.64,
        "total_daily_change_usd": -28.2, "total_daily_change_thb": -930.6, "total_daily_change_pct": -4.2,
        "hhi": 5000.0, "concentration_level": "High", "health_grade": "C", "health_score": 40.0,
        "best_pos": loser, "worst_pos": loser, "top_buy_candidates": [loser, _missing_position()],
        "forbidden_buys": [], "dip_opportunities": [], "sector_sorted": [(EVIL, 100.0)],
        "positions": [loser, _missing_position()],
        "price_missing_tickers": ["MISS"], "unpriced_cost_usd": 1000.0, "unpriced_cost_thb": 33000.0,
    }


def _recovery_summary(base_currency="USD"):
    p = _position()
    p.update({
        "avg_cost": 100.0, "close": 64.36, "unrealized_pl": -356.38, "pct_to_breakeven": 55.4,
        "fundamentals": {"rev_growth_yoy": None, "net_inc_growth_yoy": -4.2}, "hard_stop_loss": 55.0,
        "action_verdict": "hold", "catalysts": {}, "current_val": 643.62, "gain_pct_needed_on_rotation": 55.4,
        "dca_half": {"cash_needed": 321.8, "shares_to_buy": 5.0, "new_avg_cost": 88.12, "new_breakeven_gain_pct": 36.9},
        "dca_equal": {"cash_needed": 643.6, "shares_to_buy": 10.0, "new_avg_cost": 82.18, "new_breakeven_gain_pct": 27.7},
        "support_desc": "SMA200", "resistance_desc": "SMA50", "loss_thb": 11760.54,
    })
    return {
        "portfolio_name": EVIL, "fx_rate": 33.0, "total_underwater_count": 1, "base_currency": base_currency,
        "total_underwater_loss_usd": 356.38, "total_underwater_loss_thb": 11760.54, "positions": [p],
    }


def _master_data():
    return {
        "portfolio_name": EVIL, "broker": EVIL, "account_no": "1", "fx_rate": 33.0,
        "net_injected_capital_thb": 40000.0, "gross_deposits_thb": 41000.0, "transfer_out_thb": 1000.0,
        "dime_save_cash_thb": 500.0, "dime_usd_cash": 1.0, "dime_usd_cash_thb": 33.0, "total_cash_thb": 533.0,
        "stock_market_val_usd": 643.62, "stock_market_val_thb": 21239.46, "stock_cost_usd": 1000.0,
        "stock_cost_thb": 33000.0, "stock_unrealized_pl_usd": -356.38, "stock_unrealized_pl_thb": -11760.54,
        "stock_unrealized_pl_pct": -35.64, "total_net_worth_thb": 21772.46, "total_net_worth_usd": 659.77,
        "all_time_profit_thb": -18227.54, "all_time_roi_pct": -45.57,
        "trades_summary": {"total_realized_pl_usd": -39.0, "total_realized_pl_thb": -1287.0, "win_rate_pct": 0.0,
                           "total_trades": 1, "winning_trades": 0, "profit_factor": None, "profit_factor_display": "∞"},
        "closed_trades": [{"ticker": "EVL", "name": EVIL, "shares": 1.0, "buy_price_usd": 100.0, "sell_price_usd": 61.0,
                           "total_cost_usd": 100.0, "net_revenue_usd": 61.0, "realized_pl_usd": -39.0,
                           "realized_pl_thb": -1287.0, "realized_pl_pct": -39.0, "buy_tranches": []}],
        "dividends_list": [{"date": "1 ต.ค. 69", "ticker": "VOO", "amount_usd": 1.0, "fx_rate": 35.0},
                           {"date": "2 ต.ค. 69", "ticker": "VOO", "amount_usd": 1.0}],
        "total_dividends_usd": 2.0, "total_dividends_thb": 68.0, "total_realized_and_div_thb": -1219.0,
        "positions": [_position(), _missing_position()],
        "buy_orders": [{"fn": 'IMG_1"<x>.webp', "ticker": "EVL", "shares": 1.0, "price_usd": 100.0, "amt_usd": 100.0,
                        "amt_thb": 3300.0, "fx_rate": 33.0, "date": "1 ต.ค. 69", "order_type": "Market", "account": "Dime! USD"}],
        "cash_movements": [{"date_str": "07/10/2026", "type": "ชำระค่าซื้อหุ้น", "amount_thb": -4999.73, "balance_thb": 20001.33}],
    }


def _dip_data():
    priced = {"ticker": "EVL", "name": EVIL, "exchange": "NASDAQ", "business": EVIL, "entry_date": "-",
              "capital_thb": 10000.0, "capital_usd": 300.0, "buy_price_usd": 100.0, "shares": 3.0,
              "close_price": 64.36, "price_missing": False, "day_chg_pct": -4.2, "rsi": 30.0, "sma200": 90.0,
              "target_avg": 110.0, "current_val_usd": 193.08, "current_val_thb": 6371.64,
              "unrealized_pl_usd": -106.92, "unrealized_pl_thb": -3628.36, "unrealized_pl_pct": -35.64,
              "stop_loss_usd": 60.0, "take_profit_usd": 110.0, "progress_pct": 8.7, "dist_to_tp_pct": 70.9,
              "dist_to_sl_pct": 6.8, "status": "x", "status_cls": "badge-warning", "strategy_tier": "-",
              "setup_reason": EVIL, "notes": "-", "forward_outlook": {}, "tv_url": "-"}
    missing = dict(priced, ticker="MISS", close_price=None, price_missing=True, current_val_usd=None,
                   current_val_thb=None, unrealized_pl_usd=None, unrealized_pl_thb=None, unrealized_pl_pct=None,
                   progress_pct=None, dist_to_tp_pct=None, dist_to_sl_pct=None)
    return {"portfolio_name": EVIL, "description": EVIL, "fx_rate": 33.0, "total_capital_thb": 10000.0,
            "total_capital_usd": 300.0, "total_current_val_thb": 6371.64, "total_current_val_usd": 193.08,
            "total_pl_usd": -106.92, "total_pl_thb": -3628.36, "total_pl_pct": -35.64, "holdings_count": 2,
            "price_missing_tickers": ["MISS"], "hit_tp_count": 0, "hit_sl_count": 0, "in_profit_count": 0,
            "positions": [priced, missing],
            "closed_trades": [{"ticker": "OLD", "name": EVIL, "buy_price_usd": 10.0, "exit_price_usd": 9.0,
                               "capital_thb": 10000.0, "net_revenue_thb": 9000.0, "realized_pl_usd": -30.0,
                               "realized_pl_thb": -1000.0, "realized_pl_pct": -10.0}]}


class _Offline(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("src.fx.fetch_usdthb", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assertCleanHtml(self, html):
        self.assertNotIn("$-", html)
        self.assertNotIn("฿-", html)
        self.assertNotIn("+-", html)
        self.assertNotIn(EVIL, html)
        self.assertIn(EVIL_ESCAPED, html)


class FmtTest(unittest.TestCase):
    def test_money(self):
        self.assertEqual(fmt.money(-356.38), "-$356.38")
        self.assertEqual(fmt.money(1234, "THB"), "฿1,234.00")
        self.assertEqual(fmt.money(1.0), "$1.00")
        self.assertEqual(fmt.money(-39, "THB"), "-฿39.00")
        self.assertEqual(fmt.money(5, signed=True), "+$5.00")
        self.assertEqual(fmt.money(-0.001, signed=True), "$0.00")
        self.assertEqual(fmt.money(None), "-")
        self.assertEqual(fmt.money(None, na="n/a"), "n/a")

    def test_pct_and_signed(self):
        self.assertEqual(fmt.pct(4.2), "+4.2%")
        self.assertEqual(fmt.pct(-4.2), "-4.2%")
        self.assertEqual(fmt.pct(4.2, signed=False), "4.2%")
        self.assertEqual(fmt.pct(0.0), "0.0%")
        self.assertEqual(fmt.pct(None), "-")
        self.assertEqual(fmt.signed(3.5), "+3.50")
        self.assertEqual(fmt.signed(-1234.5), "-1,234.50")
        self.assertEqual(fmt.signed(None), "-")


class ReviewPageTest(_Offline):
    def test_usd_page(self):
        html = generate_portfolio_html(_review_summary())
        self.assertCleanHtml(html)
        self.assertIn("-$356.38", html)
        self.assertIn("(-35.6%)", html)
        self.assertIn("n/a", html)
        self.assertIn("ไม่ได้ราคา MISS", html)

    def test_set_page_uses_baht_for_targets(self):
        html = generate_portfolio_html(_review_summary("THB"))
        self.assertCleanHtml(html)
        self.assertIn("<strong>฿90.00</strong>", html)
        self.assertIn("฿70 - ฿120", html)
        self.assertNotIn("$90.00", html)
        self.assertRegex(html, r'href="portfolio_review.html" class="rnav-link active"')
        self.assertNotIn("portfolio_set_review.html", html)


class RecoveryPageTest(_Offline):
    def test_usd_and_set(self):
        self.assertCleanHtml(generate_recovery_html(_recovery_summary()))
        html = generate_recovery_html(_recovery_summary("THB"))
        self.assertCleanHtml(html)
        self.assertIn("฿321.80", html)
        self.assertIn("-฿11,760.54", html)
        self.assertRegex(html, r'href="portfolio_recovery.html" class="rnav-link active"')
        self.assertNotIn("portfolio_set_recovery.html", html)


class MasterPageTest(_Offline):
    def test_dashboard(self):
        html = generate_master_dashboard_html(_master_data())
        self.assertCleanHtml(html)
        self.assertIn("-$356.38", html)
        self.assertIn("function fmtMoney", html)
        self.assertIn('data-server-val-usd="643.62"', html)
        self.assertEqual(html.count("data-server-val-usd"), 1)
        self.assertIn("n/a", html)

    def test_ledger(self):
        html = generate_master_ledger_html(_master_data())
        self.assertCleanHtml(html)
        self.assertIn("-฿4,999.73", html)
        self.assertIn("-$39.00", html)
        self.assertIn("฿35.00", html)
        self.assertNotIn('IMG_1"<x>', html)
        self.assertIn("openSlipModal(&quot;", html)

    def test_dividend_fx(self):
        self.assertEqual(dividend_thb({"amount_usd": 2.0, "fx_rate": 35.0}, 33.0), 70.0)
        self.assertEqual(dividend_thb({"amount_usd": 2.0}, 33.0), 66.0)


class DipPageTest(_Offline):
    def test_render(self):
        html = dip.generate_html_report(_dip_data())
        self.assertCleanHtml(html)
        self.assertIn("-฿3,628.36", html)
        self.assertIn("n/a", html)
        self.assertIn("openChartModal(&quot;EVL&quot;", html)

    def test_missing_price_excluded_from_totals(self):
        live = [{"ticker": "EVL", "close": 50.0, "change": 1.0}]
        sim = {"fx_rate_usd_thb": 33.0, "holdings": [
            {"ticker": "EVL", "capital_thb": 3300.0, "capital_usd": 100.0, "buy_price_usd": 100.0, "shares": 1.0},
            {"ticker": "MISS", "capital_thb": 3300.0, "capital_usd": 100.0, "buy_price_usd": 100.0, "shares": 1.0},
        ]}
        with mock.patch.object(dip, "fetch_screener_data", return_value=live):
            out = dip.analyze_simulation(sim)
        self.assertEqual(out["price_missing_tickers"], ["MISS"])
        self.assertEqual(out["total_capital_usd"], 100.0)
        self.assertEqual(out["total_pl_usd"], -50.0)
        miss = [p for p in out["positions"] if p["ticker"] == "MISS"][0]
        self.assertIsNone(miss["unrealized_pl_usd"])
        self.assertIn("n/a", dip.generate_html_report(out))


class OutlookTest(unittest.TestCase):
    def test_broker_count_omitted_without_live_counts(self):
        for t in ("NVDA", "MSFT", "AMZN", "APP", "VRT", "BAC", "NOK", "ZZZ"):
            with self.subTest(ticker=t):
                v = get_forward_outlook(t, {"price_target_average": 120.0}, {}, close=100.0)["wall_street_verdict"]
                self.assertNotRegex(v, r"\d+\+? แห่ง|มากกว่า \d+%|0 Sell")

    def test_broker_count_from_live_numbers(self):
        data = {"price_target_average": 120.0, "recommendation_buy": 7, "recommendation_hold": 2, "recommendation_sell": 1}
        v = get_forward_outlook("NVDA", data, {}, close=100.0)["wall_street_verdict"]
        self.assertIn("โบรกเกอร์ 10 แห่ง (Buy 7 / Hold 2 / Sell 1)", v)
        self.assertIn("+20.0%", v)

    def test_curated_stamp_and_set_currency(self):
        o = get_forward_outlook("NVDA", {"price_target_average": 120.0, "exchange": "SET"}, {}, close=100.0)
        self.assertIn(f"(ข้อมูลอ้างอิงเขียนเอง อัปเดตล่าสุด {CURATED_AS_OF})", o["thesis_title"])
        self.assertEqual(CURATED_AS_OF, "2026-10-17")
        self.assertIn("฿120.00", o["wall_street_verdict"])
        self.assertNotIn("$", o["wall_street_verdict"])

    def test_missing_fundamentals_render_dash(self):
        o = get_forward_outlook("ZZZ", {"sector": EVIL}, {})
        txt = " ".join(o["future_growth_drivers"])
        self.assertNotIn("+0.0%", txt)
        self.assertNotIn("0.00", txt)
        self.assertIn("รายได้ระดับ - YoY", txt)
        self.assertIn(EVIL_ESCAPED, o["thesis_title"])


class NavSetPagesTest(unittest.TestCase):
    def test_set_pages_not_in_tabs(self):
        html = nav_bar_html("set_review")
        self.assertNotIn('portfolio_set_review.html', html)
        self.assertNotIn('portfolio_set_recovery.html', html)
        self.assertNotIn('หุ้นไทย', html)
        self.assertIn('href="portfolio_review.html" class="rnav-link active"', html)


if __name__ == "__main__":
    unittest.main()
