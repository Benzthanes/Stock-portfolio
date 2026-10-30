"""
Watchlist Engine & Report Generator (หุ้นที่สนใจ)
Tracks 49 popular growth stocks (48 from Shay Boloor plus SPCX added by the user) against Fibonacci support levels curated by Shay Boloor (Updated 2026-10-17).
Fetches live close, premarket, and postmarket prices from TradingView Scanner API.
"""

import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.nav import nav_bar_html
from src.trades import data_path
from src.universe import resolve_custom_tickers

SOURCE_AUTHOR = "Shay Boloor"
SOURCE_UPDATED = "2026-10-17"

WATCHLIST_STOCKS: List[Dict[str, Any]] = [
    # 1) Space
    {"group": "Space", "ticker": "RKLB", "support": 50.0},
    {"group": "Space", "ticker": "ASTS", "support": 38.0},
    {"group": "Space", "ticker": "PL", "support": 10.0},
    {"group": "Space", "ticker": "RDW", "support": 7.0},
    # Not in Shay Boloor's image: support set by the user on 2026-10-30.
    {"group": "Space", "ticker": "SPCX", "support": 115.0, "source": "ผู้ใช้กำหนดเอง 2026-10-30"},
    # 2) Quantum
    {"group": "Quantum", "ticker": "IONQ", "support": 30.0},
    {"group": "Quantum", "ticker": "RGTI", "support": 11.0},
    {"group": "Quantum", "ticker": "QBTS", "support": 10.0},
    {"group": "Quantum", "ticker": "INFQ", "support": 8.0},
    # 3) Drones
    {"group": "Drones", "ticker": "ONDS", "support": 6.0},
    {"group": "Drones", "ticker": "AVAV", "support": 102.0},
    {"group": "Drones", "ticker": "KTOS", "support": 39.0},
    {"group": "Drones", "ticker": "MRCY", "support": 74.0},
    # 4) Nuclear
    {"group": "Nuclear", "ticker": "OKLO", "support": 27.0},
    {"group": "Nuclear", "ticker": "UUUU", "support": 8.0},
    {"group": "Nuclear", "ticker": "GEV", "support": 678.0},
    {"group": "Nuclear", "ticker": "LEU", "support": 107.0},
    # 5) Photonics
    {"group": "Photonics", "ticker": "AAOI", "support": 61.0},
    {"group": "Photonics", "ticker": "LITE", "support": 765.0},
    {"group": "Photonics", "ticker": "COHR", "support": 224.0},
    {"group": "Photonics", "ticker": "AEHR", "support": 57.0},
    # 6) CPU Bottleneck
    {"group": "CPU Bottleneck", "ticker": "AMD", "support": 479.0},
    {"group": "CPU Bottleneck", "ticker": "INTC", "support": 75.0},
    {"group": "CPU Bottleneck", "ticker": "ARM", "support": 225.0},
    {"group": "CPU Bottleneck", "ticker": "AMKR", "support": 38.0},
    # 7) Physical AI
    {"group": "Physical AI", "ticker": "TSLA", "support": 353.0},
    {"group": "Physical AI", "ticker": "AMZN", "support": 231.0},
    {"group": "Physical AI", "ticker": "GOOGL", "support": 307.0},
    {"group": "Physical AI", "ticker": "VPG", "support": 60.0},
    # 8) AI Utilities
    {"group": "AI Utilities", "ticker": "IREN", "support": 26.0},
    {"group": "AI Utilities", "ticker": "NBIS", "support": 146.0},
    {"group": "AI Utilities", "ticker": "CIFR", "support": 9.0},
    {"group": "AI Utilities", "ticker": "DOCN", "support": 90.0},
    # 9) AI Power
    {"group": "AI Power", "ticker": "ON", "support": 72.0},
    {"group": "AI Power", "ticker": "BE", "support": 192.0},
    {"group": "AI Power", "ticker": "NVTS", "support": 8.0},
    {"group": "AI Power", "ticker": "VRT", "support": 195.0},
    # 10) AI Silicon
    {"group": "AI Silicon", "ticker": "NVDA", "support": 210.0},
    {"group": "AI Silicon", "ticker": "TSM", "support": 398.0},
    {"group": "AI Silicon", "ticker": "ASML", "support": 1637.0},
    {"group": "AI Silicon", "ticker": "MU", "support": 849.0},
    # 11) AI Applications
    {"group": "AI Applications", "ticker": "PLTR", "support": 172.0},
    {"group": "AI Applications", "ticker": "NOW", "support": 124.0},
    {"group": "AI Applications", "ticker": "CRWD", "support": 210.0},
    {"group": "AI Applications", "ticker": "SNOW", "support": 283.0},
    # 12) AI Connectivity
    {"group": "AI Connectivity", "ticker": "AVGO", "support": 324.0},
    {"group": "AI Connectivity", "ticker": "ALAB", "support": 251.0},
    {"group": "AI Connectivity", "ticker": "CRDO", "support": 167.0},
    {"group": "AI Connectivity", "ticker": "MRVL", "support": 222.0},
]


