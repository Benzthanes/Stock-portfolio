#!/usr/bin/env python3
"""
Simulated Dip Portfolio Engine & HTML Dashboard Generator
Tracks simulated dip purchases (paper trading) with fixed THB capital per stock.
Fetches live TradingView data, evaluates TP/SL status, and produces an interactive dashboard.
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tradingview import fetch_screener_data
from src.screener import evaluate_stock
from src.outlook import get_forward_outlook
from src.html_report import get_chart_modal_component


def _make_dip_chart_onclick(p: Dict[str, Any]) -> str:
    ticker = p.get("ticker", "")
    exchange = p.get("exchange", "NASDAQ")
    name = (p.get("name") or ticker).replace("'", "\\'")
    sector = (p.get("business") or "").replace("'", "\\'")
    cost = p.get("buy_price_usd", 0.0)
    price = p.get("close_price", 0.0)
    supp = p.get("sma200", 0.0) or 0.0
    res = p.get("take_profit_usd", 0.0)
    sl = p.get("stop_loss_usd", 0.0)
    tp = p.get("take_profit_usd", 0.0)
    target = p.get("target_avg", 0.0) or 0.0
    return f"openChartModal('{ticker}', '{exchange}', '{name}', '{sector}', {cost}, {price}, {supp}, {res}, {sl}, {tp}, {target})"


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "portfolio_dip_sim.json"
DEFAULT_HTML_PATH = Path(__file__).resolve().parent.parent / "reports" / "portfolio_dip_sim.html"


def load_simulation_data() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Simulation data file not found at {DATA_PATH}")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_simulation_data(data: Dict[str, Any]):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def analyze_simulation(sim_data: Dict[str, Any]) -> Dict[str, Any]:
    holdings = sim_data.get("holdings", [])
    closed_trades = sim_data.get("closed_trades", [])
    fx_rate = float(sim_data.get("fx_rate_usd_thb", 33.62))

    symbols_to_fetch = [f"{h.get('exchange', 'NASDAQ')}:{h['ticker']}" for h in holdings]
    live_rows = fetch_screener_data(symbols_to_fetch)
    live_dict = {r["ticker"]: r for r in live_rows}

    analyzed_positions: List[Dict[str, Any]] = []
    total_capital_thb = 0.0
    total_capital_usd = 0.0
    total_current_val_thb = 0.0
    total_current_val_usd = 0.0

    hit_tp_count = 0
    hit_sl_count = 0
    in_profit_count = 0

    for h in holdings:
        ticker = h["ticker"]
        cap_thb = float(h.get("capital_thb", 10000.0))
        cap_usd = float(h.get("capital_usd", cap_thb / fx_rate))
        buy_price = float(h.get("buy_price_usd", 1.0))
        shares = float(h.get("shares", cap_usd / buy_price))
        sl_price = float(h.get("stop_loss_usd", buy_price * 0.95))
        tp_price = float(h.get("take_profit_usd", buy_price * 1.08))

        live_row = live_dict.get(ticker, {})
        close_price = live_row.get("close") or buy_price
        day_chg_pct = live_row.get("change") or 0.0
        rsi = live_row.get("RSI")
        sma200 = live_row.get("SMA200")
        target_avg = live_row.get("price_target_average")

        current_val_usd = shares * close_price
        current_val_thb = current_val_usd * fx_rate
        unrealized_pl_usd = current_val_usd - cap_usd
        unrealized_pl_thb = current_val_thb - cap_thb
        unrealized_pl_pct = (unrealized_pl_usd / cap_usd * 100.0) if cap_usd > 0 else 0.0

        # TP / SL progress
        tp_span = max(tp_price - sl_price, 0.01)
        progress_pct = max(0.0, min(100.0, (close_price - sl_price) / tp_span * 100.0))
        dist_to_tp_pct = ((tp_price - close_price) / close_price * 100.0) if close_price > 0 else 0.0
        dist_to_sl_pct = ((close_price - sl_price) / close_price * 100.0) if close_price > 0 else 0.0

        if close_price >= tp_price:
            status = "🎯 ถึงเป้าทำกำไร (Hit TP)"
            status_cls = "badge-success"
            hit_tp_count += 1
        elif close_price <= sl_price:
            status = "🛑 แตะจุดยอมแพ้ (Hit SL)"
            status_cls = "badge-danger"
            hit_sl_count += 1
        elif unrealized_pl_pct > 0:
            status = "🟢 วิ่งในแดนบวก (In Profit)"
            status_cls = "badge-info"
            in_profit_count += 1
        else:
            status = "🟡 พักตัวรอดีด (Pullback)"
            status_cls = "badge-warning"

        total_capital_thb += cap_thb
        total_capital_usd += cap_usd
        total_current_val_thb += current_val_thb
        total_current_val_usd += current_val_usd

        # Forward Outlook
        fo = get_forward_outlook(
            ticker=ticker,
            data=live_row,
            fundamentals={
                "rev_growth_yoy": live_row.get("total_revenue_yoy_growth_ttm"),
                "net_inc_growth_yoy": live_row.get("net_income_yoy_growth_ttm"),
                "pe": live_row.get("price_earnings_ttm"),
                "peg": live_row.get("price_earnings_growth_ttm")
            },
            close=close_price
        )

        analyzed_positions.append({
            "ticker": ticker,
            "name": h.get("name", ticker),
            "exchange": h.get("exchange", "NASDAQ"),
            "business": h.get("business", "-"),
            "entry_date": h.get("entry_date", "-"),
            "capital_thb": cap_thb,
            "capital_usd": cap_usd,
            "buy_price_usd": buy_price,
            "shares": shares,
            "close_price": close_price,
            "day_chg_pct": day_chg_pct,
            "rsi": round(rsi, 1) if rsi is not None else None,
            "sma200": round(sma200, 2) if sma200 else None,
            "target_avg": round(target_avg, 2) if target_avg else None,
            "current_val_usd": current_val_usd,
            "current_val_thb": current_val_thb,
            "unrealized_pl_usd": unrealized_pl_usd,
            "unrealized_pl_thb": unrealized_pl_thb,
            "unrealized_pl_pct": unrealized_pl_pct,
            "stop_loss_usd": sl_price,
            "take_profit_usd": tp_price,
            "progress_pct": round(progress_pct, 1),
            "dist_to_tp_pct": round(dist_to_tp_pct, 1),
            "dist_to_sl_pct": round(dist_to_sl_pct, 1),
            "status": status,
            "status_cls": status_cls,
            "strategy_tier": h.get("strategy_tier", "⭐⭐ Good Setup"),
            "setup_reason": h.get("setup_reason", "-"),
            "notes": h.get("notes", "-"),
            "forward_outlook": fo,
            "tv_url": f"https://www.tradingview.com/chart/?symbol={h.get('exchange', 'NASDAQ')}:{ticker}"
        })

    total_pl_usd = total_current_val_usd - total_capital_usd
    total_pl_thb = total_current_val_thb - total_capital_thb
    total_pl_pct = (total_pl_usd / total_capital_usd * 100.0) if total_capital_usd > 0 else 0.0

    return {
        "portfolio_name": sim_data.get("portfolio_name", "พอร์ตจำลองช้อนซื้อหุ้น Dip"),
        "description": sim_data.get("description", ""),
        "created_at": sim_data.get("created_at", "-"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fx_rate": fx_rate,
        "total_capital_thb": total_capital_thb,
        "total_capital_usd": total_capital_usd,
        "total_current_val_thb": total_current_val_thb,
        "total_current_val_usd": total_current_val_usd,
        "total_pl_usd": total_pl_usd,
        "total_pl_thb": total_pl_thb,
        "total_pl_pct": total_pl_pct,
        "holdings_count": len(analyzed_positions),
        "hit_tp_count": hit_tp_count,
        "hit_sl_count": hit_sl_count,
        "in_profit_count": in_profit_count,
        "positions": analyzed_positions,
        "closed_trades": closed_trades,
        "total_realized_usd": sum(t.get("realized_pl_usd", 0.0) for t in closed_trades),
        "total_realized_thb": sum(t.get("realized_pl_thb", 0.0) for t in closed_trades)
    }


def generate_html_report(data: Dict[str, Any]) -> str:
    now_str = data["updated_at"]
    total_pl_thb = data["total_pl_thb"]
    total_pl_usd = data["total_pl_usd"]
    total_pl_pct = data["total_pl_pct"]
    pl_color = "#10b981" if total_pl_thb >= 0 else "#f43f5e"
    pl_sign = "+" if total_pl_thb >= 0 else ""

    # Generate table rows
    rows_html = ""
    for p in data["positions"]:
        p_pl_usd = p["unrealized_pl_usd"]
        p_pl_thb = p["unrealized_pl_thb"]
        p_pl_pct = p["unrealized_pl_pct"]
        c = "#10b981" if p_pl_usd >= 0 else "#f43f5e"
        s = "+" if p_pl_usd >= 0 else ""
        day_c = "#10b981" if p["day_chg_pct"] >= 0 else "#f43f5e"
        day_s = "+" if p["day_chg_pct"] >= 0 else ""

        onclick_js = _make_dip_chart_onclick(p)

        rows_html += f"""
        <tr>
            <td>
                <span class="ticker-link clickable-ticker" onclick="{onclick_js}" style="cursor: pointer;" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{p['ticker']} 📈</span>
                <div class="text-muted small">{p['exchange']}</div>
            </td>
            <td>
                <div style="font-weight: 600;">{p['name']}</div>
                <div class="text-muted small">{p['business']}</div>
            </td>
            <td style="text-align: center; color: var(--text-secondary); font-size: 0.85rem;">{p['entry_date']}</td>
            <td style="text-align: right; font-weight: 600;">
                <div>${p['buy_price_usd']:,.2f}</div>
                <div class="text-muted small">{p['shares']:.4f} หุ้น</div>
            </td>
            <td style="text-align: right; font-weight: 700;">
                <div>${p['close_price']:,.2f}</div>
                <div style="color: {day_c}; font-size: 0.80rem;">{day_s}{p['day_chg_pct']:.2f}%</div>
            </td>
            <td style="text-align: right;">
                <div>฿{p['capital_thb']:,.0f}</div>
                <div class="text-muted small">${p['capital_usd']:,.2f}</div>
            </td>
            <td style="text-align: right;">
                <div style="font-weight: 600;">฿{p['current_val_thb']:,.0f}</div>
                <div class="text-muted small">${p['current_val_usd']:,.2f}</div>
            </td>
            <td style="text-align: right; color: {c}; font-weight: 700;">
                <div>{s}{p_pl_pct:.2f}%</div>
                <div style="font-size: 0.82rem;">{s}฿{p_pl_thb:,.2f} ({s}${p_pl_usd:,.2f})</div>
            </td>
            <td>
                <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 4px;">
                    <span style="color: #f43f5e;">SL: ${p['stop_loss_usd']:,.2f}</span>
                    <span style="color: #10b981;">TP: ${p['take_profit_usd']:,.2f}</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {p['progress_pct']}%;"></div>
                </div>
                <div style="text-align: center; font-size: 0.75rem; color: var(--text-muted); margin-top: 3px;">
                    อีก {p['dist_to_tp_pct']:+.1f}% ถึงเป้า TP
                </div>
            </td>
            <td style="text-align: center;">
                <span class="badge {p['status_cls']}">{p['status']}</span>
            </td>
        </tr>
        """

    # Generate strategy detail cards
    cards_html = ""
    for p in data["positions"]:
        p_pl_usd = p["unrealized_pl_usd"]
        p_pl_thb = p["unrealized_pl_thb"]
        p_pl_pct = p["unrealized_pl_pct"]
        c = "#10b981" if p_pl_usd >= 0 else "#f43f5e"
        s = "+" if p_pl_usd >= 0 else ""

        onclick_js = _make_dip_chart_onclick(p)

        cards_html += f"""
        <div class="card card-item">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div>
                    <span class="ticker-badge clickable-ticker" onclick="{onclick_js}" style="cursor: pointer;" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{p['ticker']} 📈</span>
                    <span style="font-size: 0.95rem; font-weight: 700; margin-left: 8px;">{p['name']}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="badge {p['status_cls']}">{p['status']}</span>
                    <button onclick="{onclick_js}" style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); color: #60a5fa; border-radius: 6px; padding: 4px 10px; font-size: 0.82rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; transition: all 0.2s;">📈 ดูกราฟสด</button>
                </div>
            </div>
            <div style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 14px;">
                {p['business']}
            </div>
            <div class="metric-grid">
                <div class="metric-box">
                    <div class="metric-lbl">ทุนจำลอง (THB)</div>
                    <div class="metric-val">฿{p['capital_thb']:,.0f}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-lbl">ต้นทุนเข้าซื้อ</div>
                    <div class="metric-val">${p['buy_price_usd']:,.2f}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-lbl">ราคาตลาดสด</div>
                    <div class="metric-val">${p['close_price']:,.2f}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-lbl">กำไร/ขาดทุน</div>
                    <div class="metric-val" style="color: {c};">{s}{p_pl_pct:.2f}% ({s}฿{p_pl_thb:,.1f})</div>
                </div>
            </div>
            <div style="margin-top: 10px; background: rgba(59, 130, 246, 0.06); border-left: 3px solid var(--blue); padding: 8px 12px; border-radius: 4px;">
                <div style="font-size: 0.75rem; color: #60a5fa; font-weight: 700; margin-bottom: 2px;">🔭 วิสัยทัศน์ & ธีมการเติบโต ({p.get('forward_outlook', {}).get('quality_badge', '🔵 Strategic Dip Pick')}):</div>
                <div style="font-size: 0.82rem; color: #e2e8f0; line-height: 1.35;">{p.get('forward_outlook', {}).get('thesis_title', '-')}</div>
            </div>
            <div style="margin-top: 14px; background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--border-subtle);">
                <div style="font-size: 0.82rem; color: var(--amber); font-weight: 600; margin-bottom: 4px;">
                    🎯 กลยุทธ์ช้อนซื้อ: {p['strategy_tier']}
                </div>
                <div style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 6px;">
                    💡 <strong>เหตุผลที่เข้าซื้อ:</strong> {p['setup_reason']}
                </div>
                <div style="font-size: 0.80rem; color: var(--text-muted);">
                    🛡️ จุดตัดขาดทุน SL: <strong>${p['stop_loss_usd']:,.2f}</strong> | 🎯 จุดทำกำไร TP: <strong>${p['take_profit_usd']:,.2f}</strong>
                </div>
            </div>
        </div>
        """

    # Generate closed trades rows
    closed_rows_html = ""
    for t in data.get("closed_trades", []):
        r_pl_u = t.get("realized_pl_usd", 0.0)
        r_pl_t = t.get("realized_pl_thb", 0.0)
        r_pl_pct = t.get("realized_pl_pct", 0.0)
        c = "#10b981" if r_pl_u >= 0 else "#f43f5e"
        s = "+" if r_pl_u >= 0 else ""
        t_name_js = (t.get('name') or t['ticker']).replace("'", "\\'")
        t_click_js = f"openChartModal('{t['ticker']}', '{t.get('exchange', 'NYSE')}', '{t_name_js}', 'Closed Position', {t.get('buy_price_usd', 0)}, {t.get('exit_price_usd', 0)}, 0, 0, {t.get('exit_price_usd', 0)}, 0, 0)"

        closed_rows_html += f"""
        <tr>
            <td style="font-weight: 700; color: #fff; font-family: 'Inter', sans-serif;">
                <span class="clickable-ticker" onclick=\"{t_click_js}\" style="background: rgba(244, 63, 94, 0.15); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;" title="คลิกเปิดดูกราฟเทคนิคัล">{t['ticker']} 📈</span>
            </td>
            <td>
                <div style="font-weight: 600;">{t['name']}</div>
                <div class="text-muted small">{t.get('exit_reason', '-')}</div>
            </td>
            <td style="text-align: center; color: var(--text-secondary); font-size: 0.85rem;">{t.get('entry_date', '-')}</td>
            <td style="text-align: center; color: var(--rose); font-size: 0.85rem; font-weight: 600;">{t.get('exit_date', '-')} ({t.get('holding_days', '-')} วัน)</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">${t.get('buy_price_usd', 0):,.2f}</td>
            <td style="text-align: right; font-weight: 600; color: var(--rose); font-family: 'Inter', sans-serif;">${t.get('exit_price_usd', 0):,.2f}</td>
            <td style="text-align: right; font-family: 'Inter', sans-serif;">฿{t.get('capital_thb', 0):,.0f}</td>
            <td style="text-align: right; font-weight: 600; font-family: 'Inter', sans-serif;">฿{t.get('net_revenue_thb', 0):,.0f}</td>
            <td style="text-align: right; color: {c}; font-weight: 700; font-family: 'Inter', sans-serif;">{s}฿{r_pl_t:,.2f} ({s}${r_pl_u:,.2f})</td>
            <td style="text-align: right; color: {c}; font-weight: 700; font-family: 'Inter', sans-serif;">{s}{r_pl_pct:.2f}%</td>
            <td style="text-align: center;"><span class="badge badge-danger">ตัดขาดทุนตาม SL</span></td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['portfolio_name']} (ตัวละ ฿10,000)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #070b14;
            --bg-card: #0d1527;
            --bg-card-subtle: #111c34;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-subtle: rgba(255, 255, 255, 0.04);
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --emerald: #10b981;
            --rose: #f43f5e;
            --blue: #3b82f6;
            --amber: #f59e0b;
            --purple: #8b5cf6;
            --cyan: #06b6d4;
            --radius-sm: 8px;
            --radius-md: 14px;
            --radius-lg: 18px;
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
        .container {{ max-width: 1440px; margin: 0 auto; }}
        .header {{
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 16px; margin-bottom: 24px; padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }}
        .nav-links {{
            display: flex; gap: 10px; flex-wrap: wrap;
        }}
        .nav-pill {{
            padding: 8px 16px; border-radius: var(--radius-sm); font-size: 0.88rem;
            text-decoration: none; color: var(--text-secondary); background: var(--bg-card);
            border: 1px solid var(--border-color); transition: all 0.2s;
        }}
        .nav-pill:hover {{
            color: var(--text-main); border-color: var(--blue);
        }}
        .nav-pill.active {{
            background: rgba(59, 130, 246, 0.15); color: #60a5fa; border-color: var(--blue); font-weight: 600;
        }}
        .meta-pill {{
            background: var(--bg-card); padding: 8px 16px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-color); font-size: 0.88rem; color: var(--text-secondary);
        }}
        .grid-4-cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .grid-3-cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .card {{
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: var(--radius-md); padding: 22px;
        }}
        .kpi-label {{ font-size: 0.82rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; }}
        .kpi-value {{ font-size: 1.95rem; font-weight: 700; font-family: 'Inter', sans-serif; }}
        .kpi-subtext {{ font-size: 0.88rem; color: var(--text-muted); margin-top: 6px; }}
        .section-title {{
            font-size: 1.25rem; font-weight: 700; margin-bottom: 16px;
            display: flex; align-items: center; gap: 10px;
        }}
        table {{
            width: 100%; border-collapse: collapse; font-size: 0.90rem;
        }}
        th {{
            background: rgba(255, 255, 255, 0.03); color: var(--text-secondary);
            padding: 12px 14px; text-align: left; font-weight: 600;
            border-bottom: 1px solid var(--border-color); font-size: 0.82rem; text-transform: uppercase;
        }}
        td {{
            padding: 14px; border-bottom: 1px solid var(--border-subtle); vertical-align: middle;
        }}
        tr:hover td {{ background: rgba(255, 255, 255, 0.015); }}
        .ticker-link {{
            color: #60a5fa; font-weight: 700; text-decoration: none; font-family: 'Inter', sans-serif;
        }}
        .ticker-link:hover {{ text-decoration: underline; }}
        .ticker-badge {{
            background: rgba(59, 130, 246, 0.15); color: #60a5fa; padding: 4px 10px;
            border-radius: 6px; font-weight: 700; font-family: 'Inter', sans-serif; font-size: 0.90rem;
        }}
        .badge {{
            display: inline-block; padding: 4px 10px; border-radius: 6px;
            font-size: 0.78rem; font-weight: 600; text-align: center; white-space: nowrap;
        }}
        .badge-success {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
        .badge-danger {{ background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .badge-info {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
        .progress-bar-bg {{
            background: rgba(255, 255, 255, 0.08); border-radius: 6px; height: 8px; width: 100%; overflow: hidden;
        }}
        .progress-bar-fill {{
            background: linear-gradient(90deg, #f43f5e, #f59e0b, #10b981); height: 100%; border-radius: 6px;
        }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
        .metric-box {{
            background: rgba(255, 255, 255, 0.02); padding: 10px; border-radius: 8px;
            border: 1px solid var(--border-subtle);
        }}
        .metric-lbl {{ font-size: 0.75rem; color: var(--text-muted); margin-bottom: 2px; }}
        .metric-val {{ font-size: 1.05rem; font-weight: 700; font-family: 'Inter', sans-serif; }}
        .card-item {{
            transition: transform 0.2s, border-color 0.2s;
        }}
        .card-item:hover {{
            transform: translateY(-2px); border-color: rgba(255, 255, 255, 0.15);
        }}
        .text-muted {{ color: var(--text-muted); }}
        .small {{ font-size: 0.80rem; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <div>
                <h1 style="font-size: 1.75rem; font-weight: 800; display: flex; align-items: center; gap: 12px;">
                    <span>🧪</span> {data['portfolio_name']}
                </h1>
                <div style="color: var(--text-secondary); margin-top: 4px; font-size: 0.92rem;">
                    {data['description']} | เงินลงทุนจำลองคงที่ตัวละ <strong>฿10,000.00 THB</strong>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 10px;">
                <div class="nav-links">
                    <a href="portfolio_master.html" class="nav-pill">🏛️ พอร์ตหลักความมั่งคั่ง</a>
                    <a href="portfolio_review.html" class="nav-pill">🏥 ตรวจสุขภาพพอร์ต</a>
                    <a href="portfolio_dip_sim.html" class="nav-pill active">🧪 พอร์ตจำลองช้อนซื้อ Dip</a>
                </div>
                <div class="meta-pill">
                    อัปเดตราคาล่าสุด: <strong style="color: var(--text-main);">{now_str}</strong> | FX: {data['fx_rate']:.2f} THB/USD
                </div>
            </div>
        </div>

        <!-- KPI SUMMARY CARDS -->
        <div class="grid-4-cols">
            <div class="card" style="border-left: 4px solid var(--blue);">
                <div class="kpi-label">เงินทุนจำลองรวม (Total Capital)</div>
                <div class="kpi-value">฿{data['total_capital_thb']:,.2f}</div>
                <div class="kpi-subtext">~${data['total_capital_usd']:,.2f} USD ({data['holdings_count']} หุ้น x ฿10,000)</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--cyan);">
                <div class="kpi-label">มูลค่าพอร์ตจำลองปัจจุบัน (Simulated NAV)</div>
                <div class="kpi-value">฿{data['total_current_val_thb']:,.2f}</div>
                <div class="kpi-subtext">~${data['total_current_val_usd']:,.2f} USD</div>
            </div>
            <div class="card" style="border-left: 4px solid {pl_color};">
                <div class="kpi-label">กำไร/ขาดทุนจำลองรวม (Simulated P/L)</div>
                <div class="kpi-value" style="color: {pl_color};">{pl_sign}฿{total_pl_thb:,.2f}</div>
                <div class="kpi-subtext" style="color: {pl_color}; font-weight: 700;">{pl_sign}{total_pl_pct:.2f}% ({pl_sign}${total_pl_usd:,.2f} USD)</div>
            </div>
            <div class="card" style="border-left: 4px solid var(--purple);">
                <div class="kpi-label">สถานะการเทรดจำลอง (Trade Progress)</div>
                <div class="kpi-value" style="font-size: 1.55rem; color: #a855f7;">{data['in_profit_count']}/{data['holdings_count']} แดนบวก</div>
                <div class="kpi-subtext">ชน TP: {data['hit_tp_count']} | ชน SL: {data['hit_sl_count']}</div>
            </div>
        </div>

        <!-- SECTION 1: SIMULATION HOLDINGS TABLE -->
        <div style="margin-bottom: 32px;">
            <div class="section-title">
                <span>📊</span> 1. ตารางจำลองการถือครองหุ้น Dip รายตัว (ราคาตลาดสดจาก TradingView)
                <span class="badge badge-info">{data['holdings_count']} หุ้น</span>
            </div>
            <div class="card" style="padding: 0; overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>บริษัท & ลักษณะธุรกิจ</th>
                            <th style="text-align: center;">วันที่จำลองซื้อ</th>
                            <th style="text-align: right;">ต้นทุนเข้าซื้อ ($)</th>
                            <th style="text-align: right;">ราคาตลาดสด ($)</th>
                            <th style="text-align: right;">เงินลงทุน (฿ / $)</th>
                            <th style="text-align: right;">มูลค่าปัจจุบัน (฿ / $)</th>
                            <th style="text-align: right;">กำไร/ขาดทุนจำลอง</th>
                            <th style="min-width: 170px;">แถบวัดเป้าหมาย (SL ↔ TP)</th>
                            <th style="text-align: center;">สถานะ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 1.5: CLOSED TRADES / STOP-LOSS EXECUTIONS -->
        {f'''
        <div style="margin-bottom: 32px;">
            <div class="section-title">
                <span>🛑</span> รายการที่แตะจุดยอมแพ้และขายตัดขาดทุนจำลองแล้ว (Closed Trades: {len(data.get('closed_trades', []))} ตัว)
                <span class="badge badge-danger">ขายตัดขาดทุนตามวินัย Stop-Loss</span>
            </div>
            <div class="card" style="padding: 0; overflow-x: auto; border-left: 4px solid var(--rose);">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>บริษัท & เหตุผลการขาย</th>
                            <th style="text-align: center;">วันที่ซื้อ</th>
                            <th style="text-align: center;">วันที่ขาย</th>
                            <th style="text-align: right;">ราคาซื้อ ($)</th>
                            <th style="text-align: right;">ราคาขาย ($)</th>
                            <th style="text-align: right;">ทุน (฿)</th>
                            <th style="text-align: right;">ยอดรับสุทธิ (฿)</th>
                            <th style="text-align: right;">ผลขาดทุนจริง</th>
                            <th style="text-align: right;">% ผลขาดทุน</th>
                            <th style="text-align: center;">สถานะ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {closed_rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        ''' if closed_rows_html else ''}

        <!-- SECTION 2: TRADE STRATEGY CARDS -->
        <div style="margin-bottom: 32px;">
            <div class="section-title">
                <span>🎯</span> 2. รายละเอียดกลยุทธ์และเหตุผลการช้อนซื้อของแต่ละตัว
            </div>
            <div class="grid-3-cols">
                {cards_html}
            </div>
        </div>

        <!-- SECTION 3: RULES & PHILOSOPHY -->
        <div class="card" style="background: rgba(13, 21, 39, 0.6); border: 1px dashed var(--border-color); margin-bottom: 32px;">
            <h3 style="font-size: 1.1rem; margin-bottom: 12px; color: var(--amber);">
                💡 วัตถุประสงค์และกติกาของพอร์ตจำลอง Dip นี้ (Paper Trading Rules)
            </h3>
            <ul style="padding-left: 20px; color: var(--text-secondary); font-size: 0.90rem; line-height: 1.8;">
                <li><strong>เงินทุนเท่ากันทุกตัว:</strong> กำหนดเงินลงทุนจำลองคงที่ตัวละ ฿10,000 เพื่อวัดผลตอบแทนอย่างเที่ยงตรงโดยไม่ให้น้ำหนักตัวใดตัวหนึ่งเบี่ยงเบน.</li>
                <li><strong>แยกขาดจากพอร์ตจริง:</strong> ตัวเลขในหน้านี้เป็นข้อมูลทดลองเชิงสถิติ จะไม่ถูกนำไปนับรวมในพอร์ตหลัก Dime! ของคุณ.</li>
                <li><strong>ทดสอบวินัย Take-Profit และ Stop-Loss:</strong> บันทึกจุด Stop Loss ที่ 1.5 ATR และเป้าทำกำไรที่เส้น 50 วัน เพื่อพิสูจน์ว่าในระยะยาวอัตรา Win Rate และ Risk-to-Reward จะเป็นบวกจริงตามหลักคณิตศาสตร์.</li>
                <li><strong>สามารถกลับมาเปิดดูเพื่อประเมินผลได้ตลอดเวลา:</strong> ระบบจะเชื่อมโยงราคาตลาดสดจาก TradingView API เสมอ.</li>
            </ul>
        </div>

        <div style="text-align: center; color: var(--text-muted); font-size: 0.82rem; padding: 20px 0; border-top: 1px solid var(--border-subtle);">
            Simulated Dip Paper Trading Engine | Developed with TradingView Screener live scanner API | All data is purely for educational simulation.
        </div>
    </div>
    {get_chart_modal_component()}
</body>
</html>
"""
    return html


def add_sim_holding(ticker: str, capital_thb: float = 10000.0, notes: str = "") -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    sim_data = load_simulation_data()
    fx_rate = float(sim_data.get("fx_rate_usd_thb", 33.62))

    from src.universe import resolve_custom_tickers
    from src.profiles import get_business_summary

    symbols = resolve_custom_tickers([ticker])
    live_rows = fetch_screener_data(symbols)
    if not live_rows:
        raise ValueError(f"ไม่พบข้อมูลตลาดสำหรับหุ้น {ticker}")

    live_row = live_rows[0]
    close_price = live_row.get("close")
    if not close_price:
        raise ValueError(f"ไม่สามารถดึงราคาล่าสุดของ {ticker} ได้")

    name = live_row.get("description") or live_row.get("name") or ticker
    exchange = symbols[0].split(":")[0] if ":" in symbols[0] else "NASDAQ"
    business = get_business_summary(ticker, live_row.get("description"))

    cap_usd = capital_thb / fx_rate
    shares = round(cap_usd / close_price, 4)

    atr = live_row.get("ATR")
    if atr and atr > 0:
        sl_price = round(close_price - 1.5 * atr, 2)
    else:
        sl_price = round(close_price * 0.94, 2)

    sma50 = live_row.get("SMA50")
    if sma50 and sma50 > close_price:
        tp_price = round(sma50, 2)
    else:
        tp_price = round(close_price * 1.08, 2)

    rsi = live_row.get("RSI")
    rsi_str = f"Daily RSI {rsi:.1f}" if rsi is not None else "Dip Setup"
    setup_reason = f"{rsi_str} + ซื้อที่ราคาตลาด ${close_price:,.2f}"

    new_holding = {
        "id": f"dip-{int(datetime.now().timestamp())}",
        "ticker": ticker,
        "name": name,
        "exchange": exchange,
        "business": business,
        "entry_date": datetime.now().strftime("%Y-%m-%d"),
        "capital_thb": capital_thb,
        "capital_usd": round(cap_usd, 2),
        "buy_price_usd": round(close_price, 2),
        "shares": shares,
        "stop_loss_usd": sl_price,
        "take_profit_usd": tp_price,
        "strategy_tier": "⭐⭐⭐ Manual Dip Pick",
        "setup_reason": setup_reason,
        "notes": notes or f"เลือกช้อนซื้อจำลองตัวละ ฿{capital_thb:,.0f}"
    }

    sim_data["holdings"] = [h for h in sim_data.get("holdings", []) if h.get("ticker") != ticker]
    sim_data["holdings"].append(new_holding)
    save_simulation_data(sim_data)
    return new_holding


def remove_sim_holding(ticker: str) -> bool:
    ticker = ticker.upper().strip()
    sim_data = load_simulation_data()
    orig_len = len(sim_data.get("holdings", []))
    sim_data["holdings"] = [h for h in sim_data.get("holdings", []) if h.get("ticker") != ticker]
    if len(sim_data["holdings"]) < orig_len:
        save_simulation_data(sim_data)
        return True
    return False


def reset_sim_holdings():
    sim_data = load_simulation_data()
    sim_data["holdings"] = []
    save_simulation_data(sim_data)


def main():
    parser = argparse.ArgumentParser(description="Simulated Dip Portfolio Generator")
    parser.add_argument("--save-html", type=str, default=str(DEFAULT_HTML_PATH), help="Path to save HTML dashboard")
    parser.add_argument("--json", action="store_true", help="Output JSON analysis")
    parser.add_argument("--buy", "-b", type=str, help="Add/Buy a stock ticker into simulated dip portfolio (e.g. --buy BNY)")
    parser.add_argument("--capital", type=float, default=10000.0, help="Capital in THB for simulated purchase (default: 10000)")
    parser.add_argument("--notes", type=str, default="", help="Custom notes for simulated purchase")
    parser.add_argument("--sell", "-s", type=str, help="Remove/Sell a stock ticker from simulated dip portfolio (e.g. --sell JPM)")
    parser.add_argument("--reset", action="store_true", help="Clear all simulated holdings")
    args = parser.parse_args()

    if args.reset:
        reset_sim_holdings()
        print("ล้างพอร์ตจำลอง Dip เรียบร้อยแล้ว (0 รายการ)")

    if args.sell:
        if remove_sim_holding(args.sell):
            print(f"ขาย/ลบหุ้น {args.sell.upper()} ออกจากพอร์ตจำลองเรียบร้อยแล้ว")
        else:
            print(f"ไม่พบหุ้น {args.sell.upper()} ในพอร์ตจำลอง", file=sys.stderr)

    if args.buy:
        try:
            h = add_sim_holding(args.buy, args.capital, args.notes)
            print(f"เข้าซื้อจำลอง {h['ticker']} เรียบร้อย!")
            print(f"  - ชื่อบริษัท : {h['name']} ({h['business']})")
            print(f"  - ราคาเข้าซื้อ: ${h['buy_price_usd']:,.2f} USD")
            print(f"  - จำนวนหุ้น : {h['shares']:.4f} หุ้น (งบ ฿{h['capital_thb']:,.0f} ~ ${h['capital_usd']:,.2f})")
            print(f"  - จุดตัดขาดทุน SL : ${h['stop_loss_usd']:,.2f} USD")
            print(f"  - จุดทำกำไร TP  : ${h['take_profit_usd']:,.2f} USD")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการซื้อจำลอง {args.buy}: {e}", file=sys.stderr)
            sys.exit(1)

    sim_data = load_simulation_data()
    analyzed = analyze_simulation(sim_data)

    if args.json:
        print(json.dumps(analyzed, indent=2, ensure_ascii=False))
        return

    html_content = generate_html_report(analyzed)
    out_path = Path(args.save_html)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_content, encoding="utf-8")

    print(f"==========================================================================")
    print(f" SIMULATED DIP PORTFOLIO REPORT GENERATED")
    print(f"==========================================================================")
    print(f"Holdings Count       : {analyzed['holdings_count']} stocks")
    print(f"Total Capital (THB)  : ฿{analyzed['total_capital_thb']:,.2f} (${analyzed['total_capital_usd']:,.2f} USD)")
    print(f"Current Value (THB)  : ฿{analyzed['total_current_val_thb']:,.2f} (${analyzed['total_current_val_usd']:,.2f} USD)")
    pl_sign = "+" if analyzed['total_pl_thb'] >= 0 else ""
    print(f"Simulated P/L        : {pl_sign}฿{analyzed['total_pl_thb']:,.2f} ({pl_sign}{analyzed['total_pl_pct']:.2f}%)")
    print(f"HTML Dashboard       : {out_path.resolve()}")
    print(f"==========================================================================")


if __name__ == "__main__":
    main()
