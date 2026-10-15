"""
Trade Ledger & Realized P&L Tracker Module
Tracks closed trades, computes realized profit/loss in USD and THB,
and updates active holdings in portfolio.json.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.html_report import get_chart_modal_component

DEFAULT_PORTFOLIO_PATH = Path("data/portfolio.json")
DEFAULT_TRADES_PATH = Path("data/trades.json")


def load_trades(filepath: Optional[str] = None) -> Dict[str, Any]:
    path = Path(filepath) if filepath else DEFAULT_TRADES_PATH
    if not path.exists():
        return {
            "portfolio_name": "ไม่รวยก็ซวยอ่ะค้าบ",
            "broker": "InnovestX",
            "base_currency": "USD",
            "default_fx_rate": 33.62,
            "trades": []
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_trades(trades_data: Dict[str, Any], filepath: Optional[str] = None) -> None:
    path = Path(filepath) if filepath else DEFAULT_TRADES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(trades_data, f, indent=2, ensure_ascii=False)


def calculate_trades_summary(trades_data: Dict[str, Any]) -> Dict[str, Any]:
    trades: List[Dict[str, Any]] = trades_data.get("trades", [])
    total_trades = len(trades)
    if total_trades == 0:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "win_rate_pct": 0.0,
            "total_cost_usd": 0.0,
            "total_cost_thb": 0.0,
            "total_revenue_usd": 0.0,
            "total_revenue_thb": 0.0,
            "total_realized_pl_usd": 0.0,
            "total_realized_pl_thb": 0.0,
            "total_fees_usd": 0.0,
            "roi_pct": 0.0,
            "profit_factor": 0.0,
            "best_trade": None,
            "worst_trade": None,
        }

    winning_trades = [t for t in trades if t.get("realized_pl_usd", 0) > 0]
    losing_trades = [t for t in trades if t.get("realized_pl_usd", 0) < 0]
    breakeven_trades = [t for t in trades if t.get("realized_pl_usd", 0) == 0]

    win_rate = (len(winning_trades) / total_trades) * 100.0

    total_cost_usd = sum(t.get("total_cost_usd", 0) for t in trades)
    total_cost_thb = sum(t.get("cost_thb", 0) for t in trades)
    total_rev_usd = sum(t.get("net_revenue_usd", 0) for t in trades)
    total_rev_thb = sum(t.get("revenue_thb", 0) for t in trades)
    total_pl_usd = sum(t.get("realized_pl_usd", 0) for t in trades)
    total_pl_thb = sum(t.get("realized_pl_thb", 0) for t in trades)
    total_fees_usd = sum(t.get("fees_usd", 0) for t in trades)

    roi_pct = (total_pl_usd / total_cost_usd * 100.0) if total_cost_usd > 0 else 0.0

    gross_profit = sum(t.get("realized_pl_usd", 0) for t in winning_trades)
    gross_loss = abs(sum(t.get("realized_pl_usd", 0) for t in losing_trades))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    best_trade = max(trades, key=lambda t: t.get("realized_pl_usd", 0)) if trades else None
    worst_trade = min(trades, key=lambda t: t.get("realized_pl_usd", 0)) if trades else None

    return {
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "breakeven_trades": len(breakeven_trades),
        "win_rate_pct": round(win_rate, 1),
        "total_cost_usd": round(total_cost_usd, 2),
        "total_cost_thb": round(total_cost_thb, 2),
        "total_revenue_usd": round(total_rev_usd, 2),
        "total_revenue_thb": round(total_rev_thb, 2),
        "total_realized_pl_usd": round(total_pl_usd, 2),
        "total_realized_pl_thb": round(total_pl_thb, 2),
        "total_fees_usd": round(total_fees_usd, 2),
        "roi_pct": round(roi_pct, 2),
        "profit_factor": round(profit_factor, 2),
        "best_trade": best_trade,
        "worst_trade": worst_trade,
    }


def record_sell(
    ticker: str,
    sell_price: float,
    shares: Optional[float] = None,
    fees: float = 0.0,
    fx_rate: Optional[float] = None,
    trade_date: Optional[str] = None,
    notes: str = "",
    portfolio_path: Optional[str] = None,
    trades_path: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    p_path = Path(portfolio_path) if portfolio_path else DEFAULT_PORTFOLIO_PATH
    if not p_path.exists():
        raise FileNotFoundError(f"Portfolio file not found at {p_path}")

    with open(p_path, "r", encoding="utf-8") as f:
        portfolio_data = json.load(f)

    holdings: List[Dict[str, Any]] = portfolio_data.get("holdings", [])
    target_ticker = ticker.strip().upper()

    holding_match = None
    holding_idx = -1
    for i, h in enumerate(holdings):
        if h.get("ticker", "").upper() == target_ticker:
            holding_match = h
            holding_idx = i
            break

    if not holding_match:
        raise ValueError(f"Ticker '{target_ticker}' not found in active holdings.")

    current_shares = float(holding_match.get("shares", 0.0))
    avg_cost = float(holding_match.get("avg_cost_usd", 0.0))

    if shares is None:
        sell_shares = current_shares
    elif shares <= 0:
        raise ValueError(f"Shares to sell must be greater than 0 (got {shares}).")
    elif shares > current_shares:
        raise ValueError(f"Cannot sell {shares} shares of {target_ticker}: only {current_shares} held.")
    else:
        sell_shares = float(shares)

    current_fx = fx_rate if fx_rate is not None else float(portfolio_data.get("fx_rate_usd_thb", 33.62))
    exec_date = trade_date or datetime.now().strftime("%Y-%m-%d")

    cost_usd = round(sell_shares * avg_cost, 2)
    cost_thb = round(cost_usd * current_fx, 2)

    gross_rev_usd = round(sell_shares * sell_price, 2)
    net_rev_usd = round(gross_rev_usd - fees, 2)
    rev_thb = round(net_rev_usd * current_fx, 2)

    realized_pl_usd = round(net_rev_usd - cost_usd, 2)
    realized_pl_thb = round(realized_pl_usd * current_fx, 2)
    realized_pl_pct = round((realized_pl_usd / cost_usd * 100.0) if cost_usd > 0 else 0.0, 2)

    trades_data = load_trades(trades_path)
    trade_id = f"TRD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{target_ticker}"

    trade_entry = {
        "id": trade_id,
        "ticker": target_ticker,
        "exchange": holding_match.get("exchange", "NASDAQ"),
        "name": holding_match.get("name", target_ticker),
        "action": "SELL",
        "date": exec_date,
        "shares": sell_shares,
        "buy_price_usd": avg_cost,
        "sell_price_usd": float(sell_price),
        "total_cost_usd": cost_usd,
        "cost_thb": cost_thb,
        "gross_revenue_usd": gross_rev_usd,
        "fees_usd": float(fees),
        "net_revenue_usd": net_rev_usd,
        "revenue_thb": rev_thb,
        "realized_pl_usd": realized_pl_usd,
        "realized_pl_thb": realized_pl_thb,
        "realized_pl_pct": realized_pl_pct,
        "fx_rate": current_fx,
        "notes": notes,
        "remaining_shares": round(current_shares - sell_shares, 7),
    }

    buy_date = holding_match.get("buy_date")
    if buy_date:
        trade_entry["buy_date"] = buy_date
        try:
            trade_entry["holding_days"] = (datetime.strptime(exec_date, "%Y-%m-%d") - datetime.strptime(buy_date, "%Y-%m-%d")).days
        except ValueError:
            pass

    # Update holdings
    remaining_shares = current_shares - sell_shares
    if remaining_shares <= 0.000001:
        status_action = f"Closed position completely (sold all {sell_shares} shares)."
        if not dry_run:
            holdings.pop(holding_idx)
    else:
        new_total_cost = round(remaining_shares * avg_cost, 2)
        old_cost_thb = holding_match.get("cost_thb")
        if old_cost_thb is None:
            new_cost_thb = round(new_total_cost * current_fx, 2)
        else:
            new_cost_thb = round(float(old_cost_thb) * remaining_shares / current_shares, 2)
        status_action = f"Partial sell: {sell_shares} sold, {remaining_shares:.4f} remaining."
        if not dry_run:
            holding_match["shares"] = round(remaining_shares, 7)
            holding_match["total_cost_usd"] = new_total_cost
            holding_match["cost_thb"] = new_cost_thb

    if not dry_run:
        with open(p_path, "w", encoding="utf-8") as f:
            json.dump(portfolio_data, f, indent=2, ensure_ascii=False)

        trades_data["trades"].append(trade_entry)
        save_trades(trades_data, trades_path)

    return {
        "trade": trade_entry,
        "status_action": status_action,
        "dry_run": dry_run,
        "updated_summary": calculate_trades_summary(trades_data if not dry_run else {"trades": trades_data.get("trades", []) + [trade_entry]}),
    }


def generate_trades_markdown(trades_data: Dict[str, Any]) -> str:
    summary = calculate_trades_summary(trades_data)
    trades = trades_data.get("trades", [])

    lines = []
    lines.append("# 📈 บัญชีกำไรขาดทุนจากการซื้อขาย (Realized Trade Ledger)")
    lines.append(f"**พอร์ตโฟลิโอ:** {trades_data.get('portfolio_name', 'My Portfolio')} | **โบรกเกอร์:** {trades_data.get('broker', 'InnovestX')}\n")

    lines.append("## 📊 ภาพรวมกำไรขาดทุนสะสม (Realized Performance)")
    pl_sign = "+" if summary["total_realized_pl_usd"] >= 0 else ""
    lines.append(f"- **กำไรขาดทุนสุทธิ (Net Realized P&L):** `{pl_sign}${summary['total_realized_pl_usd']:,.2f}` (`{pl_sign}฿{summary['total_realized_pl_thb']:,.2f}`)")
    lines.append(f"- **ผลตอบแทนเฉลี่ย (Overall ROI):** `{pl_sign}{summary['roi_pct']:.2f}%`")
    lines.append(f"- **อัตราการเทรดชนะ (Win Rate):** `{summary['win_rate_pct']:.1f}%` ({summary['winning_trades']} ชนะ / {summary['losing_trades']} แพ้ จาก {summary['total_trades']} รายการ)")
    lines.append(f"- **Profit Factor:** `{summary['profit_factor']:.2f}`")
    lines.append(f"- **ต้นทุนที่ปิดการขายไป:** `${summary['total_cost_usd']:,.2f}` | **เงินรับสุทธิ (Proceeds):** `${summary['total_revenue_usd']:,.2f}`\n")

    lines.append("## 📝 รายการปิดการขาย (Closed Trades History)")
    if not trades:
        lines.append("*ยังไม่มีรายการปิดสถานะซื้อขายในประวัติ.*")
    else:
        lines.append("| วันที่ซื้อ | วันที่ขาย | ระยะถือ | หุ้น | หุ้นที่ขาย | ทุนเฉลี่ย | ราคาขาย | ต้นทุน ($) | เงินรับ ($) | กำไร/ขาดทุน ($) | กำไร/ขาดทุน (฿) | % ROI |")
        lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        for t in reversed(trades):
            pl_usd = t.get("realized_pl_usd", 0)
            pl_thb = t.get("realized_pl_thb", 0)
            pl_pct = t.get("realized_pl_pct", 0)
            sign = "+" if pl_usd >= 0 else ""
            b_date = re.sub(r"\s*\(\d+\s*ไม้\)", "", str(t.get("buy_date", "-")))
            h_days = f"{t.get('holding_days')} วัน" if t.get('holding_days') is not None else "-"
            lines.append(
                f"| {b_date} | {t.get('date', '-')} | {h_days} | **{t.get('ticker')}** | {t.get('shares'):.4f} | "
                f"${t.get('buy_price_usd'):.2f} | ${t.get('sell_price_usd'):.2f} | "
                f"${t.get('total_cost_usd'):,.2f} | ${t.get('net_revenue_usd'):,.2f} | "
                f"`{sign}${pl_usd:,.2f}` | `{sign}฿{pl_thb:,.2f}` | `{sign}{pl_pct:.2f}%` |"
            )

    return "\n".join(lines)


def generate_trades_html(trades_data: Dict[str, Any]) -> str:
    summary = calculate_trades_summary(trades_data)
    trades = trades_data.get("trades", [])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pl_val = summary["total_realized_pl_usd"]
    pl_color = "#10b981" if pl_val >= 0 else "#f43f5e"
    pl_sign = "+" if pl_val >= 0 else ""

    rows_html = ""
    for idx, t in enumerate(reversed(trades)):
        t_pl = t.get("realized_pl_usd", 0)
        t_thb = t.get("realized_pl_thb", 0)
        t_pct = t.get("realized_pl_pct", 0)
        t_color = "#10b981" if t_pl >= 0 else "#f43f5e"
        t_sign = "+" if t_pl >= 0 else ""
        tranches = t.get("buy_tranches", [])
        tranche_count = len(tranches)
        trade_id = t.get("id", f"trade_{idx}").replace("-", "_")

        buy_date_str = re.sub(r"\s*\(\d+\s*ไม้\)", "", str(t.get("buy_date", "-")))
        days = t.get("holding_days", "-")
        days_str = f"{days} วัน" if isinstance(days, (int, float)) else str(days)

        if tranche_count > 1:
            tranche_btn = f'<button onclick="toggleTranche(\'{trade_id}\')" style="background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 6px; padding: 2px 8px; font-size: 0.78rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">สะสม {tranche_count} ไม้ <span id="icon-{trade_id}">▼</span></button>'
        else:
            tranche_btn = '<span style="background: rgba(255, 255, 255, 0.08); color: #94a3b8; padding: 2px 8px; border-radius: 6px; font-size: 0.76rem;">1 ไม้</span>'

        t_ticker = t.get('ticker', '')
        t_name = (t.get('name') or t_ticker).replace("'", "\\'")
        t_click_js = f"openChartModal('{t_ticker}', '{t.get('exchange', 'NASDAQ')}', '{t_name}', 'Closed Trade', {t.get('buy_price_usd', 0)}, {t.get('sell_price_usd', 0)}, 0, 0, 0, {t.get('sell_price_usd', 0)}, 0)"

        rows_html += f"""
        <tr style="border-bottom: 1px solid var(--border-subtle);">
            <td style="white-space: nowrap; font-size: 0.85rem; color: #60a5fa; font-weight: 500;">{buy_date_str}</td>
            <td style="white-space: nowrap; font-size: 0.85rem; color: var(--text-secondary); text-align: center;">{t.get('date', '-')}</td>
            <td style="text-align: center; font-size: 0.82rem; color: var(--text-muted); white-space: nowrap;">{days_str}</td>
            <td style="font-weight: 700; font-family: 'Inter', sans-serif; font-size: 1.05rem; color: #fff;">
                <span class="clickable-ticker" onclick="{t_click_js}" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;" title="คลิกเปิดดูกราฟเทคนิคัล">{t.get('ticker')} 📈</span>
            </td>
            <td>
                <div>{t.get('name', '-')}</div>
                <div style="margin-top: 4px;">{tranche_btn}</div>
            </td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">{t.get('shares', 0):.4f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${t.get('buy_price_usd', 0):.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${t.get('sell_price_usd', 0):.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${t.get('total_cost_usd', 0):,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${t.get('net_revenue_usd', 0):,.2f}</td>
            <td style="text-align: right; font-weight: 700; color: {t_color}; font-family: 'Inter', sans-serif;">{t_sign}${t_pl:,.2f}</td>
            <td style="text-align: right; font-weight: 600; color: {t_color}; font-family: 'Inter', sans-serif;">{t_sign}฿{t_thb:,.2f}</td>
            <td style="text-align: right; font-weight: 700; color: {t_color}; font-family: 'Inter', sans-serif;">{t_sign}{t_pct:.2f}%</td>
        </tr>
        """

        if tranches:
            tranche_subrows = ""
            for tr in tranches:
                t_thb_str = f"฿{tr.get('amt_thb', 0):,.2f}" if tr.get('amt_thb', 0) > 0 else "-"
                tranche_subrows += f"""
                <tr style="background: rgba(0,0,0,0.3); border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 0.82rem;">
                    <td style="text-align: center; color: #c084fc; font-weight: 700;">ไม้ที่ {tr.get('tranche')}</td>
                    <td style="color: #60a5fa; font-family: 'Inter', sans-serif;">{tr.get('date')}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif;">{tr.get('shares'):.4f} หุ้น</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif;">${tr.get('price_usd'):.2f}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif; font-weight: 600; color: #fff;">${tr.get('amt_usd'):,.2f}</td>
                    <td style="text-align: right; font-family: 'Inter', sans-serif; color: var(--text-muted);">{t_thb_str}</td>
                    <td style="color: var(--text-secondary);">{tr.get('note', '-')}</td>
                    <td style="text-align: center; color: var(--text-muted); font-size: 0.78rem;">{tr.get('file', '-')}</td>
                </tr>
                """

            rows_html += f"""
            <tr id="details-{trade_id}" class="tranche-detail-row" style="display: none; background: rgba(139, 92, 246, 0.05);">
                <td colspan="13" style="padding: 12px 18px;">
                    <div style="background: #090e1a; border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 14px 18px;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #c084fc; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                            <span>🔍</span> รายละเอียดการเข้าซื้อทีละไม้ของ {t.get('ticker')} (ทั้งหมด {tranche_count} ไม้ | ต้นทุนเฉลี่ย ${t.get('buy_price_usd', 0):.2f}):
                        </div>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 0.78rem; color: var(--text-secondary);">
                                    <th style="text-align: center; width: 65px; background: transparent;">ไม้ที่</th>
                                    <th style="background: transparent;">วัน-เวลาที่เข้าซื้อ (Buy Date & Time)</th>
                                    <th style="text-align: right; background: transparent;">จำนวนหุ้น</th>
                                    <th style="text-align: right; background: transparent;">ราคาที่ซื้อ ($)</th>
                                    <th style="text-align: right; background: transparent;">ยอดลงทุน ($)</th>
                                    <th style="text-align: right; background: transparent;">ยอดเงินบาท (THB)</th>
                                    <th style="background: transparent;">หมายเหตุ / กลยุทธ์</th>
                                    <th style="text-align: center; background: transparent;">สลิปอ้างอิง</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tranche_subrows}
                            </tbody>
                        </table>
                    </div>
                </td>
            </tr>
            """

    if not trades:
        rows_html = '<tr><td colspan="11" style="text-align: center; padding: 28px; color: var(--text-muted);">ยังไม่มีรายการปิดสถานะซื้อขายในประวัติ</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Realized Trade Ledger - {trades_data.get('portfolio_name', 'Portfolio')}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #080d1a;
            --bg-card: #0f172a;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-subtle: rgba(255, 255, 255, 0.05);
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --emerald: #10b981;
            --rose: #f43f5e;
            --blue: #3b82f6;
            --amber: #f59e0b;
            --radius-sm: 8px;
            --radius-md: 14px;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Prompt', 'Inter', sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.6;
            padding: 24px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 16px; margin-bottom: 24px; padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }}
        .meta-pill {{
            background: var(--bg-card); padding: 6px 14px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-color); font-size: 0.9rem; color: var(--text-secondary);
        }}
        .grid-4-cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .card {{
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: var(--radius-md); padding: 22px;
        }}
        .kpi-label {{ font-size: 0.82rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 1.85rem; font-weight: 700; font-family: 'Inter', sans-serif; }}
        .kpi-subtext {{ font-size: 0.88rem; color: var(--text-muted); margin-top: 6px; }}
        table {{
            width: 100%; border-collapse: collapse; font-size: 0.92rem;
        }}
        th {{
            background: rgba(255, 255, 255, 0.03); color: var(--text-secondary);
            padding: 12px 14px; text-align: left; font-weight: 600;
            border-bottom: 1px solid var(--border-color);
        }}
        td {{
            padding: 14px; border-bottom: 1px solid var(--border-subtle);
        }}
        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="font-size: 1.85rem; font-weight: 700;">📈 บัญชีกำไรขาดทุนจากการซื้อขาย (Realized Trade Ledger)</h1>
                <p style="color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px;">
                    พอร์ต: <strong>{trades_data.get('portfolio_name')}</strong> | โบรกเกอร์: {trades_data.get('broker')}
                </p>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <button onclick="toggleAllTranches()" style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4); color: #c084fc; padding: 6px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                    <span>🔍</span> <span id="toggleAllBtnText">คลี่ดูรายละเอียดทุกไม้ (Expand All)</span>
                </button>
                <span class="meta-pill">🕒 ข้อมูล ณ: {now_str}</span>
            </div>
        </div>

        <div class="grid-4-cols">
            <div class="card">
                <div class="kpi-label">กำไรขาดทุนสะสม (Net Realized P&L)</div>
                <div class="kpi-value" style="color: {pl_color};">{pl_sign}${summary['total_realized_pl_usd']:,.2f}</div>
                <div class="kpi-subtext" style="color: {pl_color}; font-weight: 600;">{pl_sign}฿{summary['total_realized_pl_thb']:,.2f}</div>
            </div>
            <div class="card">
                <div class="kpi-label">อัตราเทรดชนะ (Win Rate)</div>
                <div class="kpi-value">{summary['win_rate_pct']:.1f}%</div>
                <div class="kpi-subtext">{summary['winning_trades']} ชนะ / {summary['losing_trades']} แพ้ (รวม {summary['total_trades']} ไม้)</div>
            </div>
            <div class="card">
                <div class="kpi-label">ผลตอบแทนเฉลี่ย (Overall ROI)</div>
                <div class="kpi-value" style="color: {pl_color};">{pl_sign}{summary['roi_pct']:.2f}%</div>
                <div class="kpi-subtext">Profit Factor: {summary['profit_factor']:.2f}</div>
            </div>
            <div class="card">
                <div class="kpi-label">เงินรับรวมสุทธิ (Net Proceeds)</div>
                <div class="kpi-value">${summary['total_revenue_usd']:,.2f}</div>
                <div class="kpi-subtext">จากต้นทุนปิดสัญญา ${summary['total_cost_usd']:,.2f}</div>
            </div>
        </div>

        <div class="card" style="padding: 0; overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>วันที่ซื้อ (Buy Date)</th>
                        <th style="text-align: center;">วันที่ขาย</th>
                        <th style="text-align: center;">ระยะถือ</th>
                        <th>หุ้น</th>
                        <th>ชื่อบริษัท / ไม้สะสม</th>
                        <th style="text-align: right;">จำนวนหุ้น</th>
                        <th style="text-align: right;">ราคาซื้อเฉลี่ย</th>
                        <th style="text-align: right;">ราคาขายจริง</th>
                        <th style="text-align: right;">ต้นทุนรวม ($)</th>
                        <th style="text-align: right;">เงินรับสุทธิ ($)</th>
                        <th style="text-align: right;">กำไร ($)</th>
                        <th style="text-align: right;">กำไร (฿)</th>
                        <th style="text-align: right;">% ผลตอบแทน</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    <script>
    function toggleTranche(id) {{
        var row = document.getElementById('details-' + id);
        var icon = document.getElementById('icon-' + id);
        if (!row) return;
        if (row.style.display === 'none' || row.style.display === '') {{
            row.style.display = 'table-row';
            if (icon) icon.innerHTML = '▲';
        }} else {{
            row.style.display = 'none';
            if (icon) icon.innerHTML = '▼';
        }}
    }}

    var allExpanded = false;
    function toggleAllTranches() {{
        var rows = document.querySelectorAll('.tranche-detail-row');
        var btnText = document.getElementById('toggleAllBtnText');
        allExpanded = !allExpanded;
        rows.forEach(function(row) {{
            row.style.display = allExpanded ? 'table-row' : 'none';
            var id = row.id.replace('details-', '');
            var icon = document.getElementById('icon-' + id);
            if (icon) icon.innerHTML = allExpanded ? '▲' : '▼';
        }});
        if (btnText) {{
            btnText.innerText = allExpanded ? 'หุบรายละเอียดทุกไม้ (Collapse All)' : 'คลี่ดูรายละเอียดทุกไม้ (Expand All)';
        }}
    }}
    </script>
    {get_chart_modal_component()}
</body>
</html>
"""
    return html