def classify_support_distance(pct_diff: Optional[float]) -> Tuple[str, str]:
    """
    Classify based on distance percentage from Fibonacci support:
    - (ก) ต่ำกว่าแนวรับ: pct_diff < 0.0
    - (ข) 0-5% เหนือแนวรับ: 0.0 <= pct_diff <= 5.0
    - (ค) เกิน 5%: pct_diff > 5.0
    Returns tuple of (code, thai_label).
    """
    if pct_diff is None:
        return ("unknown", "รอข้อมูลราคา")
    if pct_diff < 0.0:
        return ("A", "(ก) ต่ำกว่าแนวรับ")
    elif pct_diff <= 5.0:
        return ("B", "(ข) 0-5% เหนือแนวรับ")
    else:
        return ("C", "(ค) เกิน 5%")


def fetch_watchlist_prices(timeout: int = 15) -> Dict[str, Dict[str, Any]]:
    """
    Fetch market quotes (close, premarket_close, postmarket_close) for all watchlist tickers.
    Returns mapping of {ticker: {column: val}}.
    """
    tickers = [s["ticker"] for s in WATCHLIST_STOCKS]
    symbols = resolve_custom_tickers(tickers)

    url = "https://scanner.tradingview.com/america/scan"
    columns = [
        "name",
        "description",
        "close",
        "premarket_close",
        "premarket_change",
        "postmarket_close",
        "postmarket_change",
    ]
    payload = {
        "symbols": {"tickers": symbols, "query": {"types": []}},
        "columns": columns,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"⚠️ [watchlist] Failed to fetch prices from TradingView: {exc}")
        return {}

    results: Dict[str, Dict[str, Any]] = {}
    for item in data.get("data", []):
        sym_full = item.get("s", "")
        parts = sym_full.split(":", 1)
        ex = parts[0] if len(parts) > 1 else ""
        tk = parts[1] if len(parts) > 1 else sym_full
        d_vals = item.get("d", [])
        row = {"exchange": ex, "symbol_full": sym_full}
        for col_name, val in zip(columns, d_vals):
            row[col_name] = val
        results[tk] = row

    return results


def load_portfolio_holdings_tickers() -> set:
    """Read holdings in data/portfolio.json (read-only) honoring FILTER_STOCK_DATA_DIR."""
    path = data_path("portfolio.json")
    if not path.exists():
        return set()
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
        return {h["ticker"] for h in content.get("holdings", []) if "ticker" in h}
    except Exception as exc:
        print(f"⚠️ [watchlist] Error loading portfolio holdings: {exc}")
        return set()


