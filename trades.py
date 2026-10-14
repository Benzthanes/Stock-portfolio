#!/usr/bin/env python3
"""
Trade Ledger CLI Tool
Record closed stock sales, update active holdings in portfolio.json,
and calculate realized profit/loss metrics.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.trades import (
    load_trades,
    save_trades,
    record_sell,
    calculate_trades_summary,
    generate_trades_markdown,
    generate_trades_html,
    DEFAULT_PORTFOLIO_PATH,
    DEFAULT_TRADES_PATH,
)


def main():
    parser = argparse.ArgumentParser(
        description="US Stock Realized Trade Ledger & Profit/Loss Tracker"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # sell command
    sell_parser = subparsers.add_parser("sell", help="Record a sell transaction and close/reduce position")
    sell_parser.add_argument("--ticker", "-t", required=True, type=str, help="Stock ticker symbol (e.g. VST)")
    sell_parser.add_argument("--price", "-p", required=True, type=float, help="Execution sell price in USD")
    sell_parser.add_argument("--shares", "-s", type=float, default=None, help="Number of shares sold (default: all)")
    sell_parser.add_argument("--fees", type=float, default=0.0, help="Brokerage commissions/fees in USD (default: 0.0)")
    sell_parser.add_argument("--fx", type=float, default=None, help="USD/THB exchange rate (default: from portfolio.json)")
    sell_parser.add_argument("--date", "-d", type=str, default=None, help="Trade execution date (YYYY-MM-DD)")
    sell_parser.add_argument("--notes", type=str, default="", help="Trade notes or rationale")
    sell_parser.add_argument("--dry-run", action="store_true", help="Calculate realized P&L without modifying files")
    sell_parser.add_argument("--save-report", type=str, nargs="?", const="reports/trades_ledger.html", help="Save HTML report")

    # list command
    list_parser = subparsers.add_parser("list", help="List all closed trades and show realized P&L summary")
    list_parser.add_argument("--json", action="store_true", help="Output raw JSON format")
    list_parser.add_argument("--save-report", type=str, nargs="?", const="reports/trades_ledger.html", help="Save HTML report")

    # summary command
    summary_parser = subparsers.add_parser("summary", help="Show realized profit/loss summary KPIs")
    summary_parser.add_argument("--json", action="store_true", help="Output raw JSON format")

    # report command
    report_parser = subparsers.add_parser("report", help="Generate HTML or Markdown trade ledger report")
    report_parser.add_argument("--save-report", "-o", type=str, default="reports/trades_ledger.html", help="Path to output report")

    args = parser.parse_args()

    # Default to list if no command provided
    if not args.command or args.command == "list":
        trades_data = load_trades()
        if getattr(args, "json", False):
            print(json.dumps(trades_data, indent=2, ensure_ascii=False))
        else:
            report_md = generate_trades_markdown(trades_data)
            print(report_md)

        if getattr(args, "save_report", None):
            out_path = Path(args.save_report)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(generate_trades_html(trades_data), encoding="utf-8")
            print(f"\nHTML report saved to: {out_path.resolve()}", file=sys.stderr)
        return

    if args.command == "summary":
        trades_data = load_trades()
        summary = calculate_trades_summary(trades_data)
        if args.json:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            pl_sign = "+" if summary["total_realized_pl_usd"] >= 0 else ""
            print("==================================================")
            print("  US STOCK REALIZED PROFIT/LOSS SUMMARY")
            print("==================================================")
            print(f"Total Closed Trades : {summary['total_trades']}")
            print(f"Win Rate            : {summary['win_rate_pct']:.1f}% ({summary['winning_trades']} wins, {summary['losing_trades']} losses)")
            print(f"Net Realized P&L    : {pl_sign}${summary['total_realized_pl_usd']:,.2f} ({pl_sign}฿{summary['total_realized_pl_thb']:,.2f})")
            print(f"Overall ROI         : {pl_sign}{summary['roi_pct']:.2f}%")
            print(f"Profit Factor       : {summary['profit_factor']:.2f}")
            print(f"Total Cost Sold     : ${summary['total_cost_usd']:,.2f}")
            print(f"Total Net Proceeds  : ${summary['total_revenue_usd']:,.2f}")
            print("==================================================")
        return

    if args.command == "sell":
        try:
            result = record_sell(
                ticker=args.ticker,
                sell_price=args.price,
                shares=args.shares,
                fees=args.fees,
                fx_rate=args.fx,
                trade_date=args.date,
                notes=args.notes,
                dry_run=args.dry_run,
            )
        except Exception as e:
            print(f"Error processing sell transaction: {e}", file=sys.stderr)
            sys.exit(1)

        t = result["trade"]
        pl_sign = "+" if t["realized_pl_usd"] >= 0 else ""
        mode_str = "[DRY-RUN PREVIEW] " if result["dry_run"] else "[EXECUTED] "

        print(f"\n{mode_str}Successfully recorded sale for {t['ticker']}:")
        print("--------------------------------------------------")
        print(f"Ticker          : {t['ticker']} ({t['name']})")
        print(f"Shares Sold     : {t['shares']:.4f}")
        print(f"Buy Price (Avg) : ${t['buy_price_usd']:.2f}")
        print(f"Sell Price      : ${t['sell_price_usd']:.2f}")
        print(f"Total Cost      : ${t['total_cost_usd']:,.2f} (฿{t['cost_thb']:,.2f})")
        print(f"Net Revenue     : ${t['net_revenue_usd']:,.2f} (฿{t['revenue_thb']:,.2f})")
        print(f"Realized P&L    : {pl_sign}${t['realized_pl_usd']:,.2f} ({pl_sign}฿{t['realized_pl_thb']:,.2f})")
        print(f"Return (ROI)    : {pl_sign}{t['realized_pl_pct']:.2f}%")
        print(f"Status          : {result['status_action']}")
        print("--------------------------------------------------")

        if not result["dry_run"]:
            print(f"Updated active holdings in: {DEFAULT_PORTFOLIO_PATH}")
            print(f"Appended trade record to : {DEFAULT_TRADES_PATH}")

            if args.save_report:
                trades_data = load_trades()
                out_path = Path(args.save_report)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(generate_trades_html(trades_data), encoding="utf-8")
                print(f"Saved trade ledger HTML to : {out_path.resolve()}")
        else:
            print("Note: This was a dry-run. No files were modified.")
        return

    if args.command == "report":
        trades_data = load_trades()
        out_path = Path(args.save_report)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.suffix.lower() == ".html":
            out_path.write_text(generate_trades_html(trades_data), encoding="utf-8")
        else:
            out_path.write_text(generate_trades_markdown(trades_data), encoding="utf-8")
        print(f"Trade ledger report saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
