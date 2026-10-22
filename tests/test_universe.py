import unittest

from src.universe import (
    NASDAQ100_TICKERS,
    SP100_TICKERS,
    get_tv_symbols,
    get_universe,
    resolve_custom_tickers,
)


class UniverseTest(unittest.TestCase):
    def test_sp100_tickers_count_and_constituents(self):
        self.assertEqual(len(SP100_TICKERS), 102)
        self.assertEqual(SP100_TICKERS["AAPL"], "NASDAQ")
        self.assertEqual(SP100_TICKERS["JPM"], "NYSE")
        self.assertEqual(SP100_TICKERS["BRK.B"], "NYSE")

    def test_nasdaq100_tickers_count_and_constituents(self):
        self.assertEqual(len(NASDAQ100_TICKERS), 98)
        self.assertEqual(NASDAQ100_TICKERS["NVDA"], "NASDAQ")
        self.assertEqual(NASDAQ100_TICKERS["AZN"], "NYSE")

    def test_get_universe_categories(self):
        sp100 = get_universe("sp100")
        self.assertEqual(len(sp100), 102)

        ndx100 = get_universe("nasdaq100")
        self.assertEqual(len(ndx100), 98)

        all_univ = get_universe("all")
        self.assertEqual(len(all_univ), 171)

        with self.assertRaises(ValueError) as ctx:
            get_universe("invalid_cat")
        self.assertIn("Unknown universe category", str(ctx.exception))

    def test_get_tv_symbols_formatting_and_sorting(self):
        symbols = get_tv_symbols("sp100")
        self.assertEqual(len(symbols), 102)
        # Check that symbols are formatted properly with exchange prefix
        self.assertIn("NASDAQ:AAPL", symbols)
        self.assertIn("NYSE:JPM", symbols)
        self.assertEqual(symbols[0], "NASDAQ:AAPL")

    def test_resolve_custom_tickers(self):
        # 1. Known tickers
        res = resolve_custom_tickers(["AAPL", "JPM"])
        self.assertEqual(res, ["NASDAQ:AAPL", "NYSE:JPM"])

        # 2. Already formatted tickers with colons
        res_colon = resolve_custom_tickers(["SET:SCB", "AMEX:SPY"])
        self.assertEqual(res_colon, ["SET:SCB", "AMEX:SPY"])

        # 3. Unknown ticker generates candidates across NASDAQ, NYSE, AMEX
        res_unknown = resolve_custom_tickers(["CUSTOMTICKER"])
        self.assertEqual(len(res_unknown), 3)
        self.assertEqual(res_unknown, ["NASDAQ:CUSTOMTICKER", "NYSE:CUSTOMTICKER", "AMEX:CUSTOMTICKER"])

        # 4. Empty strings and duplicates
        res_dups = resolve_custom_tickers(["AAPL", "", "  ", "aapl", "NASDAQ:AAPL"])
        self.assertEqual(res_dups, ["NASDAQ:AAPL"])


if __name__ == "__main__":
    unittest.main()