def analyze_watchlist(
    price_data: Optional[Dict[str, Dict[str, Any]]] = None,
    portfolio_tickers: Optional[set] = None,
) -> Dict[str, Any]:
    """
    Analyze every watchlist stock against Fibonacci support levels.
    Sorts ascending by percentage distance (%ห่างจากแนวรับ ต่ำสุดไปสูงสุด).
    """
    if price_data is None:
        price_data = fetch_watchlist_prices()
    if portfolio_tickers is None:
        portfolio_tickers = load_portfolio_holdings_tickers()

    fetch_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    has_prices = bool(price_data)

    items = []
    group_counts = {"A": 0, "B": 0, "C": 0, "unknown": 0}

    for stock in WATCHLIST_STOCKS:
        tk = stock["ticker"]
        grp = stock["group"]
        supp = stock["support"]
        in_port = tk in portfolio_tickers

        p_info = price_data.get(tk, {}) if price_data else {}
        close = p_info.get("close")
        pm_close = p_info.get("premarket_close")
        post_close = p_info.get("postmarket_close")
        ex = p_info.get("exchange", "")
        desc = p_info.get("description", tk)

        # Pick effective price: premarket > postmarket > close
        price_type = "รอราคา"
        eff_price = None

        if pm_close is not None:
            eff_price = pm_close
            price_type = "Premarket"
        elif post_close is not None:
            eff_price = post_close
            price_type = "Postmarket"
        elif close is not None:
            eff_price = close
            price_type = "ราคาปิด (Close)"

        diff = (eff_price - supp) if eff_price is not None else None
        pct_diff = ((diff / supp) * 100.0) if diff is not None else None

        code, label = classify_support_distance(pct_diff)
        group_counts[code] = group_counts.get(code, 0) + 1

        items.append({
            "ticker": tk,
            "group": grp,
            "name": desc,
            "exchange": ex,
            "support": supp,
            "close": close,
            "premarket_close": pm_close,
            "postmarket_close": post_close,
            "effective_price": eff_price,
            "price_type": price_type,
            "diff": diff,
            "pct_diff": pct_diff,
            "status_code": code,
            "status_label": label,
            "in_portfolio": in_port,
            "source": stock.get("source"),
        })

    # Sort ascending by pct_diff (None goes to the bottom)
    items.sort(key=lambda x: (x["pct_diff"] is None, x["pct_diff"] if x["pct_diff"] is not None else 999999))

    return {
        "fetch_time": fetch_time_str,
        "has_prices": has_prices,
        "source_author": SOURCE_AUTHOR,
        "source_updated": SOURCE_UPDATED,
        "group_counts": group_counts,
        "portfolio_count": sum(1 for it in items if it["in_portfolio"]),
        "total_count": len(items),
        "items": items,
    }


def copy_watchlist_assets(reports_dir: Path) -> Path:
    """Copy shay_fibo_support_2026-10-17.jpeg to reports/assets/."""
    src_img = Path("docs/assets/shay_fibo_support_2026-10-17.jpeg")
    dst_dir = reports_dir / "assets"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_img = dst_dir / "shay_fibo_support_2026-10-17.jpeg"
    if src_img.exists() and (not dst_img.exists() or dst_img.stat().st_size != src_img.stat().st_size):
        shutil.copy2(src_img, dst_img)
    return dst_img


