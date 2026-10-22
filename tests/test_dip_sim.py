import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from scripts.generate_dip_sim_report import (
    add_sim_holding,
    analyze_simulation,
    close_triggered_holdings,
    load_simulation_data,
    remove_sim_holding,
    reset_sim_holdings,
    save_simulation_data,
)
from src.fx import FALLBACK_USDTHB


class DipSimReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp_dir.name)
        self.env_patch = mock.patch.dict(os.environ, {"FILTER_STOCK_DATA_DIR": str(self.data_dir)})
        self.env_patch.start()

        # Seed initial dummy simulation file
        self.initial_data = {
            "initial_capital_thb": 100000.0,
            "capital_per_trade_thb": 10000.0,
            "strategy": "Super Pullback in Uptrend (Simulated Dip)",
            "updated_at": "2026-10-22 10:00:00",
            "holdings": [],
            "closed_trades": [],
        }
        with open(self.data_dir / "portfolio_dip_sim.json", "w", encoding="utf-8") as f:
            json.dump(self.initial_data, f)

    def tearDown(self):
        self.env_patch.stop()
        self.tmp_dir.cleanup()

    @mock.patch("scripts.generate_dip_sim_report.fetch_screener_data")
    @mock.patch("scripts.generate_dip_sim_report.resolve_usdthb")
    def test_analyze_simulation_exact_calculations(self, mock_resolve_fx, mock_fetch):
        mock_resolve_fx.return_value = 35.0
        mock_fetch.return_value = [
            # In profit holding
            {"ticker": "AAPL", "close": 160.0, "change": 1.5, "RSI": 45.0, "SMA200": 150.0, "price_target_average": 180.0},
            # Hit TP holding
            {"ticker": "NVDA", "close": 125.0, "change": 4.0, "RSI": 60.0, "SMA200": 100.0, "price_target_average": 140.0},
            # Hit SL holding
            {"ticker": "TSLA", "close": 180.0, "change": -3.5, "RSI": 25.0, "SMA200": 210.0, "price_target_average": 220.0},
            # Price missing holding
            {"ticker": "BADTICKER", "close": None},
        ]

        sim_data = {
            "holdings": [
                {
                    "ticker": "AAPL",
                    "exchange": "NASDAQ",
                    "capital_thb": 10500.0,
                    "capital_usd": 300.0,
                    "buy_price_usd": 150.0,
                    "shares": 2.0,
                    "stop_loss_usd": 140.0,
                    "take_profit_usd": 170.0,
                },
                {
                    "ticker": "NVDA",
                    "exchange": "NASDAQ",
                    "capital_thb": 10500.0,
                    "capital_usd": 300.0,
                    "buy_price_usd": 100.0,
                    "shares": 3.0,
                    "stop_loss_usd": 90.0,
                    "take_profit_usd": 120.0,
                },
                {
                    "ticker": "TSLA",
                    "exchange": "NASDAQ",
                    "capital_thb": 10500.0,
                    "capital_usd": 300.0,
                    "buy_price_usd": 200.0,
                    "shares": 1.5,
                    "stop_loss_usd": 190.0,
                    "take_profit_usd": 220.0,
                },
                {
                    "ticker": "BADTICKER",
                    "exchange": "NYSE",
                    "capital_thb": 10500.0,
                    "capital_usd": 300.0,
                    "buy_price_usd": 50.0,
                    "shares": 6.0,
                    "stop_loss_usd": 45.0,
                    "take_profit_usd": 60.0,
                },
            ],
            "closed_trades": [
                {
                    "ticker": "MSFT",
                    "realized_pl_usd": 50.0,
                    "realized_pl_thb": 1750.0,
                    "outcome": "WIN",
                }
            ],
        }

        res = analyze_simulation(sim_data)
        self.assertEqual(res["fx_rate"], 35.0)

        # Totals for valid prices only (AAPL, NVDA, TSLA: capital = 3 * 300 = 900 USD, 3 * 10500 = 31500 THB)
        self.assertEqual(res["total_capital_usd"], 900.0)
        self.assertEqual(res["total_capital_thb"], 31500.0)

        # Current values:
        # AAPL: 2.0 * 160.0 = 320 USD
        # NVDA: 3.0 * 125.0 = 375 USD
        # TSLA: 1.5 * 180.0 = 270 USD
        # Total current USD = 320 + 375 + 270 = 965.0 USD
        self.assertEqual(res["total_current_val_usd"], 965.0)
        self.assertEqual(res["total_current_val_thb"], 965.0 * 35.0)  # 33775.0 THB
        self.assertEqual(res["total_pl_usd"], 65.0)
        self.assertEqual(res["total_pl_thb"], 2275.0)

        # Status counts
        self.assertEqual(res["hit_tp_count"], 1)
        self.assertEqual(res["hit_sl_count"], 1)
        self.assertEqual(res["in_profit_count"], 1)
        self.assertEqual(res["price_missing_tickers"], ["BADTICKER"])

        # Check AAPL position detail
        aapl_pos = next(p for p in res["positions"] if p["ticker"] == "AAPL")
        self.assertEqual(aapl_pos["current_val_usd"], 320.0)
        self.assertEqual(aapl_pos["current_val_thb"], 11200.0)
        self.assertEqual(aapl_pos["unrealized_pl_usd"], 20.0)
        self.assertEqual(aapl_pos["unrealized_pl_thb"], 700.0)
        self.assertAlmostEqual(aapl_pos["unrealized_pl_pct"], 6.6666667, places=4)
        self.assertEqual(aapl_pos["progress_pct"], 66.7)
        self.assertEqual(aapl_pos["dist_to_tp_pct"], 6.2)
        self.assertEqual(aapl_pos["dist_to_sl_pct"], 12.5)
        self.assertEqual(aapl_pos["status"], "🟢 วิ่งในแดนบวก (In Profit)")

        # Check NVDA (Hit TP)
        nvda_pos = next(p for p in res["positions"] if p["ticker"] == "NVDA")
        self.assertEqual(nvda_pos["status"], "🎯 ถึงเป้าทำกำไร (Hit TP)")

        # Check TSLA (Hit SL)
        tsla_pos = next(p for p in res["positions"] if p["ticker"] == "TSLA")
        self.assertEqual(tsla_pos["status"], "🛑 แตะจุดยอมแพ้ (Hit SL)")

        # Check BADTICKER (Missing price)
        bad_pos = next(p for p in res["positions"] if p["ticker"] == "BADTICKER")
        self.assertTrue(bad_pos["price_missing"])
        self.assertIsNone(bad_pos["current_val_usd"])
        self.assertIsNone(bad_pos["unrealized_pl_usd"])

    @mock.patch("scripts.generate_dip_sim_report.fetch_screener_data")
    @mock.patch("scripts.generate_dip_sim_report.resolve_usdthb")
    def test_close_triggered_holdings_executes_tp_and_sl(self, mock_resolve_fx, mock_fetch):
        mock_resolve_fx.return_value = FALLBACK_USDTHB  # 33.62
        mock_fetch.return_value = [
            {"ticker": "NVDA", "close": 125.0, "change": 2.0},  # hit TP (tp=120)
            {"ticker": "AAPL", "close": 160.0, "change": 0.5},  # still holding (sl=140, tp=170)
        ]

        sim_data = {
            "holdings": [
                {
                    "ticker": "NVDA",
                    "exchange": "NASDAQ",
                    "capital_thb": 10000.0,
                    "capital_usd": 10000.0 / FALLBACK_USDTHB,
                    "buy_price_usd": 100.0,
                    "shares": (10000.0 / FALLBACK_USDTHB) / 100.0,
                    "stop_loss_usd": 90.0,
                    "take_profit_usd": 120.0,
                },
                {
                    "ticker": "AAPL",
                    "exchange": "NASDAQ",
                    "capital_thb": 10000.0,
                    "capital_usd": 10000.0 / FALLBACK_USDTHB,
                    "buy_price_usd": 150.0,
                    "shares": (10000.0 / FALLBACK_USDTHB) / 150.0,
                    "stop_loss_usd": 140.0,
                    "take_profit_usd": 170.0,
                },
            ],
            "closed_trades": [],
        }
        save_simulation_data(sim_data)

        fixed_now = datetime(2026, 10, 22, 12, 0, 0)
        closed = close_triggered_holdings(now=fixed_now)

        self.assertEqual(len(closed), 1)
        trade = closed[0]
        self.assertEqual(trade["ticker"], "NVDA")
        self.assertEqual(trade["exit_price_usd"], 125.0)
        self.assertIn("Take-Profit", trade["exit_reason"])
        self.assertEqual(trade["exit_date"], "2026-10-22")
        self.assertAlmostEqual(trade["realized_pl_pct"], 25.0, places=1)

        # Check saved state in file
        updated = load_simulation_data()
        self.assertEqual(len(updated["holdings"]), 1)
        self.assertEqual(updated["holdings"][0]["ticker"], "AAPL")
        self.assertEqual(len(updated["closed_trades"]), 1)
        self.assertEqual(updated["closed_trades"][0]["ticker"], "NVDA")

    @mock.patch("scripts.generate_dip_sim_report.fetch_screener_data")
    @mock.patch("scripts.generate_dip_sim_report.resolve_usdthb")
    def test_add_remove_and_reset_holdings(self, mock_resolve_fx, mock_fetch):
        mock_resolve_fx.return_value = 35.0
        mock_fetch.return_value = [
            {
                "ticker": "GOOGL",
                "exchange": "NASDAQ",
                "close": 170.0,
                "ATR": 3.0,
                "SMA50": 185.0,
                "sector": "Technology Services",
                "industry": "Internet Software/Services",
                "name": "Alphabet Inc.",
            }
        ]

        # 1. Add sim holding
        res_add = add_sim_holding("GOOGL", capital_thb=10000.0)
        self.assertEqual(res_add["ticker"], "GOOGL")
        self.assertEqual(res_add["buy_price_usd"], 170.0)
        self.assertEqual(res_add["take_profit_usd"], 185.0)

        data = load_simulation_data()
        self.assertEqual(len(data["holdings"]), 1)
        self.assertEqual(data["holdings"][0]["ticker"], "GOOGL")

        # 2. Remove sim holding
        removed = remove_sim_holding("GOOGL")
        self.assertTrue(removed)

        data_after_remove = load_simulation_data()
        self.assertEqual(len(data_after_remove["holdings"]), 0)

        # 3. Add again and Reset
        add_sim_holding("GOOGL", capital_thb=10000.0)
        reset_sim_holdings()
        data_reset = load_simulation_data()
        self.assertEqual(data_reset["holdings"], [])


if __name__ == "__main__":
    unittest.main()
