import unittest
from unittest import mock

from src.tradingview import COLUMNS, _fetch_from_scanner, fetch_screener_data


class TradingViewTest(unittest.TestCase):
    def test_columns_structure(self):
        self.assertEqual(len(COLUMNS), 57)
        self.assertEqual(COLUMNS[0], "name")
        self.assertEqual(COLUMNS.index("close"), 2)
        self.assertEqual(COLUMNS.index("RSI"), 10)
        self.assertEqual(COLUMNS.index("SMA200"), 20)
        self.assertEqual(COLUMNS.index("EMA200"), 22)
        self.assertEqual(COLUMNS.index("return_on_equity_fq"), 44)

    def test_empty_symbols_returns_empty_list(self):
        self.assertEqual(_fetch_from_scanner("america", []), [])
        self.assertEqual(fetch_screener_data([]), [])

    @mock.patch("src.tradingview.http_post_json")
    def test_fetch_from_scanner_parses_columns_and_symbols(self, mock_post):
        dummy_row_d = [None] * len(COLUMNS)
        dummy_row_d[COLUMNS.index("name")] = "Apple Inc."
        dummy_row_d[COLUMNS.index("description")] = "Consumer Electronics"
        dummy_row_d[COLUMNS.index("close")] = 182.50
        dummy_row_d[COLUMNS.index("RSI")] = 34.2
        dummy_row_d[COLUMNS.index("SMA200")] = 175.10
        dummy_row_d[COLUMNS.index("EMA200")] = 172.40
        dummy_row_d[COLUMNS.index("total_revenue_yoy_growth_ttm")] = 15.6
        dummy_row_d[COLUMNS.index("return_on_equity_fq")] = 28.4
        dummy_row_d[COLUMNS.index("price_target_average")] = 210.0

        mock_post.return_value = {
            "totalCount": 1,
            "data": [
                {
                    "s": "NASDAQ:AAPL",
                    "d": dummy_row_d,
                }
            ]
        }

        res = _fetch_from_scanner("america", ["NASDAQ:AAPL"], timeout=10)

        self.assertEqual(len(res), 1)
        row = res[0]
        self.assertEqual(row["symbol_full"], "NASDAQ:AAPL")
        self.assertEqual(row["exchange"], "NASDAQ")
        self.assertEqual(row["ticker"], "AAPL")
        self.assertEqual(row["name"], "Apple Inc.")
        self.assertEqual(row["close"], 182.50)
        self.assertEqual(row["RSI"], 34.2)
        self.assertEqual(row["SMA200"], 175.10)
        self.assertEqual(row["EMA200"], 172.40)
        self.assertEqual(row["total_revenue_yoy_growth_ttm"], 15.6)
        self.assertEqual(row["return_on_equity_fq"], 28.4)
        self.assertEqual(row["price_target_average"], 210.0)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://scanner.tradingview.com/america/scan")
        self.assertEqual(args[1]["symbols"]["tickers"], ["NASDAQ:AAPL"])
        self.assertEqual(args[1]["columns"], COLUMNS)
        self.assertEqual(kwargs.get("timeout"), 10)

    @mock.patch("src.tradingview._fetch_from_scanner")
    def test_fetch_screener_data_routes_set_and_america_correctly(self, mock_fetch):
        def fake_fetch(market, symbols, timeout=15):
            if market == "thailand":
                return [{"ticker": "SCB", "symbol_full": "SET:SCB", "close": 105.5, "change": 1.2}]
            elif market == "america":
                return [
                    {"ticker": "AAPL", "symbol_full": "NASDAQ:AAPL", "close": 182.5, "change": -0.8},
                    {"ticker": "JPM", "symbol_full": "NYSE:JPM", "close": 195.0, "change": 0.5},
                ]
            return []

        mock_fetch.side_effect = fake_fetch

        results = fetch_screener_data(["NASDAQ:AAPL", "SET:SCB", "NYSE:JPM"])
        self.assertEqual(len(results), 3)

        scb = next(r for r in results if r["ticker"] == "SCB")
        self.assertEqual(scb["close"], 105.5)
        self.assertEqual(scb["change"], 1.2)

        aapl = next(r for r in results if r["ticker"] == "AAPL")
        self.assertEqual(aapl["close"], 182.5)
        self.assertEqual(aapl["change"], -0.8)

        jpm = next(r for r in results if r["ticker"] == "JPM")
        self.assertEqual(jpm["close"], 195.0)
        self.assertEqual(jpm["change"], 0.5)

        self.assertEqual(mock_fetch.call_count, 2)
        called_markets = [call.args[0] for call in mock_fetch.call_args_list]
        self.assertIn("thailand", called_markets)
        self.assertIn("america", called_markets)


if __name__ == "__main__":
    unittest.main()
