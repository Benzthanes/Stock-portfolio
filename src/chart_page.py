"""
Standalone Technical Chart & Rule-based Confluence Decision Page Generator.
Generates a full-page, non-overlay, high-performance interactive charting dashboard
saved to reports/stock_chart.html.
"""

import json
import sys
from html import escape
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.chart_data import (
    compact_charts_for_page,
    load_candles_cache,
    save_candles_cache,
    compute_fibo_and_indicators,
    INDICATOR_SCHEMA_VERSION,
    EARNINGS_CALENDAR_HASH,
    get_super_investors,
)
from src.scoring import EARNINGS_GUARD_DAYS, ETF_TICKERS
from src.nav import nav_bar_html

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def render_chart_template(values: Dict[str, str]) -> str:
    html = (TEMPLATES_DIR / "chart.html").read_text(encoding="utf-8")
    html = html.replace("__CHART_CSS__", (TEMPLATES_DIR / "chart.css").read_text(encoding="utf-8"), 1)
    html = html.replace("__CHART_JS__", (TEMPLATES_DIR / "chart.js").read_text(encoding="utf-8"), 1)
    for marker, value in values.items():
        html = html.replace(marker, value)
    return html


def get_all_stocks_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Collects rich metadata (name, sector, exchange, cost, price, levels, shares)
    across portfolio holdings, simulation holdings, and trade records.
    """
    meta: Dict[str, Dict[str, Any]] = {}

    # Well-known fallback names for popular US equities
    KNOWN_NAMES = {
        "NVDA": ("NVIDIA Corporation", "Semiconductors", "NASDAQ"),
        "AAPL": ("Apple Inc.", "Consumer Electronics", "NASDAQ"),
        "MSFT": ("Microsoft Corporation", "Software Infrastructure", "NASDAQ"),
        "AMZN": ("Amazon.com, Inc.", "Internet Retail", "NASDAQ"),
        "GOOGL": ("Alphabet Inc. Class A", "Internet Content & Information", "NASDAQ"),
        "PLTR": ("Palantir Technologies Inc.", "Software Infrastructure", "NASDAQ"),
        "LLY": ("Eli Lilly and Company", "Pharmaceuticals", "NYSE"),
        "ISRG": ("Intuitive Surgical, Inc.", "Medical Instruments", "NASDAQ"),
        "BMY": ("Bristol-Myers Squibb Company", "Pharmaceuticals", "NYSE"),
        "JPM": ("JPMorgan Chase & Co.", "Diversified Banking", "NYSE"),
        "CRWD": ("CrowdStrike Holdings, Inc.", "Cybersecurity Software", "NASDAQ"),
        "BNY": ("Bank of New York Mellon Corp", "Asset Management", "NYSE"),
        "SPCX": ("SpaceX (Space Exploration Technologies)", "Aerospace & Satellite Internet", "NASDAQ"),
        "QQQI": ("NEOS Nasdaq 100 High Income ETF", "High Yield ETF", "NASDAQ"),
        "ROST": ("Ross Stores, Inc.", "Apparel Retail", "NASDAQ"),
        "NOK": ("Nokia Corporation", "Telecom Equipment", "NYSE"),
        "AMAT": ("Applied Materials, Inc.", "Semiconductor Equipment", "NASDAQ"),
        "LRCX": ("Lam Research Corporation", "Semiconductor Equipment", "NASDAQ"),
        "MU": ("Micron Technology, Inc.", "Memory Semiconductors", "NASDAQ"),
        "ARM": ("Arm Holdings plc", "Semiconductor IP", "NASDAQ"),
        "JNJ": ("Johnson & Johnson", "Pharmaceuticals & Healthcare", "NYSE"),
        "VOO": ("Vanguard S&P 500 ETF", "Index ETF", "AMEX"),
        "MNST": ("Monster Beverage Corp", "Non-Alcoholic Beverages", "NASDAQ"),
        "INTC": ("Intel Corporation", "Semiconductors", "NASDAQ"),
        "VRT": ("Vertiv Holdings Co", "Data Center Infrastructure", "NYSE"),
        "NOW": ("ServiceNow, Inc.", "Enterprise Software", "NYSE"),
        "C": ("Citigroup Inc.", "Diversified Banking", "NYSE"),
        "BAC": ("Bank of America Corporation", "Diversified Banking", "NYSE"),
        "VRTX": ("Vertex Pharmaceuticals Inc.", "Biotechnology", "NASDAQ"),
        "ABNB": ("Airbnb, Inc.", "Travel Services", "NASDAQ"),
        "APP": ("AppLovin Corporation", "Application Software", "NASDAQ"),
        "VST": ("Vistra Corp.", "Independent Power Producers", "NYSE"),
        "SKHY": ("SK hynix Inc. American Depositary Shares", "Memory Semiconductors", "NASDAQ"),
    }

    # 1. From portfolio.json
    p_path = Path("data/portfolio.json")
    if p_path.exists():
        try:
            p_data = json.loads(p_path.read_text(encoding="utf-8"))
            for h in p_data.get("holdings", []):
                t = h["ticker"]
                meta[t] = {
                    "ticker": t,
                    "name": h.get("name", KNOWN_NAMES.get(t, (t, "", "NASDAQ"))[0]),
                    "sector": h.get("sector", KNOWN_NAMES.get(t, (t, "", "NASDAQ"))[1]),
                    "exchange": h.get("exchange", KNOWN_NAMES.get(t, (t, "", "NASDAQ"))[2]),
                    "cost": (h.get("avg_cost_usd") or 0.0),
                    "shares": (h.get("shares") or 0.0),
                    "total_cost": (h.get("total_cost_usd") or 0.0),
                    "cost_thb": (h.get("cost_thb") or 0.0),
                    "is_holding": True,
                    "price": (h.get("close_price") or 0.0),
                    "support": (h.get("key_support") or 0.0),
                    "resistance": (h.get("key_resistance") or 0.0),
                    "sl": (h.get("stop_loss") or 0.0),
                    "tp": (h.get("take_profit") or 0.0),
                    "target": (h.get("price_target_average") or 0.0),
                    "days_to_earnings": None,
                    "earnings_date": "-",
                    "is_earnings_near": False,
                    "earnings_guard_days": EARNINGS_GUARD_DAYS,
                }
        except Exception:
            pass

    # 2. From portfolio_dip_sim.json
    d_path = Path("data/portfolio_dip_sim.json")
    if d_path.exists():
        try:
            d_data = json.loads(d_path.read_text(encoding="utf-8"))
            for h in d_data.get("holdings", []):
                t = h["ticker"]
                if t not in meta:
                    meta[t] = {
                        "ticker": t,
                        "name": h.get("name", KNOWN_NAMES.get(t, (t, "", "NASDAQ"))[0]),
                        "sector": h.get("sector", KNOWN_NAMES.get(t, (t, "", "NASDAQ"))[1]),
                        "exchange": h.get("exchange", KNOWN_NAMES.get(t, (t, "", "NASDAQ"))[2]),
                        "cost": (h.get("avg_cost_usd") or 0.0),
                        "shares": (h.get("shares") or 0.0),
                        "total_cost": (h.get("total_cost_usd") or 0.0),
                        "cost_thb": 0.0,
                        "is_holding": False,
                        "price": (h.get("close_price") or 0.0),
                        "support": (h.get("key_support") or 0.0),
                        "resistance": (h.get("key_resistance") or 0.0),
                        "sl": (h.get("stop_loss") or 0.0),
                        "tp": (h.get("take_profit") or 0.0),
                        "target": (h.get("price_target_average") or 0.0),
                        "days_to_earnings": None,
                        "earnings_date": "-",
                        "is_earnings_near": False,
                        "earnings_guard_days": EARNINGS_GUARD_DAYS,
                    }
        except Exception:
            pass

    # 3. From trades.json
    t_path = Path("data/trades.json")
    if t_path.exists():
        try:
            t_data = json.loads(t_path.read_text(encoding="utf-8"))
            for tr in t_data.get("trades", []):
                t = tr["ticker"]
                if t not in meta:
                    meta[t] = {
                        "ticker": t,
                        "name": KNOWN_NAMES.get(t, (tr.get("name", t), "", "NASDAQ"))[0],
                        "sector": "Closed / Realized Trade",
                        "exchange": KNOWN_NAMES.get(t, (t, "", tr.get("exchange", "NASDAQ")))[2],
                        "cost": tr.get("buy_price_usd", 0.0),
                        "shares": 0.0,
                        "total_cost": 0.0,
                        "cost_thb": 0.0,
                        "is_holding": False,
                        "price": tr.get("sell_price_usd", 0.0),
                        "support": 0.0,
                        "resistance": 0.0,
                        "sl": 0.0,
                        "tp": tr.get("sell_price_usd", 0.0),
                        "target": 0.0,
                        "days_to_earnings": None,
                        "earnings_date": "-",
                        "is_earnings_near": False,
                        "earnings_guard_days": EARNINGS_GUARD_DAYS,
                    }
        except Exception:
            pass

    # 4. Enrich with technical levels & earnings calendar from analysis JSON files
    for an_file in [Path("data/.port_analysis.json"), Path("data/account_summary.json")]:
        if an_file.exists():
            try:
                an_data = json.loads(an_file.read_text(encoding="utf-8"))
                for p in an_data.get("positions", []):
                    t = p.get("ticker")
                    if t and t in meta:
                        if p.get("key_support"):
                            meta[t]["support"] = p["key_support"]
                        if p.get("key_resistance"):
                            meta[t]["resistance"] = p["key_resistance"]
                        if p.get("stop_loss"):
                            meta[t]["sl"] = p["stop_loss"]
                        if p.get("take_profit"):
                            meta[t]["tp"] = p["take_profit"]
                        if p.get("price_target_average"):
                            meta[t]["target"] = p["price_target_average"]
                        if p.get("days_to_earnings") is not None:
                            meta[t]["days_to_earnings"] = p["days_to_earnings"]
                        if p.get("earnings_date"):
                            meta[t]["earnings_date"] = p["earnings_date"]
                        if "is_earnings_near" in p:
                            meta[t]["is_earnings_near"] = p["is_earnings_near"]
            except Exception:
                pass

    # 6. Enrich with Super Investors & Whale Holdings
    for t in meta:
        meta[t]["whales"] = get_super_investors(t)

    return meta


def attach_scores(meta: Dict[str, Any], tickers: List[str]) -> None:
    """Adds the unified src/scoring.py score from one TradingView snapshot call."""
    from src.screener import evaluate_stock
    from src.tradingview import fetch_screener_data
    from src.universe import get_universe

    universe = get_universe("all")
    symbols = []
    for t in tickers:
        exchange = meta.get(t, {}).get("exchange")
        if exchange not in ("NASDAQ", "NYSE", "AMEX"):
            exchange = universe.get(t, "NASDAQ")
        symbols.append(f"{exchange}:{t}")
    try:
        rows = fetch_screener_data(symbols)
    except Exception as exc:
        print(f"[chart_page] score fetch failed: {exc}", file=sys.stderr)
        return
    for row in rows:
        t = row.get("ticker")
        if t in meta:
            ev = evaluate_stock(row)
            score = ev["stock_score"]
            meta[t]["score"] = {k: score[k] for k in ("total", "grade", "stars", "pillars", "coverage", "earnings_guard", "reasons")}
            meta[t]["score"]["timing"] = {"entry_signal": score["timing"]["entry_signal"]}
            meta[t]["score"]["guard_days_threshold"] = EARNINGS_GUARD_DAYS
            meta[t]["earnings_guard_days"] = EARNINGS_GUARD_DAYS
            meta[t]["stock_score"] = score
            meta[t]["fundamental"] = ev.get("fundamental")
            if ev.get("days_to_earnings") is not None:
                meta[t]["days_to_earnings"] = ev["days_to_earnings"]


def _format_sr_levels(vals: List[float], max_count: int = 2) -> str:
    seen = set()
    res = []
    for v in vals:
        if v and v > 0:
            vr = round(v, 2 if v < 10 else 1)
            if vr not in seen:
                seen.add(vr)
                if vr < 10:
                    res.append(f"${vr:.2f}")
                else:
                    res.append(f"${vr:,.1f}")
    if not res:
        return "-"
    return ", ".join(res[:max_count])


def generate_stock_chart_page_html() -> str:
    """
    Builds the full HTML document for reports/stock_chart.html.
    Features:
    - Standalone full-page view (no overlay, no nested scrolling).
    - Dual-Pane layout: Main OHLCV chart + Synchronized RSI (14) sub-pane with 70/30 threshold lines.
    - Swing EMA 4-Line Stack (EMA 9, 21, 50, 200) with quick toggle chips.
    - Relocated advanced indicators into a sleek collapsible tray.
    - Bottom control bar with 1D/1W/1M bar selection & 3M/6M/1Y/5Y/ALL zoom presets.
    - Smart DCA Calculator in right cockpit sidebar pulling real portfolio holdings.
    - AI Market Narrative assistant with dynamic Thai status badges.
    - Key Support/Resistance levels radar table.
    - Full Rule-based Confluence Decision Engine & Classical Pattern Deep-Dive Breakdown.
    """
    meta = get_all_stocks_metadata()
    raw_cache = load_candles_cache()

    # Pre-attach unified screener scores and fundamentals so recomputation has complete context
    all_tickers_to_score = sorted(list(set(list(raw_cache.keys()) + list(meta.keys()))))
    attach_scores(meta, all_tickers_to_score)

    updated_cache = False
    for t, entry in raw_cache.items():
        if (
            isinstance(entry, dict)
            and entry.get("candles")
            and (
                entry.get("schema_version") != INDICATOR_SCHEMA_VERSION
                or entry.get("earnings_hash") != EARNINGS_CALENDAR_HASH
            )
        ):
            try:
                m_t = meta.get(t, {})
                d_earn = m_t.get("days_to_earnings")
                sc = m_t.get("stock_score")
                fund = m_t.get("fundamental")
                new_data = compute_fibo_and_indicators(
                    entry["candles"],
                    days_to_earnings=d_earn,
                    is_etf=(t in ETF_TICKERS),
                    ticker=t,
                    stock_score=sc,
                    fundamental=fund,
                )
                new_data["timestamp"] = entry.get("timestamp", 0)
                new_data["full_history"] = entry.get("full_history", True)
                new_data["schema_version"] = INDICATOR_SCHEMA_VERSION
                new_data["earnings_hash"] = EARNINGS_CALENDAR_HASH
                raw_cache[t] = new_data
                updated_cache = True
            except Exception:
                pass
    if updated_cache:
        save_candles_cache(raw_cache)
    cache = compact_charts_for_page(raw_cache, meta)

    # Ensure all cache entries have price if missing or for closed trades
    for t, entry in cache.items():
        if t in meta and (not meta[t]["price"] or not meta[t].get("is_holding")) and entry.get("candles"):
            meta[t]["price"] = entry["candles"][-1]["close"]

    all_tickers = sorted([t for t in cache.keys() if t in meta])
    # Put portfolio core holdings first
    priority_order = ["LLY", "GOOGL", "ABNB", "NOK", "BAC", "MNST", "APP", "VRT", "VOO", "PLTR", "VST", "NOW", "SPCX", "QQQI", "SKHY"]
    sorted_tickers = [t for t in priority_order if t in all_tickers] + [t for t in all_tickers if t not in priority_order]
    sorted_tickers_json = json.dumps(sorted_tickers)

    # 7. Fetch 5 latest news items with sentiment and translate links
    try:
        import urllib.parse
        from src.news import fetch_batch_news
        batch_news = fetch_batch_news(sorted_tickers, max_items=5, max_workers=8)
    except Exception:
        batch_news = {}

    for t in sorted_tickers:
        t_news = batch_news.get(t, [])
        for item in t_news:
            raw_link = item.get("link", "")
            item["link_th"] = (
                f"https://translate.google.com/translate?sl=auto&tl=th&u={urllib.parse.quote(raw_link)}"
                if raw_link else ""
            )
        if t in meta:
            meta[t]["news"] = t_news

    # 8. Fetch & attach quarterly financials (8 quarters / 2 years)
    try:
        from src.financials import get_all_financials_payload
        financials_data = get_all_financials_payload(sorted_tickers, candles_cache=raw_cache)
    except Exception:
        financials_data = {}

    for t in sorted_tickers:
        if t in meta:
            meta[t]["financials"] = financials_data.get(t, {})

    attach_scores(meta, sorted_tickers)

    # Sanitize earnings_history for chart output:
    # ETFs never have corporate earnings announcements.
    for t in sorted_tickers:
        c = cache.get(t)
        if isinstance(c, dict) and "earnings_history" in c and t in ETF_TICKERS:
            c["earnings_history"] = []

    chart_data_json = json.dumps(cache, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps(meta, ensure_ascii=False)
    financials_json = json.dumps(financials_data, ensure_ascii=False, separators=(",", ":"))

    reports_dir = REPORTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    js_content = (
        f"window.CHARTS_DATA = {chart_data_json};\n"
        f"window.STOCKS_META = {meta_json};\n"
        f"window.FINANCIALS_DATA = {financials_json};\n"
    )
    (reports_dir / "chart_data.js").write_text(js_content, encoding="utf-8")

    pills_html = []
    for t in sorted_tickers:
        m = meta.get(t, {})
        c = raw_cache.get(t, {})
        p = m.get("price") or 0.0
        p_txt = f"${p:,.2f}" if p > 0 else "-"

        piv = c.get("pivots") or {}
        lux = c.get("luxalgo_sr") or {}
        sups = [s for s in [m.get("support"), piv.get("s1"), lux.get("support"), piv.get("s2"), m.get("sl")] if s and s > 0]
        ress = [r for r in [m.get("resistance"), piv.get("r1"), lux.get("resistance"), piv.get("r2"), m.get("tp"), m.get("target")] if r and r > 0]

        below = [s for s in sups if s <= p * 1.01]
        sups_chosen = sorted(below, reverse=True) if below else sorted(sups)
        above = [r for r in ress if r >= p * 0.99]
        ress_chosen = sorted(above) if above else sorted(ress, reverse=True)

        sup_str = _format_sr_levels(sups_chosen)
        res_str = _format_sr_levels(ress_chosen)

        is_holding = m.get("is_holding", False)
        if is_holding:
            badge_html = '<span class="sc-badge sc-badge-holding">ถืออยู่</span><span class="sc-live-dot" title="มีในพอร์ตจริง">●</span>'
        else:
            badge_html = '<span class="sc-badge sc-badge-closed">ขายแล้ว</span>'

        name_escaped = escape(str(m.get("name") or t), quote=True)
        pills_html.append(
            f'<div class="sp-pill stock-card" id="pill_{t}" onclick="selectStock(\'{t}\')" title="{name_escaped}">'
            f'<div class="sc-row-top">'
            f'<span class="sp-pill-t sc-ticker">{t}</span>'
            f'<div class="sc-badges">{badge_html}</div>'
            f'</div>'
            f'<div class="sc-row-price">'
            f'<span class="sc-label">Price</span>'
            f'<span class="sp-pill-p sc-price">{p_txt}</span>'
            f'</div>'
            f'<div class="sc-row-level sc-support">'
            f'<span class="sc-tag-support">รับ:</span>'
            f'<span class="sc-vals-support">{sup_str}</span>'
            f'</div>'
            f'<div class="sc-row-level sc-resistance">'
            f'<span class="sc-tag-resistance">ต้าน:</span>'
            f'<span class="sc-vals-resistance">{res_str}</span>'
            f'</div>'
            f'</div>'
        )
    pills_html_str = "\n".join(pills_html)

    html_content = render_chart_template({
        "__NAV_BAR__": nav_bar_html('chart'),
        "__PILLS_HTML__": pills_html_str,
        "__DEFAULT_TICKER__": sorted_tickers[0] if sorted_tickers else "LLY",
        "__SORTED_TICKERS_JSON__": sorted_tickers_json,
        "__INIT_TICKER__": sorted_tickers[0] if sorted_tickers else "LLY",
    })
    (reports_dir / "stock_chart.html").write_text(html_content, encoding="utf-8")
    return html_content


if __name__ == "__main__":
    generate_stock_chart_page_html()

