#!/usr/bin/env python3
"""
Trade Ledger CLI Tool
Record buys, sells, deposits, withdrawals and dividends. Updates active holdings
in portfolio.json, cash and capital in ledger.json, and realized profit/loss metrics.
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
    record_buy,
    record_deposit,
    record_withdraw,
    record_dividend,
    calculate_trades_summary,
    generate_trades_markdown,
    generate_trades_html,
    DEFAULT_PORTFOLIO_PATH,
    DEFAULT_TRADES_PATH,
    DEFAULT_LEDGER_PATH,
)


def print_ledger_result(result, lines):
    mode_str = "[DRY-RUN PREVIEW] " if result["dry_run"] else "[EXECUTED] "
    print(f"\n{mode_str}{lines[0]}")
    print("--------------------------------------------------")
    for line in lines[1:]:
        print(line)
    cash = result["cash"]
    print(f"Dime! Save Cash : ฿{cash['dime_save_thb']:,.2f}")
    print(f"Dime! USD Cash  : ${cash['dime_usd']:,.2f}")
    print("--------------------------------------------------")
    for w in result.get("warnings", []):
        print(f"Warning: {w}", file=sys.stderr)
    if result["dry_run"]:
        print("Note: This was a dry-run. No files were modified.")
    else:
        print(f"Updated ledger: {DEFAULT_LEDGER_PATH}")


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

    # buy command
    buy_parser = subparsers.add_parser("buy", help="Record a buy, update holdings and deduct cash")
    buy_parser.add_argument("--ticker", "-t", required=True, type=str, help="Stock ticker symbol (e.g. NVDA)")
    buy_parser.add_argument("--shares", "-s", required=True, type=float, help="Number of shares bought")
    buy_parser.add_argument("--price", "-p", required=True, type=float, help="Execution price in USD")
    buy_parser.add_argument("--fx", type=float, default=None, help="USD/THB exchange rate (default: from portfolio.json)")
    buy_parser.add_argument("--pay", choices=["thb", "usd"], default="thb", help="Pay from Dime! Save THB (default) or Dime! USD")
    buy_parser.add_argument("--exchange", type=str, default=None, help="Exchange for a new ticker (default: auto lookup)")
    buy_parser.add_argument("--date", "-d", type=str, default=None, help="Trade date (YYYY-MM-DD, default: today)")
    buy_parser.add_argument("--dry-run", action="store_true", help="Preview without modifying files")

    # deposit / withdraw commands
    dep_parser = subparsers.add_parser("deposit", help="Record a THB deposit into Dime! Save")
    dep_parser.add_argument("--amount", required=True, type=float, help="Amount in THB")
    dep_parser.add_argument("--channel", type=str, default="PROMPTPAY", help="Deposit channel (default: PROMPTPAY)")
    dep_parser.add_argument("--date", "-d", type=str, default=None, help="Date (YYYY-MM-DD, default: today)")
    dep_parser.add_argument("--dry-run", action="store_true", help="Preview without modifying files")

    wd_parser = subparsers.add_parser("withdraw", help="Record a THB withdrawal out of Dime! Save")
    wd_parser.add_argument("--amount", required=True, type=float, help="Amount in THB")
    wd_parser.add_argument("--date", "-d", type=str, default=None, help="Date (YYYY-MM-DD, default: today)")
    wd_parser.add_argument("--dry-run", action="store_true", help="Preview without modifying files")

    # dividend command
    div_parser = subparsers.add_parser("dividend", help="Record a dividend paid into Dime! USD")
    div_parser.add_argument("--ticker", "-t", required=True, type=str, help="Stock ticker symbol")
    div_parser.add_argument("--usd", required=True, type=float, help="Net dividend received in USD")
    div_parser.add_argument("--rate", type=str, default="-", help="Per-share rate label (e.g. 0.22/หุ้น)")
    div_parser.add_argument("--fx", type=float, default=None, help="USD/THB exchange rate (default: from portfolio.json)")
    div_parser.add_argument("--date", "-d", type=str, default=None, help="Payment date (YYYY-MM-DD, default: today)")
    div_parser.add_argument("--dry-run", action="store_true", help="Preview without modifying files")

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

    try:
        if args.command == "buy":
            r = record_buy(args.ticker, args.shares, args.price, fx_rate=args.fx, pay=args.pay,
                           trade_date=args.date, exchange=args.exchange, dry_run=args.dry_run)
            h, b = r["holding"], r["buy_order"]
            print_ledger_result(r, [
                f"Recorded buy of {b['ticker']}:",
                f"Bought          : {b['shares']:.4f} @ ${b['price_usd']:,.2f} = ${b['amt_usd']:,.2f} (paid via {b['account']})",
                f"Holding         : {h['shares']:.4f} sh | avg ${h['avg_cost_usd']:,.4f} | cost ${h['total_cost_usd']:,.2f} (฿{h['cost_thb']:,.2f})",
                f"Status          : {r['status_action']}",
            ])
            if not r["dry_run"]:
                print(f"Updated active holdings in: {DEFAULT_PORTFOLIO_PATH}")
            return
        if args.command in ("deposit", "withdraw"):
            if args.command == "deposit":
                r = record_deposit(args.amount, channel=args.channel, trade_date=args.date, dry_run=args.dry_run)
            else:
                r = record_withdraw(args.amount, trade_date=args.date, dry_run=args.dry_run)
            m = r["movement"]
            print_ledger_result(r, [
                f"Recorded {args.command}:",
                f"Movement        : {m['type']} ฿{m['amount_thb']:,.2f} ({m['date_str']})",
                f"Net Capital     : ฿{r['net_injected_capital_thb']:,.2f}",
            ])
            return
        if args.command == "dividend":
            r = record_dividend(args.ticker, args.usd, fx_rate=args.fx, rate=args.rate,
                                trade_date=args.date, dry_run=args.dry_run)
            d = r["dividend"]
            print_ledger_result(r, [
                f"Recorded dividend from {d['ticker']}:",
                f"Dividend        : ${d['amount_usd']:,.2f} (฿{d['amount_thb']:,.2f} @ {d['fx_rate']}) on {d['date']}",
            ])
            return
    except Exception as e:
        print(f"Error processing {args.command}: {e}", file=sys.stderr)
        sys.exit(1)

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
            print(f"Credited ${t['net_revenue_usd']:,.2f} to Dime! USD : ${result['cash']['dime_usd']:,.2f} ({DEFAULT_LEDGER_PATH})")

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
