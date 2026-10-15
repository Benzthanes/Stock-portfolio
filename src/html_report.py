"""
HTML Report Generator for Filter-Stock.
Generates a modern, luxury dark-mode, responsive financial dashboard HTML report.
"""

import json
from datetime import datetime
from html import escape
from typing import Any, Dict, List, Optional


def _fmt_curr(val: float, sym: str = "$") -> str:
    sign = "+" if val > 0 else ("-" if val < 0 else "")
    return f"{sign}{sym}{abs(val):,.2f}"


def _make_chart_onclick(p: Dict[str, Any], is_thb: bool = False) -> str:
    ticker = p.get("ticker", "")
    args = [
        ticker,
        p.get("exchange", "NASDAQ"),
        p.get("name") or ticker,
        p.get("sector") or "",
        p.get("avg_cost_thb" if is_thb else "avg_cost_usd", p.get("avg_cost_usd", 0.0)),
        p.get("close_price", 0.0),
        p.get("key_support", 0.0),
        p.get("key_resistance", 0.0),
        p.get("stop_loss", 0.0),
        p.get("take_profit", 0.0),
        p.get("price_target_average", 0.0),
    ]
    return escape(f"openChartModal({', '.join(json.dumps(a, ensure_ascii=False) for a in args)})", quote=True)


def _news_items_html(items: List[Dict[str, Any]], empty_msg: str) -> str:
    if not items:
        return f"<li><span class='text-muted'>{empty_msg}</span></li>"
    rows = []
    for b in items:
        title = escape(b.get("title", ""), quote=True)
        link = b.get("link") or ""
        if link.lower().startswith(("http://", "https://")):
            title = f"<a href='{escape(link, quote=True)}' target='_blank' rel='noopener noreferrer' class='news-headline-link' title='คลิกเพื่ออ่านข่าวต้นฉบับ'>{title} ↗</a>"
        published = f" <span class='text-muted small'>({escape(b['published'], quote=True)})</span>" if b.get("published") else ""
        rows.append(f"<li><strong class='source-tag'>[{escape(b.get('source', ''), quote=True)}]</strong> {title}{published}</li>")
    return "".join(rows)


def get_chart_modal_component(tickers: Optional[List[str]] = None) -> str:
    """
    Returns lightweight redirect handler for stock_chart.html.
    Eliminates 20MB of duplicate JSON data across all 5 portfolio report dashboards.
    """
    return """
<!-- Stock Chart Dedicated Navigation Handler -->
<script>
function openChartModal(ticker, exchange, name, sector, cost, price, support, resistance, sl, tp, targetAvg) {
    const params = new URLSearchParams();
    if (ticker) params.set('ticker', ticker);
    if (exchange) params.set('exchange', exchange);
    if (name) params.set('name', name);
    if (sector) params.set('sector', sector);
    if (cost) params.set('cost', cost);
    if (price) params.set('price', price);
    if (support) params.set('support', support);
    if (resistance) params.set('resistance', resistance);
    if (sl) params.set('sl', sl);
    if (tp) params.set('tp', tp);
    if (targetAvg) params.set('target', targetAvg);
    window.location.href = 'stock_chart.html?' + params.toString() + '#' + encodeURIComponent(ticker || '');
}
</script>
"""