def generate_watchlist_html(
    analyzed: Optional[Dict[str, Any]] = None,
    reports_dir: Optional[Path] = None,
) -> str:
    """Generate modern, luxury dark mode HTML dashboard for the Watchlist page."""
    if analyzed is None:
        analyzed = analyze_watchlist()
    if reports_dir is None:
        reports_dir = Path("reports")

    # Ensure asset image is copied
    copy_watchlist_assets(reports_dir)

    fetch_time = analyzed["fetch_time"]
    has_prices = analyzed["has_prices"]
    items = analyzed["items"]
    counts = analyzed["group_counts"]
    port_count = analyzed["portfolio_count"]
    total = analyzed["total_count"]

    # Navigation bar
    nav_html = nav_bar_html("watchlist")

    # Alert banner when prices could not be fetched
    alert_banner = ""
    if not has_prices:
        alert_banner = """
        <div class="card warning-card" style="border-left: 4px solid var(--rose); margin-bottom: 20px; padding: 14px 18px; background: rgba(244, 63, 94, 0.08); border-radius: 12px; border: 1px solid rgba(244, 63, 94, 0.3);">
            <div style="display: flex; gap: 10px; align-items: center;">
                <span style="font-size: 1.3rem;">⚠️</span>
                <div style="font-size: 0.9rem; color: #fecdd3;">
                    <strong>ไม่สามารถดึงราคาล่าสุดจาก TradingView Scanner API ได้:</strong> ระบบกำลังแสดงเฉพาะแนวรับ Fibonacci อ้างอิงตามตาราง (รอการเชื่อมต่อเพื่ออัปเดตราคา)
                </div>
            </div>
        </div>
        """

    # Build unique groups list for dropdown filter
    all_groups = sorted(list({it["group"] for it in items}))
    group_options = "".join(f'<option value="{escape(g)}">{escape(g)}</option>' for g in all_groups)

    # Build table rows
    table_rows = []
    for it in items:
        tk = it["ticker"]
        grp = it["group"]
        supp = it["support"]
        close = it["close"]
        pm = it["premarket_close"]
        post = it["postmarket_close"]
        eff_px = it["effective_price"]
        px_type = it["price_type"]
        pct_d = it["pct_diff"]
        code = it["status_code"]
        in_port = it["in_portfolio"]

        # Badge for status
        if code == "A":
            status_badge = '<span class="badge badge-rose">🔻 (ก) ต่ำกว่าแนวรับ</span>'
            row_class = "status-a"
        elif code == "B":
            status_badge = '<span class="badge badge-amber">⚠️ (ข) 0-5% เหนือแนวรับ</span>'
            row_class = "status-b"
        elif code == "C":
            status_badge = '<span class="badge badge-emerald">🟢 (ค) เกิน 5%</span>'
            row_class = "status-c"
        else:
            status_badge = '<span class="badge badge-neutral">⚪ รอราคา</span>'
            row_class = "status-unknown"

        # Price formatting
        close_disp = f"${close:.2f}" if close is not None else "-"
        pre_post_disp = "-"
        if pm is not None:
            pre_post_disp = f'<span class="text-blue" title="Premarket">${pm:.2f} <small>(Pre)</small></span>'
        elif post is not None:
            pre_post_disp = f'<span class="text-purple" title="Postmarket">${post:.2f} <small>(Post)</small></span>'

        eff_px_disp = f"${eff_px:.2f}" if eff_px is not None else "-"
        supp_disp = f"${supp:.0f}"

        # % diff formatting
        if pct_d is not None:
            pct_cls = "text-rose fw-bold" if pct_d < 0 else ("text-amber fw-bold" if pct_d <= 5.0 else "text-emerald fw-bold")
            pct_disp = f'<span class="{pct_cls}">{pct_d:+.2f}%</span>'
        else:
            pct_disp = '<span class="text-muted">-</span>'

        # Portfolio tag
        if in_port:
            port_tag = '<span class="badge badge-port" title="มีหุ้นนี้ในพอร์ตจริง (data/portfolio.json)">⭐ มีในพอร์ต</span>'
            port_attr = "true"
        else:
            port_tag = '<span class="text-muted">-</span>'
            port_attr = "false"

        source_tag = (
            f' <span class="text-muted" style="font-size:0.72rem;" title="แนวรับไม่ได้มาจากภาพ {SOURCE_AUTHOR}">✎ {escape(it["source"])}</span>'
            if it.get("source") else ""
        )

        table_rows.append(f"""
        <tr class="stock-row {row_class}" data-group="{escape(grp)}" data-status="{code}" data-portfolio="{port_attr}" data-ticker="{escape(tk)}">
            <td style="white-space: nowrap;">
                <span class="ticker-pill">{tk}</span>{source_tag}
            </td>
            <td style="white-space: nowrap;">
                <span class="group-pill">{escape(grp)}</span>
            </td>
            <td style="text-align: right; white-space: nowrap;" class="text-muted">{close_disp}</td>
            <td style="text-align: right; white-space: nowrap;">{pre_post_disp}</td>
            <td style="text-align: right; white-space: nowrap; font-weight: 600;">{eff_px_disp}</td>
            <td style="text-align: right; white-space: nowrap;" class="text-gold fw-bold">{supp_disp}</td>
            <td style="text-align: right; white-space: nowrap;">{pct_disp}</td>
            <td style="text-align: center; white-space: nowrap;">{status_badge}</td>
            <td style="text-align: center; white-space: nowrap;">{port_tag}</td>
            <td style="text-align: left; white-space: nowrap;" class="text-muted small">{px_type}</td>
        </tr>
        """)

    rows_html = "\n".join(table_rows)

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>หุ้นที่สนใจ (Watchlist Fibo Support) - Filter Stock</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #080d1a;
            --bg-card: #0f172a;
            --bg-card-hover: #1e293b;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-subtle: rgba(255, 255, 255, 0.05);
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --emerald: #10b981;
            --emerald-glow: rgba(16, 185, 129, 0.15);
            --rose: #f43f5e;
            --rose-glow: rgba(244, 63, 94, 0.15);
            --blue: #3b82f6;
            --blue-glow: rgba(59, 130, 246, 0.15);
            --amber: #f59e0b;
            --amber-glow: rgba(245, 158, 11, 0.15);
            --purple: #a855f7;
            --gold: #fbbf24;
            --radius-sm: 8px;
            --radius-md: 14px;
            --radius-lg: 20px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Prompt', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            line-height: 1.6;
            padding: 24px;
            background-image:
                radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.08) 0px, transparent 50%),
                radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.05) 0px, transparent 50%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 20px;
            padding-bottom: 18px;
            border-bottom: 1px solid var(--border-color);
        }}

        .header-title h1 {{
            font-size: 1.75rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .header-meta {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        .meta-pill {{
            background: var(--bg-card);
            padding: 5px 12px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border-color);
        }}

        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 20px;
            margin-bottom: 24px;
        }}

        /* Summary Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .stat-card:hover {{
            background: var(--bg-card-hover);
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.15);
        }}

        .stat-card.active {{
            border-color: var(--blue);
            background: rgba(59, 130, 246, 0.1);
            box-shadow: 0 0 14px var(--blue-glow);
        }}

        .stat-num {{
            font-size: 1.8rem;
            font-weight: 800;
            line-height: 1;
        }}

        .stat-label {{
            font-size: 0.82rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        /* Infographic section */
        .infographic-card {{
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.6) 100%);
            border: 1px solid rgba(59, 130, 246, 0.25);
            border-radius: var(--radius-md);
            padding: 18px 24px;
            margin-bottom: 24px;
        }}

        .thumb-wrap {{
            position: relative;
            flex: 0 0 140px;
            cursor: pointer;
            overflow: hidden;
            border-radius: 8px;
            border: 2px solid rgba(255, 255, 255, 0.15);
            transition: all 0.2s ease;
        }}

        .thumb-wrap:hover {{
            transform: scale(1.03);
            border-color: var(--blue);
            box-shadow: 0 0 15px var(--blue-glow);
        }}

        .thumb-img {{
            width: 100%;
            height: 100px;
            object-fit: cover;
            display: block;
        }}

        .thumb-overlay {{
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 0.75rem;
            font-weight: 600;
            gap: 4px;
            opacity: 0.9;
        }}

        /* Filters Bar */
        .filters-bar {{
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 16px;
            padding: 14px 18px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
        }}

        .filter-btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 6px 14px;
            border-radius: var(--radius-sm);
            font-size: 0.84rem;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.15s ease;
            white-space: nowrap;
        }}

        .filter-btn:hover {{
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-main);
        }}

        .filter-btn.active {{
            background: rgba(59, 130, 246, 0.2);
            border-color: var(--blue);
            color: #60a5fa;
            font-weight: 600;
        }}

        .search-box {{
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: var(--radius-sm);
            font-size: 0.85rem;
            font-family: inherit;
            outline: none;
            width: 180px;
            transition: border-color 0.2s;
        }}

        .search-box:focus {{
            border-color: var(--blue);
        }}

        .select-box {{
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: var(--radius-sm);
            font-size: 0.85rem;
            font-family: inherit;
            outline: none;
            cursor: pointer;
        }}

        /* Table */
        .table-wrap {{
            overflow-x: auto;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            background: var(--bg-card);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            text-align: left;
        }}

        th {{
            background: rgba(15, 23, 42, 0.95);
            color: var(--text-secondary);
            padding: 12px 14px;
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }}

        td {{
            padding: 11px 14px;
            border-bottom: 1px solid var(--border-subtle);
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}

        .ticker-pill {{
            background: rgba(59, 130, 246, 0.12);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.82rem;
            letter-spacing: 0.02em;
        }}

        .group-pill {{
            background: rgba(148, 163, 184, 0.08);
            color: var(--text-secondary);
            border: 1px solid rgba(148, 163, 184, 0.18);
            padding: 2px 7px;
            border-radius: 5px;
            font-size: 0.76rem;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.76rem;
            font-weight: 600;
            white-space: nowrap;
        }}

        .badge-rose {{
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.3);
        }}

        .badge-amber {{
            background: rgba(245, 158, 11, 0.15);
            color: #fcd34d;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}

        .badge-emerald {{
            background: rgba(16, 185, 129, 0.15);
            color: #6ee7b7;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .badge-port {{
            background: rgba(251, 191, 36, 0.15);
            color: #fef08a;
            border: 1px solid rgba(251, 191, 36, 0.4);
            font-weight: 700;
        }}

        .badge-neutral {{
            background: rgba(148, 163, 184, 0.1);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }}

        .text-emerald {{ color: var(--emerald); }}
        .text-rose {{ color: var(--rose); }}
        .text-amber {{ color: var(--amber); }}
        .text-blue {{ color: var(--blue); }}
        .text-purple {{ color: var(--purple); }}
        .text-gold {{ color: var(--gold); }}
        .text-muted {{ color: var(--text-muted); }}
        .fw-bold {{ font-weight: 700; }}
        .small {{ font-size: 0.78rem; }}

        /* Modal / Lightbox for Image */
        .modal-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.88);
            backdrop-filter: blur(4px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 99999;
            padding: 20px;
        }}

        .modal-overlay.open {{
            display: flex;
        }}

        .modal-content {{
            max-width: 90vw;
            max-height: 90vh;
            position: relative;
            background: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            overflow: auto;
            padding: 10px;
        }}

        .modal-img {{
            max-width: 100%;
            max-height: 82vh;
            display: block;
            border-radius: 8px;
            margin: 0 auto;
        }}

        .modal-close {{
            position: absolute;
            top: 14px;
            right: 18px;
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: #fff;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .modal-close:hover {{
            background: var(--rose);
        }}

        @media (max-width: 768px) {{
            body {{ padding: 12px; }}
            .stats-grid {{ grid-template-columns: 1fr 1fr; }}
            .infographic-card {{ flex-direction: column; align-items: flex-start; }}
            .thumb-wrap {{ width: 100%; height: 120px; }}
            .thumb-img {{ height: 120px; }}
            .search-box {{ width: 100%; }}
        }}
    </style>
