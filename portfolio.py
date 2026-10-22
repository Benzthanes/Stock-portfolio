#!/usr/bin/env python3
"""
Portfolio CLI Tool
Tracks holdings in data/portfolio.json against live market data from TradingView.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from src.portfolio import load_portfolio, analyze_portfolio, generate_portfolio_markdown
from src.html_report import generate_portfolio_html
from src.trades import load_trades, generate_trades_markdown, generate_trades_html



def _report_failure(failures, step, exc):
    """Log a failed step to stderr (and as a GitHub Actions warning) and keep going."""
    failures.append(step)
    msg = f"{step} failed: {type(exc).__name__}: {exc}"
    print(f"⚠️ {msg}", file=sys.stderr, flush=True)
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning title=portfolio --all::{msg}", flush=True)


def _refresh_charts():
    from src.chart_data import get_all_charts_payload
    p_path = Path("data/portfolio.json")
    t_path = Path("data/trades.json")
    d_path = Path("data/portfolio_dip_sim.json")
    p_data = json.loads(p_path.read_text(encoding="utf-8")) if p_path.exists() else {}
    t_data = json.loads(t_path.read_text(encoding="utf-8")) if t_path.exists() else {}
    d_data = json.loads(d_path.read_text(encoding="utf-8")) if d_path.exists() else {}
    all_t = set(
        [h["ticker"] for h in p_data.get("holdings", [])]
        + [t["ticker"] for t in t_data.get("trades", [])]
        + [h["ticker"] for h in d_data.get("holdings", [])]
    )
    get_all_charts_payload(list(all_t))


def _master_report(reports_dir):
    from scripts.generate_master_report import generate_master_dashboard_data, generate_master_dashboard_html
    master_data = generate_master_dashboard_data()
    master_html = generate_master_dashboard_html(master_data)
    (reports_dir / "portfolio_master.html").write_text(master_html, encoding="utf-8")
    Path("data/account_summary.json").write_text(json.dumps(master_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return master_data


def _review_report(reports_dir):
    portfolio_data = load_portfolio()
    summary = analyze_portfolio(portfolio_data)
    (reports_dir / "portfolio_review.html").write_text(generate_portfolio_html(summary), encoding="utf-8")


def _recovery_report(reports_dir):
    from recovery import analyze_all_underwater
    from src.html_report import generate_recovery_html
    rec_summary = analyze_all_underwater()
    (reports_dir / "portfolio_recovery.html").write_text(generate_recovery_html(rec_summary), encoding="utf-8")


def _dip_report(reports_dir):
    from scripts.generate_dip_sim_report import load_simulation_data, analyze_simulation, generate_html_report as generate_dip_html
    sim_summary = analyze_simulation(load_simulation_data())
    (reports_dir / "portfolio_dip_sim.html").write_text(generate_dip_html(sim_summary), encoding="utf-8")


def _ledger_report(reports_dir, master_data):
    from scripts.generate_master_report import generate_master_ledger_html
    (reports_dir / "trades_ledger.html").write_text(generate_master_ledger_html(master_data), encoding="utf-8")


def _chart_page(reports_dir):
    from src.chart_page import generate_stock_chart_page_html
    (reports_dir / "stock_chart.html").write_text(generate_stock_chart_page_html(), encoding="utf-8")


def run_all_reports():
    """Generate every report. A failed step is logged and skipped. Returns the list of failed steps."""
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    master_data = None

    def step(label, name, fn, *args):
        print(label, flush=True)
        try:
            return fn(*args)
        except Exception as e:
            _report_failure(failures, name, e)
            return None

    step("📊 [0/6] กำลังอัปเดตข้อมูลแท่งเทียนย้อนหลังและคำนวณ Fibonacci อัจฉริยะ...", "chart data refresh", _refresh_charts)
    master_data = step("🚀 [1/6] กำลังอัปเดต Master Wealth Dashboard (KKP + Dime!)...", "master dashboard", _master_report, reports_dir)
    step("🏥 [2/6] กำลังอัปเดต Portfolio Health Review (พอร์ตจริง)...", "health review", _review_report, reports_dir)
    step("🛟 [3/6] กำลังอัปเดต Drawdown Recovery Strategy (แผนแก้ดอย 360 องศา)...", "recovery strategy", _recovery_report, reports_dir)
    step("🎯 [4/6] กำลังอัปเดต Simulated Dip Portfolio (พอร์ตจำลองช้อนซื้อ)...", "dip simulation", _dip_report, reports_dir)
    if master_data is not None:
        step("📈 [5/6] กำลังอัปเดต Complete Trading Ledger (รายการซื้อขายทั้งหมด)...", "trades ledger",
             _ledger_report, reports_dir, master_data)
    else:
        _report_failure(failures, "trades ledger", RuntimeError("skipped because master dashboard failed"))
    step("🚀 [6/6] กำลังสร้าง Dedicated Stock Chart Page (หน้าวิเคราะห์กราฟ & AI เต็มจอ)...", "stock chart page", _chart_page, reports_dir)

    print("\n" + "=" * 74)
    if failures:
        print(f" ⚠️ อัปเดตไม่สำเร็จ {len(failures)} ขั้นตอน: {', '.join(failures)}")
    else:
        print(" 🎉 อัปเดตรายงานทั้งหมด 6 รายการเรียบร้อยสมบูรณ์!")
    print("=" * 74)
    if master_data is not None:
        at_sign = "+" if master_data['all_time_profit_thb'] >= 0 else ""
        print(f"💰 พอร์ตหลัก (NAV รวม)   : ฿{master_data['total_net_worth_thb']:,.2f} (~${master_data['total_net_worth_usd']:,.2f} USD)")
        print(f"📈 กำไรสุทธิสะสม         : {at_sign}฿{master_data['all_time_profit_thb']:,.2f} ({at_sign}{master_data['all_time_roi_pct']:.2f}% ROI)")
        print(f"💵 เงินสดรอลงทุน         : ฿{master_data['total_cash_thb']:,.2f}")
        print(f"📊 หุ้นในพอร์ตปัจจุบัน   : {len(master_data['positions'])} ตัว")
        print("-" * 74)
    print("1. แดชบอร์ดภาพรวมพอร์ต   : reports/portfolio_master.html")
    print("2. ตรวจสุขภาพพอร์ต       : reports/portfolio_review.html")
    print("3. กลยุทธ์ฟื้นฟู/แก้ดอย : reports/portfolio_recovery.html")
    print("4. จำลองช้อนซื้อหุ้น Dip : reports/portfolio_dip_sim.html")
    print("5. รายการซื้อขายทั้งหมด   : reports/trades_ledger.html")
    print("6. หน้ากราฟ & AI เต็มจอ  : reports/stock_chart.html")
    print("=" * 74)
    return failures


def main():
    parser = argparse.ArgumentParser(
        description="US Stock Portfolio Tracker & Technical Health Analyzer"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Path to portfolio JSON file (default: data/portfolio.json)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output raw JSON results instead of Markdown"
    )
    parser.add_argument(
        "--trades",
        action="store_true",
        help="Show realized profit/loss trade ledger"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate and update all 6 HTML reports in one shot"
    )
    parser.add_argument(
        "--save-report",
        type=str,
        nargs="?",
        const="reports/portfolio_review.html",
        help="Save report to HTML or Markdown file (default: reports/portfolio_review.html)"
    )

    args = parser.parse_args()

    if args.all:
        failures = run_all_reports()
        sys.exit(1 if failures else 0)

    if args.trades:
        trades_data = load_trades()
        if args.output_json:
            print(json.dumps(trades_data, indent=2, ensure_ascii=False))
        else:
            report = generate_trades_markdown(trades_data)
            print(report)

            if args.save_report:
                report_file = args.save_report if args.save_report != "reports/portfolio_review.html" else "reports/trades_ledger.html"
                out_path = Path(report_file)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                if out_path.suffix.lower() == ".html":
                    out_path.write_text(generate_trades_html(trades_data), encoding="utf-8")
                else:
                    out_path.write_text(report, encoding="utf-8")
                print(f"\nReport saved to: {out_path.resolve()}", file=sys.stderr)
        return

    try:
        portfolio_data = load_portfolio(args.file)
    except Exception as e:
        print(f"Error loading portfolio file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching live TradingView data for {len(portfolio_data.get('holdings', []))} portfolio holdings...", file=sys.stderr)

    try:
        summary = analyze_portfolio(portfolio_data)
    except Exception as e:
        print(f"Error analyzing portfolio: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        report = generate_portfolio_markdown(summary)
        print(report)

        if args.save_report:
            out_path = Path(args.save_report)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if out_path.suffix.lower() == ".html":
                html_content = generate_portfolio_html(summary)
                out_path.write_text(html_content, encoding="utf-8")
            else:
                out_path.write_text(report, encoding="utf-8")
            print(f"\nReport saved to: {out_path.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