def generate_portfolio_html(summary: Dict[str, Any]) -> str:
    """
    Render portfolio summary into a standalone, luxury dark-themed HTML report.
    """
    port_name = summary.get("portfolio_name", "Portfolio")
    broker = summary.get("broker", "Broker")
    fx = summary.get("fx_rate_usd_thb", 33.62)
    val_usd = summary.get("total_market_val_usd", 0.0)
    val_thb = summary.get("total_market_val_thb", 0.0)
    cost_usd = summary.get("total_cost_usd", 0.0)
    cost_thb = summary.get("total_cost_thb", 0.0)
    pl_usd = summary.get("total_pl_usd", 0.0)
    pl_thb = summary.get("total_pl_thb", 0.0)
    pl_pct = summary.get("total_pl_pct", 0.0)
    day_usd = summary.get("total_daily_change_usd", 0.0)
    day_thb = summary.get("total_daily_change_thb", 0.0)
    day_pct = summary.get("total_daily_change_pct", 0.0)
    conc_lvl = summary.get("concentration_level", "Moderate")
    hhi = summary.get("hhi", 0.0)
    grade = summary.get("health_grade", "B")
    score = summary.get("health_score", 70.0)
    status_txt = summary.get("health_status", "")
    grade_desc = summary.get("health_grade_desc", "")
    best_pos = summary.get("best_pos")
    worst_pos = summary.get("worst_pos")
    top_picks = summary.get("top_buy_candidates", [])
    forbidden = summary.get("forbidden_buys", [])
    dip_setups = summary.get("dip_opportunities", [])
    sector_sorted = summary.get("sector_sorted", [])
    positions = summary.get("positions", [])

    now_str = datetime.now().strftime("%d %b %Y, %H:%M")
    is_thb = summary.get("base_currency") == "THB"
    curr_sym = "฿" if is_thb else "$"
    sub_sym = "$" if is_thb else "฿"

    # Color tokens based on P/L
    pl_color = "var(--emerald)" if (pl_thb >= 0 if is_thb else pl_usd >= 0) else "var(--rose)"
    day_color = "var(--emerald)" if (day_thb >= 0 if is_thb else day_usd >= 0) else "var(--rose)"

    # Grade color
    if grade in ("A+", "A"):
        grade_badge_color = "var(--emerald-glow)"
        grade_border = "var(--emerald)"
    elif grade == "B+":
        grade_badge_color = "var(--amber-glow)"
        grade_border = "var(--amber)"
    elif grade == "B":
        grade_badge_color = "var(--amber-glow)"
        grade_border = "var(--amber)"
    else:
        grade_badge_color = "var(--rose-glow)"
        grade_border = "var(--rose)"

    # Sector Rows
    sector_rows_html = ""
    for sec_name, sec_pct in sector_sorted:
        bar_width = min(100.0, max(2.0, sec_pct))
        bar_color = "var(--rose)" if sec_pct >= 40.0 else ("var(--emerald)" if sec_pct >= 20.0 else "var(--blue)")
        warn_badge = '<span class="badge badge-warn">⚠️ สัดส่วนสูงมาก</span>' if sec_pct >= 40.0 else (
            '<span class="badge badge-success">🟢 สัดส่วนหลัก</span>' if sec_pct >= 20.0 else
            '<span class="badge badge-neutral">⚪ กระจายตัวดี</span>'
        )
        sector_rows_html += f"""
        <tr>
            <td style="font-weight: 600;">{escape(str(sec_name))}</td>
            <td style="width: 45%;">
                <div class="progress-wrap">
                    <div class="progress-bar" style="width: {bar_width}%; background: {bar_color};"></div>
                </div>
            </td>
            <td style="text-align: right; font-weight: 700;">{sec_pct:.1f}%</td>
            <td>{warn_badge}</td>
        </tr>
        """

    # Holdings Rows
    holdings_rows_html = ""
    for p in positions:
        t = p["ticker"]
        name = escape(p["name"])
        biz = escape(p.get("business_summary") or "")
        r = p.get("rating", {})
        stars = r.get("stars_str", "⭐")
        weight = p["weight_pct"]
        avg_cost = p["avg_cost_usd"]
        price = p["close_price"]
        p_val_usd = p["current_val_usd"]
        p_val_thb = p["current_val_thb"]
        un_pl_usd = p["unrealized_pl_usd"]
        un_pl_pct = p["unrealized_pl_pct"]
        p_chg = p["change_pct"]
        rsi = p["rsi"]
        dist_sma = p["dist_sma200_pct"]
        in_val = p.get("in_value_zone")
        alerts = p.get("alerts", [])

        pl_cls = "text-emerald" if un_pl_usd >= 0 else "text-rose"
        day_cls = "text-emerald" if p_chg >= 0 else "text-rose"
        pl_sign = "+" if un_pl_usd >= 0 else ""
        day_sign = "+" if p_chg >= 0 else ""

        rsi_html = f"{rsi:.1f}" if rsi is not None else "-"
        if rsi is not None and rsi <= 30:
            rsi_html = f'<span class="badge badge-rose">{rsi:.1f} 🚨</span>'
        elif rsi is not None and rsi <= 35:
            rsi_html = f'<span class="badge badge-amber">{rsi:.1f} 📉</span>'

        if dist_sma is not None:
            dist_sign = "+" if dist_sma >= 0 else ""
            dist_html = f"{dist_sign}{dist_sma:.1f}%"
            if in_val:
                dist_html += ' <span title="Value Zone">💎</span>'
        else:
            dist_html = "-"

        badges_html = ""
        for a in alerts:
            if "Extreme" in a or "Drawdown" in a:
                badges_html += f'<span class="badge badge-rose">{a}</span> '
            elif "Heavy" in a or "Earnings" in a:
                badges_html += f'<span class="badge badge-amber">{a}</span> '
            else:
                badges_html += f'<span class="badge badge-neutral">{a}</span> '
        if in_val:
            badges_html += '<span class="badge badge-emerald">💎 Value Zone</span> '
        if not badges_html:
            badges_html = '<span class="badge badge-neutral">Normal</span>'


        avg_cost_disp = f"฿{p.get('avg_cost_thb', avg_cost):,.2f}" if is_thb else f"${avg_cost:,.2f}"
        price_disp = f"฿{price:,.2f}" if is_thb else f"${price:,.2f}"
        supp_disp = f"รับ ฿{p.get('key_support', 0):,.2f}" if is_thb else f"รับ ${p.get('key_support', 0):,.2f}"
        res_disp = f"ต้าน ฿{p.get('key_resistance', 0):,.2f}" if is_thb else f"ต้าน ${p.get('key_resistance', 0):,.2f}"
        val_main = f"฿{p_val_thb:,.2f}" if is_thb else f"${p_val_usd:,.2f}"
        val_sub = f"≈ ${p_val_usd:,.2f}" if is_thb else f"≈ ฿{p_val_thb:,.0f}"
        un_pl_main = p.get('unrealized_pl_thb', un_pl_usd) if is_thb else un_pl_usd
        pl_sub_disp = f"({pl_sign}฿{abs(un_pl_main):,.2f})" if is_thb else f"({pl_sign}${abs(un_pl_main):,.2f})"

        onclick_js = _make_chart_onclick(p, is_thb=is_thb)

        holdings_rows_html += f"""
        <tr>
            <td>
                <span class="ticker-pill clickable-ticker" onclick="{onclick_js}" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{t} 📈</span>
            </td>
            <td>
                <div class="fw-bold">{name}</div>
                <div class="text-muted small">{biz}</div>
            </td>
            <td style="white-space: nowrap;">{stars}</td>
            <td style="text-align: right; font-weight: 700;">{weight:.1f}%</td>
            <td style="text-align: right;">{avg_cost_disp}</td>
            <td style="text-align: right; font-weight: 600;">{price_disp}</td>
            <td style="text-align: right;">
                <div class="text-emerald small fw-bold">{supp_disp}</div>
                <div class="text-amber small">{res_disp}</div>
            </td>
            <td style="text-align: right;">
                <div>{val_main}</div>
                <div class="text-muted small">{val_sub}</div>
            </td>
            <td style="text-align: right;" class="{pl_cls}">
                <div class="fw-bold">{pl_sign}{un_pl_pct:.2f}%</div>
                <div class="small">{pl_sub_disp}</div>
            </td>
            <td style="text-align: right;" class="{day_cls}">{day_sign}{p_chg:.2f}%</td>
            <td style="text-align: center;">{rsi_html}</td>
            <td style="text-align: center;">{dist_html}</td>
            <td>{badges_html}</td>
        </tr>
        """

    # Fundamentals & Targets Rows
    fund_rows_html = ""
    for p in positions:
        t = p["ticker"]
        name = escape(p["name"])
        fh = p.get("financial_health", {})
        h_badge = fh.get("health_badge", "-")
        peg_verdict = fh.get("peg_verdict", "-")
        fcf_str = fh.get("fcf_str", "-")

        if "ยอดเยี่ยม" in h_badge or "สุขภาพดี" in h_badge:
            badge_html = f"<span class='badge badge-emerald'>{h_badge}</span>"
        elif "ปานกลาง" in h_badge or "เฝ้าระวัง" in h_badge:
            badge_html = f"<span class='badge badge-amber'>{h_badge}</span>"
        elif "กำไรหดตัว" in h_badge:
            badge_html = f"<span class='badge badge-rose'>{h_badge}</span>"
        else:
            badge_html = f"<span class='badge badge-neutral'>{h_badge}</span>"

        rev_g = f"{p['rev_growth_yoy']:+.1f}%" if p.get('rev_growth_yoy') is not None else "-"
        net_g = f"{p['net_inc_growth_yoy']:+.1f}%" if p.get('net_inc_growth_yoy') is not None else "-"
        peg_str = f"{p['peg']:.2f}" if p.get('peg') is not None else "-"
        pe_str = f"{p['pe']:.1f}x" if p.get('pe') is not None else "-"

        t_avg = f"${p['price_target_average']:,.2f}" if p.get('price_target_average') else "-"
        t_up = f"({p['target_upside_pct']:+.1f}%)" if p.get('target_upside_pct') is not None else ""
        t_target_html = f"<strong>{t_avg}</strong> <span class='text-emerald small'>{t_up}</span>" if p.get('price_target_average') else "-"

        range_str = f"${p['price_target_low']:,.0f} - ${p['price_target_high']:,.0f}" if (p.get('price_target_low') and p.get('price_target_high')) else "-"

        b = p.get('rec_buy')
        h = p.get('rec_hold')
        s = p.get('rec_sell')
        if b is not None:
            votes_html = f"<span class='badge badge-emerald'>Buy {b}</span> <span class='badge badge-amber'>Hold {h}</span> <span class='badge badge-rose'>Sell {s}</span>"
        else:
            votes_html = "-"

        earn_str = f"{p['earnings_date']} ({p['days_to_earnings']}d)" if p.get('days_to_earnings') is not None else "-"
        if p.get("is_earnings_near"):
            earn_html = f"<span class='badge badge-rose'>⚠️ {earn_str}</span>"
        else:
            earn_html = f"<span class='text-muted'>{earn_str}</span>"

        fund_rows_html += f"""
        <tr>
            <td><a href="{p['tv_url']}" target="_blank" class="ticker-pill">{t}</a></td>
            <td><div class="fw-bold">{name}</div></td>
            <td>{badge_html}</td>
            <td style="text-align: right; font-weight: 600;">{rev_g}</td>
            <td style="text-align: right; font-weight: 600;">{net_g}</td>
            <td style="text-align: right;">
                <div class="fw-bold">{peg_str}</div>
                <div class="text-muted small">{peg_verdict}</div>
            </td>
            <td style="text-align: right;">{pe_str}</td>
            <td style="text-align: right; font-weight: 600;">{fcf_str}</td>
            <td style="text-align: right;">{t_target_html}</td>
            <td style="text-align: center;">{range_str}</td>
            <td>{votes_html}</td>
            <td>{earn_html}</td>
        </tr>
        """

    # Top Buy Podium Cards
    medals = ["🥇 อันดับ 1", "🥈 อันดับ 2", "🥉 อันดับ 3"]
    medal_colors = ["var(--gold)", "var(--silver)", "var(--bronze)"]
    top_cards_html = ""
    for idx, pick in enumerate(top_picks[:3]):
        medal_title = medals[idx] if idx < len(medals) else f"อันดับ {idx+1}"
        m_color = medal_colors[idx] if idx < len(medal_colors) else "var(--blue)"
        t = pick["ticker"]
        name = escape(pick["name"])
        stars = pick.get("rating", {}).get("stars_str", "⭐")
        w = pick["weight_pct"]
        c = pick["close_price"]
        sl = pick.get("stop_loss") or (c * 0.95)
        buy_low = c * 0.98
        buy_high = c * 1.01
        biz = escape(pick.get("business_summary") or "")

        target_upside = pick.get("target_upside_pct")
        if t in ("VOO", "SPY", "QQQ"):
            reason = "เป็นกองทุนดัชนีรวมที่ช่วยกระจายความเสี่ยงของพอร์ตทันที ช่วยลดการพึ่งพาหุ้นตัวใดตัวหนึ่งมากเกินไป."
        elif pick.get("in_value_zone"):
            t_avg = f"{curr_sym}{pick['price_target_average']:,.2f}" if pick.get("price_target_average") else "ไม่ระบุ"
            reason = f"ราคาพักตัวลงมาในจุดรับที่มีแต้มต่อสูง (Value Zone 💎) ใกล้เส้น 200 วัน กำไรเติบโตเด่น และสถาบันให้เป้าหมายเฉลี่ย {t_avg}."
        elif target_upside is not None:
            reason = f"หุ้นคุณภาพดี พื้นฐานแกร่ง เทรนด์ขาขึ้นเหนือเส้น 200 วัน สถาบันให้เป้าหมายมี Upside {target_upside:+.1f}%."
        else:
            reason = "หุ้นคุณภาพดี พื้นฐานมั่นคง เทรนด์ทางเทคนิคประคองตัวได้ดี."

        top_cards_html += f"""
        <div class="card buy-card" style="border-top: 4px solid {m_color};">
            <div class="buy-header">
                <span class="buy-rank" style="color: {m_color};">{medal_title}</span>
                <span class="ticker-pill">{t}</span>
            </div>
            <h4 style="margin: 8px 0 4px 0;">{name} {stars}</h4>
            <p class="text-muted small" style="margin-bottom: 12px;">{biz}</p>
            <div class="buy-reason-box">
                💡 <strong>เหตุผลสำหรับมือใหม่:</strong> {reason}
            </div>
            <div class="grid-2-cols" style="margin-top: 14px; font-size: 0.9rem;">
                <div><span class="text-muted">สัดส่วนปัจจุบัน:</span> <strong>{w:.1f}%</strong></div>
                <div><span class="text-muted">ราคาตลาด:</span> <strong>{curr_sym}{c:,.2f}</strong></div>
            </div>
            <div class="order-box">
                <div class="order-row">
                    <span>โซนตั้งซื้อ (Limit Order):</span>
                    <strong class="text-emerald">{curr_sym}{buy_low:,.2f} - {curr_sym}{buy_high:,.2f}</strong>
                </div>
                <div class="order-row">
                    <span>จุดตัดขาดทุน (SL):</span>
                    <strong class="text-rose">{curr_sym}{sl:,.2f}</strong>
                </div>
            </div>
        </div>
        """

    # Forbidden Buys List
    forbidden_html = ""
    for fb in forbidden:
        forbidden_html += f"""
        <div class="forbidden-item">
            <span class="badge badge-rose">❌ ห้ามซื้อ {fb['ticker']}</span>
            <div><strong>{escape(fb['name'])}:</strong> {fb['reason']}</div>
        </div>
        """

    # News & Catalysts Grid (Forward Intelligence Dossiers)
    catalysts_html = ""
    for p in positions:
        t = p["ticker"]
        name = escape(p["name"])
        biz = escape(p.get("business_summary") or "")
        cat = p.get("catalysts", {})
        bullish = cat.get("bullish", [])
        bearish = cat.get("bearish", [])
        t_avg = p.get("price_target_average")
        t_low = p.get("price_target_low")
        t_high = p.get("price_target_high")

        fo = p.get("forward_outlook", {})
        thesis_title = fo.get("thesis_title", f"การวิเคราะห์เจาะลึกทิศทางธุรกิจและระบบนิเวศ {t}")
        quality_badge = fo.get("quality_badge", "🔵 Strategic Core Holding")
        drivers = fo.get("future_growth_drivers", [])
        timeline = fo.get("catalyst_timeline", [])
        ws_verdict = fo.get("wall_street_verdict", "")
        tailored_roadmap = fo.get("tailored_roadmap", p.get("rating", {}).get("action", ""))
        invalidation_risk = fo.get("invalidation_risk", f"ระวังการหลุดแนวรับสำคัญ {curr_sym}{p.get('key_support', 0):,.2f}")

        # Format drivers
        drivers_li = "".join([f"<li>{d}</li>" for d in drivers]) if drivers else "<li>กำลังติดตามข้อมูลปัจจัยขับเคลื่อนเชิงลึก</li>"

        # Format timeline
        timeline_steps = "".join([
            f"""<div class="timeline-step">
                <span class="timeline-step-badge">{item.get('period', '-')}</span>
                <div class="timeline-step-desc">{item.get('event', '-')}</div>
            </div>"""
            for item in timeline
        ]) if timeline else "<div class='text-muted small'>ไม่มีกำหนดการตัวเร่งราคาเฉพาะในระยะสั้น</div>"

        # Bullish / Bearish items
        bull_items = _news_items_html(bullish, "ยังไม่มีข่าวด้านบวกโดดเด่นในสัปดาห์นี้.")
        bear_items = _news_items_html(bearish, "ไม่มีข่าวร้ายรุนแรงในระยะสั้น.")

        # Targets & Consensus
        t_low_str = f"{curr_sym}{t_low:,.2f}" if t_low else "-"
        t_avg_str = f"{curr_sym}{t_avg:,.2f}" if t_avg else "-"
        t_high_str = f"{curr_sym}{t_high:,.2f}" if t_high else "-"
        up_val = p.get('target_upside_pct')
        up_str = f" (+{up_val:.1f}%)" if (up_val is not None and up_val > 0) else (f" ({up_val:.1f}%)" if up_val is not None else "")

        ratings_summary = ""
        if p.get("rec_buy") is not None:
            ratings_summary = f"<span class='text-emerald fw-bold'>🟢 Buy: {p.get('rec_buy', 0)}</span> &nbsp;|&nbsp; <span class='text-amber fw-bold'>🟡 Hold: {p.get('rec_hold', 0)}</span> &nbsp;|&nbsp; <span class='text-rose fw-bold'>🔴 Sell: {p.get('rec_sell', 0)}</span>"

        pl_pct_pos = p.get("unrealized_pl_pct", 0.0)
        pl_cls = "badge-emerald" if pl_pct_pos >= 0 else "badge-rose"
        pl_sign = "+" if pl_pct_pos >= 0 else ""
        c_price = p.get("close_price", 0.0)
        c_avg = p.get("avg_cost_thb" if is_thb else "avg_cost_usd", 0.0)
        star_str = p.get("rating", {}).get("stars", "⭐⭐⭐")

        onclick_js = _make_chart_onclick(p, is_thb=is_thb)

        catalysts_html += f"""
        <div class="card outlook-card" style="margin-bottom: 24px; border-left: 4px solid {'var(--emerald)' if pl_pct_pos >= 0 else 'var(--rose)'};">
            <!-- Header -->
            <div class="outlook-card-header">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <span class="ticker-pill clickable-ticker" style="font-size: 1.15rem; padding: 4px 12px;" onclick="{onclick_js}" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{t} 📈</span>
                    <strong style="font-size: 1.25rem;">{name}</strong>
                    <span class="badge badge-neutral" style="font-size: 0.8rem;">{escape(p.get('sector') or '')} • {escape(p.get('industry') or '')}</span>
                    <span class="badge badge-neutral" style="font-size: 0.8rem; background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.25);">{quality_badge}</span>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                    <span class="badge {pl_cls}" style="font-size: 0.95rem; padding: 5px 12px;">{pl_sign}{pl_pct_pos:.2f}%</span>
                    <span class="badge badge-neutral" style="font-size: 0.85rem;">สัดส่วน {p.get('weight_pct', 0.0):.1f}% ({star_str})</span>
                    <button onclick="{onclick_js}" style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); color: #60a5fa; border-radius: 6px; padding: 5px 12px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; transition: all 0.2s;">📈 ดูกราฟสด & แนวรับแนวต้าน</button>
                </div>
            </div>

            <!-- Thesis Banner -->
            <div class="thesis-banner">
                <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #93c5fd; margin-bottom: 4px;">🔭 วิสัยทัศน์และธีมการเติบโตหลักในอนาคต (Growth Thesis):</div>
                <div style="color: #ffffff; font-size: 1.05rem; line-height: 1.4;">{thesis_title}</div>
            </div>

            <!-- 4 Future Growth Drivers -->
            <div class="drivers-box">
                <div style="font-size: 0.88rem; font-weight: 700; color: #38bdf8; margin-bottom: 8px;">🚀 4 เครื่องจักรขับเคลื่อนการเติบโตในอนาคต (Future Growth Drivers 1-12 เดือน):</div>
                <ul class="drivers-list">
                    {drivers_li}
                </ul>
            </div>

            <!-- Catalyst Timeline -->
            <div style="margin-bottom: 18px;">
                <div style="font-size: 0.88rem; font-weight: 700; color: #cbd5e1; margin-bottom: 10px;">📅 ปฏิทินตัวเร่งราคาและปัจจัยสำคัญตามช่วงเวลา (Catalyst Timeline):</div>
                <div class="timeline-strip">
                    {timeline_steps}
                </div>
            </div>

            <!-- Wall Street Consensus & Targets -->
            <div class="wallstreet-box">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div class="fw-bold" style="font-size: 0.95rem; color: #10b981;">🎯 มุมมองราคาเป้าหมายสถาบันการเงินวอลล์สตรีท (Wall Street Consensus)</div>
                    <div class="small">{ratings_summary}</div>
                </div>
                <div class="ws-targets-grid">
                    <div class="ws-target-cell">
                        <div class="text-muted small">ต้นทุนของคุณ</div>
                        <div class="fw-bold text-main" style="font-size: 1.1rem;">{curr_sym}{c_avg:,.2f}</div>
                    </div>
                    <div class="ws-target-cell">
                        <div class="text-muted small">ราคาปัจจุบัน</div>
                        <div class="fw-bold {'text-emerald' if pl_pct_pos >= 0 else 'text-rose'}" style="font-size: 1.1rem;">{curr_sym}{c_price:,.2f}</div>
                    </div>
                    <div class="ws-target-cell">
                        <div class="text-muted small">เป้าต่ำสุด (Low)</div>
                        <div class="fw-bold text-amber" style="font-size: 1.1rem;">{t_low_str}</div>
                    </div>
                    <div class="ws-target-cell">
                        <div class="text-muted small">เป้าเฉลี่ย (Average)</div>
                        <div class="fw-bold text-emerald" style="font-size: 1.1rem;">{t_avg_str} <span class="small">{up_str}</span></div>
                    </div>
                    <div class="ws-target-cell">
                        <div class="text-muted small">เป้าสูงสุด (High)</div>
                        <div class="fw-bold text-blue" style="font-size: 1.1rem;">{t_high_str}</div>
                    </div>
                </div>
                <div class="small" style="color: #cbd5e1; background: rgba(0, 0, 0, 0.2); padding: 8px 12px; border-radius: 6px; border-left: 3px solid var(--emerald); margin-top: 6px;">
                    📌 <strong>ข้อสรุปของวอลล์สตรีท:</strong> {ws_verdict}
                </div>
            </div>

            <!-- Live News & Catalysts Grid -->
            <div class="grid-2-cols" style="gap: 14px; margin-bottom: 18px;">
                <div class="bull-box" style="background: rgba(16, 185, 129, 0.04); padding: 14px; border-radius: var(--radius-sm); border: 1px solid rgba(16, 185, 129, 0.2);">
                    <div class="cat-label text-emerald fw-bold small" style="margin-bottom: 8px;">🟢 พาดหัวข่าวจริงเชิงบวกและปัจจัยหนุน (Positive News):</div>
                    <ul class="cat-list">{bull_items}</ul>
                </div>
                <div class="bear-box" style="background: rgba(244, 63, 94, 0.04); padding: 14px; border-radius: var(--radius-sm); border: 1px solid rgba(244, 63, 94, 0.2);">
                    <div class="cat-label text-rose fw-bold small" style="margin-bottom: 8px;">🔴 พาดหัวข่าวจริงที่ต้องระวังและความเสี่ยง (Risk Factors):</div>
                    <ul class="cat-list">{bear_items}</ul>
                </div>
            </div>

            <!-- Tailored Strategic Roadmap & Invalidation Risk -->
            <div class="roadmap-callout">
                <div style="font-size: 0.85rem; font-weight: 700; color: #fbbf24; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                    🧭 แผนกลยุทธ์ฟันธงสำหรับ {t} (Action Roadmap):
                </div>
                <div style="font-size: 0.95rem; color: #ffffff; line-height: 1.5; margin-bottom: 10px;">
                    {tailored_roadmap}
                </div>
                <div style="font-size: 0.85rem; color: #fca5a5; background: rgba(244, 63, 94, 0.08); padding: 8px 12px; border-radius: 6px; border-left: 3px solid var(--rose);">
                    🛑 <strong>สัญญาณเตือนภัย / จุดระวัง (Invalidation Risk):</strong> {invalidation_risk}
                </div>
            </div>
        </div>
        """

    # Assemble complete HTML
    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Health & Performance Report - {port_name}</title>
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
            --purple: #8b5cf6;
            --gold: #fbbf24;
            --silver: #cbd5e1;
            --bronze: #d97706;
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
                radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.08) 0px, transparent 50%),
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
            margin-bottom: 24px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }}

        .header-title h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .header-meta {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        .meta-pill {{
            background: var(--bg-card);
            padding: 6px 14px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border-color);
        }}

        /* Grid utilities */
        .grid-4-cols {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }}

        .grid-3-cols {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}

        .grid-2-cols {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}

        /* Cards */
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 22px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}

        .card:hover {{
            border-color: rgba(255, 255, 255, 0.15);
        }}

        /* Scoreboard KPI */
        .kpi-card {{
            position: relative;
            overflow: hidden;
        }}

        .kpi-label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }}

        .kpi-value {{
            font-size: 1.85rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            font-family: 'Inter', sans-serif;
        }}

        .kpi-subtext {{
            font-size: 0.88rem;
            color: var(--text-muted);
            margin-top: 6px;
        }}

        /* Grade Ring */
        .grade-box {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .grade-badge {{
            width: 72px;
            height: 72px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            font-weight: 800;
            font-family: 'Inter', sans-serif;
            background: {grade_badge_color};
            border: 3px solid {grade_border};
            box-shadow: 0 0 20px {grade_badge_color};
        }}

        /* Layman Hero Card */
        .layman-hero-card {{
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85));
            border-left: 4px solid var(--blue);
            margin-bottom: 24px;
        }}

        .layman-checklist {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 14px;
        }}

        .layman-checklist li {{
            background: rgba(255, 255, 255, 0.03);
            padding: 12px 16px;
            border-radius: var(--radius-sm);
            border-left: 3px solid var(--blue);
            font-size: 0.95rem;
        }}

        /* Badges & Pills */
        .ticker-pill {{
            display: inline-block;
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-family: 'Inter', sans-serif;
            text-decoration: none;
        }}

        .ticker-pill:hover {{
            background: rgba(59, 130, 246, 0.3);
        }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .badge-emerald {{ background: var(--emerald-glow); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); }}
        .badge-rose {{ background: var(--rose-glow); color: var(--rose); border: 1px solid rgba(244, 63, 94, 0.3); }}
        .badge-amber {{ background: var(--amber-glow); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.3); }}
        .badge-neutral {{ background: rgba(255, 255, 255, 0.05); color: var(--text-secondary); border: 1px solid var(--border-color); }}
        .badge-warn {{ background: var(--amber-glow); color: var(--amber); }}
        .badge-success {{ background: var(--emerald-glow); color: var(--emerald); }}

        /* Tables */
        .table-responsive {{
            overflow-x: auto;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            margin-bottom: 24px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
            background: var(--bg-card);
        }}

        th {{
            background: rgba(15, 23, 42, 0.95);
            color: var(--text-secondary);
            padding: 14px 16px;
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}

        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-subtle);
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}

        /* Progress bars */
        .progress-wrap {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 4px;
            overflow: hidden;
        }}

        .progress-bar {{
            height: 100%;
            border-radius: 4px;
        }}

        /* Fresh Capital Podium Cards */
        .buy-card {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .buy-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .buy-rank {{
            font-weight: 700;
            font-size: 1.1rem;
        }}

        .buy-reason-box {{
            background: rgba(255, 255, 255, 0.03);
            border-left: 3px solid var(--emerald);
            padding: 10px 14px;
            border-radius: var(--radius-sm);
            font-size: 0.88rem;
            margin: 10px 0;
        }}

        .order-box {{
            background: rgba(0, 0, 0, 0.3);
            padding: 12px 14px;
            border-radius: var(--radius-sm);
            margin-top: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 0.88rem;
        }}

        .order-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        /* Forbidden Buys */
        .forbidden-card {{
            background: rgba(244, 63, 94, 0.06);
            border: 1px solid rgba(244, 63, 94, 0.25);
            border-radius: var(--radius-md);
            padding: 18px 22px;
            margin-bottom: 24px;
        }}

        .forbidden-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 10px;
            font-size: 0.92rem;
        }}

        /* Catalysts */
        .catalyst-card {{
            margin-bottom: 16px;
        }}

        .catalyst-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-subtle);
        }}

        .catalyst-target-box {{
            background: rgba(59, 130, 246, 0.08);
            border-radius: var(--radius-sm);
            padding: 8px 14px;
            margin-top: 12px;
            font-size: 0.88rem;
            color: #93c5fd;
        }}

        .cat-label {{
            font-weight: 700;
            font-size: 0.88rem;
            margin-bottom: 8px;
        }}

        .cat-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 0.85rem;
        }}

        .cat-list li {{
            padding-left: 12px;
            border-left: 2px solid var(--border-color);
        }}

        .cat-list a.news-headline-link {{
            color: var(--text-main);
            text-decoration: underline;
            text-decoration-color: rgba(255, 255, 255, 0.25);
            text-underline-offset: 3px;
            transition: color 0.15s ease, text-decoration-color 0.15s ease;
        }}

        .cat-list a.news-headline-link:hover {{
            color: #60a5fa;
            text-decoration-color: #60a5fa;
        }}

        .cat-list .source-tag {{
            color: var(--text-secondary);
        }}

        /* Forward Outlook & Dossier Styles */
        .outlook-card {{
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(15, 23, 42, 0.88));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius-md);
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        }}
        .outlook-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 18px;
        }}
        .thesis-banner {{
            background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.10));
            border-left: 4px solid var(--blue);
            padding: 12px 18px;
            border-radius: var(--radius-sm);
            margin-bottom: 18px;
        }}
        .drivers-box {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 16px;
            margin-bottom: 18px;
        }}
        .drivers-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 0.88rem;
            line-height: 1.5;
        }}
        .drivers-list li {{
            position: relative;
            padding-left: 18px;
            color: #cbd5e1;
        }}
        .drivers-list li::before {{
            content: "✦";
            position: absolute;
            left: 2px;
            color: var(--emerald);
            font-size: 0.8rem;
        }}
        .timeline-strip {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
        }}
        .timeline-step {{
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: var(--radius-sm);
            padding: 12px 14px;
        }}
        .timeline-step-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            margin-bottom: 6px;
        }}
        .timeline-step-desc {{
            font-size: 0.85rem;
            color: #e2e8f0;
            line-height: 1.4;
        }}
        .wallstreet-box {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.04), rgba(15, 23, 42, 0.6));
            border: 1px solid rgba(16, 185, 129, 0.22);
            border-radius: var(--radius-sm);
            padding: 16px 20px;
            margin-bottom: 18px;
        }}
        .ws-targets-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin: 12px 0;
            text-align: center;
        }}
        .ws-target-cell {{
            background: rgba(0, 0, 0, 0.25);
            padding: 8px 10px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .roadmap-callout {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(15, 23, 42, 0.8));
            border-left: 4px solid var(--amber);
            border-radius: var(--radius-sm);
            padding: 16px 20px;
            margin-bottom: 18px;
        }}

        /* Typography helpers */
        .text-emerald {{ color: var(--emerald); }}
        .text-rose {{ color: var(--rose); }}
        .text-amber {{ color: var(--amber); }}
        .text-muted {{ color: var(--text-muted); }}
        .fw-bold {{ font-weight: 700; }}
        .small {{ font-size: 0.8rem; }}

        /* Disclaimer */
        .disclaimer-card {{
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 20px;
            margin-top: 32px;
            font-size: 0.82rem;
            color: var(--text-muted);
            text-align: center;
            line-height: 1.6;
        }}

        /* Section Headings */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 32px 0 16px 0;
            font-size: 1.35rem;
            font-weight: 700;
        }}

        @media (max-width: 768px) {{
            body {{ padding: 14px; }}
            .header {{ flex-direction: column; align-items: flex-start; }}
            .grade-box {{ flex-direction: column; align-items: flex-start; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-title">
                <h1>📊 {port_name}</h1>
            </div>
            <div class="header-meta">
                <span class="meta-pill">🏦 <strong>Broker:</strong> {broker}</span>
                <span class="meta-pill">💱 <strong>FX Rate:</strong> {fx:.2f} THB/USD</span>
                <span class="meta-pill">🕒 <strong>อัปเดต:</strong> {now_str}</span>
            </div>
        </header>

        <!-- KPI Scoreboard -->
        <div class="grid-4-cols">
            <div class="card kpi-card">
                <div class="kpi-label">🏥 เกรดสุขภาพพอร์ต</div>
                <div class="grade-box">
                    <div class="grade-badge">{grade}</div>
                    <div>
                        <div class="fw-bold" style="font-size: 1.1rem;">{score:.0f}/100 คะแนน</div>
                        <div class="kpi-subtext">{status_txt}</div>
                    </div>
                </div>
            </div>

            <div class="card kpi-card">
                <div class="kpi-label">💰 มูลค่าพอร์ตปัจจุบัน</div>
                <div class="kpi-value">{'฿' + f'{val_thb:,.2f}' if is_thb else '$' + f'{val_usd:,.2f}'}</div>
                <div class="kpi-subtext">{'≈ $' + f'{val_usd:,.2f} USD (ต้นทุน ฿{cost_thb:,.2f})' if is_thb else '≈ ฿' + f'{val_thb:,.2f} THB (ต้นทุน ${cost_usd:,.2f})'}</div>
            </div>

            <div class="card kpi-card">
                <div class="kpi-label">📈 กำไร/ขาดทุนสุทธิ (Unrealized)</div>
                <div class="kpi-value" style="color: {pl_color};">{_fmt_curr(pl_thb, '฿') if is_thb else _fmt_curr(pl_usd, '$')} ({pl_pct:+.2f}%)</div>
                <div class="kpi-subtext">{'≈ ' + _fmt_curr(pl_usd, '$') + ' USD' if is_thb else '≈ ' + _fmt_curr(pl_thb, '฿') + ' THB'}</div>
            </div>

            <div class="card kpi-card">
                <div class="kpi-label">⚡ กำไร/ขาดทุนวันนี้ (1D Change)</div>
                <div class="kpi-value" style="color: {day_color};">{_fmt_curr(day_thb, '฿') if is_thb else _fmt_curr(day_usd, '$')} ({day_pct:+.2f}%)</div>
                <div class="kpi-subtext">HHI: {hhi:.0f} ({conc_lvl})</div>
            </div>
        </div>

        <!-- Layman Summary Hero -->
        <div class="card layman-hero-card">
            <h3 style="font-size: 1.15rem; margin-bottom: 8px;">👶 1. สรุปสถานะพอร์ตภาษาคน สำหรับมือใหม่</h3>
            <p style="color: var(--text-secondary); margin-bottom: 12px;">{grade_desc}</p>
            <div class="grid-2-cols" style="margin-bottom: 12px; gap: 12px;">
                <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: var(--radius-sm);">
                    🚀 <strong>ฮีโร่แบกพอร์ต:</strong> {f"[{best_pos['ticker']}] {escape(best_pos['name'])} (+{best_pos['unrealized_pl_pct']:.1f}%)" if best_pos else "-"}
                </div>
                <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: var(--radius-sm);">
                    🔻 <strong>ตัวฉุดดอยหนัก:</strong> {f"[{worst_pos['ticker']}] {escape(worst_pos['name'])} ({worst_pos['unrealized_pl_pct']:.1f}%)" if worst_pos else "-"}
                </div>
            </div>
            <ul class="layman-checklist">
                <li>💡 <strong>1. ห้ามรีบถัวเฉลี่ยหุ้นที่กำลังดิ่ง:</strong> หุ้นที่ติดลบต้องรอให้กราฟสร้างฐานชัดเจนก่อน อย่าเอาเงินดีไปถมหุ้นที่กำลังปรับฐาน.</li>
                <li>💡 <strong>2. ระวังวันประกาศงบการเงิน 14 วัน:</strong> หุ้นที่กำลังจะประกาศงบราคามักผันผวนสูง ให้ระงับการเติมเงินใหม่จนกว่างบจะออกเสร็จสิ้น.</li>
                <li>💡 <strong>3. ปล่อยให้กำไรทำงานต่อไป (Let Profits Run):</strong> หุ้นเทรนด์ขาขึ้นแข็งแรงให้ถือตามระบบ ไม่รีบขายหมูเพื่อไปถัวหุ้นขาดทุน.</li>
            </ul>
        </div>

        <!-- Sector Allocation -->
        <div class="section-header">🍰 2. สัดส่วนการลงทุนแยกตามกลุ่มธุรกิจ (Sector Allocation)</div>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>กลุ่มธุรกิจ (Sector)</th>
                        <th>แถบสัดส่วน</th>
                        <th style="text-align: right;">เปอร์เซ็นต์</th>
                        <th>การประเมินสำหรับมือใหม่</th>
                    </tr>
                </thead>
                <tbody>
                    {sector_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Holdings Table -->
        <div class="section-header">📈 3. สรุปสถานะการถือครอง (Current Holdings & Technical Status)</div>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>บริษัทและลักษณะธุรกิจ</th>
                        <th>Rating</th>
                        <th style="text-align: right;">สัดส่วน</th>
                        <th style="text-align: right;">ทุนเฉลี่ย</th>
                        <th style="text-align: right;">ราคาตลาด</th>
                        <th style="text-align: right;">แนวรับ / แนวต้าน</th>
                        <th style="text-align: right;">มูลค่ารวม ($ / ฿)</th>
                        <th style="text-align: right;">กำไร/ขาดทุน</th>
                        <th style="text-align: right;">1D Chg</th>
                        <th style="text-align: center;">Daily RSI</th>
                        <th style="text-align: center;">200D Trend</th>
                        <th>สถานะ & สัญญาณ</th>
                    </tr>
                </thead>
                <tbody>
                    {holdings_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Fundamentals & Institutional Targets -->
        <div class="section-header">🔬 4. งบการเงินและราคาเป้าหมายจากสถาบัน (Fundamentals & Wall St Targets)</div>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>บริษัท</th>
                        <th>สุขภาพงบ</th>
                        <th style="text-align: right;">Rev YoY</th>
                        <th style="text-align: right;">Net YoY</th>
                        <th style="text-align: right;">PEG Ratio</th>
                        <th style="text-align: right;">P/E</th>
                        <th style="text-align: right;">FCF กระแสเงินสด</th>
                        <th style="text-align: right;">เป้าหมายสถาบัน (Upside)</th>
                        <th style="text-align: center;">กรอบราคา (Low - High)</th>
                        <th>มติสถาบัน</th>
                        <th>ปฏิทินงบ</th>
                    </tr>
                </thead>
                <tbody>
                    {fund_rows_html}
                </tbody>
            </table>
        </div>

        <!-- Fresh Capital Rebalancing Top Picks -->
        <div class="section-header">💵 5. ถ้ามีเงินใหม่ ควรซื้อตัวไหนเพิ่ม? (Top Rebalancing Buys)</div>
        <div class="grid-3-cols">
            {top_cards_html}
        </div>

        <!-- Forbidden Buys -->
        {f'''
        <div class="forbidden-card">
            <h4 style="color: var(--rose); margin-bottom: 8px;">🚫 หุ้นในพอร์ตที่ "ห้ามซื้อเพิ่มเด็ดขาด" ในตอนนี้</h4>
            {forbidden_html}
        </div>
        ''' if forbidden else ''}

        <!-- Catalysts & Forward Intelligence -->
        <div class="section-header">🔭 6. บทวิเคราะห์เจาะลึกวิสัยทัศน์ & ตัวเร่งราคาในอนาคต (Forward Intelligence & Catalysts: {len(positions)} ตัว)</div>
        <div style="display: flex; flex-direction: column; gap: 24px;">
            {catalysts_html}
        </div>

        <!-- 5 Golden Rules -->
        <div class="card" style="margin-top: 24px;">
            <h3 style="margin-bottom: 12px;">🛡️ กฎเหล็ก 5 ข้อห้ามเด็ดขาดของมือใหม่</h3>
            <ol style="margin-left: 20px; display: flex; flex-direction: column; gap: 8px; font-size: 0.95rem;">
                <li><strong>ห้ามถัวหุ้นที่กำไรหดตัวหรือกำลังมีคดีความ:</strong> ยิ่งถัวเงินจะยิ่งจม อย่าเอาเงินดีไปถมในธุรกิจที่กำลังมีปัญหา.</li>
                <li><strong>ห้ามทุ่มเงินซื้อไม้เดียวหมดหน้าตัก:</strong> ให้แบ่งเงินเป็น 2 ถึง 3 ไม้เสมอ เพื่อรองรับการพักฐาน.</li>
                <li><strong>ห้ามซื้อหุ้นก่อนวันประกาศงบการเงิน 14 วัน:</strong> วันประกาศงบราคามักผันผวนสูง ควรรอให้งบออกเสร็จสิ้นก่อน.</li>
                <li><strong>ห้ามขายหุ้นที่กำลังทำกำไรเพื่อเอาเงินไปถัวหุ้นที่ขาดทุนหนัก:</strong> อย่าตัดดอกไม้ทิ้งเพื่อไปรดน้ำวัชพืช.</li>
                <li><strong>ห้ามถือหุ้นโดยไม่มีจุดตัดขาดทุน (Stop Loss):</strong> ยอมขาดทุนเล็กน้อย 5% แก้ไขได้ง่ายกว่าการปล่อยให้ติดลบ 50%.</li>
            </ol>
        </div>

        <!-- Disclaimer -->
        <div class="disclaimer-card">
            ⚠️ <strong>ข้อสงวนสิทธิ์และความเสี่ยง (Risk Disclaimer):</strong> รายงานนี้สร้างขึ้นโดยระบบวิเคราะห์ข้อมูลอัตโนมัติจากข้อมูลตลาดสาธารณะและสถิติ TradingView เพื่อเป็นข้อมูลประกอบการตัดสินใจและให้ความรู้เท่านั้น ไม่ใช่คำแนะนำในการลงทุน ซื้อ หรือขายหลักทรัพย์ ผู้ลงทุนต้องศึกษาข้อมูล ทำความเข้าใจความเสี่ยง และใช้วิจารณญาณของตนเองก่อนการตัดสินใจลงทุนทุกครั้ง.
            <div style="margin-top: 8px; font-size: 0.75rem;">Report generated by Filter-Stock Automated Engine. All rights reserved.</div>
        </div>
    </div>
    {get_chart_modal_component()}
</body>
</html>
"""
    return html


def generate_recovery_html(summary: Dict[str, Any]) -> str:
    """
    Render portfolio recovery analysis into a standalone, luxury dark-themed HTML report.
    """
    port_name = summary.get("portfolio_name", "Portfolio")
    fx = summary.get("fx_rate", 33.62)
    count = summary.get("total_underwater_count", 0)
    loss_usd = summary.get("total_underwater_loss_usd", 0.0)
    loss_thb = summary.get("total_underwater_loss_thb", 0.0)
    positions = summary.get("positions", [])
    now_str = datetime.now().strftime("%d %b %Y, %H:%M")
    is_thb = summary.get("base_currency") == "THB"
    curr_sym = "฿" if is_thb else "$"
    sub_sym = "$" if is_thb else "฿"

    # Table rows
    table_rows = ""
    deep_dive_cards = ""
    for p in positions:
        t = p["ticker"]
        name = escape(p["name"])
        biz = escape(p.get("business_summary") or "")
        avg = p["avg_cost"]
        c = p["close"]
        loss_pct = p["unrealized_pl_pct"]
        loss_u = p["unrealized_pl"]
        be_gap = p["pct_to_breakeven"]
        f = p["fundamentals"]
        sl = p["hard_stop_loss"]
        t_avg = p.get("price_target_average")
        t_up = p.get("target_upside_pct")
        verdict = p["action_verdict"]
        cat = p.get("catalysts", {})
        dca_half = p["dca_half"]
        gain_rot = p["gain_pct_needed_on_rotation"]

        rev_g = f"{f['rev_growth_yoy']:+.1f}%" if f.get('rev_growth_yoy') is not None else "-"
        net_g = f"{f['net_inc_growth_yoy']:+.1f}%" if f.get('net_inc_growth_yoy') is not None else "-"
        fund_str = f"Rev {rev_g} | Net {net_g}"

        earn_str = f"{p['days_to_earnings']}d" if p.get('days_to_earnings') is not None else "-"
        earn_badge = f"<span class='badge badge-rose'>⚠️ {earn_str}</span>" if p.get("is_earnings_imminent") else f"<span class='badge badge-neutral'>{earn_str}</span>"

        target_str = f"<strong>{curr_sym}{t_avg:,.1f}</strong> <span class='text-emerald small'>({t_up:+.0f}%)</span>" if (t_avg and t_up is not None) else (f"<strong>{curr_sym}{t_avg:,.1f}</strong>" if t_avg else "-")
        loss_disp = f"(-฿{p.get('loss_thb', abs(loss_u)):,.0f})" if is_thb else f"(-${abs(loss_u):,.1f})"

        onclick_js = _make_chart_onclick(p, is_thb=is_thb)

        table_rows += f"""
        <tr>
            <td><span class="ticker-pill clickable-ticker" onclick="{onclick_js}" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{t} 📈</span></td>
            <td><div class="fw-bold">{name}</div><div class="text-muted small">{biz}</div></td>
            <td style="text-align: right;">{curr_sym}{avg:,.2f}<br><span class="text-muted small">{curr_sym}{c:,.2f}</span></td>
            <td style="text-align: right;" class="text-rose fw-bold">{loss_pct:.1f}%<br><span class="small">{loss_disp}</span></td>
            <td style="text-align: right;">
                <div class="text-emerald fw-bold">รับ {curr_sym}{p.get('key_support', 0):,.2f}</div>
                <div class="text-amber small">ต้าน {curr_sym}{p.get('key_resistance', 0):,.2f}</div>
            </td>
            <td style="text-align: right;" class="text-emerald fw-bold">+{be_gap:.1f}%</td>
            <td style="text-align: right;">{target_str}</td>
            <td style="text-align: center;"><span class="badge badge-neutral">{fund_str}</span></td>
            <td style="text-align: center;">{earn_badge}</td>
            <td><span class="badge badge-amber">{verdict}</span></td>
        </tr>
        """

        # Forward Outlook & Deep Recovery Dossier
        fo = p.get("forward_outlook", {})
        thesis_title = fo.get("thesis_title", f"การวิเคราะห์เจาะลึกทิศทางธุรกิจ {t}")
        quality_badge = fo.get("quality_badge", "🟡 Growth & Recovery Candidate")
        drivers = fo.get("future_growth_drivers", [])
        drawdown_reasons = fo.get("drawdown_root_cause", [])
        timeline = fo.get("catalyst_timeline", [])
        ws_verdict = fo.get("wall_street_verdict", "")
        tailored_roadmap = fo.get("tailored_roadmap", p.get("layman_action", ""))
        invalidation_risk = fo.get("invalidation_risk", f"หลุดจุดตัดขาดทุน {curr_sym}{sl:,.2f} ต้องลดพอร์ตเพื่อจำกัดความเสียหาย")

        drivers_li = "".join([f"<li>{d}</li>" for d in drivers]) if drivers else "<li>กำลังติดตามข้อมูลปัจจัยขับเคลื่อนเชิงลึก</li>"
        drawdown_li = "".join([f"<li>{r}</li>" for r in drawdown_reasons]) if drawdown_reasons else "<li>การพักฐานตามภาวะตลาดรวมและแรงกดดันทางเทคนิค</li>"

        timeline_steps = "".join([
            f"""<div class="timeline-step">
                <span class="timeline-step-badge">{item.get('period', '-')}</span>
                <div class="timeline-step-desc">{item.get('event', '-')}</div>
            </div>"""
            for item in timeline
        ]) if timeline else "<div class='text-muted small'>ไม่มีกำหนดการตัวเร่งราคาเฉพาะในระยะสั้น</div>"

        # News Headlines & Catalysts
        bull_items = _news_items_html(cat.get("bullish", []), "ไม่มีข่าวเชิงบวกเด่นชัดในสัปดาห์นี้.")
        bear_items = _news_items_html(cat.get("bearish", []), "ไม่มีข่าวร้ายรุนแรงในระยะสั้น.")

        # Wall Street Consensus Targets
        t_low = p.get("price_target_low")
        t_high = p.get("price_target_high")
        t_low_str = f"{curr_sym}{t_low:,.2f}" if t_low else "-"
        t_avg_str = f"{curr_sym}{t_avg:,.2f}" if t_avg else "-"
        t_high_str = f"{curr_sym}{t_high:,.2f}" if t_high else "-"
        
        ratings_summary = ""
        if p.get("rec_buy") is not None:
            ratings_summary = f"<span class='text-emerald fw-bold'>🟢 Buy: {p.get('rec_buy', 0)}</span> &nbsp;|&nbsp; <span class='text-amber fw-bold'>🟡 Hold: {p.get('rec_hold', 0)}</span> &nbsp;|&nbsp; <span class='text-rose fw-bold'>🔴 Sell: {p.get('rec_sell', 0)}</span>"

        loss_card_str = f"-฿{p.get('loss_thb', abs(loss_u)):,.2f} THB" if is_thb else f"-${abs(loss_u):,.2f} USD"
        dca_cash_disp = f"฿{dca_half['cash_needed_usd']:,.2f}" if is_thb else f"${dca_half['cash_needed_usd']:,.2f}"

        onclick_js = _make_chart_onclick(p, is_thb=is_thb)

        deep_dive_cards += f"""
        <div class="card outlook-card" style="margin-bottom: 32px; border-left: 4px solid var(--rose);">
            <!-- Card Header -->
            <div class="outlook-card-header">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <span class="ticker-pill clickable-ticker" style="font-size: 1.15rem; padding: 4px 12px;" onclick="{onclick_js}" title="คลิกเปิดดูกราฟเทคนิคัลอัจฉริยะ">{t} 📈</span>
                    <strong style="font-size: 1.25rem;">{name}</strong>
                    <span class="badge badge-neutral" style="font-size: 0.8rem;">{escape(p.get('sector') or '')} • {escape(p.get('industry') or '')}</span>
                    <span class="badge badge-neutral" style="font-size: 0.8rem; background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.25);">{quality_badge}</span>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                    <span class="badge badge-rose" style="font-size: 0.95rem; padding: 5px 12px;">ติดลบ {loss_pct:.1f}% ({loss_card_str})</span>
                    <span class="badge badge-amber" style="font-size: 0.95rem; padding: 5px 12px;">{verdict}</span>
                    <button onclick="{onclick_js}" style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); color: #60a5fa; border-radius: 6px; padding: 5px 12px; font-size: 0.85rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; transition: all 0.2s;">📈 ดูกราฟสด & แนวรับแนวต้าน</button>
                </div>
            </div>

            <!-- Thesis Banner -->
            <div class="thesis-banner">
                <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #93c5fd; margin-bottom: 4px;">🔭 วิสัยทัศน์และธีมการเติบโตหลักในอนาคต (Growth Thesis):</div>
                <div style="color: #ffffff; font-size: 1.05rem; line-height: 1.4;">{thesis_title}</div>
            </div>

            <!-- Key Metrics Strip -->
            <div class="kpi-strip">
                <div class="kpi-box">
                    <div class="text-muted small">ต้นทุนของคุณ (Cost)</div>
                    <div class="fw-bold" style="font-size: 1.15rem;">{curr_sym}{avg:,.2f}</div>
                    <div class="text-muted small">จำนวน: {p.get('shares', 0):,.4f} หุ้น</div>
                </div>
                <div class="kpi-box">
                    <div class="text-muted small">ราคาตลาด (Market Price)</div>
                    <div class="fw-bold" style="font-size: 1.15rem;">{curr_sym}{c:,.2f}</div>
                    <div class="text-rose small">ห่างจากทุน: {loss_pct:.1f}%</div>
                </div>
                <div class="kpi-box">
                    <div class="text-muted small">ระยะทางดีดคืนทุน (Gap)</div>
                    <div class="text-emerald fw-bold" style="font-size: 1.15rem;">+{be_gap:.1f}%</div>
                    <div class="text-muted small">ต้องการราคาแตะ {curr_sym}{avg:,.2f}</div>
                </div>
                <div class="kpi-box">
                    <div class="text-muted small">แนวรับดักช้อน (Key Support)</div>
                    <div class="text-emerald fw-bold" style="font-size: 1.15rem;">{curr_sym}{p.get('key_support', 0):,.2f}</div>
                    <div class="text-muted small">{p.get('support_desc', '-')}</div>
                </div>
                <div class="kpi-box">
                    <div class="text-muted small">แนวต้านรีบาวด์ (Key Resistance)</div>
                    <div class="text-amber fw-bold" style="font-size: 1.15rem;">{curr_sym}{p.get('key_resistance', 0):,.2f}</div>
                    <div class="text-muted small">{p.get('resistance_desc', '-')}</div>
                </div>
                <div class="kpi-box">
                    <div class="text-muted small">จุดตัดขาดทุน (SL Guard)</div>
                    <div class="text-rose fw-bold" style="font-size: 1.15rem;">{curr_sym}{sl:,.2f}</div>
                    <div class="text-muted small">หลุดต้องลดพอร์ต</div>
                </div>
            </div>

            <!-- Future Drivers vs Drawdown Root Causes -->
            <div class="outlook-grid-2">
                <div class="outlook-subcard" style="border-top: 3px solid var(--emerald);">
                    <div class="subcard-title text-emerald">
                        <span>🚀 4 ปัจจัยขับเคลื่อนการเติบโตในอนาคต (1-12 เดือนข้างหน้า)</span>
                    </div>
                    <ul class="outlook-list drivers">
                        {drivers_li}
                    </ul>
                </div>
                <div class="outlook-subcard" style="border-top: 3px solid var(--rose);">
                    <div class="subcard-title text-rose">
                        <span>🔍 สาเหตุที่แท้จริงที่ทำให้ราคาพักตัว / ติดลบ (Drawdown Root Cause)</span>
                    </div>
                    <ul class="outlook-list drawdown">
                        {drawdown_li}
                    </ul>
                </div>
            </div>

            <!-- Catalyst Timeline -->
            <div class="outlook-subcard" style="margin-bottom: 18px; border-top: 3px solid var(--blue);">
                <div class="subcard-title text-blue">
                    <span>⏳ ไทม์ไลน์ตัวเร่งราคาและการฟื้นตัว (Catalyst Timeline & Milestones)</span>
                </div>
                <div class="timeline-grid">
                    {timeline_steps}
                </div>
            </div>

            <!-- Wall Street Consensus vs User Cost -->
            <div class="wallstreet-box">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div class="fw-bold" style="font-size: 0.95rem; color: #10b981;">🎯 การประเมินมูลค่าของสถาบันการเงินวอลล์สตรีท เทียบกับต้นทุนของคุณ</div>
                    <div class="small">{ratings_summary}</div>
                </div>
                <div class="ws-targets-grid">
                    <div class="ws-target-cell">
                        <div class="text-muted small">ต้นทุนของคุณ</div>
                        <div class="fw-bold text-main" style="font-size: 1.1rem;">{curr_sym}{avg:,.2f}</div>
                    </div>
                    <div class="ws-target-cell">
                        <div class="text-muted small">ราคาปัจจุบัน</div>
                        <div class="fw-bold text-rose" style="font-size: 1.1rem;">{curr_sym}{c:,.2f}</div>
                    </div>
                    <div class="ws-target-cell">
                        <div class="text-muted small">เป้าต่ำสุด (Low Target)</div>
                        <div class="fw-bold text-amber" style="font-size: 1.1rem;">{t_low_str}</div>
                    </div>
                    <div class="ws-target-cell">
                        <div class="text-muted small">เป้าเฉลี่ย (Average Target)</div>
                        <div class="fw-bold text-emerald" style="font-size: 1.1rem;">{t_avg_str} <span class="small">({t_up:+.0f}%)</span></div>
                    </div>
                    <div class="ws-target-cell">
                        <div class="text-muted small">เป้าสูงสุด (High Target)</div>
                        <div class="fw-bold text-blue" style="font-size: 1.1rem;">{t_high_str}</div>
                    </div>
                </div>
                <div class="small" style="color: #cbd5e1; background: rgba(0, 0, 0, 0.2); padding: 8px 12px; border-radius: 6px; border-left: 3px solid var(--emerald); margin-top: 6px;">
                    📌 <strong>มุมมองเปรียบเทียบ:</strong> {ws_verdict}
                </div>
            </div>

            <!-- Live News & Market Catalysts -->
            <div class="grid-2-cols" style="gap: 14px; margin-bottom: 18px;">
                <div class="bull-box" style="background: rgba(16, 185, 129, 0.04); padding: 14px; border-radius: var(--radius-sm); border: 1px solid rgba(16, 185, 129, 0.2);">
                    <div class="cat-label text-emerald fw-bold small" style="margin-bottom: 8px;">🟢 พาดหัวข่าวจริงเชิงบวกและปัจจัยหนุน (Positive News):</div>
                    <ul class="cat-list">{bull_items}</ul>
                </div>
                <div class="bear-box" style="background: rgba(244, 63, 94, 0.04); padding: 14px; border-radius: var(--radius-sm); border: 1px solid rgba(244, 63, 94, 0.2);">
                    <div class="cat-label text-rose fw-bold small" style="margin-bottom: 8px;">🔴 พาดหัวข่าวจริงที่ต้องระวังและความเสี่ยง (Risk Factors):</div>
                    <ul class="cat-list">{bear_items}</ul>
                </div>
            </div>

            <!-- Tailored Strategic Roadmap & Invalidation Risk -->
            <div class="roadmap-callout">
                <div style="font-size: 0.85rem; font-weight: 700; color: #fbbf24; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                    🧭 แผนยุทธศาสตร์ฟันธงสำหรับ {t} โดยเฉพาะ (Tailored Gameplan):
                </div>
                <div style="font-size: 0.95rem; color: #ffffff; line-height: 1.5; margin-bottom: 10px;">
                    {tailored_roadmap}
                </div>
                <div style="font-size: 0.85rem; color: #fca5a5; background: rgba(244, 63, 94, 0.08); padding: 8px 12px; border-radius: 6px; border-left: 3px solid var(--rose);">
                    🛑 <strong>สัญญาณเตือนภัย / จุดยอมแพ้ (Invalidation Risk):</strong> {invalidation_risk}
                </div>
            </div>

            <!-- Tactical Execution Simulation (Smart DCA vs Rotation) -->
            <div class="table-responsive" style="margin-bottom: 0;">
                <table>
                    <thead>
                        <tr>
                            <th>ทางเลือกกลยุทธ์</th>
                            <th>แผนการปฏิบัติการ</th>
                            <th style="text-align: right;">เงินที่ต้องใช้เพิ่ม</th>
                            <th style="text-align: right;">จุดขายเป้าหมาย</th>
                            <th>ความคุ้มค่าและความเสี่ยง</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>1. ถือรอเฉยๆ (Hold)</strong></td>
                            <td>ไม่เติมเงิน รอราคาฟื้นตัวกลับหาทุนเดิมตามปัจจัยพื้นฐาน</td>
                            <td style="text-align: right;">{curr_sym}0.00</td>
                            <td style="text-align: right;"><strong>{curr_sym}{avg:,.2f}</strong> (+{be_gap:.1f}%)</td>
                            <td><span class="text-muted">ความเสี่ยงต่ำสุด แต่เงินจมและเสียโอกาสทำกำไร</span></td>
                        </tr>
                        <tr>
                            <td><strong>2. Smart DCA</strong></td>
                            <td>ซื้อเพิ่ม {dca_half['shares_to_buy']:.4f} หุ้น ที่แนวรับ <strong>{curr_sym}{p.get('key_support', 0):,.2f}</strong> ({p.get('support_desc', '-')})</td>
                            <td style="text-align: right;" class="text-amber"><strong>{dca_cash_disp}</strong></td>
                            <td style="text-align: right;" class="text-emerald"><strong>{curr_sym}{dca_half['new_avg_cost']:,.2f}</strong> (+{dca_half['new_breakeven_gain_pct']:.1f}%)</td>
                            <td><span class="text-emerald">ดึงทุนต่ำลง คืนทุนเร็วขึ้น (ห้ามถัวหากใกล้วันงบออก)</span></td>
                        </tr>
                        <tr>
                            <td><strong>3. สลับตัว (Rotation)</strong></td>
                            <td>ตัดขายแล้วย้ายเงินที่เหลือ {curr_sym}{p['current_val']:,.2f} ไปเข้าหุ้น Dip ตัวแกร่ง</td>
                            <td style="text-align: right;">{curr_sym}0.00</td>
                            <td style="text-align: right;" class="text-blue"><strong>หุ้นใหม่กำไร +{gain_rot:.1f}%</strong></td>
                            <td><span class="text-muted">เหมาะเฉพาะเมื่อพื้นฐานหุ้นเดิมพัง หรือกำไรหดตัวยาวนาน</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Recovery & Drawdown Analyzer - {port_name}</title>
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

        .grid-3-cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; margin-bottom: 24px; }}
        .grid-2-cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 18px; margin-bottom: 24px; }}

        .card {{
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: var(--radius-md); padding: 22px;
        }}

        .kpi-label {{ font-size: 0.85rem; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 1.85rem; font-weight: 700; font-family: 'Inter', sans-serif; }}
        .kpi-subtext {{ font-size: 0.88rem; color: var(--text-muted); margin-top: 6px; }}

        .ticker-pill {{
            background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 2px 8px; border-radius: 6px; font-weight: 700; font-family: 'Inter', sans-serif; text-decoration: none;
        }}

        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }}
        .badge-rose {{ background: rgba(244, 63, 94, 0.15); color: var(--rose); border: 1px solid rgba(244, 63, 94, 0.3); }}
        .badge-amber {{ background: rgba(245, 158, 11, 0.15); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.3); }}
        .badge-emerald {{ background: rgba(16, 185, 129, 0.15); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); }}
        .badge-neutral {{ background: rgba(255, 255, 255, 0.05); color: var(--text-secondary); border: 1px solid var(--border-color); }}

        .table-responsive {{ overflow-x: auto; border-radius: var(--radius-md); border: 1px solid var(--border-color); margin-bottom: 24px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; background: var(--bg-card); }}
        th {{ background: rgba(15, 23, 42, 0.95); color: var(--text-secondary); padding: 14px 16px; font-weight: 600; border-bottom: 1px solid var(--border-color); font-size: 0.75rem; text-transform: uppercase; }}
        td {{ padding: 14px 16px; border-bottom: 1px solid var(--border-subtle); }}

        .text-emerald {{ color: var(--emerald); }}
        .text-rose {{ color: var(--rose); }}
        .text-amber {{ color: var(--amber); }}
        .text-blue {{ color: var(--blue); }}
        .text-muted {{ color: var(--text-muted); }}
        .fw-bold {{ font-weight: 700; }}
        .small {{ font-size: 0.8rem; }}

        .cat-list {{ list-style: none; display: flex; flex-direction: column; gap: 8px; font-size: 0.85rem; }}
        .cat-list li {{ padding-left: 10px; border-left: 2px solid var(--border-color); }}
        .cat-list a.news-headline-link {{
            color: var(--text-main);
            text-decoration: underline;
            text-decoration-color: rgba(255, 255, 255, 0.25);
            text-underline-offset: 3px;
            transition: color 0.15s ease, text-decoration-color 0.15s ease;
        }}
        .cat-list a.news-headline-link:hover {{
            color: #60a5fa;
            text-decoration-color: #60a5fa;
        }}
        .cat-list .source-tag {{ color: var(--text-secondary); }}

        /* Forward Outlook & Dossier Styles */
        .outlook-card {{
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(15, 23, 42, 0.88));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius-md);
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        }}
        .outlook-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 18px;
        }}
        .thesis-banner {{
            background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.10));
            border-left: 4px solid var(--blue);
            padding: 12px 18px;
            border-radius: var(--radius-sm);
            margin-bottom: 18px;
        }}
        .kpi-strip {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 18px;
        }}
        .kpi-box {{
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: var(--radius-sm);
            padding: 10px 14px;
        }}
        .outlook-grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 16px;
            margin-bottom: 18px;
        }}
        .outlook-subcard {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            padding: 16px;
        }}
        .subcard-title {{
            font-size: 0.88rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            margin-bottom: 10px;
        }}
        .outlook-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-size: 0.88rem;
            line-height: 1.5;
        }}
        .outlook-list li {{
            position: relative;
            padding-left: 18px;
            color: #cbd5e1;
        }}
        .outlook-list.drivers li::before {{
            content: "✦";
            position: absolute;
            left: 2px;
            color: var(--emerald);
            font-size: 0.8rem;
        }}
        .outlook-list.drawdown li::before {{
            content: "▼";
            position: absolute;
            left: 2px;
            color: var(--rose);
            font-size: 0.75rem;
        }}
        .timeline-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
        }}
        .timeline-step {{
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: var(--radius-sm);
            padding: 12px 14px;
        }}
        .timeline-step-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            margin-bottom: 6px;
        }}
        .timeline-step-desc {{
            font-size: 0.85rem;
            color: #e2e8f0;
            line-height: 1.4;
        }}
        .wallstreet-box {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.04), rgba(15, 23, 42, 0.6));
            border: 1px solid rgba(16, 185, 129, 0.22);
            border-radius: var(--radius-sm);
            padding: 16px 20px;
            margin-bottom: 18px;
        }}
        .ws-targets-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin: 12px 0;
            text-align: center;
        }}
        .ws-target-cell {{
            background: rgba(0, 0, 0, 0.25);
            padding: 8px 10px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .roadmap-callout {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(15, 23, 42, 0.8));
            border-left: 4px solid var(--amber);
            border-radius: var(--radius-sm);
            padding: 16px 20px;
            margin-bottom: 18px;
        }}

        .disclaimer-card {{
            background: rgba(0, 0, 0, 0.4); border: 1px solid var(--border-color); border-radius: var(--radius-md);
            padding: 20px; margin-top: 32px; font-size: 0.82rem; color: var(--text-muted); text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div>
                <h1>🧗 แผนกลยุทธ์แก้หลุดดอย 360 องศา</h1>
                <div class="text-muted">พอร์ต: <strong>{port_name}</strong></div>
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <span class="meta-pill">💱 <strong>FX Rate:</strong> {fx:.2f} THB/USD</span>
                <span class="meta-pill">🕒 <strong>อัปเดต:</strong> {now_str}</span>
            </div>
        </header>

        <div class="grid-3-cols">
            <div class="card">
                <div class="kpi-label">🔻 หุ้นที่ติดลบในพอร์ต</div>
                <div class="kpi-value text-rose">{count} ตัว</div>
                <div class="kpi-subtext">เรียงตามเปอร์เซ็นต์ขาดทุนจากมากไปน้อย</div>
            </div>
            <div class="card">
                <div class="kpi-label">{'💸 ยอดขาดทุนรวม (THB)' if is_thb else '💸 ยอดขาดทุนรวม (USD)'}</div>
                <div class="kpi-value text-rose">{'-฿' + f'{loss_thb:,.2f}' if is_thb else '-$' + f'{loss_usd:,.2f}'}</div>
                <div class="kpi-subtext">{'เงินลงทุนที่จมอยู่ ณ ราคาตลาดปัจจุบัน' if is_thb else 'เงินลงทุนที่จมอยู่ ณ ราคาตลาดปัจจุบัน'}</div>
            </div>
            <div class="card">
                <div class="kpi-label">{'฿ ยอดเทียบเท่า (USD)' if is_thb else '฿ ยอดขาดทุนรวม (THB)'}</div>
                <div class="kpi-value text-rose">{'-$' + f'{loss_usd:,.2f}' if is_thb else '-฿' + f'{loss_thb:,.2f}'}</div>
                <div class="kpi-subtext">คำนวณที่อัตราแลกเปลี่ยน {fx:.2f} THB/USD</div>
            </div>
        </div>

        <h3 style="margin-bottom: 14px;">📊 1. ตารางเปรียบเทียบสภาวะหุ้นติดลบและแผนปฏิบัติการ</h3>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>บริษัทและลักษณะธุรกิจ</th>
                        <th style="text-align: right;">ทุน / ตลาด</th>
                        <th style="text-align: right;">ขาดทุน (%)</th>
                        <th style="text-align: right;">แนวรับ / แนวต้าน</th>
                        <th style="text-align: right;">ดีดคืนทุน</th>
                        <th style="text-align: right;">เป้าหมายสถาบัน (Upside)</th>
                        <th style="text-align: center;">งบการเงิน (YoY)</th>
                        <th style="text-align: center;">ปฏิทินงบ</th>
                        <th>แผนแนะนำที่ปฏิบัติได้จริง</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <h3 style="margin: 32px 0 16px 0;">🛠️ 2. แผนปฏิบัติการแก้ขาดทุนเจาะลึกรายตัว (Actionable Playbooks)</h3>
        {deep_dive_cards}

        <div class="card" style="margin-top: 24px;">
            <h3 style="margin-bottom: 12px;">📱 คู่มือการเปิดแอปไปตั้งคำสั่งจริง สำหรับมือใหม่ (Broker Execution Guide)</h3>
            <ol style="margin-left: 20px; display: flex; flex-direction: column; gap: 10px; font-size: 0.95rem;">
                <li><strong>ประเภทคำสั่งที่ควรใช้ (Order Type):</strong> ให้ใช้คำสั่งแบบ <strong>Limit Order</strong> (ระบุราคาที่ต้องการซื้อหรือขายเอง) เสมอ. ห้ามใช้ Market Order เด็ดขาด เพราะระบบจะจับคู่ที่ราคาตลาดทันทีซึ่งอาจได้ราคาแพงกว่าที่ตั้งใจไว้.</li>
                <li><strong>การตั้งจุดยอมแพ้ตัดขาดทุน (Stop Loss) ในแอป (Dime / InnovestX / IBKR):</strong> เข้าไปที่เมนู Order Details ของหุ้นตัวที่ต้องการ แล้วเลือกประเภทคำสั่ง <strong>Stop Limit</strong> หรือ <strong>Stop Loss</strong> ระบุราคาตามค่า Stop-Loss Guard.</li>
                <li><strong>การตั้งเป้าหมายขายทำกำไร / เท่าทุน (Take Profit / Breakeven Order):</strong> ตั้งคำสั่งขายล่วงหน้า (Good 'Til Canceled - GTC) ไว้ที่ระดับราคาต้นทุนเดิม หรือราคา New Breakeven Cost หลังทำ Smart DCA.</li>
            </ol>
        </div>

        <div class="disclaimer-card">
            ⚠️ <strong>ข้อสงวนสิทธิ์และความเสี่ยง (Risk Disclaimer):</strong> รายงานนี้สร้างขึ้นโดยระบบวิเคราะห์ข้อมูลอัตโนมัติจากข้อมูลตลาดสาธารณะและสถิติ TradingView เพื่อเป็นข้อมูลประกอบการตัดสินใจและให้ความรู้เท่านั้น ไม่ใช่คำแนะนำในการลงทุน ซื้อ หรือขายหลักทรัพย์ ผู้ลงทุนต้องศึกษาข้อมูล ทำความเข้าใจความเสี่ยง และใช้วิจารณญาณของตนเองก่อนการตัดสินใจลงทุนทุกครั้ง.
            <div style="margin-top: 8px; font-size: 0.75rem;">Report generated by Filter-Stock Automated Engine. All rights reserved.</div>
        </div>
    </div>
    {get_chart_modal_component()}
</body>
</html>
"""
    return html

