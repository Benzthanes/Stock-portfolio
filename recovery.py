#!/usr/bin/env python3
"""
Stock Recovery & Breakeven Strategy Analyzer (เทคนิคแก้หลุดดอย 360 องศา)
Calculates quantitative recovery paths, fundamental viability, earnings calendar risks,
Bullish vs Bearish catalyst breakdowns, and layman-friendly beginner verdicts.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.portfolio import load_portfolio
from src.tradingview import fetch_screener_data
from src.news import get_catalyst_breakdown, fetch_batch_catalysts
from src.profiles import get_business_summary
from src.html_report import generate_recovery_html


def evaluate_fundamental_health(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate business quality, earnings growth, valuation, and analyst consensus.
    """
    rev_growth = data.get("total_revenue_yoy_growth_ttm")
    net_inc_growth = data.get("net_income_yoy_growth_ttm")
    peg = data.get("price_earnings_growth_ttm")
    pe = data.get("price_earnings_ttm")
    roe = data.get("return_on_equity_fq")
    rec_mark = data.get("recommendation_mark")
    fcf = data.get("free_cash_flow_ttm")

    if rec_mark is not None:
        if rec_mark <= 1.5:
            rec_label = "Strong Buy (มุมมองบวกมาก)"
        elif rec_mark <= 2.2:
            rec_label = "Buy (แนะนำซื้อ)"
        elif rec_mark <= 3.2:
            rec_label = "Hold (แนะนำถือ)"
        else:
            rec_label = "Underperform / Sell (แนะนำลดสัดส่วน)"
    else:
        rec_label = "N/A"

    if net_inc_growth is not None and net_inc_growth > 20.0 and (rev_growth or 0) > 10.0:
        quality_tier = "🟢 High Quality Growth (ธุรกิจเติบโตสูง)"
        quality_score = 3
    elif net_inc_growth is not None and net_inc_growth >= 0.0:
        quality_tier = "🟡 Resilient / Stable (ธุรกิจประคองตัวได้)"
        quality_score = 2
    elif net_inc_growth is not None and net_inc_growth < 0.0:
        quality_tier = "🔴 Profit Contraction (กำไรหดตัว ชะลอตัว)"
        quality_score = 1
    else:
        quality_tier = "⚪ Neutral (ข้อมูลไม่เพียงพอ)"
        quality_score = 1

    return {
        "rev_growth_yoy": round(rev_growth, 2) if rev_growth is not None else None,
        "net_inc_growth_yoy": round(net_inc_growth, 2) if net_inc_growth is not None else None,
        "peg": round(peg, 2) if peg is not None else None,
        "pe": round(pe, 2) if pe is not None else None,
        "roe": round(roe, 2) if roe is not None else None,
        "fcf": fcf,
        "rec_mark": round(rec_mark, 2) if rec_mark is not None else None,
        "rec_label": rec_label,
        "quality_tier": quality_tier,
        "quality_score": quality_score
    }


from src.outlook import get_forward_outlook



