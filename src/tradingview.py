"""
TradingView Screener API Client
Fetches batch technical and fundamental data directly from TradingView Scanner API.
"""

from src.http import http_post_json
from typing import Any, Dict, List

SCANNER_URL = "https://scanner.tradingview.com/america/scan"

COLUMNS = [
    "name",
    "description",
    "close",
    "open",
    "high",
    "low",
    "change",
    "volume",
    "average_volume_30d_calc",
    "relative_volume_10d_calc",
    "RSI",
    "RSI[1]",
    "RSI|1W",
    "Stoch.RSI.K",
    "Stoch.RSI.D",
    "Stoch.RSI.K[1]",
    "Stoch.RSI.D[1]",
    "SMA20",
    "SMA50",
    "SMA100",
    "SMA200",
    "EMA50",
    "EMA200",
    "BB.lower",
    "BB.upper",
    "MACD.macd",
    "MACD.signal",
    "MACD.hist",
    "MACD.hist[1]",
    "MoneyFlow",
    "ATR",
    "ADX",
    "ADX+DI",
    "ADX-DI",
    "Recommend.All",
    "recommendation_mark",
    "earnings_release_date",
    "earnings_release_next_date",
    "earnings_per_share_basic_ttm",
    "price_earnings_ttm",
    "price_earnings_growth_ttm",
    "price_sales_current",
    "total_revenue_yoy_growth_ttm",
    "net_income_yoy_growth_ttm",
    "return_on_equity_fq",
    "debt_to_equity_fq",
    "free_cash_flow_ttm",
    "market_cap_basic",
    "sector",
    "industry",
    "price_target_average",
    "price_target_high",
    "price_target_low",
    "price_target_median",
    "recommendation_buy",
    "recommendation_hold",
    "recommendation_sell"
]


def _fetch_from_scanner(market: str, symbols: List[str], timeout: int = 15) -> List[Dict[str, Any]]:
    if not symbols:
        return []
    url = f"https://scanner.tradingview.com/{market}/scan"
    payload = {
        "symbols": {
            "tickers": symbols,
            "query": {"types": []}
        },
        "columns": COLUMNS
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    }
    raw_data = http_post_json(url, payload, headers=headers, timeout=timeout)

    results: List[Dict[str, Any]] = []
    for item in raw_data.get("data", []):
        symbol_full = item.get("s", "")
        exchange, ticker = symbol_full.split(":", 1) if ":" in symbol_full else ("", symbol_full)
        d_vals = item.get("d", [])
        
        row_dict = {
            "symbol_full": symbol_full,
            "exchange": exchange,
            "ticker": ticker
        }
        for col_name, val in zip(COLUMNS, d_vals):
            row_dict[col_name] = val
            
        results.append(row_dict)
    return results


def fetch_screener_data(symbols: List[str], timeout: int = 15) -> List[Dict[str, Any]]:
    """
    Fetch technical indicator data for a list of TradingView symbols (e.g. ['NASDAQ:AAPL', 'SET:SCB']).
    Automatically routes to appropriate regional scanner (America or Thailand).
    Returns list of dicts with parsed column values.
    """
    if not symbols:
        return []

    set_symbols = [s for s in symbols if s.startswith("SET:")]
    other_symbols = [s for s in symbols if not s.startswith("SET:")]

    results: List[Dict[str, Any]] = []
    if set_symbols:
        results.extend(_fetch_from_scanner("thailand", set_symbols, timeout=timeout))
    if other_symbols:
        results.extend(_fetch_from_scanner("america", other_symbols, timeout=timeout))

    return results
