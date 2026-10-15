#!/usr/bin/env python3
"""
Portfolio CLI Tool
Tracks holdings in data/portfolio.json against live market data from TradingView.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.portfolio import load_portfolio, analyze_portfolio, generate_portfolio_markdown
from src.html_report import generate_portfolio_html
from src.trades import load_trades, generate_trades_markdown, generate_trades_html



def run_all_reports():
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("📊 [0/6] กำลังอัปเดตข้อมูลแท่งเทียนย้อนหลังและคำนวณ Fibonacci อัจฉริยะ...", flush=True)
    try:
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
            + [c["ticker"] for c in d_data.get("closed_trades", [])]
        )
        get_all_charts_payload(list(all_t))
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาดในการโหลดแท่งเทียน: {e}", flush=True)

    print("🚀 [1/6] กำลังอัปเดต Master Wealth Dashboard (KKP + Dime!)...", flush=True)
    from scripts.generate_master_report import generate_master_dashboard_data, generate_master_dashboard_html
    master_data = generate_master_dashboard_data()
    master_html = generate_master_dashboard_html(master_data)
    (reports_dir / "portfolio_master.html").write_text(master_html, encoding="utf-8")
    Path("data/account_summary.json").write_text(json.dumps(master_data, indent=2, ensure_ascii=False), encoding="utf-8")
    from scripts.sync_skill_numbers import sync_skill_numbers
    sync_skill_numbers(master_data)

    print("🏥 [2/6] กำลังอัปเดต Portfolio Health Review (พอร์ตจริง)...", flush=True)
    portfolio_data = load_portfolio()
    summary = analyze_portfolio(portfolio_data)
    review_html = generate_portfolio_html(summary)
    (reports_dir / "portfolio_review.html").write_text(review_html, encoding="utf-8")

    print("🛟 [3/6] กำลังอัปเดต Drawdown Recovery Strategy (แผนแก้ดอย 360 องศา)...", flush=True)
    from recovery import analyze_all_underwater
    from src.html_report import generate_recovery_html
    rec_summary = analyze_all_underwater()
    rec_html = generate_recovery_html(rec_summary)
    (reports_dir / "portfolio_recovery.html").write_text(rec_html, encoding="utf-8")

    print("🎯 [4/6] กำลังอัปเดต Simulated Dip Portfolio (พอร์ตจำลองช้อนซื้อ)...", flush=True)
    from scripts.generate_dip_sim_report import load_simulation_data, analyze_simulation, generate_html_report as generate_dip_html
    sim_data = load_simulation_data()
    sim_summary = analyze_simulation(sim_data)
    dip_html = generate_dip_html(sim_summary)
    (reports_dir / "portfolio_dip_sim.html").write_text(dip_html, encoding="utf-8")

    print("📈 [5/6] กำลังอัปเดต Complete Trading Ledger (รายการซื้อขายทั้งหมด)...", flush=True)
    from scripts.generate_master_report import generate_master_ledger_html
    trades_html = generate_master_ledger_html(master_data)
    (reports_dir / "trades_ledger.html").write_text(trades_html, encoding="utf-8")

    print("🚀 [6/6] กำลังสร้าง Dedicated Stock Chart Page (หน้าวิเคราะห์กราฟ & AI เต็มจอ)...", flush=True)
    from src.chart_page import generate_stock_chart_page_html
    chart_page_html = generate_stock_chart_page_html()
    (reports_dir / "stock_chart.html").write_text(chart_page_html, encoding="utf-8")

    at_sign = "+" if master_data['all_time_profit_thb'] >= 0 else ""
    print("\n" + "=" * 74)
    print(" 🎉 อัปเดตรายงานทั้งหมด 6 รายการเรียบร้อยสมบูรณ์!")
    print("=" * 74)
    print(f"💰 พอร์ตหลัก (NAV รวม)   : ฿{master_data['total_net_worth_thb']:,.2f} (~${master_data['total_net_worth_usd']:,.2f} USD)")
    print(f"📈 กำไรสุทธิสะสม         : {at_sign}฿{master_data['all_time_profit_thb']:,.2f} ({at_sign}{master_data['all_time_roi_pct']:.2f}% ROI)")
    print(f"💵 เงินสดรอลงทุน         : ฿{master_data['total_cash_thb']:,.2f}")
    print(f"📊 หุ้นในพอร์ตปัจจุบัน   : {len(master_data['positions'])} ตัว")
    print("-" * 74)
    print(f"1. แดชบอร์ดภาพรวมพอร์ต   : reports/portfolio_master.html")
    print(f"2. ตรวจสุขภาพพอร์ต       : reports/portfolio_review.html")
    print(f"3. กลยุทธ์ฟื้นฟู/แก้ดอย : reports/portfolio_recovery.html")
    print(f"4. จำลองช้อนซื้อหุ้น Dip : reports/portfolio_dip_sim.html")
    print(f"5. รายการซื้อขายทั้งหมด   : reports/trades_ledger.html")
    print(f"6. หน้ากราฟ & AI เต็มจอ  : reports/stock_chart.html")
    print("=" * 74)


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
        run_all_reports()
        return

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