</head>
<body>
<div class="container">
    {nav_html}

    <div class="header">
        <div class="header-title">
            <h1>📋 หุ้นที่สนใจ (Watchlist Fibo Support)</h1>
        </div>
        <div class="header-meta">
            <span class="meta-pill">🔍 อ้างอิง: <strong>{SOURCE_AUTHOR} ({SOURCE_UPDATED})</strong></span>
            <span class="meta-pill">⏱️ เวลาของราคา: <strong>{fetch_time}</strong></span>
            <span class="meta-pill">📊 ทั้งหมด: <strong>{total} ตัว</strong></span>
        </div>
    </div>

    {alert_banner}

    <!-- Disclaimer / Limitations Callout Box -->
    <div class="card" style="border-left: 4px solid var(--amber); margin-bottom: 24px; padding: 16px 20px; background: rgba(245, 158, 11, 0.05); border-radius: 12px; border: 1px solid rgba(245, 158, 11, 0.25);">
        <div style="display: flex; gap: 12px; align-items: flex-start;">
            <span style="font-size: 1.5rem; line-height: 1;">⚠️</span>
            <div>
                <div style="font-weight: 700; color: #fbbf24; font-size: 0.98rem; margin-bottom: 4px;">
                    ข้อจำกัดและคำเตือนสำคัญ (Risk Disclaimer)
                </div>
                <ul style="margin: 0; padding-left: 18px; color: var(--text-secondary); font-size: 0.86rem; line-height: 1.6;">
                    <li><strong>แนวรับ Fibo จากภาพยังไม่ผ่าน backtest:</strong> เป็นการประเมินโซนราคาทางเทคนิคจากภายนอก ห้ามนำไปใช้เป็นคะแนนในระบบหลัก (Unified Score) และห้ามใช้บล็อกการซื้อขาย</li>
                    <li><strong>สภาพคล่องช่วง Premarket ต่ำ:</strong> ราคาซื้อขายนอกเวลาทำการปกติมีความผันผวนสูงและมี Spread กว้าง โปรดใช้ความระมัดระวัง</li>
                    <li><strong>ไม่ใช่คำแนะนำการลงทุน:</strong> ข้อมูลนี้จัดทำเพื่อการติดตามและศึกษา Risk/Reward เท่านั้น ผู้ลงทุนต้องวิเคราะห์ปัจจัยพื้นฐานและความเสี่ยงด้วยตนเอง</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- Infographic Preview & Source Attribution -->
    <div class="infographic-card">
        <div class="thumb-wrap" onclick="openImageModal()" title="คลิกเพื่อดูภาพต้นฉบับขนาดเต็ม">
            <img src="assets/shay_fibo_support_2026-10-17.jpeg" alt="Shay Boloor Fibo Support" class="thumb-img">
            <div class="thumb-overlay">
                <span>🔍 คลิกขยายภาพ</span>
            </div>
        </div>
        <div style="flex: 1; min-width: 260px;">
            <div style="font-weight: 700; color: #f8fafc; font-size: 1.05rem; margin-bottom: 4px;">
                ภาพต้นฉบับ: คีย์แนวรับ Fibonacci หุ้นเติบโต 12 ธีม
            </div>
            <div style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.5; margin-bottom: 8px;">
                รวบรวมโดย <strong>{SOURCE_AUTHOR}</strong> (อัปเดต 17 ต.ค. 2026) ครอบคลุม 12 ธีมเทคโนโลยี เช่น Space, Quantum, Nuclear, Photonics, AI Silicon, AI Power และ AI Utilities
            </div>
            <button class="filter-btn" onclick="openImageModal()" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.4); color: #93c5fd;">
                🖼️ เปิดดูภาพแนวรับ Fibo ต้นฉบับเต็มจอ
            </button>
        </div>
    </div>

    <!-- Summary Stats Cards -->
    <div class="stats-grid">
        <div class="stat-card" id="card-all" onclick="filterByStatus('all')">
            <div>
                <div class="stat-num text-blue">{total}</div>
                <div class="stat-label">หุ้นทั้งหมดในตาราง</div>
            </div>
            <span style="font-size: 1.6rem;">📋</span>
        </div>
        <div class="stat-card" id="card-a" onclick="filterByStatus('A')">
            <div>
                <div class="stat-num text-rose">{counts.get('A', 0)}</div>
                <div class="stat-label">(ก) ต่ำกว่าแนวรับแล้ว</div>
            </div>
            <span style="font-size: 1.6rem;">🔻</span>
        </div>
        <div class="stat-card" id="card-b" onclick="filterByStatus('B')">
            <div>
                <div class="stat-num text-amber">{counts.get('B', 0)}</div>
                <div class="stat-label">(ข) 0-5% เหนือแนวรับ</div>
            </div>
            <span style="font-size: 1.6rem;">⚠️</span>
        </div>
        <div class="stat-card" id="card-c" onclick="filterByStatus('C')">
            <div>
                <div class="stat-num text-emerald">{counts.get('C', 0)}</div>
                <div class="stat-label">(ค) ยังห่างเกิน 5%</div>
            </div>
            <span style="font-size: 1.6rem;">🟢</span>
        </div>
        <div class="stat-card" id="card-port" onclick="filterByPortfolio()">
            <div>
                <div class="stat-num text-gold">{port_count}</div>
                <div class="stat-label">ตัวที่มีในพอร์ตจริง</div>
            </div>
            <span style="font-size: 1.6rem;">⭐</span>
        </div>
    </div>

    <!-- Filters & Controls Bar -->
    <div class="filters-bar">
        <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center;">
            <span style="font-size: 0.82rem; color: var(--text-secondary); font-weight: 600;">ตัวกรองสถานะ:</span>
            <button class="filter-btn active" id="btn-filter-all" onclick="filterByStatus('all')">ทั้งหมด ({total})</button>
            <button class="filter-btn" id="btn-filter-a" onclick="filterByStatus('A')">ต่ำกว่าแนวรับ ({counts.get('A', 0)})</button>
            <button class="filter-btn" id="btn-filter-b" onclick="filterByStatus('B')">0-5% จ่อรับ ({counts.get('B', 0)})</button>
            <button class="filter-btn" id="btn-filter-c" onclick="filterByStatus('C')">ห่างเกิน 5% ({counts.get('C', 0)})</button>
            <button class="filter-btn" id="btn-filter-port" onclick="filterByPortfolio()">⭐ ในพอร์ตจริง ({port_count})</button>
        </div>

        <div style="display: flex; gap: 10px; margin-left: auto; flex-wrap: wrap; align-items: center;">
            <select class="select-box" id="group-select" onchange="filterByGroup(this.value)">
                <option value="all">ทุกกลุ่มอุตสาหกรรม (12 กลุ่ม)</option>
                {group_options}
            </select>
            <input type="text" class="search-box" id="search-input" placeholder="ค้นหา Ticker..." oninput="handleSearch(this.value)">
        </div>
    </div>

    <!-- Main Table -->
    <div class="table-wrap">
        <table id="stocks-table">
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>กลุ่มอุตสาหกรรม</th>
                    <th style="text-align: right;">ราคาปิด ($)</th>
                    <th style="text-align: right;">ราคา Pre/Post ($)</th>
                    <th style="text-align: right;">ราคาที่ใช้วัด ($)</th>
                    <th style="text-align: right;">แนวรับ Fibo ($)</th>
                    <th style="text-align: right;">% ห่างจากแนวรับ</th>
                    <th style="text-align: center;">สถานะแนวรับ</th>
                    <th style="text-align: center;">พอร์ตจริง</th>
                    <th style="text-align: left;">ประเภทราคา</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>

    <div style="margin-top: 16px; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: var(--text-muted); flex-wrap: wrap; gap: 10px;">
        <div>
            💡 เรียงลำดับจาก % ห่างต่ำสุดไปสูงสุด (ราคาต่ำกว่าแนวรับขึ้นก่อน) | สูตร: <code>((ราคา - แนวรับ) / แนวรับ) * 100</code>
        </div>
        <div id="row-count-display">
            แสดง {total} จาก {total} ตัว
        </div>
    </div>