def analyze_recovery(ticker: str, custom_shares: Optional[float] = None, custom_cost: Optional[float] = None, portfolio_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute quantitative recovery plans, fundamentals, earnings proximity, news, and business summary.
    """
    portfolio = load_portfolio(portfolio_path)
    holdings = portfolio.get("holdings", [])
    base_currency = str(portfolio.get("base_currency", "USD")).upper()
    curr_sym = "฿" if base_currency == "THB" else "$"
    
    pos = next((h for h in holdings if h["ticker"].upper() == ticker.upper()), None)
    
    if not pos and custom_cost is None:
        raise ValueError(
            f"หุ้น '{ticker.upper()}' ไม่ได้อยู่ในพอร์ตของคุณ กรุณาระบุต้นทุนเฉลี่ยด้วย '--cost <ราคา {base_currency}>' (และระบุ '--shares <จำนวนหุ้น>' เพิ่มเติมได้)"
        )

    shares = custom_shares if custom_shares is not None else (pos.get("shares", 1.0) if pos else 1.0)
    avg_cost = custom_cost if custom_cost is not None else (float(pos.get("avg_cost_thb") or pos.get("avg_cost_usd", 0.0)) if pos else 0.0)
    if shares <= 0:
        raise ValueError(f"Shares must be greater than 0 (got {shares}).")
    
    from src.universe import get_universe
    all_univ = get_universe("all")
    exchange = pos.get("exchange") if pos else all_univ.get(ticker.upper(), "NASDAQ")
    name = pos.get("name", ticker.upper()) if pos else ticker.upper()

    symbol_tv = f"{exchange}:{ticker.upper()}"
    market_data_list = fetch_screener_data([symbol_tv])
    if not market_data_list and exchange == "NASDAQ":
        # Try NYSE fallback
        alt_data = fetch_screener_data([f"NYSE:{ticker.upper()}"])
        if alt_data:
            market_data_list = alt_data
            exchange = "NYSE"
            symbol_tv = f"NYSE:{ticker.upper()}"
    if not market_data_list:
        raise ValueError(f"Unable to fetch market data for {symbol_tv} from TradingView.")

    data = market_data_list[0]
    close = data.get("close") or 0.0
    if close <= 0:
        raise ValueError(f"No valid close price for {symbol_tv} from TradingView.")
    atr = data.get("ATR") or (close * 0.03)
    sma20 = data.get("SMA20") or 0.0
    sma50 = data.get("SMA50") or 0.0
    sma200 = data.get("SMA200") or 0.0
    ema50 = data.get("EMA50") or 0.0
    rsi = data.get("RSI") or 0.0
    bb_lower = data.get("BB.lower") or 0.0

    current_val = shares * close
    total_cost = shares * avg_cost
    unrealized_pl = current_val - total_cost
    unrealized_pl_pct = (unrealized_pl / total_cost * 100.0) if total_cost > 0 else 0.0
    pct_to_breakeven = ((avg_cost - close) / close * 100.0) if close > 0 else 0.0

    # Earnings Proximity
    now_ts = time.time()
    next_earnings_ts = data.get("earnings_release_next_date") or data.get("earnings_release_date")
    days_to_earnings = None
    earnings_date_str = "-"
    is_earnings_imminent = False
    if next_earnings_ts and next_earnings_ts > now_ts:
        diff_days = (next_earnings_ts - now_ts) / 86400.0
        days_to_earnings = round(diff_days, 1)
        is_earnings_imminent = (days_to_earnings <= 14.0)
        try:
            earnings_date_str = datetime.fromtimestamp(next_earnings_ts, tz=timezone.utc).strftime("%d %b %Y")
        except Exception:
            earnings_date_str = str(next_earnings_ts)

    # Fundamental Health
    fundamentals = evaluate_fundamental_health(data)

    # Business Profile
    sector = data.get("sector", "-")
    industry = data.get("industry", "-")
    biz_summary = get_business_summary(ticker, sector=sector, industry=industry)

    # Catalysts & News (Bullish vs Bearish)
    catalysts = get_catalyst_breakdown(ticker, max_items=4)

    # Technical ATR Bands, Stop-Loss & Key Support Levels
    target_rebound_1atr = close + (1.0 * atr)
    target_rebound_2atr = close + (2.0 * atr)
    hard_stop_loss = round(close - (1.5 * atr), 2)

    if sma200 > 0 and abs(close - sma200) / close <= 0.08:
        key_support = round(sma200, 2)
        support_desc = "เส้น 200 วัน (SMA 200)"
    elif bb_lower > 0 and bb_lower < close:
        key_support = round(bb_lower, 2)
        support_desc = "ขอบล่าง Bollinger Band"
    else:
        key_support = round(hard_stop_loss, 2)
        support_desc = "แนวรับความผันผวน 1.5 ATR"

    # Key Resistance Levels
    bb_upper = data.get("BB.upper") or 0.0
    if sma20 > 0 and sma20 > close:
        key_resistance = round(sma20, 2)
        resistance_desc = "เส้น 20 วัน (SMA 20)"
    elif sma50 > 0 and sma50 > close:
        key_resistance = round(sma50, 2)
        resistance_desc = "เส้น 50 วัน (SMA 50)"
    elif bb_upper > 0 and bb_upper > close:
        key_resistance = round(bb_upper, 2)
        resistance_desc = "ขอบบน Bollinger Band"
    elif data.get("price_target_average") and data.get("price_target_average") > close:
        key_resistance = round(data.get("price_target_average"), 2)
        resistance_desc = "ราคาเป้าหมายเฉลี่ยสถาบัน"
    else:
        key_resistance = round(target_rebound_2atr, 2)
        resistance_desc = "เป้าหมายรีบาวด์ 2.0 ATR"

    # DCA Scenarios
    shares_add_a = shares * 0.5
    cost_add_a = shares_add_a * close
    new_avg_a = (total_cost + cost_add_a) / (shares + shares_add_a)
    be_gain_a = ((new_avg_a - close) / close * 100.0)

    shares_add_b = shares * 1.0
    cost_add_b = shares_add_b * close
    new_avg_b = (total_cost + cost_add_b) / (shares + shares_add_b)
    be_gain_b = ((new_avg_b - close) / close * 100.0)

    # Capital Rotation Simulation
    loss_amount = abs(unrealized_pl)
    gain_pct_needed_on_rotation = (loss_amount / current_val * 100.0) if current_val > 0 else 0.0

    # Concrete Recovery Classification
    if is_earnings_imminent:
        action_verdict = f"🟠 Freeze DCA (งบออกใน {days_to_earnings} วัน ห้ามถัวเด็ดขาด)"
        dca_permitted = False
        primary_playbook = "Freeze & Hedge"
        layman_action = f"งบจะออกในอีก {days_to_earnings} วัน ให้หยุดเติมเงินทันที รอให้งบออกก่อน ค่อยตัดสินใจเพื่อป้องกันราคาเปิดกระโดดลงแรง."
    elif fundamentals["quality_score"] == 3 and not is_earnings_imminent and rsi <= 35:
        action_verdict = "🟢 Smart DCA เมื่อคอนเฟิร์มฐาน (พื้นฐานโตแกร่ง ทยอยดึงทุนต่ำได้)"
        dca_permitted = True
        primary_playbook = "Smart DCA"
        layman_action = f"หุ้นตัวนี้ธุรกิจโตแรงมาก การตกใจของราคาเป็นโอกาสสะสม รอให้แท่งเทียนรายวันปิดเขียวที่แนวรับ ${key_support:.2f} ({support_desc}) ก่อนแล้วค่อยแบ่งเงินซื้อเพิ่มเพื่อดึงต้นทุนลง."
    elif avg_cost <= sma20 and sma20 > 0:
        action_verdict = "🎯 Rebound Exit (ทุนต่ำกว่า SMA20 รอเด้งออกเท่าทุน ไม่เติมเงิน)"
        dca_permitted = False
        primary_playbook = "Rebound Exit"
        layman_action = "ต้นทุนอยู่ใกล้แนวต้านมาก ไม่ต้องควักเงินเติมเพิ่ม แค่รอราคาเด้งทดสอบทุนแล้วตั้งขายคืนเงินต้นกลับมา."
    elif fundamentals["quality_score"] == 1:
        action_verdict = "🔄 Capital Rotation (กำไรหดตัว โยกเงินไปหุ้นผู้นำขาขึ้น)"
        dca_permitted = False
        primary_playbook = "Capital Rotation"
        layman_action = "กำไรของบริษัทเริ่มชะลอตัวลงอย่างชัดเจน ไม่ควรจมเงินไว้ แนะนำตัดขาดทุนแล้วโยกเงินไปเข้าหุ้นผู้นำขาขึ้นที่แข็งแรงกว่า."
    else:
        action_verdict = f"🛡️ ถือติดตามแนวรับ {curr_sym}{key_support:.2f} (เกาะเส้น Stop-Loss ไม่หลุดทรงหลัก)"
        dca_permitted = False
        primary_playbook = "Hold & Guard"
        layman_action = f"ถือรอดูอาการต่อไป โดยเฝ้าแนวรับสำคัญที่ {curr_sym}{key_support:.2f} และตั้งจุดตัดขาดทุนไว้ที่ {curr_sym}{hard_stop_loss:.2f} หากไม่หลุดเส้นนี้ยังไม่ต้องตกใจขาย."

    target_avg = data.get("price_target_average")
    target_high = data.get("price_target_high")
    target_low = data.get("price_target_low")
    target_median = data.get("price_target_median")
    rec_buy = data.get("recommendation_buy")
    rec_hold = data.get("recommendation_hold")
    rec_sell = data.get("recommendation_sell")
    target_upside_pct = round(((target_avg - close) / close * 100.0), 1) if (target_avg and close > 0) else None
    target_vs_cost_pct = round(((target_avg - avg_cost) / avg_cost * 100.0), 1) if (target_avg and avg_cost > 0) else None

    forward_outlook = get_forward_outlook(ticker, data, fundamentals, days_to_earnings, avg_cost, close)

    return {
        "ticker": ticker.upper(),
        "name": name,
        "exchange": exchange,
        "sector": sector,
        "industry": industry,
        "business_summary": biz_summary,
        "base_currency": base_currency,
        "curr_sym": curr_sym,
        "shares": shares,
        "avg_cost": avg_cost,
        "total_cost": total_cost,
        "close": close,
        "current_val": current_val,
        "unrealized_pl": unrealized_pl,
        "unrealized_pl_pct": unrealized_pl_pct,
        "pct_to_breakeven": pct_to_breakeven,
        "rsi": round(rsi, 2),
        "atr": round(atr, 2),
        "key_support": key_support,
        "support_desc": support_desc,
        "key_resistance": key_resistance,
        "resistance_desc": resistance_desc,
        "hard_stop_loss": hard_stop_loss,
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "ema50": round(ema50, 2),
        "sma200": round(sma200, 2),
        "bb_lower": round(bb_lower, 2),
        "target_rebound_1atr": round(target_rebound_1atr, 2),
        "target_rebound_2atr": round(target_rebound_2atr, 2),
        "days_to_earnings": days_to_earnings,
        "earnings_date_str": earnings_date_str,
        "is_earnings_imminent": is_earnings_imminent,
        "fundamentals": fundamentals,
        "catalysts": catalysts,
        "forward_outlook": forward_outlook,
        "price_target_average": round(target_avg, 2) if target_avg else None,
        "price_target_high": round(target_high, 2) if target_high else None,
        "price_target_low": round(target_low, 2) if target_low else None,
        "target_upside_pct": target_upside_pct,
        "target_vs_cost_pct": target_vs_cost_pct,
        "rec_buy": rec_buy,
        "rec_hold": rec_hold,
        "rec_sell": rec_sell,
        "action_verdict": action_verdict,
        "dca_permitted": dca_permitted,
        "primary_playbook": primary_playbook,
        "layman_action": layman_action,
        "gain_pct_needed_on_rotation": round(gain_pct_needed_on_rotation, 1),
        "dca_half": {
            "shares_to_buy": round(shares_add_a, 4),
            "cash_needed_usd": round(cost_add_a, 2),
            "cash_needed": round(cost_add_a, 2),
            "new_avg_cost": round(new_avg_a, 2),
            "new_breakeven_gain_pct": round(be_gain_a, 2),
        },
        "dca_equal": {
            "shares_to_buy": round(shares_add_b, 4),
            "cash_needed_usd": round(cost_add_b, 2),
            "cash_needed": round(cost_add_b, 2),
            "new_avg_cost": round(new_avg_b, 2),
            "new_breakeven_gain_pct": round(be_gain_b, 2),
        }
    }


def analyze_all_underwater(portfolio_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Scan portfolio for all underwater positions with catalysts, fundamentals, and business profiles.
    """
    portfolio = load_portfolio(portfolio_path)
    holdings = portfolio.get("holdings", [])
    base_currency = str(portfolio.get("base_currency", "USD")).upper()
    fx_rate = float(portfolio.get("fx_rate_usd_thb", 33.62))
    curr_sym = "฿" if base_currency == "THB" else "$"

    symbols = [f"{h.get('exchange', 'NASDAQ')}:{h['ticker']}" for h in holdings]
    market_data = fetch_screener_data(symbols)
    market_map = {d.get("name", "").upper(): d for d in market_data}
    market_map.update({d.get("ticker", "").upper(): d for d in market_data})

    tickers = [h["ticker"].upper() for h in holdings]
    all_catalysts = fetch_batch_catalysts(tickers, max_items=4)

    underwater_list = []
    total_underwater_loss_usd = 0.0
    total_underwater_loss_thb = 0.0

    for h in holdings:
        t = h["ticker"].upper()
        d = market_map.get(t, {})
        close = d.get("close") or 0.0
        shares = float(h.get("shares", 0.0))
        if close <= 0 or shares <= 0:
            print(f"Warning: skipping {t} (missing quote or zero shares).", file=sys.stderr)
            continue
        avg_cost = float(h.get("avg_cost_thb") or h.get("avg_cost_usd", 0.0))
        total_cost = float(h.get("total_cost_thb") or h.get("total_cost_usd", shares * avg_cost))
        current_val = shares * close
        unrealized_pl = current_val - total_cost
        unrealized_pl_pct = (unrealized_pl / total_cost * 100.0) if total_cost > 0 else 0.0

        if unrealized_pl < 0:
            rec = analyze_recovery(t, custom_shares=shares, custom_cost=avg_cost, portfolio_path=portfolio_path)
            if base_currency == "THB":
                rec["loss_thb"] = abs(unrealized_pl)
                rec["loss_usd"] = abs(unrealized_pl) / fx_rate
                total_underwater_loss_thb += abs(unrealized_pl)
                total_underwater_loss_usd += abs(unrealized_pl) / fx_rate
            else:
                rec["loss_usd"] = abs(unrealized_pl)
                rec["loss_thb"] = abs(unrealized_pl) * fx_rate
                total_underwater_loss_usd += abs(unrealized_pl)
                total_underwater_loss_thb += abs(unrealized_pl) * fx_rate

            if t in all_catalysts:
                rec["catalysts"] = all_catalysts[t]
            underwater_list.append(rec)

    underwater_list.sort(key=lambda x: x["unrealized_pl_pct"])

    return {
        "portfolio_name": portfolio.get("portfolio_name", "Portfolio"),
        "base_currency": base_currency,
        "curr_sym": curr_sym,
        "fx_rate": fx_rate,
        "total_underwater_count": len(underwater_list),
        "total_underwater_loss_usd": total_underwater_loss_usd,
        "total_underwater_loss_thb": total_underwater_loss_thb,
        "positions": underwater_list
    }


def generate_single_report(res: Dict[str, Any]) -> str:
    """
    Format single stock recovery analysis into a beginner-friendly 360-degree report.
    """
    t = res["ticker"]
    c = res["close"]
    avg = res["avg_cost"]
    be_pct = res["pct_to_breakeven"]
    pl_pct = res["unrealized_pl_pct"]
    pl_usd = res["unrealized_pl"]
    sma20 = res["sma20"]
    sma50 = res["sma50"]
    sl = res["hard_stop_loss"]
    f = res["fundamentals"]
    cat = res["catalysts"]

    curr_sym = res.get("curr_sym", "฿" if res.get("base_currency") == "THB" else "$")
    curr_code = res.get("base_currency", "USD")

    rev_g_str = f"{f['rev_growth_yoy']:+.1f}%" if f.get('rev_growth_yoy') is not None else "-"
    net_g_str = f"{f['net_inc_growth_yoy']:+.1f}%" if f.get('net_inc_growth_yoy') is not None else "-"
    be_str = f"+{be_pct:.1f}%" if be_pct > 0 else f"{be_pct:.1f}%"

    lines = [
        f"# 🧗 แผนกลยุทธ์แก้หลุดดอยเจาะลึก 360 องศา: {t} ({res['name']})",
        f"*วิเคราะห์ข้อมูลราคาจริงจาก TradingView ณ ราคาตลาด {curr_sym}{c:.2f} {curr_code}*",
        "",
        "---",
        "",
        "## 👶 1. สรุปภาษาคน สำหรับมือใหม่ (Beginner Layman Verdict)",
        "",
        f"- **สรุปอาการติดลบตอนนี้:** ขาดทุนอยู่ที่ {pl_pct:.2f}% (เงินหายไป {curr_sym}{abs(pl_usd):,.2f} {curr_code}). ต้องการแรงดีดกลับ {be_str} เพื่อคืนทุนเดิมที่ {curr_sym}{avg:.2f} {curr_code}.",
        f"- **สุขภาพของธุรกิจ:** {f['quality_tier']}. รายได้ YoY {rev_g_str}, กำไรสุทธิ YoY {net_g_str}.",
        f"- **คำแนะนำแบบเข้าใจง่ายทันที:** {res['layman_action']}",
        "",
        "---",
        "",
        "## ⚖️ 2. ตาชั่งข่าวดี vs ข่าวร้าย (Bullish Catalysts vs Bearish Risks)",
        ""
    ]

    # Bullish items
    lines.append("### 🟢 ข่าวดีและปัจจัยบวก (Good News & Upside Drivers):")
    if cat.get("bullish"):
        for it in cat["bullish"]:
            title_link = f"[{it['title']}]({it['link']})" if it.get("link") else it["title"]
            lines.append(f"- **[{it['source']}]** {title_link} *({it['published']})*")
    else:
        lines.append("- ยังไม่มีหัวข้อข่าวเชิงบวกเด่นชัดในรอบสัปดาห์นี้.")
    lines.append(f"- ปัจจัยพื้นฐาน: รายได้เติบโต YoY {rev_g_str}, นักวิเคราะห์ให้มุมมอง {f['rec_label']}.")

    # Bearish items
    lines.append("\n### 🔴 ข่าวร้ายและความเสี่ยงที่ต้องระวัง (Bad News & Downside Risks):")
    if cat.get("bearish"):
        for it in cat["bearish"]:
            title_link = f"[{it['title']}]({it['link']})" if it.get("link") else it["title"]
            lines.append(f"- **[{it['source']}]** {title_link} *({it['published']})*")
    else:
        lines.append("- ไม่พบหัวข้อข่าวเชิงลบรุนแรงในรอบสัปดาห์นี้.")
    
    if res["is_earnings_imminent"]:
        lines.append(f"- ⚠️ **ความเสี่ยงวันประกาศงบ:** บริษัทมีกำหนดประกาศงบในอีก **{res['days_to_earnings']} วัน ({res['earnings_date_str']})** มีความเสี่ยงราคาเหวี่ยงแรง.")

    # Institutional Price Targets section
    if res.get("price_target_average"):
        b_cnt = res.get("rec_buy") or 0
        h_cnt = res.get("rec_hold") or 0
        s_cnt = res.get("rec_sell") or 0
        comp_txt = ""
        if res.get("target_vs_cost_pct") is not None:
            if res["target_vs_cost_pct"] > 0:
                comp_txt = f"ราคาเป้าหมายเฉลี่ยของสถาบัน **สูงกว่าทุนของคุณ ({curr_sym}{avg:.2f}) ถึง +{res['target_vs_cost_pct']:.1f}%**. สถาบันมองว่าราคามีศักยภาพดีดทะลุต้นทุนเดิมของคุณได้."
            else:
                comp_txt = f"ราคาเป้าหมายเฉลี่ยของสถาบัน **ต่ำกว่าทุนของคุณ ({curr_sym}{avg:.2f}) อยู่ {abs(res['target_vs_cost_pct']):.1f}%**. สถาบันมองว่าราคาอาจยังไม่กลับไปแตะทุนเดิมในระยะ 1 ปี ควรใช้แผน Rebound Exit หรือโยกเงินทุน."

        lines.extend([
            "",
            "---",
            "",
            "## 🎯 3. การเปรียบเทียบต้นทุนของคุณกับราคาเป้าหมายสถาบัน (Institutional Targets)",
            "",
            f"- **ต้นทุนเฉลี่ยของคุณ:** **{curr_sym}{avg:.2f} {curr_code}**.",
            f"- **ราคาตลาดปัจจุบัน:** **{curr_sym}{c:.2f} {curr_code}** (ต้องการดีดกลับ **{be_str}** เพื่อคืนทุน).",
            f"- **ราคาเป้าหมายเฉลี่ยที่สถาบันให้:** **{curr_sym}{res['price_target_average']:,.2f} {curr_code}** (โอกาสเติบโต Upside **{res['target_upside_pct']:+.1f}%** จากราคาปัจจุบัน).",
            (f"- **กรอบราคาต่ำสุด ถึง สูงสุดที่สถาบันประเมิน:** **{curr_sym}{res['price_target_low']:,.2f} - {curr_sym}{res['price_target_high']:,.2f} {curr_code}**." if res.get('price_target_low') is not None and res.get('price_target_high') is not None else "- **กรอบราคาต่ำสุด ถึง สูงสุดที่สถาบันประเมิน:** -"),
            f"- **ฉันทามตินักวิเคราะห์:** **{b_cnt} สถาบันแนะนำซื้อ**, **{h_cnt} สถาบันแนะนำถือ**, **{s_cnt} สถาบันแนะนำขาย**.",
            f"- **บทสรุปเปรียบเทียบกับทุนของคุณ:** {comp_txt}",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## 📌 4. ข้อมูลสถานะการถือครองและเทคนิคอล",
        "",
        f"- จำนวนหุ้นที่ถือ: {res['shares']:.4f} หุ้น.",
        f"- ต้นทุนเฉลี่ย: {curr_sym}{avg:.2f} {curr_code} (เงินลงทุนรวม {curr_sym}{res['total_cost']:.2f} {curr_code}).",
        f"- มูลค่าตลาดปัจจุบัน: {curr_sym}{res['current_val']:.2f} {curr_code}.",
        f"- กำไร/ขาดทุนที่ยังไม่รับรู้: {curr_sym}{pl_usd:+.2f} {curr_code} ({pl_pct:+.2f}%).",
        f"- ดัชนีโมเมนตัม RSI: {res['rsi']}.",
        f"- แนวรับสำคัญ (Key Support): **{curr_sym}{res['key_support']:.2f} {curr_code}** ({res['support_desc']}).",
        f"- จุดตัดขาดทุนรักษาเงินต้น (Hard Stop-Loss): **{curr_sym}{sl:.2f} {curr_code}** (หลุดต้องลดพอร์ต).",
        f"- แนวต้านสั้น (SMA 20): **{curr_sym}{sma20:.2f} {curr_code}**.",
        f"- แนวต้านใหญ่ (Key Resistance): **{curr_sym}{res['key_resistance']:.2f} {curr_code}** ({res['resistance_desc']}).",
        "",
        "---",
        "",
        "## 🛠️ 5. แผนปฏิบัติการแก้ขาดทุนจริง 4 ทางเลือก (Actionable Playbooks)",
        "",
        "### ทางเลือกที่ 1: การรอจังหวะดีดตัวทางเทคนิคเพื่อลดพอร์ต (Rebound Exit - ไม่เติมเงินใหม่)",
        f"- **ความเหมาะสม:** {'แนะนำเป็นแผนหลัก' if res['primary_playbook'] == 'Rebound Exit' else 'ทางเลือกเสริม'}.",
        f"- **แนวปฏิบัติ:** ทุนเฉลี่ยเดิมอยู่ที่ {curr_sym}{avg:.2f} เทียบกับแนวต้าน SMA 20 ({curr_sym}{sma20:.2f}). หากราคาดีดตัวทดสอบแนวต้านให้ทยอยขายคืนทุนเพื่อดึงเงินสดกลับมา.",
        "",
        "### ทางเลือกที่ 2: การถัวเฉลี่ยเชิงกลยุทธ์ (Smart DCA เมื่อคอนเฟิร์มฐาน)",
        f"- **สถานะสิทธิ์การถัว:** {'✅ อนุญาตให้ถัวได้เมื่อเกิดสัญญาณกลับตัว' if res['dca_permitted'] else '⛔ ห้ามเติมเงินถัวเด็ดขาดในจังหวะนี้'}.",
        f"- **ราคาแนวรับที่ควรตั้งซื้อ:** **{curr_sym}{res['key_support']:.2f} {curr_code}** ({res['support_desc']}).",
    ])

    if res['is_earnings_imminent']:
        lines.append(f"- **คำเตือนความเสี่ยงวันงบ:** งบการเงินจะประกาศในอีก {res['days_to_earnings']} วัน. การซื้อถัวก่อนงบมีความเสี่ยงเกิด Gap Down รุนแรง. ต้องรอให้งบออกและตลาดซึมซับข่าวก่อน.")
    elif res['fundamentals']['quality_score'] == 1:
        lines.append("- **เหตุผลที่ห้ามถัว:** กำไรสุทธิของบริษัทยังหดตัวหนัก. การถัวเฉลี่ยในหุ้นที่พื้นฐานอ่อนแอจะกลายเป็นการติดกับดักมูลค่า (Value Trap).")
    else:
        lines.append("- **เงื่อนไขสำคัญก่อนเข้าซื้อ:** รอให้เกิดแท่งเทียนเขียว Daily ปิดเหนือราคาเปิด และเส้น Stoch RSI %K ตัดขึ้นเหนือ %D ก่อนเสมอ.")

    lines.extend([
        f"- **สูตรซื้อเพิ่ม 50%:** ซื้อเพิ่ม {res['dca_half']['shares_to_buy']:.4f} หุ้น (เงินทุน {curr_sym}{res['dca_half']['cash_needed_usd']:,.2f} {curr_code}). ทุนเฉลี่ยใหม่จะลดเหลือ **{curr_sym}{res['dca_half']['new_avg_cost']:.2f} {curr_code}** (ต้องการรีบาวด์เพียง **{res['dca_half']['new_breakeven_gain_pct']:+.1f}%** เพื่อคืนทุน).",
        f"- **สูตรซื้อเพิ่ม 100%:** ซื้อเพิ่ม {res['dca_equal']['shares_to_buy']:.4f} หุ้น (เงินทุน {curr_sym}{res['dca_equal']['cash_needed_usd']:,.2f} {curr_code}). ทุนเฉลี่ยใหม่จะลดเหลือ **{curr_sym}{res['dca_equal']['new_avg_cost']:.2f} {curr_code}** (ต้องการรีบาวด์เพียง **{res['dca_equal']['new_breakeven_gain_pct']:+.1f}%** เพื่อคืนทุน).",
        "",
        "### ทางเลือกที่ 3: การโยกย้ายเงินทุนไปหาหุ้นผู้นำขาขึ้น (Capital Rotation)",
        f"- **หลักการ:** หากตัดสินใจตัดขาดทุน {curr_sym}{abs(pl_usd):,.2f} {curr_code} แล้วนำเงินสดที่เหลือ {curr_sym}{res['current_val']:,.2f} {curr_code} ไปเข้าหุ้น Dip ขาขึ้นที่เข้าเกณฑ์ `/dip` (เช่น หุ้นที่มี R:R ≥ 2.0x).",
        f"- **เป้าหมายคืนทุน:** หุ้นตัวใหม่ต้องการอัตราผลตอบแทนเพียง **+{res['gain_pct_needed_on_rotation']:.1f}%** เพื่อกู้เงินต้นที่ขาดทุนไปกลับมาทั้งหมด.",
        "",
        "### ทางเลือกที่ 4: การตั้งจุดยอมจำนนเด็ดขาด (Cut Loss Guard)",
        f"- **ระดับราคาตัดขาดทุน:** {curr_sym}{sl:.2f} {curr_code}.",
        f"- **เหตุผล:** หากราคาหลุดกรอบความผันผวน 1.5 ATR แสดงว่าแรงขายยังไม่สิ้นสุด. การตัดขาดทุนจะช่วยรักษาเงินก้อนใหญ่ไว้ไม่ให้ลุกลาม.",
        "",
        "---",
        "### ⚠️ ข้อสงวนสิทธิ์และความเสี่ยง (Risk Disclaimer)",
        "รายงานนี้สร้างขึ้นโดยระบบวิเคราะห์ข้อมูลอัตโนมัติจากข้อมูลตลาดสาธารณะ เพื่อเป็นข้อมูลประกอบการตัดสินใจและให้ความรู้เท่านั้น ไม่ใช่คำแนะนำในการลงทุน ซื้อ หรือขายหลักทรัพย์ ผู้ลงทุนต้องศึกษาข้อมูล ทำความเข้าใจความเสี่ยง และใช้วิจารณญาณของตนเองก่อนการตัดสินใจลงทุนทุกครั้ง."
    ])

    return "\n".join(lines)


def generate_portfolio_recovery_report(summary: Dict[str, Any]) -> str:
    """
    Format all underwater portfolio holdings into an actionable multi-dimensional dashboard.
    """
    curr_sym = summary.get("curr_sym", "฿" if summary.get("base_currency") == "THB" else "$")
    curr_code = summary.get("base_currency", "USD")
    if curr_code == "THB":
        loss_header = f"**ยอดขาดทุนรวมที่ยังไม่รับรู้:** -฿{summary['total_underwater_loss_thb']:,.2f} THB"
    else:
        loss_header = f"**ยอดขาดทุนรวมที่ยังไม่รับรู้:** -${summary['total_underwater_loss_usd']:,.2f} USD (-฿{summary['total_underwater_loss_thb']:,.2f} THB)"

    lines = [
        "# 🚑 แดชบอร์ดวิเคราะห์แก้ติดลบในพอร์ตโฟลิโอ 360 องศา (Portfolio Recovery Dashboard)",
        f"**พอร์ต:** {summary['portfolio_name']} | **หุ้นติดลบทั้งหมด:** {summary['total_underwater_count']} ตัว",
        loss_header,
        "",
        "---",
        "",
        "## 📊 1. ตารางเปรียบเทียบสภาวะหุ้นติดลบและแผนปฏิบัติการ",
        "",
        "| Ticker | บริษัทและลักษณะธุรกิจ | ทุน / ตลาด | ขาดทุน (%) | แนวรับ / แนวต้าน | ดีดคืนทุน | เป้าหมายสถาบัน (Upside) | งบการเงิน (YoY) | ปฏิทินงบ | แผนแนะนำที่ปฏิบัติได้จริง |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |"
    ]

    for p in summary["positions"]:
        t = p["ticker"]
        name = p["name"][:14]
        biz = p.get("business_summary", "")
        c = p["close"]
        avg = p["avg_cost"]
        loss_pct = p["unrealized_pl_pct"]
        loss_usd = p["unrealized_pl"]
        loss_thb = p.get("loss_thb", abs(loss_usd) * summary["fx_rate"])
        be_gap = p["pct_to_breakeven"]
        f = p["fundamentals"]
        earnings_str = f"{p['days_to_earnings']}d" if p['days_to_earnings'] is not None else "-"
        if p["is_earnings_imminent"]:
            earnings_str = f"⚠️ **{earnings_str}**"

        rev_g = f"{f['rev_growth_yoy']:+.0f}%" if f['rev_growth_yoy'] is not None else "-"
        net_g = f"{f['net_inc_growth_yoy']:+.0f}%" if f['net_inc_growth_yoy'] is not None else "-"
        fund_str = f"Rev {rev_g}<br>Net {net_g}"

        t_avg = f"{curr_sym}{p['price_target_average']:.2f}" if p.get('price_target_average') else "-"
        t_up = f"({p['target_upside_pct']:+.0f}%)" if p.get('target_upside_pct') is not None else ""
        target_col = f"🎯 {t_avg}<br><small>{t_up}</small>" if p.get('price_target_average') else "-"
        supp_res_col = f"รับ {curr_sym}{p['key_support']:.2f}<br>ต้าน {curr_sym}{p['key_resistance']:.2f}"

        lines.append(
            f"| **[{t}](https://www.tradingview.com/chart/?symbol={p['exchange']}:{t})** | {name}<br><small>*{biz}*</small> | {curr_sym}{avg:.2f}<br>{curr_sym}{c:.2f} | **{loss_pct:.1f}%** | {supp_res_col} | **+{be_gap:.1f}%** | {target_col} | <small>{fund_str}</small> | {earnings_str} | <small>{p['action_verdict']}</small> |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## ⚖️ 2. ตาชั่งข่าวดี vs ข่าวร้ายของหุ้นติดลบ (Bullish Catalysts vs Bearish Risks)",
        ""
    ])

    for p in summary["positions"]:
        t = p["ticker"]
        cat = p.get("catalysts", {})
        lines.append(f"### • [{t}] {p['name']} (*{p.get('business_summary', '')}*)")
        
        # Bullish
        lines.append("**🟢 ข่าวดีและปัจจัยบวก (Good News & Upside Drivers):**")
        if cat.get("bullish"):
            for item in cat["bullish"]:
                title_link = f"[{item['title']}]({item['link']})" if item.get("link") else item["title"]
                lines.append(f"- **[{item['source']}]** {title_link} *({item['published']})*")
        else:
            lines.append("- ยังไม่มีหัวข้อข่าวเชิงบวกเด่นชัดในรอบสัปดาห์นี้.")
        p_rev = f"{p['fundamentals']['rev_growth_yoy']:+.1f}%" if p['fundamentals'].get('rev_growth_yoy') is not None else "-"
        lines.append(f"- การเติบโตของรายได้ YoY {p_rev}, นักวิเคราะห์ {p['fundamentals']['rec_label']}.")

        # Bearish
        lines.append("\n**🔴 ข่าวร้ายและความเสี่ยง (Bad News & Downside Risks):**")
        if cat.get("bearish"):
            for item in cat["bearish"]:
                title_link = f"[{item['title']}]({item['link']})" if item.get("link") else item["title"]
                lines.append(f"- **[{item['source']}]** {title_link} *({item['published']})*")
        else:
            lines.append("- ไม่พบหัวข้อข่าวเชิงลบรุนแรงในรอบสัปดาห์นี้.")

        if p.get("price_target_average"):
            b_cnt = p.get('rec_buy') or 0
            h_cnt = p.get('rec_hold') or 0
            s_cnt = p.get('rec_sell') or 0
            lines.append("**🎯 มุมมองราคาเป้าหมายจากสถาบันการเงิน (Wall Street Targets):**")
            lines.append(
                f"- ราคาเฉลี่ยที่สถาบันให้: **{curr_sym}{p['price_target_average']:,.2f}** "
                f"(โอกาสทำกำไร Upside: **{p['target_upside_pct']:+.1f}%** จากราคาตลาด {curr_sym}{p['close']:.2f})."
            )
            if p.get('price_target_low') is not None and p.get('price_target_high') is not None:
                lines.append(
                    f"- กรอบราคาต่ำสุด ถึง สูงสุดที่สถาบันประเมิน: **{curr_sym}{p['price_target_low']:,.2f} - {curr_sym}{p['price_target_high']:,.2f}**."
                )
            lines.append(
                f"- มตินักวิเคราะห์: **{b_cnt} สถาบันแนะนำซื้อ**, **{h_cnt} สถาบันแนะนำถือ**, **{s_cnt} สถาบันแนะนำขาย**."
            )
            if p.get("target_vs_cost_pct") is not None:
                if p["target_vs_cost_pct"] > 0:
                    lines.append(f"- **เปรียบเทียบกับทุนของคุณ:** ราคาเป้าหมายเฉลี่ยสถาบัน **สูงกว่าทุนของคุณ ({curr_sym}{p['avg_cost']:.2f}) ถึง +{p['target_vs_cost_pct']:.1f}%**. สถาบันมองว่าราคาจะสามารถกลับขึ้นไปทะลุต้นทุนเดิมของคุณได้.")
                else:
                    lines.append(f"- **เปรียบเทียบกับทุนของคุณ:** ราคาเป้าหมายเฉลี่ยสถาบัน **ต่ำกว่าทุนของคุณ ({curr_sym}{p['avg_cost']:.2f}) อยู่ {abs(p['target_vs_cost_pct']):.1f}%**. สถาบันมองว่าราคายังขึ้นไปไม่ถึงทุนเดิมใน 1 ปี ควรใช้แผน Rebound Exit หรือโยกเงิน.")

        if p["is_earnings_imminent"]:
            lines.append(f"- ⚠️ **วันประกาศงบการเงินใกล้เข้ามา:** อีก **{p['days_to_earnings']} วัน ({p['earnings_date_str']})** มีความเสี่ยง Gap รุนแรง.")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## 🧭 3. สรุปขั้นตอนปฏิบัติการกู้พอร์ตรายตัวตามลำดับความสำคัญ",
        ""
    ])

    for idx, p in enumerate(summary["positions"], 1):
        t = p["ticker"]
        avg = p["avg_cost"]
        be_gap = p["pct_to_breakeven"]
        sl = p["hard_stop_loss"]
        sma20 = p["sma20"]
        f = p["fundamentals"]

        # Emergency Triage & Recommended choice
        if p["is_earnings_imminent"]:
            triage_badge = "🔴 ดอยอันตราย (วันงบออกใกล้มาก ห้ามถัวเด็ดขาด)"
            recommended_choice = "ทางเลือกที่ 1 (ถือรอเฉยๆ) ห้ามเติมเงินก่อนวันงบออกเด็ดขาด"
        elif f.get("net_inc_growth_yoy") is not None and f["net_inc_growth_yoy"] < -10.0:
            triage_badge = "🔴 ดอยอันตราย (กำไรหดตัวแรง ห้ามถัวเด็ดขาด)"
            recommended_choice = "ทางเลือกที่ 3 (สลับตัวกู้พอร์ต) ย้ายเงินไปเข้าหุ้นผู้นำตัวอื่นเพื่อดึงทุนคืน"
        elif p["dca_permitted"]:
            triage_badge = "🟡 ดอยปานกลาง (พื้นฐานแกร่ง กราฟมีโซนรับ)"
            recommended_choice = f"ทางเลือกที่ 2 (Smart DCA) ซื้อเพิ่มที่แนวรับเพื่อดึงทุนลงเหลือ {curr_sym}{p['dca_half']['new_avg_cost']:.2f}"
        else:
            triage_badge = "🟢 ดอยชั่วคราว (รอราคาเด้งกลับ)"
            tvc = p.get("target_vs_cost_pct")
            if tvc is None:
                recommended_choice = "ทางเลือกที่ 1 (ถือรอเฉยๆ) ยังไม่มีข้อมูลราคาเป้าหมายสถาบันเทียบต้นทุนของคุณ"
            elif tvc >= 0:
                recommended_choice = "ทางเลือกที่ 1 (ถือรอเฉยๆ) ราคาเป้าหมายสถาบันอยู่สูงกว่าต้นทุนเดิมของคุณ"
            else:
                recommended_choice = "ทางเลือกที่ 1 (ถือรอเฉยๆ) แต่ราคาเป้าหมายสถาบันยังต่ำกว่าต้นทุนเดิมของคุณ"

        target_info = f" สถาบันให้เป้าหมายเฉลี่ย {curr_sym}{p['price_target_average']:,.2f} (Upside {p['target_upside_pct']:+.1f}%, เทียบทุนคุณ {p['target_vs_cost_pct']:+.1f}%)." if p.get('price_target_average') else " ไม่มีข้อมูลเป้าหมาย."

        f_rev = f"{f['rev_growth_yoy']:+.1f}%" if f.get('rev_growth_yoy') is not None else "-"
        f_net = f"{f['net_inc_growth_yoy']:+.1f}%" if f.get('net_inc_growth_yoy') is not None else "-"

        lines.extend([
            f"### {idx}. [{t}] {p['name']} (ติดลบ {p['unrealized_pl_pct']:.1f}%)",
            f"- **ระดับความเร่งด่วน:** {triage_badge}",
            f"- **สรุปภาษาคน สำหรับมือใหม่:** {p['layman_action']}",
            f"- **คำตัดสินกลยุทธ์:** **{p['action_verdict']}**",
            f"- **ระยะทางคืนทุนเดิม:** ต้องการราคาดีดขึ้น {be_gap:+.1f}% แตะระดับ **{curr_sym}{avg:.2f} {curr_code}**.",
            f"- **แนวรับสำคัญ (Key Support):** **{curr_sym}{p['key_support']:.2f} {curr_code}** ({p['support_desc']}).",
            f"- **แนวต้านสำคัญ (Key Resistance):** **{curr_sym}{p['key_resistance']:.2f} {curr_code}** ({p['resistance_desc']}).",
            f"- **แนวรับยอมจำนน (Stop-Loss Guard):** **{curr_sym}{sl:.2f} {curr_code}** (หลุดจุดนี้ต้องลดพอร์ตทันที).",
            f"- **ราคาเป้าหมายสถาบัน:**{target_info}",
            f"- **การประเมินงบการเงิน:** รายได้ YoY {f_rev}, กำไรสุทธิ YoY {f_net}, นักวิเคราะห์ {f['rec_label']}.",
            "",
            "#### 📊 ตารางเปรียบเทียบ 3 ทางเลือกสำหรับหุ้นตัวนี้",
            "",
            "| ทางเลือก | แผนการปฏิบัติการ | เงินที่ต้องใช้เพิ่ม | จุดขายเป้าหมาย | ความเสี่ยงหลัก |",
            "| :--- | :--- | :---: | :---: | :--- |",
            f"| **1. ถือรอเฉยๆ (Hold)** | ไม่เติมเงิน รอราคาฟื้นตัวกลับหาทุนเดิม | {curr_sym}0.00 | **{curr_sym}{avg:.2f}** ({be_gap:+.1f}%) | เงินจมและเสียเวลา |",
            f"| **2. Smart DCA** | ซื้อเพิ่ม {p['dca_half']['shares_to_buy']:.4f} หุ้น ที่แนวรับ **{curr_sym}{p['key_support']:.2f}** ({p['support_desc']}) | **{curr_sym}{p['dca_half']['cash_needed_usd']:,.2f}** | **{curr_sym}{p['dca_half']['new_avg_cost']:.2f}** ({p['dca_half']['new_breakeven_gain_pct']:+.1f}%) | เสี่ยงขาดทุนเพิ่มหากหลุด SL |",
            f"| **3. สลับตัว (Rotation)** | ย้ายเงินที่เหลือ {curr_sym}{p['current_val']:,.2f} ไปเข้าหุ้น Dip | {curr_sym}0.00 | หุ้นใหม่กำไร **{p['gain_pct_needed_on_rotation']:+.1f}%** | เสี่ยงขายหมูหากตัวเดิมเด้ง |",
            "",
            f"👉 💡 **ทางเลือกที่แนะนำที่สุดสำหรับมือใหม่:** **{recommended_choice}**",
            ""
        ])

        if p["is_earnings_imminent"]:
            lines.append(f"- ⚠️ **คำเตือนวันประกาศงบ:** บริษัทมีกำหนดประกาศงบในอีก **{p['days_to_earnings']} วัน ({p['earnings_date_str']})** ให้ระงับการซื้อถัวเฉลี่ยเพื่อหลีกเลี่ยงความผันผวนของ Gap.")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## 📱 4. คู่มือการเปิดแอปไปตั้งคำสั่งจริง สำหรับมือใหม่ (Broker Execution Guide)",
        "",
        "1. **ประเภทคำสั่งที่ควรใช้ (Order Type):**",
        "   - ให้ใช้คำสั่งแบบ **Limit Order** (ระบุราคาที่ต้องการซื้อหรือขายเอง) เสมอ.",
        "   - **ห้ามใช้ Market Order** เด็ดขาด เพราะระบบจะจับคู่ที่ราคาตลาดทันที ซึ่งอาจได้ราคาแพงกว่าที่ตั้งใจไว้.",
        "",
        "2. **การตั้งจุดยอมแพ้ตัดขาดทุน (Stop Loss) ในแอป (Dime / InnovestX / IBKR):**",
        "   - เข้าไปที่เมนู Order Details ของหุ้นตัวที่ต้องการ แล้วเลือกประเภทคำสั่ง **Stop Limit** หรือ **Stop Loss**.",
        "   - ระบุราคา Trigger Price ตามค่า **Stop-Loss Guard** ที่ระบบคำนวณให้ เพื่อจำกัดความเสี่ยงอัตโนมัติหากตลาดผันผวนรุนแรง.",
        "",
        "3. **การตั้งเป้าหมายขายทำกำไร / เท่าทุน (Take Profit / Breakeven Order):**",
        "   - สามารถตั้งคำสั่งขายล่วงหน้า (Good 'Til Canceled - GTC) ไว้ที่ระดับราคาต้นทุนเดิม หรือราคา New Breakeven Cost หลังทำ Smart DCA.",
        "",
        "---",
        "",
        "## 📖 5. พจนานุกรมแปลศัพท์สำหรับคนติดดอยฉบับ 1 บรรทัด (Underwater Beginner Glossary)",
        "",
        "- **Breakeven Gap (+%):** อัตราผลตอบแทนที่ราคาหุ้นต้องวิ่งขึ้นจากราคาปัจจุบัน เพื่อให้เงินลงทุนของคุณกลับมาเท่าทุน 0%.",
        "- **Smart DCA:** การซื้อถัวเฉลี่ยเฉพาะที่แนวรับทางเทคนิคสำคัญเพื่อดึงต้นทุนลง ไม่ใช่การถัวมั่วซั่วตอนราคากำลังดิ่ง.",
        "- **Hard Stop Loss:** ระดับราคาแนวรับสุดท้ายที่หากหลุดลงไป แปลว่ากราฟเสียทรง ต้องยอมจำนนตัดขาดทุนเพื่อรักษาเงินต้น.",
        "- **Capital Rotation (การโยกเงิน):** การยอมตัดขาดทุนจากหุ้นที่พื้นฐานพัง เพื่อย้ายเงินไปลงทุนในหุ้นขาขึ้นตัวอื่นที่ทำกำไรชดเชยได้เร็วกว่า.",
        "- **Earnings Proximity (ระยะห่างวันประกาศงบ):** จำนวนวันก่อนที่บริษัทจะแถลงผลประกอบการ หากน้อยกว่า 14 วันถือเป็นเขตอันตราย.",
        "",
        "---",
        "### ⚠️ ข้อสงวนสิทธิ์และความเสี่ยง (Risk Disclaimer)",
        "รายงานนี้สร้างขึ้นโดยระบบวิเคราะห์ข้อมูลอัตโนมัติจากข้อมูลตลาดสาธารณะ เพื่อเป็นข้อมูลประกอบการตัดสินใจและให้ความรู้เท่านั้น ไม่ใช่คำแนะนำในการลงทุน ซื้อ หรือขายหลักทรัพย์ ผู้ลงทุนต้องศึกษาข้อมูล ทำความเข้าใจความเสี่ยง และใช้วิจารณญาณของตนเองก่อนการตัดสินใจลงทุนทุกครั้ง."
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Stock Recovery & Breakeven Strategy Analyzer")
    parser.add_argument("ticker", nargs="?", default=None, help="Stock ticker to analyze (default: all underwater holdings)")
    parser.add_argument("--file", "-f", type=str, default=None, help="Path to portfolio JSON file (default: data/portfolio.json)")
    parser.add_argument("--shares", type=float, default=None, help="Custom share quantity")
    parser.add_argument("--cost", type=float, default=None, help="Custom average cost")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--save-report", type=str, nargs="?", const="", default="", help="Save report to HTML or Markdown file (default: reports/portfolio_recovery.html, or reports/recovery_<TICKER>.md for a single ticker)")

    args = parser.parse_args()

    # Automatically set Thai recovery report name if Thai portfolio is specified
    if not args.save_report:
        if args.ticker:
            args.save_report = f"reports/recovery_{args.ticker.upper()}.md"
        elif args.file and ("set" in Path(args.file).name.lower() or "thai" in Path(args.file).name.lower()):
            args.save_report = "reports/portfolio_set_recovery.html"
        else:
            args.save_report = "reports/portfolio_recovery.html"

    if args.ticker:
        try:
            res = analyze_recovery(args.ticker, args.shares, args.cost, portfolio_path=args.file)
        except Exception as e:
            print(f"Error analyzing recovery for {args.ticker}: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            report = generate_single_report(res)
            print(report)
            if args.save_report:
                p = Path(args.save_report)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(report, encoding="utf-8")
                print(f"\nReport saved to: {p.resolve()}", file=sys.stderr)
    else:
        try:
            summary = analyze_all_underwater(portfolio_path=args.file)
        except Exception as e:
            print(f"Error analyzing underwater portfolio: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            report = generate_portfolio_recovery_report(summary)
            print(report)
            if args.save_report:
                p = Path(args.save_report)
                p.parent.mkdir(parents=True, exist_ok=True)
                if p.suffix.lower() == ".html":
                    html_content = generate_recovery_html(summary)
                    p.write_text(html_content, encoding="utf-8")
                else:
                    p.write_text(report, encoding="utf-8")
                print(f"\nReport saved to: {p.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    main()
