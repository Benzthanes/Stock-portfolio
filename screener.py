#!/usr/bin/env python3
"""
US Stock Dip Screener CLI (S&P 100 + Nasdaq 100)
Scans mega/large-cap US stocks for high-probability dip buying opportunities using TradingView Screener API.
"""

import argparse
import json
import sys
from pathlib import Path

from src.universe import get_tv_symbols, resolve_custom_tickers
from src.tradingview import fetch_screener_data
from src.screener import filter_stocks, generate_markdown_report



def main():
    parser = argparse.ArgumentParser(
        description="US Stock Dip Screener (Strategy: Super Pullback in Uptrend)"
    )
    parser.add_argument(
        "--rsi-max",
        type=float,
        default=35.0,
        help="Maximum Daily RSI threshold (default: 35.0)"
    )
    parser.add_argument(
        "--universe",
        choices=["all", "sp100", "nasdaq100"],
        default="all",
        help="Stock universe to scan: 'all' (S&P 100 + Nasdaq 100), 'sp100', or 'nasdaq100' (default: all)"
    )
    parser.add_argument(
        "-t", "--tickers",
        nargs="+",
        help="Custom list of stock tickers to scan (e.g. -t AAPL NVDA MSFT or -t AAPL,NVDA)"
    )
    parser.add_argument(
        "--sector",
        type=str,
        default=None,
        help="Filter stocks by sector name (e.g. Technology, Financials, Health)"
    )
    parser.add_argument(
        "--no-sma200",
        action="store_true",
        help="Disable SMA 200 trend filter (show all oversold stocks regardless of 200-day trend)"
    )
    parser.add_argument(
        "--require-ema200",
        action="store_true",
        help="Enforce Price > EMA 200 filter"
    )
    parser.add_argument(
        "--no-weekly-filter",
        action="store_true",
        help="Disable Weekly RSI filter (do not require Weekly RSI >= 45)"
    )
    parser.add_argument(
        "--weekly-rsi-min",
        type=float,
        default=45.0,
        help="Minimum Weekly RSI threshold (default: 45.0)"
    )
    parser.add_argument(
        "--min-rr",
        type=float,
        default=None,
        help="Minimum Risk-to-Reward (R:R) ratio threshold (e.g. 2.0)"
    )
    parser.add_argument(
        "--allow-falling-knife",
        action="store_true",
        help="Do not exclude active plunge day stocks (-3%% or red candle <= -1.5%%)"
    )
    parser.add_argument(
        "--stoch-cross",
        action="store_true",
        help="Require Stochastic RSI bullish crossover in oversold zone"
    )
    parser.add_argument(
        "--actionable", "--require-reversal",
        action="store_true",
        help="Strictly filter for actionable dip setups with confirmed RSI hook up (exclude active plunge days and earnings guard)"
    )
    parser.add_argument(
        "--auto-fallback",
        action="store_true",
        help="Automatically broaden scan (RSI <= 40) if strict criteria yields 0 results"
    )
    parser.add_argument(
        "--require-growth",
        action="store_true",
        help="Enforce Quality Growth filter (require YoY Revenue Growth > 0%%)"
    )
    parser.add_argument(
        "--allow-declining-growth",
        action="store_true",
        help="Allow stocks with zero or negative YoY revenue growth (disabled by default for quality dip buys)"
    )
    parser.add_argument(
        "--max-peg",
        type=float,
        default=None,
        help="Filter by maximum PEG ratio threshold (e.g. 2.0)"
    )
    parser.add_argument(
        "--strong-buy",
        action="store_true",
        help="Require Wall Street Strong Buy / Buy analyst consensus"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output raw JSON data instead of formatted Markdown"
    )
    parser.add_argument(
        "--save-report",
        type=str,
        nargs="?",
        const="reports/latest_screener_report.md",
        help="Save markdown report to specified file (default: reports/latest_screener_report.md)"
    )

    args = parser.parse_args()

    # Determine symbols
    if args.tickers:
        raw_tickers = []
        for item in args.tickers:
            raw_tickers.extend([t.strip() for t in item.split(",") if t.strip()])
        symbols = resolve_custom_tickers(raw_tickers)
        univ_label = f"Custom Tickers ({', '.join(raw_tickers)})"
    else:
        symbols = get_tv_symbols(args.universe)
        universe_labels = {
            "all": "S&P 100 + Nasdaq 100",
            "sp100": "S&P 100 (OEX)",
            "nasdaq100": "Nasdaq 100 (NDX)"
        }
        univ_label = universe_labels.get(args.universe, args.universe)

    print(f"Scanning {len(symbols)} symbols from {univ_label} via TradingView Screener API...", file=sys.stderr)

    try:
        raw_data = fetch_screener_data(symbols)
    except Exception as e:
        print(f"Error fetching data from TradingView: {e}", file=sys.stderr)
        sys.exit(1)

    # When analyzing custom tickers explicitly, show their full analysis without strict dip filtering
    require_sma200 = False if args.tickers else (not args.no_sma200)
    weekly_rsi_min = None if (args.tickers or args.no_weekly_filter) else args.weekly_rsi_min
    exclude_falling_knife = False if args.tickers else (not args.allow_falling_knife)
    effective_rsi = 100.0 if (args.tickers and args.rsi_max == 35.0) else args.rsi_max
    enforce_growth = False if (args.tickers or args.allow_declining_growth) else True

    filtered_results = filter_stocks(
        raw_stock_data=raw_data,
        rsi_max=effective_rsi,
        require_sma200=require_sma200,
        require_ema200=args.require_ema200,
        weekly_rsi_min=weekly_rsi_min,
        require_stoch_cross=args.stoch_cross,
        sector_filter=args.sector,
        min_rr_ratio=args.min_rr,
        exclude_falling_knife=exclude_falling_knife,
        require_growth=enforce_growth,
        max_peg=args.max_peg,
        require_strong_buy=args.strong_buy,
        require_reversal=args.actionable
    )

    effective_rsi_max = effective_rsi
    if not filtered_results and args.auto_fallback and effective_rsi_max <= 35.0:
        fallback_rsi = 40.0
        print(f"No stocks found at RSI <= {args.rsi_max}. Auto-fallback active: expanding scan to RSI <= {fallback_rsi}...", file=sys.stderr)
        filtered_results = filter_stocks(
            raw_stock_data=raw_data,
            rsi_max=fallback_rsi,
            require_sma200=require_sma200,
            require_ema200=args.require_ema200,
            weekly_rsi_min=weekly_rsi_min,
            require_stoch_cross=args.stoch_cross,
            sector_filter=args.sector,
            min_rr_ratio=args.min_rr,
            exclude_falling_knife=exclude_falling_knife,
            require_growth=enforce_growth,
            max_peg=args.max_peg,
            require_strong_buy=args.strong_buy,
            require_reversal=args.actionable
        )
        effective_rsi_max = fallback_rsi

    if args.output_json:
        print(json.dumps(filtered_results, indent=2, ensure_ascii=False))
    else:
        report = generate_markdown_report(
            matched_stocks=filtered_results,
            total_scanned=len(raw_data),
            rsi_max=effective_rsi_max,
            require_sma200=require_sma200,
            weekly_rsi_min=weekly_rsi_min,
            universe_name=univ_label,
            sector_name=args.sector,
            require_ema200=args.require_ema200,
            min_rr_ratio=args.min_rr,
            require_growth=args.require_growth
        )
        print(report)

        if args.save_report:
            out_path = Path(args.save_report)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report, encoding="utf-8")
            print(f"\nReport saved to: {out_path.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