</div>

<!-- Modal Overlay for Image Zoom -->
<div class="modal-overlay" id="image-modal" onclick="closeImageModal(event)">
    <div class="modal-content" onclick="event.stopPropagation()">
        <button class="modal-close" onclick="closeImageModal()">&times;</button>
        <div style="padding: 10px 10px 14px 10px; color: var(--text-secondary); font-size: 0.85rem; display: flex; justify-content: space-between; align-items: center;">
            <strong style="color: #fff;">🖼️ ภาพต้นฉบับแนวรับ Fibonacci หุ้นเติบโต (Shay Boloor, 17/10/2026)</strong>
            <span>กด ESC หรือคลิกด้านนอกเพื่อปิด</span>
        </div>
        <img src="assets/shay_fibo_support_2026-10-17.jpeg" alt="Fibo Support Large" class="modal-img">
    </div>
</div>

<script>
let currentStatus = 'all';
let currentGroup = 'all';
let currentSearch = '';
let currentPortOnly = false;

function applyFilters() {{
    const rows = document.querySelectorAll('.stock-row');
    let visibleCount = 0;

    rows.forEach(row => {{
        const rowStatus = row.getAttribute('data-status');
        const rowGroup = row.getAttribute('data-group');
        const rowPort = row.getAttribute('data-portfolio') === 'true';
        const rowTicker = row.getAttribute('data-ticker').toLowerCase();

        let matchStatus = (currentStatus === 'all') || (rowStatus === currentStatus);
        if (currentPortOnly) {{
            matchStatus = matchStatus && rowPort;
        }}
        const matchGroup = (currentGroup === 'all') || (rowGroup === currentGroup);
        const matchSearch = (!currentSearch) || (rowTicker.includes(currentSearch));

        if (matchStatus && matchGroup && matchSearch) {{
            row.style.display = '';
            visibleCount++;
        }} else {{
            row.style.display = 'none';
        }}
    }});

    const countDisplay = document.getElementById('row-count-display');
    if (countDisplay) {{
        countDisplay.textContent = `แสดง ${{visibleCount}} จาก ${{rows.length}} ตัว`;
    }}
}}

function filterByStatus(status) {{
    currentStatus = status;
    currentPortOnly = false;

    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));

    if (status === 'all') {{
        document.getElementById('btn-filter-all')?.classList.add('active');
        document.getElementById('card-all')?.classList.add('active');
    }} else if (status === 'A') {{
        document.getElementById('btn-filter-a')?.classList.add('active');
        document.getElementById('card-a')?.classList.add('active');
    }} else if (status === 'B') {{
        document.getElementById('btn-filter-b')?.classList.add('active');
        document.getElementById('card-b')?.classList.add('active');
    }} else if (status === 'C') {{
        document.getElementById('btn-filter-c')?.classList.add('active');
        document.getElementById('card-c')?.classList.add('active');
    }}

    applyFilters();
}}

function filterByPortfolio() {{
    currentPortOnly = !currentPortOnly;
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));

    const btn = document.getElementById('btn-filter-port');
    const card = document.getElementById('card-port');
    if (currentPortOnly) {{
        btn?.classList.add('active');
        card?.classList.add('active');
    }} else {{
        currentStatus = 'all';
        document.getElementById('btn-filter-all')?.classList.add('active');
        document.getElementById('card-all')?.classList.add('active');
    }}
    applyFilters();
}}

function filterByGroup(group) {{
    currentGroup = group;
    applyFilters();
}}

function handleSearch(query) {{
    currentSearch = (query || '').trim().toLowerCase();
    applyFilters();
}}

function openImageModal() {{
    const modal = document.getElementById('image-modal');
    if (modal) modal.classList.add('open');
}}

function closeImageModal(e) {{
    const modal = document.getElementById('image-modal');
    if (modal) modal.classList.remove('open');
}}

document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') closeImageModal();
}});
</script>
</body>
</html>
"""


def generate_watchlist_page(reports_dir: Optional[Path] = None) -> Path:
    """Generate reports/watchlist.html. Returns the Path to the written file."""
    if reports_dir is None:
        reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    analyzed = analyze_watchlist()
    html_content = generate_watchlist_html(analyzed, reports_dir=reports_dir)
    out_file = reports_dir / "watchlist.html"
    out_file.write_text(html_content, encoding="utf-8")
    return out_file


if __name__ == "__main__":
    out = generate_watchlist_page()
    print(f"Generated {out}")
